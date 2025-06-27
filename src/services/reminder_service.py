# src/services/reminder_service.py
from src.api.sms_client import SMSClient
from src.utils.whatsapp import send_whatsapp_message
from src.utils.logger import setup_logger
from src.utils.database import init_db, StudentContact
import datetime

logger = setup_logger(__name__)

def send_balance_reminders(student_id, term, phone_number=None):
    """Send reminders for outstanding balances."""
    try:
        client = SMSClient()
        session = init_db()
        
        # Log database connection and all contacts
        logger.debug(f"Database session initialized for {student_id}: {session}")
        contacts = session.query(StudentContact).all()
        logger.debug(f"All contacts in database: {[(c.student_id, c.firstname, c.lastname, c.preferred_phone_number) for c in contacts]}")

        # Fetch contact from database or API
        if not phone_number:
            contact = session.query(StudentContact).filter_by(student_id=student_id).first()
            if contact:
                phone_number = contact.preferred_phone_number
                fullname = f"{contact.firstname} {contact.lastname}".strip() if contact.firstname and contact.lastname else "Parent/Guardian"
                logger.info(f"Found contact in database for {student_id}: {phone_number}")
            else:
                logger.debug(f"No contact in database for {student_id}, trying API")
                try:
                    profile = client.get_student_profile(student_id)
                    logger.debug(f"Profile response for {student_id}: {profile}")
                    profile_data = profile.get("data", {})
                    firstname = profile_data.get("firstname")
                    lastname = profile_data.get("lastname")
                    student_mobile = profile_data.get("student_mobile")  # Parent's number
                    guardian_mobile = profile_data.get("guardian_mobile_number")
                    if student_mobile and not student_mobile.startswith("+"):
                        student_mobile = f"+263{student_mobile.lstrip('0')}"
                    if guardian_mobile and not guardian_mobile.startswith("+"):
                        guardian_mobile = f"+263{guardian_mobile.lstrip('0')}"
                    phone_number = student_mobile or guardian_mobile
                    if not phone_number:
                        logger.error(f"No phone number found in profile for {student_id}")
                        return {"error": "No phone number found in profile"}
                    fullname = f"{firstname} {lastname}".strip() if firstname and lastname else "Parent/Guardian"
                    # Cache in database
                    contact = StudentContact(
                        student_id=student_id,
                        firstname=firstname,
                        lastname=lastname,
                        student_mobile=student_mobile,
                        guardian_mobile_number=guardian_mobile,
                        preferred_phone_number=phone_number,
                        last_updated=datetime.datetime.utcnow()
                    )
                    session.add(contact)
                    session.commit()
                    logger.info(f"Cached contact for {student_id}: {phone_number}")
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
            f"Dear {fullname}, your child ({student_id}) has an outstanding balance of ${balance} for Term {term}. "
            f"Kindly settle by June 30."
        )
        send_whatsapp_message(phone_number, message)
        logger.info(f"Balance reminder sent for {student_id} to {phone_number}")
        return {"status": "Balance reminder sent", "phone_number": phone_number}
    except Exception as e:
        logger.error(f"Error sending reminder for {student_id}: {str(e)}")
        return {"error": str(e)}