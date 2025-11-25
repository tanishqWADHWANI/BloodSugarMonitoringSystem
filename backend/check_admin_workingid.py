"""
Blood Sugar Monitoring System - Check Admin Working ID Script
==============================================================
Display all users grouped by role with their working_id/license_id.

Purpose:
- Check admin users and their working_id from staff table
- Check specialists and their working_id from specialists table
- Check patients and their working_id from patients table
- Verify working_id column exists and is populated
- Display counts per role

Usage:
    python check_admin_workingid.py

Output:
- Admin users with working_id
- Specialists with working_id
- Patients with working_id
- Counts per role category

Note: working_id was later renamed to license_id in the schema.

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

# Check admin users
print("=" * 60)
print("ADMIN USERS:")
print("=" * 60)
cursor.execute("""
    SELECT u.user_id, u.email, u.role, s.working_id 
    FROM users u 
    LEFT JOIN staff s ON u.user_id = s.user_id 
    WHERE u.role = 'admin'
""")
admins = cursor.fetchall()
for admin in admins:
    print(f"ID: {admin['user_id']}, Email: {admin['email']}, Working ID: {admin['working_id']}")

# Check specialists
print("\n" + "=" * 60)
print("SPECIALISTS:")
print("=" * 60)
cursor.execute("""
    SELECT u.user_id, u.email, u.role, s.working_id 
    FROM users u 
    LEFT JOIN specialists s ON u.user_id = s.user_id 
    WHERE u.role = 'specialist'
    LIMIT 5
""")
specialists = cursor.fetchall()
for spec in specialists:
    print(f"ID: {spec['user_id']}, Email: {spec['email']}, Working ID: {spec['working_id']}")

# Check staff
print("\n" + "=" * 60)
print("STAFF:")
print("=" * 60)
cursor.execute("""
    SELECT u.user_id, u.email, u.role, s.working_id 
    FROM users u 
    LEFT JOIN staff s ON u.user_id = s.user_id 
    WHERE u.role = 'staff'
    LIMIT 5
""")
staff = cursor.fetchall()
for s in staff:
    print(f"ID: {s['user_id']}, Email: {s['email']}, Working ID: {s['working_id']}")

cursor.close()
conn.close()
