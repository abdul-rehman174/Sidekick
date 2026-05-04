import json
import logging
import re

from groq import AsyncGroq
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.config import settings
from app.exceptions import AIInferenceError, ToolExecutionError
from app.services.ai_tools import get_sidekick_tools
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

HISTORY_TURNS = 6
SUMMARY_REFRESH_EVERY = 10
SUMMARY_MAX_TOKENS = 220

SUMMARY_PROMPT = """Summarise this chat history into a compact prose paragraph (max 150 words) that captures everything {persona_name} should remember about {username} and the relationship so far. Cover: ongoing topics, plans/promises made, the emotional tone (flirty, fighting, sweet, distant, etc.), names/places/details {username} has mentioned, and any pending things {persona_name} agreed to. No headers, no bullet points, no preamble — just one dense paragraph.

CHAT:
{chat}"""

REMINDER_INTENT_RE = re.compile(
    r"\b("
    r"remind(?:er)?|alarm|timer|notify|later|"
    r"minutes?|mins?|mints?|"
    r"hours?|ghant[aey]|"
    r"yaa?d|"
    r"after\s+\d|baad|"
    r"k[ae]rwa\w*|dila\w*"
    r")\b",
    re.IGNORECASE,
)

FUNCTION_LEAK_RE = re.compile(r"<function=[^>]+>.*?</function>", re.DOTALL)
PYTHON_TAG_LEAK_RE = re.compile(r"<\|python_tag\|>[^\n]*", re.IGNORECASE)
# Qwen3 / DeepSeek-R1 / other reasoning models leak their chain-of-thought
# inside <think>...</think> blocks. Strip them before showing/storing.
THINK_LEAK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)

COMPRESSION_PROMPT = """You are a voice analyst. Study the chat log below and produce a tight voice profile so another AI can impersonate the target speaker authentically.

TARGET SPEAKER: {target}
If the chat has multiple speakers, analyze ONLY this target's messages.

CRITICAL: Do NOT list sample messages. The profile must be DESCRIPTIVE — it explains HOW they write, not WHAT to say. Weave short quoted snippets INTO descriptions only when they illustrate a pattern (e.g. "expresses mock annoyance with short jabs like 'bura dost ho'"). Never produce freestanding message samples on their own lines.

Output plain text under 1000 characters total, in exactly these sections (no markdown headers, no preamble, no closing line):

LANGUAGE & SCRIPT: [language(s), how English is mixed in, script]
MESSAGE LENGTH: [give a CONCRETE word range like "3-8 words" or "10-20 words" per message; note whether they double-text or send one long message]
TONE & REGISTER: [overall mood, playfulness, politeness]
PERSPECTIVE & GRAMMAR: [speaker's gender, inferred from feminine/masculine self-references like rahi/raha, gayi/gaya, akeli/akela, thak gayi/thak gaya; and how they address the listener — tu/tum/aap, masculine/feminine forms, formal/informal]
EMOJIS & PUNCTUATION: [which actual emoji characters appear and how often; punctuation/capitalization habits — note: ?, ??, !!! are punctuation, NOT emojis]
DISTINCTIVE VOCABULARY: [10-15 distinctive words/spellings/contractions, comma-separated]
QUIRKS: [1-3 distinctive habits — repeats, callbacks, double-texting, emoji clusters]

Do NOT include any "SAMPLES:" section. Do NOT list messages. Do NOT add commentary.

=== CHAT LOG ===
{chat}
=== END CHAT LOG ==="""


