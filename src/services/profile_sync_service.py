# src/services/profile_sync_service.py
from src.api.sms_client import SMSClient
from src.utils.database import init_db, StudentContact
from src.utils.logger import setup_logger
import datetime

logger = setup_logger(__name__)

def sync_student_profiles():
    """Sync student profiles from /students/accounts-in-debt and /student/payments/."""
    try:
        client = SMSClient()
        session = init_db()
        student_ids = set()

        # Fetch students in debt
        try:
            debt_data = client.get_students_in_debt()
            student_ids.update(student["student"]["student_number"] for student in debt_data.get("data", []))
            logger.info(f"Fetched {len(student_ids)} students from /students/accounts-in-debt")
        except Exception as e:
            logger.error(f"Error fetching students in debt: {str(e)}")

        # Fetch students with recent payments (last 30 days)
        try:
            for student_id in student_ids.copy():
                try:
                    payment_data = client.get_student_payments(student_id, "2025-1")
                    if payment_data.get("data"):
                        student_ids.add(student_id)
                except Exception as e:
                    logger.debug(f"No payments for {student_id}: {str(e)}")
            logger.info(f"Total students to sync: {len(student_ids)}")
        except Exception as e:
            logger.error(f"Error checking payments: {str(e)}")

        # Sync profiles
        for student_id in student_ids:
            try:
                profile = client.get_student_profile(student_id)
                profile_data = profile.get("data", {})
                firstname = profile_data.get("firstname")
                lastname = profile_data.get("lastname")
                student_mobile = profile_data.get("student_mobile")  # Parent's number
                guardian_mobile = profile_data.get("guardian_mobile_number")
                
                # Format phone numbers
                if student_mobile and not student_mobile.startswith("+"):
                    student_mobile = f"+263{student_mobile.lstrip('0')}"
                if guardian_mobile and not guardian_mobile.startswith("+"):
                    guardian_mobile = f"+263{guardian_mobile.lstrip('0')}"
                preferred_phone = student_mobile or guardian_mobile
                if not preferred_phone:
                    logger.warning(f"No phone number for {student_id}; skipping")
                    continue

                # Update or insert contact
                contact = session.query(StudentContact).filter_by(student_id=student_id).first()
                if contact:
                    contact.firstname = firstname
                    contact.lastname = lastname
                    contact.student_mobile = student_mobile
                    contact.guardian_mobile_number = guardian_mobile
                    contact.preferred_phone_number = preferred_phone
                    contact.last_updated = datetime.datetime.utcnow()
                    logger.info(f"Updated profile for {student_id}")
                else:
                    contact = StudentContact(
                        student_id=student_id,
                        firstname=firstname,
                        lastname=lastname,
                        student_mobile=student_mobile,
                        guardian_mobile_number=guardian_mobile,
                        preferred_phone_number=preferred_phone,
                        last_updated=datetime.datetime.utcnow()
                    )
                    session.add(contact)
                    logger.info(f"Added profile for {student_id}")
                session.commit()
            except Exception as e:
                logger.error(f"Error syncing profile for {student_id}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error syncing profiles: {str(e)}")
        raise