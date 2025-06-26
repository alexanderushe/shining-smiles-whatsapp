# src/utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.reminder_service import send_balance_reminders
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def init_scheduler():
    """Initialize scheduler for balance reminders."""
    try:
        scheduler = BackgroundScheduler()
        # Schedule weekly reminders (e.g., every Monday at 9 AM)
        scheduler.add_job(
            lambda: send_balance_reminders("SSC20257279", "2025-1"),
            trigger="cron",
            day_of_week="mon",
            hour=9,
            minute=0
        )
        scheduler.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise