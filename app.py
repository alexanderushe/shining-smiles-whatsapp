# app.py
from flask import Flask, request
from src.utils.logger import setup_logger
from src.utils.scheduler import init_scheduler
from src.services.payment_service import check_new_payments
from src.services.reminder_service import send_balance_reminders
from config import get_config
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.config.from_object(get_config())  # Corrected: Call from_object directly

# Initialize logger
logger = setup_logger(__name__)

# Initialize scheduler
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
        phone_number = request.args.get("phone_number", "")  # Replace with actual number
        if not phone_number:
            logger.error("Phone number not provided")
            return {"error": "Phone number required"}, 400
        check_new_payments(student_id, term, phone_number)
        logger.info(f"Payment check triggered for {student_id}")
        return {"status": "Payment check triggered"}, 200
    except Exception as e:
        logger.error(f"Error triggering payments: {str(e)}")
        return {"error": str(e)}, 500
    
@app.route("/trigger-reminders", methods=["POST"])
def trigger_reminders():
    """Manual trigger for balance reminders (for testing)."""
    try:
        student_id = request.args.get("student_id_number", "SSC20257279")
        term = request.args.get("term", "2025-1")
        phone_number = request.args.get("phone_number", "")  # Replace with actual number
        if not phone_number:
            logger.error("Phone number not provided")
            return {"error": "Phone number required"}, 400
        send_balance_reminders(student_id, term, phone_number)
        logger.info(f"Balance reminder triggered for {student_id}")
        return {"status": "Balance reminder triggered"}, 200
    except Exception as e:
        logger.error(f"Error triggering reminders: {str(e)}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])