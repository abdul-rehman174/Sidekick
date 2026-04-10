from celery import Celery
import time
from app.database import SessionLocal
from app import models
from app.config import settings

app = Celery('sidekick', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@app.task(name="send_reminder_task")
def send_reminder_task(reminder_id: int):
    """
    This runs in the background. After the 'countdown',
    it updates the DB using the unique RECORD ID.
    """
    db = SessionLocal()
    try:
        reminder = db.query(models.Reminder).filter(
            models.Reminder.id == reminder_id
        ).first()

        if reminder:
            # 1. Debouncing Check (Precision check for NOTIFICATION messages only)
            notif_prefix = f"Time for your reminder: '{reminder.task}'"
            recent_log_check = db.query(models.ChatLog).filter(
                models.ChatLog.user_id == reminder.user_id,
                models.ChatLog.role == "model",
                models.ChatLog.content.ilike(f"{notif_prefix}%")
            ).order_by(models.ChatLog.id.desc()).first()
            
            if recent_log_check:
                reminder.status = "completed" # Mark as done but skip log
                db.commit()
                print(f"[REDUNDANCY] Task '{reminder.task}' was already notified. Skipping.")
                return f"Reminder ID {reminder_id} suppressed as duplicate."

            reminder.status = "completed"
            
            user = db.query(models.User).filter(models.User.id == reminder.user_id).first()
            flirty_message = f"Time for your reminder: '{reminder.task}'"
            
            new_chat_log = models.ChatLog(
                user_id=reminder.user_id,
                role="model",
                content=flirty_message
            )
            db.add(new_chat_log)
            db.commit()
            print(f"[SUCCESS] Reminder ID {reminder_id} notified.")
        else:
            print(f"[WARNING] Reminder ID {reminder_id} not found in DB")

    except Exception as e:
        print(f"[ERROR] Database Update Failed: {e}")
    finally:
        db.close()

    return f"Reminder ID {reminder_id} processed!"