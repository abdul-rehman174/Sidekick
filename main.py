from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from google import genai
from database import SessionLocal, ChatLog
from config import settings

app = FastAPI()
client = genai.Client(api_key=settings.GOOGLE_API_KEY)


# 1. DEFINE THE TOOL (The 'Hand')
def save_reminder(task: str):
    """
    Saves a task or reminder for Abdul Rehman.
    Use this when he mentions things he needs to do or remember.
    """
    # For now, we print to console. In Phase 5, this triggers a Celery task.
    print(f"ALARM SET: {task}")
    return f"Don't worry, jan. I've noted down: '{task}'. I've got your back! 😘"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Tighter instruction to save tokens
SYSTEM_INSTRUCTION = (
    f"You are {settings.BOT_NAME}, Abdul Rehman's witty, flirty girlfriend from Bahawalpur. "
    "Keep replies under 3 sentences. Be sarcastic but loving and naughty and horny. "
    "If he mentions a task or reminder, use the save_reminder tool. "
)


@app.post("/chat")
async def chat_with_sidekick(user_message: str, db: Session = Depends(get_db)):
    db_history = db.query(ChatLog).order_by(ChatLog.id.desc()).limit(10).all()

    formatted_history = []
    for msg in reversed(db_history):
        formatted_history.append({
            "role": msg.role,
            "parts": [{"text": msg.content}]
        })

    # 2. REGISTER THE TOOL
    chat = client.chats.create(
        model="gemini-2.5-flash",  # Note: Ensure you use the 2.0-flash name from AI Studio
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": [save_reminder],  #
            "automatic_function_calling": {"disable": False}
        },
        history=formatted_history
    )

    response = chat.send_message(user_message)

    # 3. Persistence
    db.add(ChatLog(role="user", content=user_message))
    db.add(ChatLog(role="model", content=response.text))
    db.commit()

    return {f"{settings.BOT_NAME}": response.text}