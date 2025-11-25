"""
Blood Sugar Monitoring System - Check Demo Accounts Script
===========================================================
Verify all demo accounts exist and test password authentication.

Purpose:
- Test all demo account credentials
- Verify password hashing works correctly
- Display demo user information
- Check account roles and IDs

Usage:
    python check_demo_accounts.py

Demo Accounts Tested:
- alice@x.com / password123
- bob@x.com / password123
- sarah@x.com / password123
- michael@x.com / password123
- emma@x.com / password123
- alice@example.com / password123
- bob@example.com / password123

Output:
- Account existence status
- User ID, name, and role
- Password verification result (✅ or ❌)
- Account readiness for login

NOTE: This is a diagnostic script with inline code, no functions.
"""

import mysql.connector
from werkzeug.security import check_password_hash

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

print("="*80)
print("CHECKING DEMO ACCOUNTS")
print("="*80)

# Test accounts from patient.html
demo_accounts = [
    ('alice@x.com', 'password123'),
    ('bob@x.com', 'password123'),
    ('sarah@x.com', 'password123'),
    ('michael@x.com', 'password123'),
    ('emma@x.com', 'password123'),
    ('alice@example.com', 'password123'),
    ('bob@example.com', 'password123'),
]

for email, password in demo_accounts:
    cursor.execute("SELECT user_id, email, password_hash, first_name, last_name, role FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user:
        # Check if password matches
        password_ok = check_password_hash(user['password_hash'], password)
        print(f"\n✓ {email}")
        print(f"  ID: {user['user_id']}, Name: {user['first_name']} {user['last_name']}, Role: {user['role']}")
        print(f"  Password: {'✓ CORRECT' if password_ok else '✗ WRONG'}")
        
        # Check health records
        cursor2 = conn.cursor(dictionary=True)
        cursor2.execute("SELECT COUNT(*) as count FROM bloodsugarreadings WHERE user_id = %s", (user['user_id'],))
        count = cursor2.fetchone()['count']
        cursor2.close()
        print(f"  Health Records: {count}")
    else:
        print(f"\n✗ {email} - NOT FOUND IN DATABASE")

cursor.close()
conn.close()

print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)
print("Update patient.html demo accounts to match database emails:")
print("  - If database has @example.com, update HTML to @example.com")
print("  - OR update database emails to @x.com")
