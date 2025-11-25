"""Fix Jane Smith staff account password"""
import mysql.connector
import bcrypt

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Check current Jane Smith account
cursor.execute("SELECT * FROM users WHERE user_id = 13")
jane = cursor.fetchone()

print("=" * 80)
print("CURRENT JANE SMITH ACCOUNT")
print("=" * 80)
print(f"User ID: {jane['user_id']}")
print(f"Email: {jane['email']}")
print(f"Name: {jane['first_name']} {jane['last_name']}")
print(f"Role: {jane['role']}")
print(f"Password Hash Length: {len(jane['password_hash'])} chars")
print(f"Created: {jane['created_at']}")

# Generate proper bcrypt hash for password 'staff123'
password = 'staff123'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

print("\n" + "=" * 80)
print("UPDATING PASSWORD")
print("=" * 80)
print(f"New Password: {password}")
print(f"New Hash Length: {len(hashed)} chars")

# Update password
cursor.execute("""
    UPDATE users 
    SET password_hash = %s, updated_at = NOW()
    WHERE user_id = 13
""", (hashed,))

conn.commit()

# Verify update
cursor.execute("SELECT user_id, email, first_name, last_name, LENGTH(password_hash) as hash_len FROM users WHERE user_id = 13")
updated = cursor.fetchone()

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)
print(f"User ID: {updated['user_id']}")
print(f"Email: {updated['email']}")
print(f"Name: {updated['first_name']} {updated['last_name']}")
print(f"Password Hash Length: {updated['hash_len']} chars ✅")

print("\n" + "=" * 80)
print("LOGIN CREDENTIALS FOR JANE SMITH")
print("=" * 80)
print(f"Email: staff2@test.com")
print(f"Password: staff123")
print("=" * 80)

# Show all staff login info
print("\n" + "=" * 80)
print("ALL STAFF LOGIN CREDENTIALS")
print("=" * 80)
print("\n1. Jane Smith")
print("   Email: staff2@test.com")
print("   Password: staff123")
print("\n2. Staff Demo")
print("   Email: staff@clinic.com")
print("   Password: demo123")
print("=" * 80)

cursor.close()
conn.close()

print("\n✅ Jane Smith password fixed successfully!")
