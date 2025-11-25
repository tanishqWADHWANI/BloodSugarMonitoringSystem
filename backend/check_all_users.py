"""
Blood Sugar Monitoring System - Check All Users Script
=======================================================
Display all users and their health records count from database.

Purpose:
- List all users grouped by role (admin, patient, specialist, staff)
- Display user details (user_id, email, name)
- Count health records for each patient
- Verify user data and roles

Usage:
    python check_all_users.py

Output:
- All users organized by role:
  * Admins
  * Patients
  * Specialists
  * Staff
- Health records count per patient
- Total users per role

NOTE: This is a diagnostic script with inline code, no functions.
"""

import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Get all users
cursor.execute("SELECT user_id, email, first_name, last_name, role FROM users ORDER BY role, user_id")
users = cursor.fetchall()

print("="*80)
print("ALL USERS IN DATABASE:")
print("="*80)

current_role = None
for u in users:
    if u['role'] != current_role:
        current_role = u['role']
        print(f"\n{current_role.upper()}S:")
        print("-"*80)
    print(f"  ID: {u['user_id']:3d} | Email: {u['email']:25s} | Name: {u['first_name']} {u['last_name']}")

# Check health records for patients
print("\n" + "="*80)
print("HEALTH RECORDS COUNT:")
print("="*80)

cursor.execute("""
    SELECT u.user_id, u.email, u.first_name, COUNT(b.reading_id) as record_count
    FROM users u
    LEFT JOIN bloodsugarreadings b ON u.user_id = b.user_id
    WHERE u.role = 'patient'
    GROUP BY u.user_id, u.email, u.first_name
    ORDER BY u.user_id
""")
health_data = cursor.fetchall()

for h in health_data:
    print(f"  {h['email']:30s} - {h['record_count']:3d} records")

cursor.close()
conn.close()
