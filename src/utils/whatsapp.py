# src/utils/whatsapp.py

import re
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from src.utils.logger import setup_logger
from config import get_config

config = get_config()
logger = setup_logger(__name__)

# Accepts any international number in E.164 format (e.g. +263..., +1..., +44...)
PHONE_REGEX = re.compile(r'^\+[1-9]\d{7,14}$')

def send_whatsapp_message(to, message):
    """Send a WhatsApp message via Twilio."""
    try:
        to = to.strip()

        # Try auto-correcting if user forgot the '+'
        if not to.startswith('+') and to.replace(' ', '').isdigit():
            to = f'+{to}'

        if not PHONE_REGEX.match(to):
            raise ValueError(f"Invalid phone number format: '{to}'")

        to_whatsapp = f"whatsapp:{to}"
        from_whatsapp = f"whatsapp:{config.TWILIO_WHATSAPP_NUMBER}"

        logger.debug(f"Config values: SID={config.TWILIO_ACCOUNT_SID}, Token=****, Number={from_whatsapp}")
        logger.debug(f"Sending to: {to_whatsapp}")

        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        response = client.messages.create(
            from_=from_whatsapp,
            body=message,
            to=to_whatsapp
        )

        logger.debug(f"Twilio response: {response.__dict__}")
        logger.info(f"WhatsApp message sent to {to}: {response.sid}")
        return response.sid

    except TwilioRestException as e:
        logger.error(f"Twilio error sending WhatsApp message to {to}: {e.code} - {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending WhatsApp message to {to}: {str(e)}")
        raise
