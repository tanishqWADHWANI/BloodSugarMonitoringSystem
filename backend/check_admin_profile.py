"""
Check Admin Profile Data
========================
Verify if admin user has complete profile information in the database.
"""

from models import Database

db = Database()

# Check admin by email
print("Checking admin@clinic.com...")
admin = db.get_user_by_email('admin@clinic.com')

if admin:
    print("\n✓ Admin found in database!")
    print(f"User ID: {admin.get('user_id')}")
    print(f"First Name: {admin.get('first_name')}")
    print(f"Last Name: {admin.get('last_name')}")
    print(f"Email: {admin.get('email')}")
    print(f"Phone: {admin.get('phone')}")
    print(f"DOB: {admin.get('date_of_birth')}")
    print(f"Role: {admin.get('role')}")
    print(f"License ID: {admin.get('license_id')}")
    print(f"Profile Image: {admin.get('profile_image')}")
else:
    print("\n✗ Admin NOT found in database!")
    print("Running create_demo_users.py to create admin...")
    import subprocess
    subprocess.run(['python', 'create_demo_users.py'])

db.close()
