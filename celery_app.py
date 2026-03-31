from celery import Celery
import time
# We need to import our DB tools
from database import SessionLocal
import models

app = Celery('sidekick', broker='redis://localhost:6379/0')


@app.task(name="send_reminder_task")
def send_reminder_task(task_text):
    """
    This runs in the background. After the 'countdown',
    it updates the DB before finishing.
    """
    # 1. The 'Work' (Wait for the time to pass)
    print(f"⏰ Reminder Started: {task_text}")

    # 2. Update the Database
    db = SessionLocal()
    try:
        # Find the reminder in the DB by its task name
        # (In a bigger app, we'd use the unique ID)
        reminder = db.query(models.Reminder).filter(
            models.Reminder.task == task_text,
            models.Reminder.status == "pending"
        ).first()

        if reminder:
            # You can either DELETE it or mark as COMPLETED
            reminder.status = "completed"
            db.commit()
            print(f"✅ Database Updated: '{task_text}' is now COMPLETED")

    except Exception as e:
        print(f"❌ Database Update Failed: {e}")
    finally:
        db.close()

    return f"Reminder for '{task_text}' finished!"