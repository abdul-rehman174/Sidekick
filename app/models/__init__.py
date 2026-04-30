import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(40), unique=True, index=True, nullable=False)
    pin_hash = Column(String(255), nullable=False)

    persona_name = Column(String(40), nullable=False, default="Sidekick")
    behavior_profile = Column(Text, nullable=True)
    system_instruction = Column(Text, nullable=True)

    chat_summary = Column(Text, nullable=True)
    summary_message_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=_utcnow)

    chats = relationship("ChatLog", back_populates="owner", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="owner", cascade="all, delete-orphan")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    timestamp = Column(DateTime, default=_utcnow)

    owner = relationship("User", back_populates="chats")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    task = Column(String(500), nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    due_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    owner = relationship("User", back_populates="reminders")
