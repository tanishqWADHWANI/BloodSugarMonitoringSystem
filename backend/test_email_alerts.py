"""
Blood Sugar Monitoring System - Email Alert Testing Script
==========================================================
Comprehensive test for email notification functionality.

This script tests:
1. SMTP configuration validity
2. Basic email sending functionality
3. Alert email generation
4. Environment variable configuration
5. Database integration for alerts

Usage:
    python test_email_alerts.py

Configuration:
- Set SMTP_USERNAME, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT in environment
- For Gmail: Use App Password (not regular password)
  - Go to Google Account > Security > 2-Step Verification > App Passwords
  - Generate password for "Mail" on "Windows Computer"
  - Use this 16-character password as SMTP_PASSWORD

Test Modes:
- Mode 1: Test basic SMTP connection
- Mode 2: Test basic email sending
- Mode 3: Test alert email with HTML formatting
- Mode 4: Test notification service class
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def test_environment_variables():
    """Test 1: Check if all required environment variables are set"""
    print_header("TEST 1: Environment Variables Check")
    
    required_vars = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD')
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask password for security
            display_value = var_value if var_name != 'SMTP_PASSWORD' else '*' * len(var_value)
            print_success(f"{var_name}: {display_value}")
        else:
            print_error(f"{var_name}: NOT SET")
            all_set = False
    
    if all_set:
        print_success("\nAll environment variables are configured!")
        return True
    else:
        print_error("\nSome environment variables are missing!")
        print_warning("\nTo configure email alerts:")
        print_info("1. Create a .env file in the backend directory")
        print_info("2. Add the following lines:")
        print_info("   SMTP_SERVER=smtp.gmail.com")
        print_info("   SMTP_PORT=587")
        print_info("   SMTP_USERNAME=your-email@gmail.com")
        print_info("   SMTP_PASSWORD=your-app-password")
        print_info("\nFor Gmail App Password:")
        print_info("   Google Account > Security > 2-Step Verification > App Passwords")
        return False

def test_smtp_connection():
    """Test 2: Test SMTP server connection"""
    print_header("TEST 2: SMTP Server Connection")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        print_error("Cannot test connection: SMTP credentials not configured")
        return False
    
    try:
        print_info(f"Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print_success("Connected to SMTP server")
        
        print_info("Starting TLS encryption...")
        server.starttls()
        print_success("TLS encryption enabled")
        
        print_info(f"Logging in as {smtp_username}...")
        server.login(smtp_username, smtp_password)
        print_success("Login successful")
        
        server.quit()
        print_success("\nSMTP connection test passed!")
        return True
    except smtplib.SMTPAuthenticationError:
        print_error("Authentication failed - Check username/password")
        print_warning("For Gmail: Use App Password, not regular password")
        return False
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False

def test_basic_email():
    """Test 3: Send a basic test email"""
    print_header("TEST 3: Basic Email Sending")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        print_error("Cannot send email: SMTP credentials not configured")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = 'Blood Sugar System - Test Email'
        msg['From'] = smtp_username
        msg['To'] = smtp_username
        
        body = """
Hello!

This is a test email from the Blood Sugar Monitoring System.

If you received this email, your email alert system is configured correctly!

Test Details:
- SMTP Server: {}
- From: {}
- To: {}

