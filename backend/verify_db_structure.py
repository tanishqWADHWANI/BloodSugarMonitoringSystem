import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("DATABASE STRUCTURE CHECK FOR WORKING_ID SUPPORT")
print("=" * 80)

# Check specialists table structure
print("\n1. SPECIALISTS TABLE STRUCTURE:")
print("-" * 80)
cursor.execute("DESCRIBE specialists")
for col in cursor.fetchall():
    print(f"   {col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5}")

# Check staff table structure
print("\n2. STAFF TABLE STRUCTURE:")
print("-" * 80)
cursor.execute("DESCRIBE staff")
for col in cursor.fetchall():
    print(f"   {col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5}")

# Check patients table structure
print("\n3. PATIENTS TABLE STRUCTURE:")
print("-" * 80)
cursor.execute("DESCRIBE patients")
for col in cursor.fetchall():
    print(f"   {col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5}")

# Check users table for profile_image
print("\n4. USERS TABLE (relevant columns):")
print("-" * 80)
cursor.execute("DESCRIBE users")
for col in cursor.fetchall():
    if col['Field'] in ['user_id', 'role', 'profile_image']:
        print(f"   {col['Field']:20} {col['Type']:30} {col['Null']:5}")

# Count users with working_id
print("\n" + "=" * 80)
print("DATA VERIFICATION - Users with Working IDs:")
print("=" * 80)

cursor.execute("""
    SELECT COUNT(*) as total FROM specialists WHERE working_id IS NOT NULL
""")
spec_count = cursor.fetchone()['total']
print(f"Specialists with working_id: {spec_count}")

cursor.execute("""
    SELECT COUNT(*) as total FROM staff WHERE working_id IS NOT NULL
""")
staff_count = cursor.fetchone()['total']
print(f"Staff with working_id: {staff_count}")

# Check if any admin users exist in staff table
cursor.execute("""
    SELECT COUNT(*) as total 
    FROM users u 
    INNER JOIN staff s ON u.user_id = s.user_id 
    WHERE u.role = 'admin'
""")
admin_staff = cursor.fetchone()['total']
print(f"Admin users in staff table: {admin_staff}")

# Sample data
print("\n" + "=" * 80)
print("SAMPLE DATA:")
print("=" * 80)

print("\nSpecialists (sample):")
cursor.execute("""
    SELECT u.user_id, u.email, s.working_id 
    FROM users u 
    INNER JOIN specialists s ON u.user_id = s.user_id 
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"   ID: {row['user_id']}, Email: {row['email']}, Working ID: {row['working_id']}")

print("\nStaff (sample):")
cursor.execute("""
    SELECT u.user_id, u.email, s.working_id 
    FROM users u 
    INNER JOIN staff s ON u.user_id = s.user_id 
    WHERE u.role = 'staff'
    LIMIT 3
""")
for row in cursor.fetchall():
    print(f"   ID: {row['user_id']}, Email: {row['email']}, Working ID: {row['working_id']}")

print("\n" + "=" * 80)
print("✅ DATABASE STRUCTURE CHECK COMPLETE")
print("=" * 80)

cursor.close()
conn.close()
