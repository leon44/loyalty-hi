import os
import requests
import logging

MJ_APIKEY_PUBLIC = os.environ.get('MJ_APIKEY_PUBLIC')
MJ_APIKEY_PRIVATE = os.environ.get('MJ_APIKEY_PRIVATE')
MAILJET_API_URL = 'https://api.mailjet.com/v3.1/send' # Corrected endpoint version

FROM_EMAIL = 'loyalty@hotelsinternational.co.uk' # Replace with a verified sender email in your MailJet account
FROM_NAME = 'Hotels International'

def send_magic_link(recipient_email, magic_link):
    """Sends a magic link email using MailJet's API."""
    if not MJ_APIKEY_PUBLIC or not MJ_APIKEY_PRIVATE:
        logging.error('MailJet API keys not configured. Cannot send email.')
        return False

    data = {
        'Messages': [
            {
                'From': {
                    'Email': FROM_EMAIL,
                    'Name': FROM_NAME
                },
                'To': [
                    {
                        'Email': recipient_email
                    }
                ],
                'Subject': 'Your Magic Link to Log In',
                'TextPart': f'Here is your magic link to log in: {magic_link}',
                'HTMLPart': f'<h3>Your Magic Link</h3><p>Click the link below to log in:</p><p><a href="{magic_link}">{magic_link}</a></p>'
            }
        ]
    }

    try:
        response = requests.post(
            MAILJET_API_URL,
            json=data,
            auth=(MJ_APIKEY_PUBLIC, MJ_APIKEY_PRIVATE)
        )
        response.raise_for_status()
        logging.info(f'Successfully sent magic link email to {recipient_email}. Response: {response.json()}')
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f'Failed to send magic link email to {recipient_email}: {e}')
        if e.response:
            logging.error(f'MailJet API Response: {e.response.text}')
        return False
