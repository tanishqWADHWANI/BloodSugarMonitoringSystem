"""
Blood Sugar Monitoring System - Check Alice Data Script
========================================================
Verify Alice's user account and blood sugar readings.

Purpose:
- Find Alice's user record by email (alice@x.com)
- Count total blood sugar readings for Alice (user_id 315)
- Display last 5 blood sugar readings
- Verify demo data population for Alice

Usage:
    python check_alice_data.py

Output:
- Alice's user information (user_id, email)
- Total count of blood sugar readings
- Last 5 readings with:
  * Date/time
  * Blood sugar value
  * Food intake

NOTE: This is a diagnostic script with inline code, no functions.
"""

import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor()

# Check Alice's user
cursor.execute("SELECT user_id, email FROM users WHERE email LIKE 'alice%'")
print('Alice user:', cursor.fetchall())

# Check readings count
cursor.execute('SELECT COUNT(*) FROM bloodsugarreadings WHERE user_id = 315')
count = cursor.fetchone()[0]
print(f'Readings count for user_id 315: {count}')

# Check last 5 readings
cursor.execute('SELECT date_time, value, food_intake FROM bloodsugarreadings WHERE user_id = 315 ORDER BY date_time DESC LIMIT 5')
print('Last 5 readings:')
for row in cursor.fetchall():
    print(row)

conn.close()
