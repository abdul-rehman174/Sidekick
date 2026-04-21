import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app import models
from app.config import settings

class ReminderService:
    @staticmethod
    async def get_reminders(db: AsyncSession, user_id: int, status: str = "pending"):
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        result = await db.execute(
            select(models.Reminder).filter(
                models.Reminder.user_id == user_id,
                models.Reminder.status == status,
                models.Reminder.created_at >= seven_days_ago
            ).order_by(models.Reminder.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def delete_reminder(db: AsyncSession, user_id: int, reminder_id: int):
        result = await db.execute(
            select(models.Reminder).filter(
                models.Reminder.id == reminder_id,
                models.Reminder.user_id == user_id
            )
        )
        reminder = result.scalars().first()
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        
        await db.delete(reminder)
        await db.commit()
        return True

    @staticmethod
    async def complete_reminder(db: AsyncSession, user_id: int, reminder_id: int):
        result = await db.execute(
            select(models.Reminder).filter(
                models.Reminder.id == reminder_id,
                models.Reminder.user_id == user_id
            )
        )
        reminder = result.scalars().first()
        
        if not reminder or reminder.status != "pending":
            raise HTTPException(status_code=400, detail="Reminder already completed or invalid.")
        
        reminder.status = "completed"
        await db.commit()
        return True

    @staticmethod
    async def create_reminder(db: AsyncSession, user_id: int, task: str, minutes: int = 1):
        """
        Creates a new reminder with a fuzzy duplicate check.
        Returns: (is_new: bool, message: str)
        """
        now = datetime.datetime.utcnow()
        recent_check = now - datetime.timedelta(minutes=120)
        
        task_norm = task.lower().strip().rstrip("s").rstrip("!")
        
        result = await db.execute(
            select(models.Reminder).filter(
                models.Reminder.user_id == user_id,
                models.Reminder.task.ilike(f"%{task_norm}%"),
                models.Reminder.created_at >= recent_check
            )
        )
        existing = result.scalars().first()
        
        if existing:
            return False, "This task is already being tracked, jan. 🫦"

        # 2. Save Reminder
        due_at = now + datetime.timedelta(minutes=minutes)
        new_reminder = models.Reminder(user_id=user_id, task=task, status="pending", due_at=due_at)
        db.add(new_reminder)
        await db.commit()
        await db.refresh(new_reminder)
        
        success_msg = f"I've got your '{task}' on my list now. I'll make sure you don't forget."
        return True, success_msg
