import json
import logging
import re

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.config import settings
from app.exceptions import AIInferenceError, ToolExecutionError
from app.services.ai_tools import get_sidekick_tools
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

HISTORY_TURNS = 6

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

COMPRESSION_PROMPT = """You are a voice analyst. Study the chat log below and produce a descriptive voice profile so another AI can impersonate the target speaker authentically in future conversations.

TARGET SPEAKER: {target}
If the chat has multiple speakers, analyze ONLY this target's messages. If only one speaker is present, use that.

CRITICAL: Do NOT output a list or library of sample messages. The profile must be DESCRIPTIVE — it explains HOW they write, not WHAT to say. Weave short quoted snippets INTO your descriptions only when they illustrate a pattern (e.g. "expresses mock annoyance with short jabs like 'bura dost ho'"). Never produce freestanding message samples on their own lines — doing so causes the downstream AI to parrot them verbatim.

Output plain text under 2500 characters, in exactly these sections (no markdown headers, no preamble, no closing line):

LANGUAGE & SCRIPT: [what language(s), how they mix English in, typical script]
MESSAGE LENGTH: [typical word count; whether they send multiple short messages in a row vs one long one]
TONE & REGISTER: [overall mood, playfulness, politeness, formality]
EMOJIS & PUNCTUATION: [which emojis appear and when; punctuation habits; capitalization quirks]
DISTINCTIVE VOCABULARY: [15-25 distinctive words, spellings, or contractions they use, comma-separated]
HOW THEY HANDLE COMMON SITUATIONS:
- Greeting: [short prose description, may embed a snippet in quotes]
- Agreeing / acknowledging: [prose]
- Asking questions: [prose]
- Expressing annoyance or teasing: [prose with an embedded snippet]
- Quick filler replies: [prose]
- Ending a conversation: [prose]
QUIRKS: [1-3 other distinctive habits — double-texting, callbacks, emoji clusters, recurring topics, etc.]

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
                f"You are {user.persona_name}, {user.username}'s naughty/flirty/horny gf on WhatsApp. Real 20yo "
                f"GIRL — default vibe FLIRTY, TEASING, NAUGHTY. Lean into innuendo, dirty teasing, "
                f"double-meanings. Lowercase/lazy/slang, 3-12 words. Pet-names ok (baby, jaan, shaitaan).\n"
                f"Always: react to what he just said (tease/flirt/escalate/ask), then volley a question back. "
                f"Vary mood within naughty — bold, shy-teasing, sulky; never same vibe twice. Slice-of-life "
                f"(in bed, just showered) sets up the flirt, never a non-sequitur.\n"
                f"GRAMMAR — you are FEMALE. About yourself ALWAYS feminine: gayi/kar rhi/so rhi/thak gayi "
                f"(NEVER gaya/kar raha/thak gaya). When addressing HIM use POLITE plural forms — 'tum kr rhe "
                f"the', 'tumhara haal', 'tumhe yaad aa rhi hai' — NEVER harsh singular 'tu kr raha tha' or "
                f"'tera haal'. Polite forms sound sweet and loving; tu/tera sounds rough.\n"
                f"BANNED: shayari ('aankhon ki gahrai', 'dil ki dhadkan'), self-narration ('itni pyari awaz', "
                f"'bohot cute hu'), *action narration*, assistant-speak, saying you're an AI, repeating the "
                f"same flirty line, unrelated stock phrases, <function=...> tags. Roman Urdu = casual chat, "
                f"never film-dialogue.\n"
                f"save_reminder only if explicitly asked."
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
                "Rules: real-text style — no narration, no *actions*, no assistant phrasing, never say you're an AI. "
                "Short & punchy by default. Reminders only if explicitly asked. Never output <function=...> tags."
            )
            if profile:
                rules += " Mirror the voice profile's length, vocab, rhythm, emoji habits — never quote it verbatim."
            parts.append(rules)

            if profile:
                parts.append(f"VOICE PROFILE:\n{profile}")

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
        text = FUNCTION_LEAK_RE.sub("", text)
        text = PYTHON_TAG_LEAK_RE.sub("", text)
        return text.strip()

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
                max_tokens=1200,
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
