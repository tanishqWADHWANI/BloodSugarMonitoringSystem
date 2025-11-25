# Email Alert System - Setup and Testing Guide

## Overview
The Blood Sugar Monitoring System includes an email alert feature that sends notifications to patients and specialists when abnormal blood sugar readings are detected.

## Current Status
✗ **Email alerts are NOT configured** - Environment variables are missing

## How Email Alerts Work

### Automatic Alerts
The system automatically sends email alerts when:
- A patient has **3 or more abnormal readings** in the last **7 days**
- The alert is sent to both the patient AND their assigned specialist
- Alerts are checked periodically by the scheduler service

### Alert Triggers
- **Low Blood Sugar**: < 70 mg/dL
- **High Blood Sugar**: > 180 mg/dL
- **Critical**: < 50 or > 300 mg/dL

## Setup Instructions

### Step 1: Get Gmail App Password (Recommended)

1. **Enable 2-Step Verification**
   - Go to: https://myaccount.google.com/security
   - Click "2-Step Verification" and turn it on
   - Follow the prompts to set up

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account > Security > 2-Step Verification > App Passwords
   - Select "Mail" and "Windows Computer"
   - Click "Generate"
   - Copy the 16-character password (no spaces)

### Step 2: Create .env File

1. Navigate to the `backend` directory
2. Create a new file named `.env` (note: starts with a dot)
3. Add the following configuration:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

**Example:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=bloodsugar.demo@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

### Step 3: Test the Configuration

Run the comprehensive test script:

```bash
cd backend
python test_email_alerts.py
```

### What the Test Does

The test script runs 5 comprehensive tests:

1. **Environment Variables Check** ✓
   - Verifies all SMTP settings are configured
   - Shows which variables are missing

2. **SMTP Server Connection** ✓
   - Tests connection to email server
   - Verifies TLS encryption
   - Validates login credentials

3. **Basic Email Sending** ✓
   - Sends a simple test email
   - Confirms end-to-end delivery works

4. **HTML Alert Email** ✓
   - Sends a beautifully formatted alert
   - Tests the actual alert email template
   - Includes high blood sugar warning

5. **NotificationService Class** ✓
   - Tests the Python class used by the system
   - Verifies integration with the app

### Expected Output (When Configured)

```
============================================================
TEST SUMMARY
============================================================

ENV: PASSED
CONNECTION: PASSED
BASIC: PASSED
HTML: PASSED
SERVICE: PASSED

Total: 5/5 tests passed

🎉 All tests passed! Email alerts are fully functional!
ℹ Check your email inbox to see the test messages
```

## Alternative Email Providers

### Using Outlook/Hotmail

```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Using Yahoo Mail

```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

**Note:** Yahoo also requires app-specific passwords for third-party apps.

## Troubleshooting

### "Authentication Failed"
- **Gmail**: Make sure you're using an App Password, not your regular password
- **2-Step Verification**: Must be enabled for Gmail App Passwords
- **Password**: Check for extra spaces or incorrect characters

### "Connection Timeout"
- Check SMTP_SERVER address is correct
- Verify SMTP_PORT (usually 587 for TLS)
- Check firewall settings

### "No Module Named 'dotenv'"
Install python-dotenv:
```bash
pip install python-dotenv
```

### Emails Not Being Sent
1. Check logs in terminal where `app.py` is running
2. Verify environment variables are loaded
3. Test with `test_email_alerts.py`
4. Check spam folder in email inbox

## How to Verify It's Working in Production

### Method 1: Check Logs
When the app is running, you'll see:
```
Email sent to patient@email.com
Email sent to specialist@email.com
Alerts sent for user 123
```

### Method 2: Trigger an Alert Manually

1. Log in as a patient (e.g., alice@johnson.com)
2. Add 3 high blood sugar readings (> 180 mg/dL)
3. Wait for the scheduler to run (every 30 minutes)
4. Check email inbox for alert

### Method 3: Use the Test Script

Run the test script anytime to verify configuration:
```bash
python backend/test_email_alerts.py
```

## Email Alert Examples

### Patient Alert Email
```
Subject: ⚠️ Blood Sugar Alert - High Reading Detected

Dear John,

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
```

### Specialist Alert Email
```
Subject: Patient Alert: John Doe

Patient John Doe (ID: 123) has 4 abnormal readings 
in the last 7 days.

Please review the patient's recent readings and 
consider scheduling a follow-up appointment.
```

## Files Involved

- `backend/notification_service.py` - Email sending service
- `backend/scheduler_service.py` - Automatic alert checking
- `backend/test_email_alerts.py` - Comprehensive testing script
- `backend/.env` - Configuration file (you need to create this)
- `backend/.env.example` - Example configuration template

## Security Notes

- **Never commit `.env` file to version control** (it contains passwords)
- The `.env` file is already in `.gitignore`
- Use App Passwords instead of regular passwords for Gmail
- Store credentials securely
- Don't share your SMTP credentials

## Quick Start Checklist

- [ ] Enable 2-Step Verification on Gmail
- [ ] Generate Gmail App Password
- [ ] Create `backend/.env` file
- [ ] Add SMTP configuration to `.env`
- [ ] Run `python backend/test_email_alerts.py`
- [ ] Verify you receive test emails
- [ ] Check spam folder if emails don't appear
- [ ] Test with actual patient data

## Need Help?

Common issues and solutions are in the Troubleshooting section above.

For Gmail App Password setup, visit:
https://support.google.com/accounts/answer/185833

---

**Status:** Email system is implemented and ready to use once configured!
