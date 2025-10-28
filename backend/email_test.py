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

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(smtp_username, to_email, email_text)
    server.quit()
    print("Email sent successfully!")
except Exception as e:
    print("Error:", e)

  