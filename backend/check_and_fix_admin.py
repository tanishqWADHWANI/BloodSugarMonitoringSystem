"""
Quick Check: Does Admin User Exist?
"""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

print("Checking for admin user...")
cursor.execute("SELECT user_id, first_name, last_name, email, role FROM users WHERE role = 'admin' OR user_id = 999")
admins = cursor.fetchall()

if admins:
    print(f"\n✓ Found {len(admins)} admin user(s):")
    for admin in admins:
        print(f"  ID: {admin['user_id']}, Name: {admin['first_name']} {admin['last_name']}, Email: {admin['email']}")
        
        # Check staff entry
        cursor.execute("SELECT * FROM staff WHERE user_id = %s", (admin['user_id'],))
        staff = cursor.fetchone()
        if staff:
            print(f"  ✓ Has staff entry (license_id: {staff.get('license_id')})")
        else:
            print(f"  ✗ NO staff entry - CREATING ONE...")
            cursor.execute("INSERT INTO staff (user_id) VALUES (%s)", (admin['user_id'],))
            conn.commit()
            print(f"  ✓ Staff entry created!")
else:
    print("\n✗ NO ADMIN USER FOUND!")
    print("Creating admin user...")
    import hashlib
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute("""
        INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash)
        VALUES (999, 'admin', 'Admin', 'User', 'admin@clinic.com', '555-0999', '1980-01-01', %s)
    """, (password_hash,))
    conn.commit()
    
    cursor.execute("INSERT INTO staff (user_id) VALUES (999)")
    conn.commit()
    
    print("✓ Admin user created (ID: 999)")
    print("  Email: admin@clinic.com")
    print("  Password: admin123")

cursor.close()
conn.close()
print("\nDone!")
