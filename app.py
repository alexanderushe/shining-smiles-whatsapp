# app.py
from flask import Flask, request
from src.utils.logger import setup_logger
from src.utils.scheduler import init_scheduler
from src.services.payment_service import check_new_payments
from src.services.reminder_service import send_balance_reminders
from src.utils.database import init_db, StudentContact
from config import get_config
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
app = Flask(__name__)
app.config.from_object(get_config())

logger = setup_logger(__name__)
init_scheduler()

@app.route("/health")
def health_check():
    """Health check endpoint."""
    logger.info("Health endpoint called")
    return {"status": "healthy"}, 200

@app.route("/trigger-payments", methods=["POST"])
def trigger_payments():
    """Manual trigger for checking new payments (for testing)."""
    try:
        student_id = request.args.get("student_id_number", "SSC20257279")
        term = request.args.get("term", "2025-1")
        phone_number = request.args.get("phone_number")
        logger.debug(f"Triggering payment check for student_id={student_id}, term={term}, phone_number={phone_number}")
        result = check_new_payments(student_id, term, phone_number)
        if "error" in result:
            logger.error(f"Error in check_new_payments: {result['error']}")
            return {"status": "Payment check failed", "error": result["error"]}, 400
        logger.info(f"Payment check triggered for {student_id}")
        return {"status": "Payment check triggered", "result": result}, 200
    except Exception as e:
        logger.error(f"Error triggering payments: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/trigger-reminders", methods=["POST"])
def trigger_reminders():
    """Manual trigger for balance reminders (for testing)."""
    try:
        student_id = request.args.get("student_id_number", "SSC20257279")
        term = request.args.get("term", "2025-1")
        phone_number = request.args.get("phone_number")
        logger.debug(f"Triggering reminder for student_id={student_id}, term={term}, phone_number={phone_number}")
        result = send_balance_reminders(student_id, term, phone_number)
        if "error" in result:
            logger.error(f"Error in send_balance_reminders: {result['error']}")
            return {"status": "Reminder failed", "error": result["error"]}, 400
        logger.info(f"Balance reminder triggered for {student_id}")
        return {"status": "Balance reminder triggered", "result": result}, 200
    except Exception as e:
        logger.error(f"Error triggering reminders: {str(e)}")
        return {"error": str(e)}, 500

@app.route("/update-contact", methods=["POST"])
def update_contact():
    """Update or add a contact."""
    try:
        student_id = request.args.get("student_id")
        phone_number = request.args.get("phone_number")
        firstname = request.args.get("firstname")
        lastname = request.args.get("lastname")
        if not student_id or not phone_number:
            logger.error("Missing student_id or phone_number")
            return {"error": "student_id and phone_number required"}, 400
        session = init_db()
        if not phone_number.startswith("+"):
            phone_number = f"+263{phone_number.lstrip('0')}"
        contact = session.query(StudentContact).filter_by(student_id=student_id).first()
        if contact:
            contact.firstname = firstname or contact.firstname
            contact.lastname = lastname or contact.lastname
            contact.student_mobile = phone_number  # Parent's number
            contact.guardian_mobile_number = phone_number if not contact.guardian_mobile_number else contact.guardian_mobile_number
            contact.preferred_phone_number = phone_number
            contact.last_updated = datetime.datetime.utcnow()
            logger.info(f"Updated contact for {student_id}: {phone_number}")
        else:
            contact = StudentContact(
                student_id=student_id,
                firstname=firstname,
                lastname=lastname,
                student_mobile=phone_number,
                guardian_mobile_number=phone_number,
                preferred_phone_number=phone_number,
                last_updated=datetime.datetime.utcnow()
            )
            session.add(contact)
            logger.info(f"Added contact for {student_id}: {phone_number}")
        session.commit()
        return {"status": "Contact updated"}, 200
    except Exception as e:
        logger.error(f"Error updating contact for {student_id}: {str(e)}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)