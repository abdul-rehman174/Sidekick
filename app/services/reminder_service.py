import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import models

DUPLICATE_WINDOW_MINUTES = 120
HISTORY_WINDOW_DAYS = 7


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ReminderService:
    @staticmethod
    async def get_reminders(db: AsyncSession, user_id: int, status: str = "pending"):
        cutoff = _utcnow() - datetime.timedelta(days=HISTORY_WINDOW_DAYS)
        result = await db.execute(
            select(models.Reminder)
            .filter(
                models.Reminder.user_id == user_id,
                models.Reminder.status == status,
                models.Reminder.created_at >= cutoff,
            )
            .order_by(models.Reminder.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def delete_reminder(db: AsyncSession, user_id: int, reminder_id: int) -> None:
        reminder = await ReminderService._get_owned(db, user_id, reminder_id)
        await db.delete(reminder)
        await db.commit()

    @staticmethod
    async def complete_reminder(db: AsyncSession, user_id: int, reminder_id: int) -> None:
        reminder = await ReminderService._get_owned(db, user_id, reminder_id)
        if reminder.status != "pending":
            raise HTTPException(status_code=400, detail="Reminder already completed.")
        reminder.status = "completed"
        await db.commit()

    @staticmethod
    async def create_reminder(
        db: AsyncSession, user_id: int, task: str, minutes: int = 1
    ) -> tuple[bool, models.Reminder | None]:
        """Create a reminder, rejecting near-duplicates within the duplicate window."""
        now = _utcnow()
        recent_cutoff = now - datetime.timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
        task_norm = task.lower().strip().rstrip("s").rstrip("!")

        dup_result = await db.execute(
            select(models.Reminder).filter(
                models.Reminder.user_id == user_id,
                models.Reminder.task.ilike(f"%{_escape_like(task_norm)}%", escape="\\"),
                models.Reminder.created_at >= recent_cutoff,
            )
        )
        if dup_result.scalars().first() is not None:
            return False, None

        reminder = models.Reminder(
            user_id=user_id,
            task=task,
            status="pending",
            due_at=now + datetime.timedelta(minutes=minutes),
        )
        db.add(reminder)
        await db.commit()
        await db.refresh(reminder)
        return True, reminder

    @staticmethod
    async def _get_owned(db: AsyncSession, user_id: int, reminder_id: int) -> models.Reminder:
        result = await db.execute(
            select(models.Reminder).filter(
                models.Reminder.id == reminder_id,
                models.Reminder.user_id == user_id,
            )
        )
        reminder = result.scalars().first()
        if reminder is None:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        return reminder
