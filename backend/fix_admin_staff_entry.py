"""
Fix Admin User - Ensure Staff Table Entry
==========================================
Ensures that admin users have corresponding staff table entries
for storing license_id and other staff-related data.
"""

import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Find all admin users
cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE role = 'admin'")
admins = cursor.fetchall()

print(f"Found {len(admins)} admin user(s)")

for admin in admins:
    user_id = admin['user_id']
    email = admin['email']
    print(f"\nChecking admin: {admin['first_name']} {admin['last_name']} ({email}, ID: {user_id})")
    
    # Check if staff entry exists
    cursor.execute("SELECT user_id FROM staff WHERE user_id = %s", (user_id,))
    staff_entry = cursor.fetchone()
    
    if staff_entry:
        print(f"  ✓ Staff entry exists")
    else:
        print(f"  ✗ No staff entry found - creating one...")
        cursor.execute("INSERT INTO staff (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        print(f"  ✓ Staff entry created")

print("\n" + "="*60)
print("All admin users now have staff table entries!")
print("="*60)

cursor.close()
conn.close()
