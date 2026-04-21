import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Project-wide configuration and environment variable orchestration.
    Ensure all API keys are provided via the system environment.
    """
    GROQ_API_KEY: str

    DATABASE_URL: str = "sqlite+aiosqlite:///./sidekick.db"
    
    SECRET_KEY: str = "sidekick-security-vault-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day duration

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()