# src/services/payment_service.py
from src.api.sms_client import SMSClient
from src.utils.whatsapp import send_whatsapp_message
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def check_new_payments(student_id, term, phone_number):
    """Check for new payments and send confirmation."""
    try:
        client = SMSClient()
        payments_data = client.get_student_payments(student_id, term)
        logger.debug(f"Payments data for {student_id}: {payments_data}")
        # Extract payments list from data
        payments = payments_data.get("data", {}).get("payments", [])
        if not payments:
            logger.info(f"No payments found for {student_id}")
            return

        # Assuming payments are sorted by date, get the latest
        latest_payment = payments[-1]
        logger.debug(f"Latest payment: {latest_payment}")
        amount = latest_payment.get("amount", 0)
        if amount <= 0:
            logger.info(f"No new payment amount for {student_id}")
            return

        # Get current balance
        statement = client.get_student_account_statement(student_id, term)
        logger.debug(f"Account statement: {statement}")
        balance = statement.get("balance", 0)

        # Send WhatsApp message
        message = (
            f"Hi Mr. Nkomo, thank you for your payment of ${amount} for {student_id}. "
            f"Your balance is now ${balance}."
        )
        send_whatsapp_message(phone_number, message)
        logger.info(f"Payment confirmation sent for {student_id}")
    except Exception as e:
        logger.error(f"Error processing payments for {student_id}: {str(e)}")
        raise