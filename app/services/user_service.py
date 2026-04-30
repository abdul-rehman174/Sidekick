from fastapi import HTTPException
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.auth.security import hash_password, verify_password


class UserService:
    @staticmethod
    async def register_user(
        db: AsyncSession,
        username: str,
        password: str,
        persona_name: str,
    ) -> models.User:
        """Create a new account. Raises 409 if the username is already taken."""
        result = await db.execute(select(models.User).filter(models.User.username == username))
        if result.scalars().first() is not None:
            raise HTTPException(status_code=409, detail="Username is already taken.")

        user = models.User(
            username=username,
            pin_hash=hash_password(password),
            persona_name=persona_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> models.User:
        """Look up a user and verify their password. Raises 401 on either miss."""
        result = await db.execute(select(models.User).filter(models.User.username == username))
        user = result.scalars().first()
        if user is None or not verify_password(password, user.pin_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        return user

    @staticmethod
    async def clear_all_data(db: AsyncSession, user_id: int) -> None:
        await db.execute(delete(models.ChatLog).where(models.ChatLog.user_id == user_id))
        await db.execute(delete(models.Reminder).where(models.Reminder.user_id == user_id))
        await db.execute(
            update(models.User)
            .where(models.User.id == user_id)
            .values(chat_summary=None, summary_message_count=0)
        )
        await db.commit()

    @staticmethod
    async def update_persona(
        db: AsyncSession,
        user: models.User,
        persona_name: str | None,
        behavior_profile: str | None,
        system_instruction: str | None,
    ) -> models.User:
        if persona_name is not None:
            user.persona_name = persona_name
        if behavior_profile is not None:
            user.behavior_profile = behavior_profile or None
        if system_instruction is not None:
            user.system_instruction = system_instruction or None
        await db.commit()
        await db.refresh(user)
        return user
