# src/services/reminder_service.py
from src.api.sms_client import SMSClient
from src.utils.whatsapp import send_whatsapp_message
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def send_balance_reminders(student_id, term, phone_number):
    """Send reminders for outstanding balances."""
    try:
        client = SMSClient()
        statement = client.get_student_account_statement(student_id, term)
        logger.debug(f"Account statement for {student_id}: {statement}")
        balance = statement.get("data", {}).get("balance", 0)

        if balance <= 0:
            logger.info(f"No outstanding balance for {student_id}")
            return

        # Send WhatsApp reminder
        message = (
            f"Reminder: {student_id} has an outstanding balance of ${balance} for Term {term}. "
            f"Kindly settle by June 30."
        )
        send_whatsapp_message(phone_number, message)
        logger.info(f"Balance reminder sent for {student_id}")
    except Exception as e:
        logger.error(f"Error sending reminder for {student_id}: {str(e)}")
        raise