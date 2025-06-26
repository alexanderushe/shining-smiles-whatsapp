# src/services/reminder_service.py
from src.api.sms_client import SMSClient
from src.utils.whatsapp import send_whatsapp_message
from src.utils.logger import setup_logger
from src.utils.database import init_db, StudentContact

logger = setup_logger(__name__)

def send_balance_reminders(student_id, term, phone_number=None):
    """Send reminders for outstanding balances."""
    try:
        client = SMSClient()
        session = init_db()
        
        # Log database connection
        logger.debug(f"Database session initialized for {student_id}")

        # Fetch phone number from database or API
        if not phone_number:
            contact = session.query(StudentContact).filter_by(student_id=student_id).first()
            if contact:
                phone_number = contact.phone_number
                logger.info(f"Found phone number in database for {student_id}: {phone_number}")
            else:
                logger.debug(f"No phone number in database for {student_id}, trying API")
                try:
                    profile = client.get_student_profile(student_id)
                    logger.debug(f"Profile response for {student_id}: {profile}")
                    phone_number = profile.get("data", {}).get("guardian_mobile_number") or \
                                   profile.get("data", {}).get("student_mobile")
                    if not phone_number:
                        logger.error(f"No phone number found in profile for {student_id}")
                        return {"error": "No phone number found in profile"}
                    if not phone_number.startswith("+"):
                        phone_number = f"+263{phone_number.lstrip('0')}"
                    # Cache in database
                    contact = StudentContact(student_id=student_id, phone_number=phone_number)
                    session.add(contact)
                    session.commit()
                    logger.info(f"Cached phone number for {student_id}: {phone_number}")
                except Exception as e:
                    logger.error(f"Failed to fetch profile for {student_id}: {str(e)}")
                    return {"error": f"Failed to fetch profile: {str(e)}"}

        # Validate phone number
        if not phone_number:
            logger.error(f"No phone number available for {student_id}")
            return {"error": "Phone number required"}

        # Fetch balance from /students/accounts-in-debt
        debt_data = client.get_students_in_debt(student_id=student_id)
        balance = 0
        for student in debt_data.get("data", []):
            if student["student"]["student_number"] == student_id:
                balance = student["outstanding_balance"]
                break

        if balance <= 0:
            logger.info(f"No outstanding balance for {student_id}")
            return {"status": f"No outstanding balance for {student_id}"}

        # Send WhatsApp reminder
        message = (
            f"Reminder: {student_id} has an outstanding balance of ${balance} for Term {term}. "
            f"Kindly settle by June 30."
        )
        send_whatsapp_message(phone_number, message)
        logger.info(f"Balance reminder sent for {student_id} to {phone_number}")
        return {"status": "Balance reminder sent", "phone_number": phone_number}
    except Exception as e:
        logger.error(f"Error sending reminder for {student_id}: {str(e)}")
        return {"error": str(e)}