Best regards,
Blood Sugar Monitoring System
        """.format(smtp_server, smtp_username, smtp_username)
        
        msg.attach(MIMEText(body, 'plain'))
        
        print_info(f"Sending test email to {smtp_username}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print_success(f"Test email sent successfully to {smtp_username}")
        print_info("Check your inbox to confirm receipt!")
        return True
    except Exception as e:
        print_error(f"Failed to send email: {str(e)}")
        return False

def test_html_alert_email():
    """Test 4: Send an HTML-formatted alert email"""
    print_header("TEST 4: HTML Alert Email")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        print_error("Cannot send email: SMTP credentials not configured")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '⚠️ Blood Sugar Alert - High Reading Detected'
        msg['From'] = smtp_username
        msg['To'] = smtp_username
        
        # HTML version with styling
        html_body = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                .content { background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }
                .alert-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
                .reading { font-size: 24px; font-weight: bold; color: #dc3545; }
                .footer { background: #004080; color: white; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; }
                .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">🩺 Blood Sugar Alert</h1>
                </div>
                <div class="content">
                    <h2>High Blood Sugar Reading Detected</h2>
                    <p>Dear Test User,</p>
                    <div class="alert-box">
                        <strong>⚠️ Alert:</strong> Your recent blood sugar reading is outside the normal range.
                    </div>
                    <p><strong>Latest Reading:</strong> <span class="reading">185 mg/dL</span></p>
                    <p><strong>Status:</strong> <span style="color:#dc3545;font-weight:bold;">HIGH</span></p>
                    <p><strong>Date/Time:</strong> November 24, 2025 at 2:30 PM</p>
                    <p><strong>Recommendation:</strong></p>
                    <ul>
                        <li>Check your blood sugar again in 1-2 hours</li>
                        <li>Avoid sugary foods and drinks</li>
                        <li>Stay hydrated with water</li>
                        <li>Consider light physical activity</li>
                        <li>Contact your healthcare provider if reading remains high</li>
                    </ul>
                    <a href="http://127.0.0.1:5500/frontend/patient_dashboard.html" class="button">View Dashboard</a>
                </div>
                <div class="footer">
                    <p style="margin:0;">Blood Sugar Monitoring System</p>
                    <p style="margin:5px 0 0 0;font-size:12px;">This is an automated alert. Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version as fallback
        text_body = """
⚠️ BLOOD SUGAR ALERT ⚠️

Dear Test User,

Your recent blood sugar reading is outside the normal range.

Latest Reading: 185 mg/dL
Status: HIGH
Date/Time: November 24, 2025 at 2:30 PM

RECOMMENDATIONS:
- Check your blood sugar again in 1-2 hours
- Avoid sugary foods and drinks
- Stay hydrated with water
- Consider light physical activity
- Contact your healthcare provider if reading remains high

Visit your dashboard: http://127.0.0.1:5500/frontend/patient_dashboard.html

---
Blood Sugar Monitoring System
This is an automated alert. Do not reply to this email.
        """
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        print_info(f"Sending HTML alert email to {smtp_username}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print_success(f"HTML alert email sent successfully to {smtp_username}")
        print_info("Check your inbox - the email should have nice formatting!")
        return True
    except Exception as e:
        print_error(f"Failed to send HTML email: {str(e)}")
        return False

def test_notification_service():
    """Test 5: Test the NotificationService class"""
    print_header("TEST 5: NotificationService Class")
    
    try:
        from notification_service import NotificationService
        
        print_info("Initializing NotificationService...")
        service = NotificationService()
        
        if not service.smtp_username or not service.smtp_password:
            print_warning("NotificationService initialized but SMTP not configured")
            print_info("The service will log warnings instead of sending emails")
            return False
        
        print_success("NotificationService initialized successfully")
        
        smtp_username = os.getenv('SMTP_USERNAME')
        print_info(f"Sending test email via NotificationService to {smtp_username}...")
        
        subject = "NotificationService Test"
        body = "This email was sent using the NotificationService class.\n\nIf you received this, the service is working correctly!"
        
        result = service.send_email(smtp_username, subject, body)
        
        if result:
            print_success("NotificationService test email sent successfully!")
            return True
        else:
            print_error("NotificationService failed to send email")
            return False
    except ImportError:
        print_error("Could not import NotificationService - check notification_service.py")
        return False
    except Exception as e:
        print_error(f"NotificationService test failed: {str(e)}")
        return False

def main():
    """Run all email tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   BLOOD SUGAR MONITORING SYSTEM - EMAIL ALERT TEST         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    results = {}
    
    # Test 1: Environment Variables
    results['env'] = test_environment_variables()
    
    if not results['env']:
        print_warning("\nCannot proceed with email tests - configure environment variables first")
        return
    
    # Test 2: SMTP Connection
    results['connection'] = test_smtp_connection()
    
    if not results['connection']:
        print_warning("\nCannot proceed with email tests - fix SMTP connection first")
        return
    
    # Test 3: Basic Email
    results['basic'] = test_basic_email()
    
    # Test 4: HTML Alert Email
    results['html'] = test_html_alert_email()
    
    # Test 5: NotificationService
    results['service'] = test_notification_service()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{test_name.upper()}: {status}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("\n🎉 All tests passed! Email alerts are fully functional!")
        print_info("Check your email inbox to see the test messages")
    else:
        print_warning(f"\n⚠️ {total - passed} test(s) failed - email alerts may not work properly")

if __name__ == "__main__":
    main()
