from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.reminder_service import ReminderService
from app.auth.jwt_handler import get_current_user
from app.models import User

router = APIRouter(prefix="/api/reminders")

@router.get("")
async def get_reminders(status: str = "pending", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ReminderService.get_reminders(db, user.id, status)

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ReminderService.delete_reminder(db, user.id, reminder_id)
    return {"status": "success"}

@router.post("/{reminder_id}/complete")
async def complete_reminder(reminder_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ReminderService.complete_reminder(db, user.id, reminder_id)
    return {"status": "success"}