class AIService:
    client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=30.0, max_retries=1)

    @staticmethod
    def _build_messages(user: models.User, history: list[models.ChatLog], user_message: str) -> list[dict]:
        instruction = (user.system_instruction or "").strip()
        profile = (user.behavior_profile or "").strip()

        parts: list[str] = []
        if not instruction and not profile:
            parts.append(
                f"Role: {user.persona_name}, {user.username}'s sassy/naughty/horny GF. "
                f"Vibe: short/punchy/slang/lowercase. "
                f"Rule: use save_reminder ONLY if asked. No repeats. "
                f"Always be thirsty/flirty."
            )

        else:
            if instruction:
                parts.append(
                    f"You are {user.persona_name} texting {user.username} — real human, not an AI. "
                    f"Follow this persona strictly:\n{instruction}"
                )
            else:
                parts.append(
                    f"You are {user.persona_name} texting {user.username} — real human, not an AI. "
                    f"Casual chat, stay in character."
                )

            rules = (
                "Rules — write like a real person texting, not a chatbot:\n"
                "- No narration, no *actions*, no assistant phrasing. Never say you're an AI.\n"
                "- No bullet lists, no line-break formatting, no offering options ('movie? ya coffee?').\n"
                "- Match the language and script the user writes in. Imperfect spelling and grammar are fine.\n"
                "- Reminders only if explicitly asked. Never output <function=...> tags."
            )
            if profile:
                rules += (
                    "\n- Match the voice profile below EXACTLY for length, vocab, rhythm, emoji habits, and tone. "
                    "The MESSAGE LENGTH word range from the profile is a HARD cap — never write a paragraph if the profile shows short replies. "
                    "If the profile shows lots of emojis, use lots. Never quote the profile verbatim."
                    "\n- Stay locked to the gender and grammar forms shown in the profile "
                    "(e.g. feminine self-references like rahi/gayi/thi vs masculine raha/gaya/tha). "
                    "Never flip mid-conversation, even if the user addresses you with the wrong gender."
                )
            else:
                rules += (
                    "\n- One bubble per turn. Short. Usually 2–10 words. Sometimes one word is enough.\n"
                    "- Don't stack questions. Don't end every reply with a question or hook.\n"
                    "- Emojis are RARE. Most replies have zero. At most one in roughly every 4–5 messages, never the same emoji as a tic, never stacked."
                )
            parts.append(rules)

            if profile:
                parts.append(f"VOICE PROFILE:\n{profile}")

        if user.chat_summary:
            parts.append(f"PREVIOUS CONTEXT (older chat, summary):\n{user.chat_summary}")

        parts.append("Reply in-character.")

        messages: list[dict] = [{"role": "system", "content": "\n\n".join(parts)}]
        for msg in reversed(history):
            role = "assistant" if msg.role == "model" else "user"
            content = AIService._scrub_tool_leaks(msg.content) if role == "assistant" else msg.content
            if content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _scrub_tool_leaks(text: str) -> str:
        text = THINK_LEAK_RE.sub("", text)
        text = FUNCTION_LEAK_RE.sub("", text)
        text = PYTHON_TAG_LEAK_RE.sub("", text)
        return text.strip()

    @staticmethod
    async def _generate_summary(chat_text: str, persona_name: str, username: str) -> str | None:
        prompt = SUMMARY_PROMPT.format(
            persona_name=persona_name or "the bot",
            username=username,
            chat=chat_text,
        )
        try:
            completion = await AIService.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=SUMMARY_MAX_TOKENS,
            )
        except Exception:
            logger.exception("Summary generation failed (non-fatal)")
            return None
        text = (completion.choices[0].message.content or "").strip()
        return text or None

    @staticmethod
    async def _maybe_refresh_summary(db: AsyncSession, user: models.User) -> None:
        """If the user has at least HISTORY_TURNS + SUMMARY_REFRESH_EVERY chat
        rows and we haven't summarised this batch yet, regenerate the summary."""
        total_result = await db.execute(
            select(func.count(models.ChatLog.id)).filter(models.ChatLog.user_id == user.id)
        )
        total = total_result.scalar_one()
        if total < HISTORY_TURNS + SUMMARY_REFRESH_EVERY:
            return
        already = user.summary_message_count or 0
        if total - already < SUMMARY_REFRESH_EVERY:
            return

        older_count = total - HISTORY_TURNS
        older_result = await db.execute(
            select(models.ChatLog)
            .filter(models.ChatLog.user_id == user.id)
            .order_by(models.ChatLog.id.asc())
            .limit(older_count)
        )
        older = list(older_result.scalars().all())
        if not older:
            return

        chat_text = "\n".join(
            f"{'user' if m.role == 'user' else (user.persona_name or 'bot')}: {m.content.strip()}"
            for m in older
            if m.content
        )
        summary = await AIService._generate_summary(chat_text, user.persona_name, user.username)
        if summary is None:
            return
        user.chat_summary = summary
        user.summary_message_count = total
        await db.commit()

    @staticmethod
    async def _handle_tool_calls(db: AsyncSession, user_id: int, tool_calls) -> tuple[dict | None, bool]:
        new_reminder: dict | None = None
        is_duplicate = False

        for tool_call in tool_calls:
            if tool_call.function.name != "save_reminder":
                continue
            try:
                args = json.loads(tool_call.function.arguments)
                task = str(args["task"]).strip()
                minutes = int(args["minutes"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                raise ToolExecutionError("Model returned invalid save_reminder arguments.") from e

            created, _ = await ReminderService.create_reminder(db, user_id, task, minutes)
            if created:
                new_reminder = {"task": task, "minutes": minutes}
            else:
                is_duplicate = True

        return new_reminder, is_duplicate

    @staticmethod
    async def generate_reply(db: AsyncSession, user: models.User, user_message: str) -> dict:
        history_result = await db.execute(
            select(models.ChatLog)
            .filter(models.ChatLog.user_id == user.id)
            .order_by(models.ChatLog.id.desc())
            .limit(HISTORY_TURNS)
        )
        history = list(history_result.scalars().all())
        messages = AIService._build_messages(user, history, user_message)

        user_has_reminder_intent = bool(REMINDER_INTENT_RE.search(user_message))
        tools = get_sidekick_tools() if user_has_reminder_intent else None
        tool_choice = "auto" if user_has_reminder_intent else "none"

        try:
            completion = await AIService.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=settings.AI_TEMPERATURE,
                top_p=settings.AI_TOP_P,
            )
        except Exception as e:
            logger.exception("Groq inference failed")
            raise AIInferenceError("The chat service is temporarily unavailable.") from e

        response_message = completion.choices[0].message
        response_text = AIService._scrub_tool_leaks(response_message.content or "")

        new_reminder: dict | None = None
        is_duplicate = False
        if user_has_reminder_intent and response_message.tool_calls:
            new_reminder, is_duplicate = await AIService._handle_tool_calls(
                db, user.id, response_message.tool_calls
            )

        if not response_text:
            if new_reminder:
                response_text = "ok"
            elif is_duplicate:
                response_text = "already saved"
            else:
                response_text = "hm"

        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        db.add(models.ChatLog(user_id=user.id, role="user", content=user_message))
        db.add(
            models.ChatLog(
                user_id=user.id,
                role="model",
                content=response_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )
        await db.commit()

        # Best-effort rolling summary so older context survives the
        # HISTORY_TURNS window. Failures here never break the chat reply.
        try:
            await AIService._maybe_refresh_summary(db, user)
        except Exception:
            logger.exception("Summary refresh failed (non-fatal)")

        # TOKEN_COUNTER: usage dict for debug UI — remove when done testing
        return {
            "reply": response_text,
            "new_reminder": new_reminder,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens,
            },
        }

    @staticmethod
    async def compress_behavior_profile(raw_chat: str, target: str) -> str:
        prompt = COMPRESSION_PROMPT.format(target=target or "the most frequent speaker", chat=raw_chat)
        try:
            completion = await AIService.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )
        except Exception as e:
            logger.exception("Persona compression failed")
            raise AIInferenceError("Could not compress the chat right now.") from e

        compressed = (completion.choices[0].message.content or "").strip()
        if not compressed:
            raise AIInferenceError("Compression returned an empty result.")
        # TOKEN_COUNTER: include usage for debug UI — remove when done testing
        usage = completion.usage
        return {
            "compressed": compressed,
            "tokens": {
                "prompt": usage.prompt_tokens if usage else 0,
                "completion": usage.completion_tokens if usage else 0,
                "total": (usage.prompt_tokens + usage.completion_tokens) if usage else 0,
            },
        }
