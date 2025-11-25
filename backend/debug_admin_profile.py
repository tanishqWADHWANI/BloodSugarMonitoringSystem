"""
Debug Admin Profile Loading
============================
Check all aspects of admin profile data flow.
"""

from models import Database
import json

db = Database()

print("="*60)
print("1. CHECKING DATABASE FOR ADMIN USER")
print("="*60)

# Check by ID
admin = db.get_user(999)
if admin:
    print("✓ Admin user found (ID: 999)")
    print(f"  Name: {admin.get('first_name')} {admin.get('last_name')}")
    print(f"  Email: {admin.get('email')}")
    print(f"  Phone: {admin.get('phone')}")
    print(f"  DOB: {admin.get('date_of_birth')}")
    print(f"  Role: {admin.get('role')}")
    print(f"  License ID: {admin.get('license_id')}")
    print(f"  Profile Image: {'Yes' if admin.get('profile_image') else 'No'}")
else:
    print("✗ Admin user NOT found!")

# Check by email
print("\n" + "="*60)
print("2. CHECKING BY EMAIL")
print("="*60)
admin_by_email = db.get_user_by_email('admin@clinic.com')
if admin_by_email:
    print("✓ Admin found by email")
    print(f"  User ID: {admin_by_email.get('user_id')}")
else:
    print("✗ Admin NOT found by email")

# Check staff table entry
print("\n" + "="*60)
print("3. CHECKING STAFF TABLE ENTRY")
print("="*60)
cursor = db._get_cursor()
cursor.execute("SELECT * FROM staff WHERE user_id = 999")
staff_entry = cursor.fetchone()
if staff_entry:
    print("✓ Staff entry exists")
    print(f"  Staff ID: {staff_entry.get('staff_id')}")
    print(f"  User ID: {staff_entry.get('user_id')}")
    print(f"  License ID: {staff_entry.get('license_id')}")
else:
    print("✗ No staff entry found")
    print("  Creating staff entry...")
    cursor.execute("INSERT INTO staff (user_id) VALUES (999)")
    db.connection.commit()
    print("  ✓ Staff entry created")

# Test get_user function with license_id
print("\n" + "="*60)
print("4. TESTING get_user() WITH LICENSE_ID")
print("="*60)
admin_full = db.get_user(999)
if admin_full:
    print("✓ Full admin data retrieved")
    print(f"  Has license_id field: {'license_id' in admin_full}")
    print(f"  License ID value: {admin_full.get('license_id')}")
else:
    print("✗ Failed to get full admin data")

# Check if get_user joins staff table properly
print("\n" + "="*60)
print("5. CHECKING get_user() QUERY")
print("="*60)
cursor.execute("""
    SELECT u.*, s.license_id
    FROM users u
    LEFT JOIN staff s ON u.user_id = s.user_id
    WHERE u.user_id = 999
""")
manual_check = cursor.fetchone()
if manual_check:
    print("✓ Manual query successful")
    print(f"  User ID: {manual_check.get('user_id')}")
    print(f"  First Name: {manual_check.get('first_name')}")
    print(f"  Last Name: {manual_check.get('last_name')}")
    print(f"  Email: {manual_check.get('email')}")
    print(f"  License ID: {manual_check.get('license_id')}")

print("\n" + "="*60)
print("DIAGNOSIS COMPLETE")
print("="*60)

db.close()
