import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        """Initialize email service"""
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP not configured. Emails disabled.")
    
    def send_email(self, to_email, subject, body, html=False):
        """Send email"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning(f"Email not sent: SMTP not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Email error: {e}")
            return False
    
    def check_and_send_alerts(self, user_id):
        """Check and send alerts if needed"""
        from models import Database
        db = Database()
        
        try:
            abnormal_count = db.get_abnormal_count(user_id, days=7)
            
            if abnormal_count >= 3:
                user = db.get_user(user_id)
                if not user:
                    return
                
                # Create alert
                db.create_alert(user_id, f"{abnormal_count} abnormal readings in last 7 days")
                
                # Send email
                subject = "Blood Sugar Alert"
                body = f"Dear {user['first_name']},\n\nYou have {abnormal_count} abnormal readings in the last 7 days.\n\nPlease consult your healthcare provider.\n\nBest regards,\nBlood Sugar Monitoring Team"
                self.send_email(user['email'], subject, body)
                
                # Send to specialist if assigned
                specialist = db.get_patient_specialist(user_id)
                if specialist:
                    spec_subject = f"Patient Alert: {user['first_name']} {user['last_name']}"
                    spec_body = f"Patient {user['first_name']} {user['last_name']} (ID: {user_id}) has {abnormal_count} abnormal readings."
                    self.send_email(specialist['email'], spec_subject, spec_body)
                
                logger.info(f"Alerts sent for user {user_id}")
        except Exception as e:
            logger.error(f"Alert error: {e}")
        finally:
            db.close()