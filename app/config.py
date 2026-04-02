import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Settings:
    """
    Project-wide configuration and environment variable orchestration.
    Ensure all API keys are provided via the system environment.
    """
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    BOT_NAME: str = os.getenv("BOT_NAME", "Sidekick")
    
    # Infrastructure configuration
    # Note: In the official Docker all-in-one container, Redis resides at localhost.
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sidekick.db")
    
    # Security Protocols: JWT Cryptography
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sidekick-security-vault-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week duration

# Singleton instance for project-wide access
settings = Settings()