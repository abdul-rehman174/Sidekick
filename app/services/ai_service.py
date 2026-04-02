import json
import re
from groq import Groq
from sqlalchemy.orm import Session
from app import models
from .ai_tools import get_sidekick_tools
from .reminder_service import ReminderService
from app.config import settings

class AIService:
    client = Groq(api_key=settings.GROQ_API_KEY)

    @staticmethod
    def generate_reply(db: Session, user, user_message: str):
        # 1. Intent Scanner: Is the user actually asking for a reminder? (v8.3 Physical Gating)
        intent_keywords = r"(remind|set|save|timer|alarm|minutes|min|hour|yaad|karwa|notify|task|item)"
        has_intent = re.search(intent_keywords, user_message.lower())
        
        # 2. Fetch History (Last 15 messages)
        history = db.query(models.ChatLog).filter(
            models.ChatLog.user_id == user.id
        ).order_by(models.ChatLog.id.desc()).limit(10).all()

        # 3. Build Messages
        system_content = (
            f"Role:{user.bot_name}, {user.username}'s sassy/flirty/horny GF. "
            f"Vibe:Short/punchy/slang/lowercase. "
            f"Rule:Use 'save_reminder' ONLY if asked. No repeats. "
            f"Always be thirsty/flirty. "
        )
        messages = [{"role": "system", "content": system_content}]
        
        # Professional Filtering (v8.3 Memory Cleanup): Skip redundant duplicate loops in context
        dup_marker = "already on top of that"
        for msg in reversed(history):
            if dup_marker in msg.content.lower(): continue # Skip the noise in history
            role = "assistant" if msg.role == "model" else "user"
            messages.append({"role": role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_message})

        # 4. Groq Call: Physical Tool Gating (v8.3)
        try:
            tools_param = get_sidekick_tools() if has_intent else None
            
            completion = AIService.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
            
            # CLEANING: Remove any technical tags from the final chat display
            response_text = re.sub(pattern, "", response_text).strip()

            # 6. [ZERO-FAILURE FALLBACK]: Ensure response_text is NEVER empty
            if not response_text:
                if new_reminder:
                    response_text = f"Right away jan. I've set your '{new_reminder['task']}'."
                elif is_duplicate:
                    response_text = f"Babe, I'm already set the reminder for you. 🫦"
                else:
                    response_text = f"I'm here, {user.username}. What's on your mind?"
            
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
            print(f"CRITICAL AI FAILURE: {e}")
            return {user.bot_name: "Internal error. The service is currently re-stabilizing.", "new_reminder": None}
