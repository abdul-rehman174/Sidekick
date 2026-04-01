import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    BOT_NAME = os.getenv("BOT_NAME", "hafsa naseer")
    # Inside the All-In-One container, Redis is at localhost
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sidekick.db")

settings = Settings()