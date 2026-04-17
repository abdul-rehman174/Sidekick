import json
import re
from groq import Groq
from sqlalchemy.orm import Session
from app import models
from .ai_tools import get_sidekick_tools
from .reminder_service import ReminderService
from app.config import settings
import random

class AIService:
    client = Groq(api_key=settings.GROQ_API_KEY)

    @staticmethod
    def scrub_ai_refusals(text: str, user):
        """Physical code-based scrub for AI hallucinations (v9.0)"""
        refusal_patterns = [
            r"I cannot (create|fulfill|comply|do|provide)",
            r"As an AI model",
            r"I am an artificial intelligence",
            r"language model",
            r"I'm sorry, (but|I can't)",
            r"I'm afraid I can't"
        ]
        for pattern in refusal_patterns:
            if re.search(pattern, text, re.I):
                # Replace with in-character, flirty teases that bypass the immersion break
                phrases = [
                    "Mm.. naughty boy. Let's take it a little slower first... 🫦",
                    "Oh you're bad... you'll have to try harder to get me to do that! 😘",
                    "Aha.. someone is eager. Let's just talk for now babe. 😏",
                    "I love when you talk like that, but I'm gonna make you wait a little bit. ✨"
                ]
                return random.choice(phrases)
        return text

    @staticmethod
    def generate_reply(db: Session, user, user_message: str):
        intent_keywords = r"(remind|set|save|timer|alarm|minutes|min|hour|yaad|karwa|notify|task|item)"
        has_intent = re.search(intent_keywords, user_message.lower())
        
        model_name = "llama-3.3-70b-versatile"

        # 3. Fetch History (Last 15 messages)
        history = db.query(models.ChatLog).filter(
            models.ChatLog.user_id == user.id
        ).order_by(models.ChatLog.id.desc()).limit(10).all()

        # 4. Build Messages (Immersion & Token Optimization v10.0)
        base_vibe = (
            f"You are {user.bot_name}, {user.username}'s horny AI girlfriend. "
            f"STRICT RULES: 1. EXTREMELY CONCISE (max 15 words). 2. WhatsApp text style only. "
            f"3. NO NARRATION of your body/actions. 4. Use very FEW emojis (max 1-2). "
        )
        
        if user.persona_training:
            system_content = base_vibe + f"DIALECT/SLANG MIRROR: {user.persona_training[:1500]}"
        else:
            system_content = base_vibe + "VIBE: Standard flirty/horny mode."
        
        system_content += " Never type function names. Never use formal AI refusals. Stay in character."
        
        messages = [{"role": "system", "content": system_content}]
        
        # Professional Filtering (v8.3 Memory Cleanup)
        dup_marker = "already on top of that"
        for msg in reversed(history):
            if dup_marker in msg.content.lower(): continue 
            role = "assistant" if msg.role == "model" else "user"
            messages.append({"role": role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_message})

        # 5. Groq Call: Physical Tool Gating (v8.3)
        try:
            tools_param = get_sidekick_tools() if has_intent else None
            
            completion = AIService.client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools_param,
                tool_choice="auto" if has_intent else "none"
            )
            
            response_message = completion.choices[0].message
            response_text = response_message.content or ""
            
            # 5. Robust Tool Extraction (v8.2 Professional Gating)
            new_reminder = None
            is_duplicate = False
            
            # A. Check Formal API Tool Calls (only if tools were provided)
            if has_intent and response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "save_reminder":
                        try:
                            args = json.loads(tool_call.function.arguments)
                            task_val = args.get("task")
                            min_val = int(args.get("minutes", 1))
                            success, _ = ReminderService.create_reminder(db, user.id, task_val, min_val)
                            
                            if success:
                                new_reminder = {"task": task_val, "minutes": min_val}
                            else:
                                is_duplicate = True
                        except Exception as e:
                            print(f"Tool parse error (formal): {e}")

            # B. Scrub Inline Hallucinations (v8.0 Self-Correction)
            pattern = r"<function=save_reminder>(.*?)</function>"
            matches = re.findall(pattern, response_text)
            for match in matches:
                # Still scrub if accidental, but only process if intent was there
                if has_intent and not new_reminder and not is_duplicate:
                    try:
                        args = json.loads(match)
                        task_val = args.get("task")
                        min_val = int(args.get("minutes", 1))
                        success, _ = ReminderService.create_reminder(db, user.id, task_val, min_val)
                        
                        if success:
                            new_reminder = {"task": task_val, "minutes": min_val}
                        else:
                            is_duplicate = True
                    except: pass
            
            # [NEW] Scrub Loose Inline Hallucinations (e.g. "save_reminder: task")
            inline_hallucination = r"(save_reminder|set_reminder|reminder):?\s?.*"
            response_text = re.sub(inline_hallucination, "", response_text, flags=re.I).strip()
            
            response_text = re.sub(pattern, "", response_text).strip()

            if not response_text:
                if new_reminder:
                    # Dynamic Style Fallback: Ask the AI for a short confirmation in the mirrored style
                    try:
                        fallback_messages = [
                            {"role": "system", "content": f"You just set a reminder for '{new_reminder['task']}'. Respond with a very short (1 sentence) sweet acknowledgment in this exact style: {user.persona_training if user.persona_training else 'sassy/flirty girlfriend'}."},
                        ]
                        fallback_completion = AIService.client.chat.completions.create(
                            model="llama3-8b-8192", # Use a faster model for the quick acknowledgment
                            messages=fallback_messages,
                            max_tokens=50
                        )
                        response_text = fallback_completion.choices[0].message.content.strip()
                    except:
                        # Physical Fallback if API fails
                        response_text = f"Got it, jan! I've set your '{new_reminder['task']}'. 🫦"
                elif is_duplicate:
                    response_text = f"Babe, I've already set that reminder for you. ❤️ "
                else:
                    response_text = f"I'm here, {user.username}. What's on your mind? 🫦"
            
            # Final Scrub: Move AI refusals to code (v9.0 Transition)
            response_text = AIService.scrub_ai_refusals(response_text, user)

            # 7. Atomic DB Commit with Usage Metrics (v8.6 Monitoring)
            usage = completion.usage
            p_tokens = usage.prompt_tokens if usage else 0
            c_tokens = usage.completion_tokens if usage else 0

            db.add(models.ChatLog(user_id=user.id, role="user", content=user_message))
            db.add(models.ChatLog(
                user_id=user.id, 
                role="model", 
                content=response_text,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens
            ))
            db.commit()

            return {user.bot_name: response_text, "new_reminder": new_reminder}

        except Exception as e:
            db.rollback()
            print(f"CRITICAL AI FAILURE: {e}")
            return {user.bot_name: "Internal error. The service is currently re-stabilizing.", "new_reminder": None}
