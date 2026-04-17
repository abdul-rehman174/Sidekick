import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Project-wide configuration and environment variable orchestration.
    Ensure all API keys are provided via the system environment.
    """
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sidekick.db")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sidekick-security-vault-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day duration

settings = Settings()