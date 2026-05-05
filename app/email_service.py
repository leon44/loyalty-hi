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

from flask import current_app

def send_login_code(recipient_email, code):
    """Sends a 4-digit login code email using MailJet's SMTP server."""
    if current_app.debug:
        logging.info(f'Login code for {recipient_email}: {code}')
        return True

    if not MJ_APIKEY_PUBLIC or not MJ_APIKEY_PRIVATE:
        logging.error('MailJet API keys not configured. Cannot send email.')
        return False

    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Your Hotels International Login Code: {code}'
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = recipient_email

    # Create the plain-text and HTML version of your message
    text = f'Your Hotels International login code is: {code}\n\nThis code expires in 15 minutes and can be used up to 4 times.'
    html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h3 style="color: #333;">Your Login Code</h3>
        <p style="color: #666;">Please enter this 4-digit code in the app to log in to your Hotels International Loyalty account:</p>
        <div style="background-color: #f8f8f8; border: 2px solid #1a1a1a; padding: 20px; text-align: center; margin: 30px 0; border-radius: 8px;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1a1a1a;">{code}</span>
        </div>
        <p style="color: #999; font-size: 14px;">
            <strong>Important:</strong> This code expires in 15 minutes and can be used up to 4 times.<br>
            If you didn't request this code, you can safely ignore this email.
        </p>
    </div>
    '''

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
            logging.info(f'Successfully sent login code email to {recipient_email}.')
        return True
    except Exception as e:
        logging.error(f'Failed to send login code email to {recipient_email}: {e}')
        return False
