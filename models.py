from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime

class ChatLog(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    task = Column(String)
    celery_id = Column(String, nullable=True) # Add this to track the background task
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)