"""Check all staff accounts and their details"""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Get all staff from users table
print("=" * 100)
print("ALL STAFF ACCOUNTS IN USERS TABLE")
print("=" * 100)

cursor.execute("""
    SELECT user_id, email, first_name, last_name, role, created_at
    FROM users 
    WHERE role = 'staff'
    ORDER BY user_id
""")

staff_users = cursor.fetchall()

print(f"{'User ID':<10} {'Email':<35} {'Name':<25} {'Created'}")
print("-" * 100)

for s in staff_users:
    name = f"{s['first_name']} {s['last_name']}"
    created = s['created_at'].strftime("%Y-%m-%d %H:%M:%S") if s['created_at'] else ""
    print(f"{s['user_id']:<10} {s['email']:<35} {name:<25} {created}")

print(f"\nTotal Staff in Users: {len(staff_users)}")

# Check staff table
print("\n" + "=" * 100)
print("STAFF TABLE ENTRIES")
print("=" * 100)

cursor.execute("""
    SELECT s.staff_id, s.user_id, s.license_id, u.email, u.first_name, u.last_name
    FROM staff s
    LEFT JOIN users u ON s.user_id = u.user_id
    ORDER BY s.staff_id
""")

staff_table = cursor.fetchall()

print(f"{'Staff ID':<12} {'User ID':<10} {'License ID':<15} {'Email':<35} {'Name'}")
print("-" * 100)

for s in staff_table:
    name = f"{s['first_name']} {s['last_name']}" if s['first_name'] else "MISSING USER"
    email = s['email'] if s['email'] else "N/A"
    license_id = s['license_id'] if s['license_id'] else "None"
    print(f"{s['staff_id']:<12} {s['user_id']:<10} {license_id:<15} {email:<35} {name}")

print(f"\nTotal Staff in Staff Table: {len(staff_table)}")

# Check if Staff Demo is in staff table
print("\n" + "=" * 100)
print("STAFF DEMO (User ID 106) DETAILS")
print("=" * 100)

cursor.execute("""
    SELECT u.*, s.staff_id, s.license_id
    FROM users u
    LEFT JOIN staff s ON u.user_id = s.user_id
    WHERE u.user_id = 106
""")

staff_demo = cursor.fetchone()

if staff_demo:
    print(f"User ID: {staff_demo['user_id']}")
    print(f"Email: {staff_demo['email']}")
    print(f"Name: {staff_demo['first_name']} {staff_demo['last_name']}")
    print(f"Role: {staff_demo['role']}")
    print(f"Staff ID: {staff_demo['staff_id'] if staff_demo['staff_id'] else 'NOT IN STAFF TABLE ❌'}")
    print(f"License ID: {staff_demo['license_id'] if staff_demo['license_id'] else 'None'}")
    print(f"Created: {staff_demo['created_at']}")
else:
    print("User 106 not found")

# Check password hash exists
cursor.execute("SELECT user_id, email, LENGTH(password_hash) as hash_length FROM users WHERE role = 'staff'")
pwd_check = cursor.fetchall()

print("\n" + "=" * 100)
print("PASSWORD STATUS")
print("=" * 100)
print(f"{'User ID':<10} {'Email':<35} {'Password Hash Length'}")
print("-" * 100)

for p in pwd_check:
    print(f"{p['user_id']:<10} {p['email']:<35} {p['hash_length']} chars")

cursor.close()
conn.close()
