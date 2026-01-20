import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# MailJet SMTP Configuration
MJ_SMTP_HOST = 'in-v3.mailjet.com'
MJ_SMTP_PORT = 587
MJ_APIKEY_PUBLIC = os.environ.get('MJ_APIKEY_PUBLIC')
MJ_APIKEY_PRIVATE = os.environ.get('MJ_APIKEY_PRIVATE')

FROM_EMAIL = 'loyalty@hotelsinternational.co.uk'
FROM_NAME = 'Hotels International'

def send_magic_link(recipient_email, magic_link):
    """Sends a magic link email using MailJet's SMTP server."""
    if not MJ_APIKEY_PUBLIC or not MJ_APIKEY_PRIVATE:
        logging.error('MailJet API keys not configured. Cannot send email.')
        return False

    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Your Magic Link to Log In'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = recipient_email

    # Create the plain-text and HTML version of your message
    text = f'Here is your magic link to log in: {magic_link}'
    html = f'<h3>Your Magic Link</h3><p>Click the link below to log in:</p><p><a href="{magic_link}">{magic_link}</a></p>'

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(MJ_SMTP_HOST, MJ_SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(MJ_APIKEY_PUBLIC, MJ_APIKEY_PRIVATE)
            server.sendmail(FROM_EMAIL, recipient_email, msg.as_string())
            logging.info(f'Successfully sent magic link email to {recipient_email}.')
        return True
    except Exception as e:
        logging.error(f'Failed to send magic link email to {recipient_email}: {e}')
        return False
