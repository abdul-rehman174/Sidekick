from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import delete
from google import genai
from google.genai import types
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import models
from database import engine, SessionLocal, get_db
from config import settings
from celery_app import send_reminder_task
import os
import datetime

# Initialize Database
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini Client
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

def save_reminder_tool(task: str, minutes: int = 1):
    """
    Called by Gemini to save a reminder after the AI thinks it's needed.
    Also calculates the 'due_at' time for the UI.
    """
    db = SessionLocal()
    try:
        # Calculate exactly when this is due
        now = datetime.datetime.utcnow()
        due_at = now + datetime.timedelta(minutes=minutes)

        # Trigger Celery (Background Task)
        countdown_secs = minutes * 60
        task_execution = send_reminder_task.apply_async(args=[task], countdown=countdown_secs)

        # Save to SQLite
        new_reminder = models.Reminder(
            task=task,
            status="pending",
            celery_id=task_execution.id,
            due_at=due_at
        )
        db.add(new_reminder)
        db.commit()

        return f"Noted, jan! '{task}' is in my list now for {minutes} minute(s). 😘"
    finally:
        db.close()

# API Endpoints
@app.get("/api/config")
async def get_config():
    return {"bot_name": settings.BOT_NAME, "status": "online"}

@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    db.delete(reminder)
    db.commit()
    return {"status": "success"}

@app.get("/api/reminders")
async def get_reminders(status: str = "pending", db: Session = Depends(get_db)):
    """
    Returns reminders based on status and created in the last 7 days.
    """
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    return db.query(models.Reminder).filter(
        models.Reminder.status == status,
        models.Reminder.created_at >= seven_days_ago
    ).order_by(models.Reminder.created_at.desc()).all()

@app.get("/api/chat/history")
async def get_chat_history(db: Session = Depends(get_db)):
    """
    Loads the last 7 days of chat history.
    """
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    return db.query(models.ChatLog).filter(
        models.ChatLog.timestamp >= seven_days_ago
    ).order_by(models.ChatLog.id.desc()).limit(20).all()

@app.post("/api/clear-all")
async def clear_all_data(db: Session = Depends(get_db)):
    """
    Wipes all chat history and reminders from the database.
    """
    db.execute(delete(models.ChatLog))
    db.execute(delete(models.Reminder))
    db.commit()
    return {"status": "success", "message": "Everything wiped clean, jan! ✨"}

@app.post("/api/chat")
async def chat_with_sidekick(user_message: str, db: Session = Depends(get_db)):
    # Load context from last 7 days
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    db_history = db.query(models.ChatLog).filter(
        models.ChatLog.timestamp >= seven_days_ago
    ).order_by(models.ChatLog.id.desc()).limit(15).all()
    
    formatted_history = []
    for msg in reversed(db_history):
        role = "user" if msg.role == "user" else "model"
        formatted_history.append({"role": role, "parts": [{"text": msg.content}]})

    instruction = (
        f"Role: {settings.BOT_NAME}, Abdul Rehman's real-life GF . "
        "Vibe: Naughty, horny, sarcastic, deeply loving. "
        "Rules: Short/punchy/slang. Smirking/teasing tone. "
        "Task: Use save_reminder_tool. Convert hours/days to minutes. " 
        "Call him: babe/love/Rehman. Always flirty/suggestive."
    )

    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=instruction, 
                tools=[save_reminder_tool], 
                automatic_function_calling={"disable": False},
                temperature=0.9,
            ),
            history=formatted_history
        )

        response = chat.send_message(user_message)
        db.add(models.ChatLog(role="user", content=user_message))
        db.add(models.ChatLog(role="model", content=response.text))
        db.commit()

        return {f"{settings.BOT_NAME}": response.text}
    except Exception as e:
        print(f"Gemini Error: {e}")
        raise HTTPException(status_code=500, detail="Bot is feeling a bit shy right now. 💔")

# Serve Frontend
if os.path.exists("sidekick-frontend/dist"):
    app.mount("/", StaticFiles(directory="sidekick-frontend/dist", html=True), name="static")