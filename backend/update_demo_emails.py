"""
Blood Sugar Monitoring System - Update Demo Emails Script
==========================================================
Update demo patient email addresses to @x.com domain.

Purpose:
- Remove duplicate older demo users (user_id 201, 202)
- Update email addresses for demo patients (315-319) to @x.com domain
- Standardize demo account email format
- Verify all updates successful

Usage:
    python update_demo_emails.py

Email Updates:
- Alice (315): alice@example.com → alice@x.com
- Bob (316): bob@example.com → bob@x.com
- Sarah (317): sarah@example.com → sarah@x.com
- Michael (318): michael@example.com → michael@x.com
- Emma (319): emma@example.com → emma@x.com

Process:
1. Delete old duplicate users (201, 202)
2. Update emails for users 315-319
3. Verify each update
4. Display final email addresses

NOTE: This is a database migration script with inline code, no functions.
"""

import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor()

# First, delete the older duplicate users (201 and 202) since we have newer ones (315-319)
print("Removing older duplicate users (201, 202)...")
cursor.execute("DELETE FROM users WHERE user_id IN (201, 202)")
print(f"  ✓ Deleted {cursor.rowcount} old user records")

conn.commit()

# Update email addresses for demo patients (315-319)
updates = [
    (315, 'alice@x.com'),
    (316, 'bob@x.com'),
    (317, 'sarah@x.com'),
    (318, 'michael@x.com'),
    (319, 'emma@x.com')
]

print("\nUpdating demo patient email addresses to @x.com domain...")

for user_id, new_email in updates:
    cursor.execute("UPDATE users SET email = %s WHERE user_id = %s", (new_email, user_id))
    print(f"  ✓ Updated user_id {user_id} to {new_email}")

conn.commit()

# Verify updates
print("\nVerifying updates:")
cursor.execute("SELECT user_id, first_name, last_name, email FROM users WHERE user_id IN (315, 316, 317, 318, 319) ORDER BY user_id")
results = cursor.fetchall()

for row in results:
    print(f"  User ID {row[0]}: {row[1]} {row[2]} - {row[3]}")

cursor.close()
conn.close()

print("\n✅ Email updates completed successfully!")
