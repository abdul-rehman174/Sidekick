from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai_service import AIService
from app.services.user_service import UserService
from app.auth.jwt_handler import get_current_user
from app.models import User

router = APIRouter(prefix="/api")

from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    user_message: str

@router.post("/chat")
async def chat_with_sidekick(request: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AIService.generate_reply(db, user, request.user_message)

@router.get("/chat/history")
async def get_chat_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app import models
    return db.query(models.ChatLog).filter(models.ChatLog.user_id == user.id).order_by(models.ChatLog.id.desc()).limit(20).all()

@router.post("/clear-all")
async def clear_all_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if UserService.clear_all_data(db, user.id):
        return {"status": "success", "message": "All user data has been successfully cleared."}
    raise HTTPException(status_code=500, detail="Failed to wipe data")
