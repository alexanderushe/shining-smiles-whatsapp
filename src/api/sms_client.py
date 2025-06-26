# src/api/sms_client.py
import requests
from src.utils.logger import setup_logger
from config import get_config

config = get_config()
logger = setup_logger(__name__)

class SMSClient:
    """Client for Shining Smiles SMS API."""
    def __init__(self):
        self.base_url = config.SMS_API_BASE_URL
        self.headers = {
            "Authorization": f"Api-Key {config.SMS_API_KEY}",
            "User-Agent": "ShiningSmilesWhatsApp/1.0",
            "Accept": "application/json"
        }

    def get_student_account_statement(self, student_id, term):
        """Fetch student account statement."""
        try:
            params = {"student_id_number": student_id, "term": term}
            response = requests.get(
                f"{self.base_url}/student-account-statement/",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Fetched account statement for {student_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching account statement for {student_id}: {str(e)}")
            raise

    def get_student_payments(self, student_id, term):
        """Fetch student payments for a term."""
        try:
            params = {"student_id_number": student_id, "term": term}
            response = requests.get(
                f"{self.base_url}/student/payments/",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Fetched payments for {student_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching payments for {student_id}: {str(e)}")
            raise

    def get_students_in_debt(self, student_id=None):
        """Fetch students with outstanding balances."""
        try:
            params = {"student_id_number": student_id} if student_id else {}
            response = requests.get(
                f"{self.base_url}/students/accounts-in-debt",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Fetched students in debt for {student_id or 'all students'}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching students in debt: {str(e)}")
            raise

    def get_student_profile(self, student_id):
        """Fetch student profile."""
        try:
            params = {"student_id_number": student_id}
            logger.debug(f"Requesting profile for {student_id}: URL={self.base_url}/student/profile/, Params={params}, Headers={self.headers}")
            response = requests.get(
                f"{self.base_url}/student/profile/",  # Updated endpoint
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Fetched student profile for {student_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching student profile for {student_id}: {str(e)}")
            raise