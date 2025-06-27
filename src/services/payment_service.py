# src/services/payment_service.py
from src.api.sms_client import SMSClient
from src.utils.whatsapp import send_whatsapp_message
from src.utils.logger import setup_logger
from src.utils.database import init_db, StudentContact
import datetime

logger = setup_logger(__name__)

def check_new_payments(student_id, term, phone_number=None):
    """Check for new payments and send confirmation."""
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

        # Check payments
        try:
            payment_data = client.get_student_payments(student_id, term)
            logger.debug(f"Payment data for {student_id}: {payment_data}")
            if not isinstance(payment_data, dict) or "data" not in payment_data:
                logger.error(f"Invalid payment data format for {student_id}: {payment_data}")
                return {"error": f"Invalid payment data format: {payment_data}"}
        except Exception as e:
            if "404 Client Error" in str(e):
                logger.info(f"No payments found for {student_id} in term {term}")
                return {"status": f"No payments found for {student_id}"}
            logger.error(f"Failed to fetch payments for {student_id}: {str(e)}")
            return {"error": f"Failed to fetch payments: {str(e)}"}

        if not payment_data.get("data"):
            logger.info(f"No new payments for {student_id}")
            return {"status": f"No new payments for {student_id}"}

        # Calculate total paid
        total_paid = sum(payment.get("amount", 0) for payment in payment_data["data"])
        if total_paid <= 0:
            logger.info(f"No valid payments found for {student_id}")
            return {"status": f"No valid payments for {student_id}"}

        # Get current balance
        statement = client.get_student_account_statement(student_id, term)
        balance = statement.get("balance", 0)

        # Send WhatsApp confirmation
        message = (
            f"Dear {fullname}, thank you for your payment of ${total_paid} for {student_id} (Term {term}). "
            f"Your current balance is ${balance}."
        )
        send_whatsapp_message(phone_number, message)
        logger.info(f"Payment confirmation sent for {student_id} to {phone_number}")
        return {"status": "Payment confirmation sent", "phone_number": phone_number}
    except Exception as e:
        logger.error(f"Error checking payments for {student_id}: {str(e)}")
        return {"error": str(e)}