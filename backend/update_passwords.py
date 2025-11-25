"""
Blood Sugar Monitoring System - Update Passwords Script
========================================================
Update staff and admin password hashes using werkzeug hashing.

Purpose:
- Generate proper werkzeug password hashes for staff and admin
- Update password_hash column for user_id 106 (staff)
- Update password_hash column for user_id 999 (admin)
- Verify hash generation successful

Usage:
    python update_passwords.py

Password Updates:
- Staff (user_id 106): demo123 → werkzeug pbkdf2 hash
- Admin (user_id 999): admin123 → werkzeug pbkdf2 hash

Process:
1. Generate werkzeug hashes using generate_password_hash()
2. Update users table with new hashes
3. Commit changes to database
4. Verify updates by retrieving and displaying hash prefixes

NOTE: This is a database migration script with inline code, no functions.
"""

from werkzeug.security import generate_password_hash
from models import Database

db = Database()
cursor = db.connection.cursor()

# Generate proper hashes
staff_hash = generate_password_hash('demo123')
admin_hash = generate_password_hash('admin123')

print("Updating password hashes...")
print(f"Staff hash: {staff_hash[:50]}...")
print(f"Admin hash: {admin_hash[:50]}...")

# Update staff user
cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = 106", (staff_hash,))
# Update admin user  
cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = 999", (admin_hash,))

db.connection.commit()
cursor.close()

print("\nPasswords updated successfully!")
print("Staff: staff@clinic.com / demo123")
print("Admin: admin@clinic.com / admin123")

# Verify
admin = db.get_user(999)
staff = db.get_user(106)
print(f"\nVerified - Admin hash starts with: {admin['password_hash'][:20]}...")
print(f"Verified - Staff hash starts with: {staff['password_hash'][:20]}...")
