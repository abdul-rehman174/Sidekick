from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app import models
from app.config import settings

class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        result = await db.execute(select(models.User).filter(models.User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def onboard_user(db: AsyncSession, username: str, bot_name: str, pin: str = "0000"):
        result = await db.execute(select(models.User).filter(models.User.username == username))
        user = result.scalars().first()
        if not user:
            user = models.User(username=username, bot_name=bot_name, pin=pin)
            db.add(user)
        else:
            if user.pin and user.pin != pin:
                return None # Unauthorized
            user.bot_name = bot_name
        
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def clear_all_data(db: AsyncSession, user_id: int):
        await db.execute(delete(models.ChatLog).where(models.ChatLog.user_id == user_id))
        await db.execute(delete(models.Reminder).where(models.Reminder.user_id == user_id))
        await db.commit()
        return True
