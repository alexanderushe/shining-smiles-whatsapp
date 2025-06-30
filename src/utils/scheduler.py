# src/utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.reminder_service import send_balance_reminders
from src.services.payment_service import check_new_payments
from src.services.profile_sync_service import sync_student_profiles
from src.api.sms_client import SMSClient
from src.utils.logger import setup_logger
import datetime

logger = setup_logger(__name__)

def send_all_reminders():
    """Send reminders for all students in debt."""
    try:
        client = SMSClient()
        debt_data = client.get_students_in_debt()
        for student in debt_data.get("data", []):
            student_id = student["student"]["student_number"]
            send_balance_reminders(student_id, "2025-1")
        logger.info("Completed batch reminder job")
    except Exception as e:
        logger.error(f"Error in batch reminders: {str(e)}")

def check_all_payments():
    """Check payments for all relevant students."""
    try:
        client = SMSClient()
        student_ids = set()
        # Get students in debt
        debt_data = client.get_students_in_debt()
        student_ids.update(student["student"]["student_number"] for student in debt_data.get("data", []))
        # Get students with recent payments
        for student_id in student_ids.copy():
            try:
                payment_data = client.get_student_payments(student_id, "2025-1")
                if payment_data.get("data"):
                    student_ids.add(student_id)
            except Exception as e:
                logger.debug(f"No payments for {student_id}: {str(e)}")
        logger.info(f"Checking payments for {len(student_ids)} students")
        for student_id in student_ids:
            check_new_payments(student_id, "2025-1")
        logger.info("Completed batch payment check job")
    except Exception as e:
        logger.error(f"Error in batch payment check: {str(e)}")

def init_scheduler():
    """Initialize scheduler for balance reminders, payment checks, and profile sync."""
    try:
        scheduler = BackgroundScheduler()
        # src/utils/scheduler.py (temporary)
        #scheduler.add_job(sync_student_profiles, trigger="date", run_date=datetime.datetime.now() + datetime.timedelta(seconds=30))
        # Daily profile sync (every day at 2 AM)
        scheduler.add_job(
            sync_student_profiles,
            trigger="cron",
            hour=2,
            minute=0
        )
        # Weekly reminders for all students in debt (every Monday at 9 AM)
        scheduler.add_job(
            send_all_reminders,
            trigger="cron",
            day_of_week="mon",
            hour=9,
            minute=0
        )
        # Daily payment checks (every day at 8 AM)
        scheduler.add_job(
            check_all_payments,
            trigger="cron",
            hour=8,
            minute=0
        )
        scheduler.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise