from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# This is the "Connection String"
DATABASE_URL = "sqlite:///./sidekick.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# This is your Schema
class ChatLog(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # "user" or "model"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# This line is what actually creates the file and the table!
Base.metadata.create_all(bind=engine)