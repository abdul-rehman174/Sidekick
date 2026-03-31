from celery import Celery
import time
from database import SessionLocal
import models
from config import settings

app = Celery('sidekick', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@app.task(name="send_reminder_task")
def send_reminder_task(task_text):
    """
    This runs in the background. After the 'countdown',
    it updates the DB before finishing.
    """
    print(f"⏰ Reminder Started: {task_text}")

    db = SessionLocal()
    try:
        reminder = db.query(models.Reminder).filter(
            models.Reminder.task == task_text,
            models.Reminder.status == "pending"
        ).first()

        if reminder:
            reminder.status = "completed"
            db.commit()
            print(f"✅ Database Updated: '{task_text}' is now COMPLETED")

    except Exception as e:
        print(f"❌ Database Update Failed: {e}")
    finally:
        db.close()

    return f"Reminder for '{task_text}' finished!"