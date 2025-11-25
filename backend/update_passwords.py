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
