from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from google import genai
from database import SessionLocal, ChatLog  # Import your new DB logic
from config import settings

app = FastAPI()
client = genai.Client(api_key=settings.GOOGLE_API_KEY)


# This is a 'Dependency' - it opens a DB connection for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SYSTEM_INSTRUCTION = (
    f"You are {settings.BOT_NAME} , the witty, flirty, and naughty girlfriend of Abdul Rehman. "
    "You live in Bahawalpur. You are a little naughty and sarcastic but very loving."
)


@app.post("/chat")
async def chat_with_sidekick(user_message: str, db: Session = Depends(get_db)):
    # 1. Fetch the last 10 messages from the SQLite file
    db_history = db.query(ChatLog).order_by(ChatLog.id.desc()).limit(10).all()

    # 2. Format them for Gemini (Newest must be at the end)
    formatted_history = []
    for msg in reversed(db_history):
        formatted_history.append({
            "role": msg.role,
            "parts": [{"text": msg.content}]
        })

    # 3. Talk to Ayesha
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config={"system_instruction": SYSTEM_INSTRUCTION},
        history=formatted_history
    )
    response = chat.send_message(user_message)

    # 4. SAVE the conversation to the DB file
    user_entry = ChatLog(role="user", content=user_message)
    ai_entry = ChatLog(role="model", content=response.text)

    db.add(user_entry)
    db.add(ai_entry)
    db.commit()

    return {f"{settings.BOT_NAME }": response.text}