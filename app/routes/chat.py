from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.auth.jwt_handler import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ChatRequest
from app.services.ai_service import AIService
from app.services.user_service import UserService

router = APIRouter(prefix="/api")


@router.post("/chat")
async def chat_with_sidekick(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AIService.generate_reply(db, user, request.user_message)


@router.get("/chat/history")
async def get_chat_history(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.ChatLog)
        .filter(models.ChatLog.user_id == user.id)
        .order_by(models.ChatLog.id.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/clear-all")
async def clear_all_data(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await UserService.clear_all_data(db, user.id)
    return {"status": "success"}
