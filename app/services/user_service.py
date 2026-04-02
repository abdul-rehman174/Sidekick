from sqlalchemy.orm import Session
from sqlalchemy import delete
from app import models
from app.config import settings
from app.database import get_db

class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return db.query(models.User).filter(models.User.id == user_id).first()

    @staticmethod
    def onboard_user(db: Session, username: str, bot_name: str, pin: str = "0000"):
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            user = models.User(username=username, bot_name=bot_name, pin=pin)
            db.add(user)
        else:
            if user.pin and user.pin != pin:
                return None # Unauthorized
            user.bot_name = bot_name
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def clear_all_data(db: Session, user_id: int):
        db.execute(delete(models.ChatLog).where(models.ChatLog.user_id == user_id))
        db.execute(delete(models.Reminder).where(models.Reminder.user_id == user_id))
        db.commit()
        return True
