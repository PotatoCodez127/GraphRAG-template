# tools/email_sender.py
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_confirmation_email(recipient_email: str, full_name: str, start_time: str, meeting_id: str):
    """Sends a meeting confirmation email using SMTP."""
    sender_email = settings.SENDER_EMAIL
    sender_password = settings.SENDER_APP_PASSWORD
    
    if not sender_email or not sender_password:
        logger.error("Sender email or password not configured. Cannot send email.")
        return False

    confirmation_url = f"{settings.API_BASE_URL}/confirm-meeting/{meeting_id}"
    
    # Create the email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Please Confirm Your Onboarding Call with Zappies AI"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    html_body = f"""
    <html>
    <body>
        <p>Hi {full_name},</p>
        <p>Thanks for booking your 'Project Pipeline AI' onboarding call for <strong>{start_time}</strong>.</p>
        <p>To secure your spot, please click the link below to confirm your attendance:</p>
        <p><a href="{confirmation_url}" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Confirm Your Meeting</a></p>
        <p>We're excited to connect with you!</p>
        <p>Best,<br>The Zappies AI Team</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        logger.info(f"Confirmation email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}", exc_info=True)
        return False