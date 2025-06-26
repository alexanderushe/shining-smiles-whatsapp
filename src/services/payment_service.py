# src/services/payment_service.py
from src.api.sms_client import SMSClient
from src.utils.whatsapp import send_whatsapp_message
from src.utils.logger import setup_logger
from src.utils.database import init_db, StudentContact

logger = setup_logger(__name__)

def check_new_payments(student_id, term, phone_number=None):
    """Check for new payments and send confirmation."""
    try:
        client = SMSClient()
        session = init_db()

        # Fetch phone number from database or API
        if not phone_number:
            contact = session.query(StudentContact).filter_by(student_id=student_id).first()
            if contact:
                phone_number = contact.phone_number
            else:
                profile = client.get_student_profile(student_id)
                phone_number = profile.get("data", {}).get("guardian_mobile_number") or \
                               profile.get("data", {}).get("student_mobile")
                if not phone_number:
                    logger.error(f"No phone number found for {student_id}")
                    return
                if not phone_number.startswith("+"):
                    phone_number = f"+263{phone_number.lstrip('0')}"
                # Cache in database
                contact = StudentContact(student_id=student_id, phone_number=phone_number)
                session.add(contact)
                session.commit()
                logger.info(f"Cached phone number for {student_id}: {phone_number}")

        # Fetch payments
        payments = client.get_student_payments(student_id, term)
        if not payments:
            logger.info(f"No payments found for {student_id}")
            return

        # Assuming payments are sorted by date, get the latest
        latest_payment = payments[-1]
        amount = latest_payment.get("amount", 0)
        if amount <= 0:
            logger.info(f"No new payment amount for {student_id}")
            return

        # Get current balance
        statement = client.get_student_account_statement(student_id, term)
        balance = statement.get("balance", 0)

        # Send WhatsApp message
        message = (
            f"Hi Mr. Nkomo, thank you for your payment of ${amount} for {student_id}. "
            f"Your balance is now ${balance}."
        )
        send_whatsapp_message(phone_number, message)
        logger.info(f"Payment confirmation sent for {student_id} to {phone_number}")
    except Exception as e:
        logger.error(f"Error processing payments for {student_id}: {str(e)}")
        raise