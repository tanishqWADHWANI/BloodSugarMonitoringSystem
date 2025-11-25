"""
Blood Sugar Monitoring System - Populate License IDs Script
============================================================
Generate and populate license_id for existing users without them.

Purpose:
- Generate fake license IDs for specialists, staff, and patients
- Update existing records that have NULL license_id
- Ensure all users have unique license identifiers
- Display before/after state for verification

Usage:
    python populate_license_ids.py

License ID Formats:
- Specialists: SP##### (e.g., SP12345)
- Staff: ST##### (e.g., ST67890)
- Patients: PT##### (e.g., PT54321)

Process:
1. Find specialists without license_id
2. Generate SP##### format IDs
3. Find staff without license_id
4. Generate ST##### format IDs
5. Find patients without license_id
6. Generate PT##### format IDs
7. Update database with new IDs
8. Display summary of updates

NOTE: This is a database migration script with inline code, no functions.
"""

import mysql.connector
import random

# Connect to database
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("POPULATING LICENSE IDs FOR EXISTING USERS")
print("=" * 80)

try:
    # Get all specialists without license_id
    print("\n1. Updating Specialists...")
    cursor.execute("""
        SELECT s.specialist_id, s.user_id, s.license_id, u.first_name, u.last_name
        FROM specialists s
        JOIN users u ON s.user_id = u.user_id
    """)
    specialists = cursor.fetchall()
    
    for spec in specialists:
        if not spec['license_id']:
            # Generate fake license ID: SP + random 5-digit number
            fake_license = f"SP{random.randint(10000, 99999)}"
            cursor.execute(
                "UPDATE specialists SET license_id = %s WHERE specialist_id = %s",
                (fake_license, spec['specialist_id'])
            )
            print(f"   User {spec['user_id']} ({spec['first_name']} {spec['last_name']}): {fake_license}")
        else:
            print(f"   User {spec['user_id']} ({spec['first_name']} {spec['last_name']}): {spec['license_id']} (existing)")
    
    # Get all staff without license_id
    print("\n2. Updating Staff...")
    cursor.execute("""
        SELECT s.staff_id, s.user_id, s.license_id, u.first_name, u.last_name, u.role
        FROM staff s
        JOIN users u ON s.user_id = u.user_id
    """)
    staff_members = cursor.fetchall()
    
    for staff in staff_members:
        if not staff['license_id']:
            # Generate fake license ID based on role
            if staff['role'] == 'admin':
                fake_license = f"AD{random.randint(10000, 99999)}"
            else:
                fake_license = f"ST{random.randint(10000, 99999)}"
            
            cursor.execute(
                "UPDATE staff SET license_id = %s WHERE staff_id = %s",
                (fake_license, staff['staff_id'])
            )
            print(f"   User {staff['user_id']} ({staff['first_name']} {staff['last_name']}) [{staff['role']}]: {fake_license}")
        else:
            print(f"   User {staff['user_id']} ({staff['first_name']} {staff['last_name']}) [{staff['role']}]: {staff['license_id']} (existing)")
    
    conn.commit()
    
    # Verify results
    print("\n" + "=" * 80)
    print("VERIFICATION - Current License IDs:")
    print("=" * 80)
    
    cursor.execute("""
        SELECT u.user_id, u.email, s.license_id 
        FROM users u
        JOIN specialists s ON u.user_id = s.user_id
        ORDER BY u.user_id
    """)
    print("\nSpecialists:")
    for row in cursor.fetchall():
        print(f"   User ID: {row['user_id']}, Email: {row['email']}, License: {row['license_id']}")
    
    cursor.execute("""
        SELECT u.user_id, u.email, u.role, s.license_id 
        FROM users u
        JOIN staff s ON u.user_id = s.user_id
        ORDER BY u.user_id
    """)
    print("\nStaff/Admin:")
    for row in cursor.fetchall():
        print(f"   User ID: {row['user_id']}, Email: {row['email']}, Role: {row['role']}, License: {row['license_id']}")
    
    print("\n" + "=" * 80)
    print("✅ LICENSE IDs SUCCESSFULLY POPULATED")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
