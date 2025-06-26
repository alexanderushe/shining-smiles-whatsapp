# scripts/add_guardian_contact.py
import os
import sys
# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.database import init_db, StudentContact
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def add_guardian_contact(student_id, phone_number):
    """Manually add or update a guardian phone number."""
    try:
        session = init_db()
        if not phone_number.startswith("+"):
            phone_number = f"+263{phone_number.lstrip('0')}"
        contact = session.query(StudentContact).filter_by(student_id=student_id).first()
        if contact:
            contact.phone_number = phone_number
            logger.info(f"Updated phone number for {student_id}: {phone_number}")
        else:
            contact = StudentContact(student_id=student_id, phone_number=phone_number)
            session.add(contact)
            logger.info(f"Added phone number for {student_id}: {phone_number}")
        session.commit()
    except Exception as e:
        logger.error(f"Error adding contact for {student_id}: {str(e)}")
        raise

if __name__ == "__main__":
    add_guardian_contact("SSC20257279", "0711206287")