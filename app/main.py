from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine
from app import models
from app.routes import users, reminders, chat
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🫦 Database Genesis: Professional Startup Sequence
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database Genesis: Absolute Success! 🚤✨⚓️🛡️✨")
    except Exception as e:
        print(f"Database Genesis: Postponed/Failed! {e} 💔")
    yield

app = FastAPI(title="Sidekick AI Pro", lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(users.router)
app.include_router(reminders.router)
app.include_router(chat.router)

# Serve Frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print(f"💡 Info: No 'static' folder found. (Safe to ignore if using npm run dev!)")
