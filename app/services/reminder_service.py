import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import models
from app.config import settings

class ReminderService:
    @staticmethod
    def get_reminders(db: Session, user_id: int, status: str = "pending"):
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        return db.query(models.Reminder).filter(
            models.Reminder.user_id == user_id,
            models.Reminder.status == status,
            models.Reminder.created_at >= seven_days_ago
        ).order_by(models.Reminder.created_at.desc()).all()

    @staticmethod
    def delete_reminder(db: Session, user_id: int, reminder_id: int):
        reminder = db.query(models.Reminder).filter(
            models.Reminder.id == reminder_id,
            models.Reminder.user_id == user_id
        ).first()
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        
        db.delete(reminder)
        db.commit()
        return True

    @staticmethod
    def complete_reminder(db: Session, user_id: int, reminder_id: int):
        reminder = db.query(models.Reminder).filter(
            models.Reminder.id == reminder_id,
            models.Reminder.user_id == user_id
        ).first()
        
        if not reminder or reminder.status != "pending":
            raise HTTPException(status_code=400, detail="Reminder already completed or invalid.")
        
        reminder.status = "completed"
        # 🫦 Logic Refinement: We no longer inject a redundant chat log record here.
        # This resolves the 'Double-Reminder' issue reported by the user.
        db.commit()
        return True

    @staticmethod
    def create_reminder(db: Session, user_id: int, task: str, minutes: int = 1):
        """
        Creates a new reminder with a fuzzy duplicate check.
        Returns: (is_new: bool, message: str)
        """
        now = datetime.datetime.utcnow()
        recent_check = now - datetime.timedelta(minutes=120)
        
        task_norm = task.lower().strip().rstrip("s").rstrip("!")
        
        existing = db.query(models.Reminder).filter(
            models.Reminder.user_id == user_id,
            models.Reminder.task.ilike(f"%{task_norm}%"),
            models.Reminder.created_at >= recent_check
        ).first()
        
        if existing:
            return False, "This task is already being tracked, jan. 🫦"

        # 2. Save Reminder
        due_at = now + datetime.timedelta(minutes=minutes)
        new_reminder = models.Reminder(user_id=user_id, task=task, status="pending", due_at=due_at)
        db.add(new_reminder)
        db.commit()
        db.refresh(new_reminder)
        
        success_msg = f"I've got your '{task}' on my list now. I'll make sure you don't forget."
        return True, success_msg
