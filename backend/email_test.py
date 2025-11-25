"""
Blood Sugar Monitoring System - SMTP Email Test Script
=======================================================
Test SMTP email configuration and sending capability.

Purpose:
- Verify SMTP server credentials are correct
- Test email sending functionality
- Validate environment variables are properly configured
- Send test email to verify end-to-end email delivery

Usage:
    python email_test.py

Environment Variables Required:
- SMTP_SERVER: SMTP server address (e.g., smtp.gmail.com)
- SMTP_PORT: SMTP port (e.g., 587 for TLS)
- SMTP_USERNAME: Email account username
- SMTP_PASSWORD: Email account password (App Password for Gmail)

Test Process:
1. Load environment variables from .env file
2. Connect to SMTP server
3. Start TLS encryption
4. Login with credentials
5. Send test email to configured email address
6. Display success/error message

NOTE: This is a simple test script with no functions, just inline code.
"""

import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")

to_email = smtp_username  # send to yourself

subject = "SMTP Test Successful"
message = "This is a test email sent from your Python backend."

email_text = f"Subject: {subject}\n\n{message}"

# Mask credentials for display
masked_username = smtp_username[:3] + '***@' + smtp_username.split('@')[1] if smtp_username and '@' in smtp_username else '***'

try:
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    print(f"Logging in as {masked_username}...")
    server.login(smtp_username, smtp_password)
    server.sendmail(smtp_username, to_email, email_text)
    server.quit()
    print("✓ Email sent successfully!")
    print(f"Check inbox at {masked_username}")
except Exception as e:
    print("✗ Error:", e)

  