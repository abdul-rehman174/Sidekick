import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app import models
from app.config import settings
from app.database import engine
from app.exceptions import AIServiceException
from app.routes import chat, reminders, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Columns added after the initial schema. Listed here so existing DBs
# (Supabase + local sqlite) get them on startup without dropping data.
_SOFT_MIGRATIONS = [
    ("users", "chat_summary", "TEXT"),
    ("users", "summary_message_count", "INTEGER NOT NULL DEFAULT 0"),
]


async def _apply_soft_migrations(conn) -> None:
    dialect = conn.dialect.name
    for table, column, ddl in _SOFT_MIGRATIONS:
        try:
            if dialect == "postgresql":
                await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl}'))
            else:
                await conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl}'))
        except Exception as e:
            # SQLite raises if the column already exists; ignore silently.
            logger.debug("soft-migration skipped for %s.%s: %s", table, column, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        await _apply_soft_migrations(conn)
    logger.info("Database schema ready.")
    yield


app = FastAPI(title="Sidekick", lifespan=lifespan)


@app.exception_handler(AIServiceException)
async def ai_service_exception_handler(request: Request, exc: AIServiceException):
    logger.warning("AI service error on %s: %s", request.url.path, exc.message)
    return JSONResponse(status_code=503, content={"status": "error", "message": exc.message})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(users.router)
app.include_router(reminders.router)
app.include_router(chat.router)

frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    logger.info("No 'static' folder found — frontend is expected to run via `npm run dev`.")
