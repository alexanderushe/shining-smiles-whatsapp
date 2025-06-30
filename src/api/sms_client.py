import requests
import json
from src.utils.logger import setup_logger
from config import get_config

config = get_config()
logger = setup_logger(__name__)

class SMSClient:
    """Client for Shining Smiles SMS API."""
    def __init__(self):
        self.base_url = config.SMS_API_BASE_URL
        self.api_key = config.SMS_API_KEY
        logger.info(f"Initializing SMSClient with base_url: {self.base_url}, api_key: {self.api_key}")
        if not self.base_url:
            logger.error("SMS_API_BASE_URL not set")
            raise ValueError("SMS_API_BASE_URL environment variable is required")
        if not self.api_key:
            logger.error("SMS_API_KEY not set")
            raise ValueError("SMS_API_KEY environment variable is required")
        self.headers = {
            "Authorization": f"Api-Key {self.api_key.strip()}",
            "User-Agent": "ShiningSmilesWhatsApp/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def safe_json_response(self, response):
        try:
            return response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}. Raw response: {response.text}")
            return {"error": "Invalid JSON response", "raw": response.text}

    def get_student_account_statement(self, student_id, term):
        """Fetch student account statement."""
        try:
            params = {"student_id_number": student_id, "term": term}
            url = f"{self.base_url}/student/account-statement/"
            logger.debug(f"Requesting account statement: {url} | Params: {params} | Headers: {self.headers}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=False)
            logger.debug(f"Response [{response.status_code}]: {response.text}")
            response.raise_for_status()
            return self.safe_json_response(response)
        except requests.RequestException as e:
            logger.error(f"Error fetching account statement: {str(e)}, Response: {e.response.text if e.response else 'No response'}")
            raise

    def get_student_payments(self, student_id, term):
        """Fetch student payment data."""
        try:
            params = {"student_id_number": student_id, "term": term}
            url = f"{self.base_url}/student/payments/"
            logger.debug(f"Requesting payments: {url} | Params: {params} | Headers: {self.headers}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=False)
            logger.debug(f"Payment Response [{response.status_code}]: {response.text}")
            response.raise_for_status()
            return self.safe_json_response(response)
        except requests.RequestException as e:
            logger.error(f"Error fetching payments: {str(e)}, Response: {e.response.text if e.response else 'No response'}")
            raise

    def get_students_in_debt(self, student_id=None):
        """Fetch students with outstanding balances."""
        try:
            params = {"student_id_number": student_id} if student_id else {}
            url = f"{self.base_url}/students/accounts-in-debt/"
            logger.debug(f"Requesting debt data: {url} | Params: {params} | Headers: {self.headers}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=False)
            logger.debug(f"Debt Response [{response.status_code}]: {response.text}")
            response.raise_for_status()
            return self.safe_json_response(response)
        except requests.RequestException as e:
            logger.error(f"Error fetching debt data: {str(e)}, Response: {e.response.text if e.response else 'No response'}")
            raise

    def get_student_profile(self, student_id):
        """Fetch student profile."""
        try:
            params = {"student_id_number": student_id}
            url = f"{self.base_url}/student-profile/"
            logger.debug(f"Requesting profile: {url} | Params: {params} | Headers: {self.headers}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30, verify=False)
            logger.debug(f"Profile Response [{response.status_code}]: {response.text}")
            response.raise_for_status()
            return self.safe_json_response(response)
        except requests.RequestException as e:
            logger.error(f"Error fetching profile: {str(e)}, Response: {e.response.text if e.response else 'No response'}")
            raise
