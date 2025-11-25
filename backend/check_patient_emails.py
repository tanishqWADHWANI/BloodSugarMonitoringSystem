"""
Blood Sugar Monitoring System - Check Patient Emails Script
============================================================
Display all patient emails and verify data availability.

Purpose:
- Retrieve all patients from database
- Display patient count
- Show first 5 patients with email addresses
- Verify patient data structure

Usage:
    python check_patient_emails.py

Output:
- Total patient count
- First 5 patients with:
  * Patient ID
  * Full name
  * Email address

NOTE: This is a diagnostic script with inline code, no functions.
"""

from models import Database

db = Database()
patients = db.get_all_patients()

print(f"Total patients: {len(patients)}")
print("\nFirst 5 patients:")
for p in patients[:5]:
    print(f"Patient {p['patient_id']}: {p.get('first_name', 'No name')} {p.get('last_name', '')} - Email: {p.get('email', 'NO EMAIL')}")
