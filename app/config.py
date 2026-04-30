import logging
import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _ephemeral_secret() -> str:
    key = secrets.token_urlsafe(32)
    logger.warning(
        "SECRET_KEY not set in environment — generated an ephemeral one. "
        "Tokens will be invalidated on every restart. "
        "For stable sessions, set SECRET_KEY in your .env or HF Space secrets."
    )
    return key


class Settings(BaseSettings):
    GROQ_API_KEY: str
    SECRET_KEY: str = Field(default_factory=_ephemeral_secret)

    DATABASE_URL: str = "sqlite+aiosqlite:///./sidekick.db"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    CORS_ORIGINS: str = "http://localhost:5173"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
