from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models
from app.auth.security import hash_pin, verify_pin


class UserService:
    @staticmethod
    async def authenticate_or_register(
        db: AsyncSession,
        username: str,
        pin: str,
        persona_name: str,
    ) -> models.User | None:
        """Register a new user, or log an existing user in if the PIN matches.

        Returns None when the username exists but the PIN is wrong.
        """
        result = await db.execute(select(models.User).filter(models.User.username == username))
        user = result.scalars().first()

        if user is None:
            user = models.User(
                username=username,
                pin_hash=hash_pin(pin),
                persona_name=persona_name,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

        if not verify_pin(pin, user.pin_hash):
            return None
        return user

    @staticmethod
    async def clear_all_data(db: AsyncSession, user_id: int) -> None:
        await db.execute(delete(models.ChatLog).where(models.ChatLog.user_id == user_id))
        await db.execute(delete(models.Reminder).where(models.Reminder.user_id == user_id))
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
