import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor(dictionary=True)

# Find Christina Lee's specialist_id
print("Finding Dr. Christina Lee's specialist_id...")
cursor.execute("SELECT * FROM specialists WHERE user_id IN (SELECT user_id FROM users WHERE email LIKE '%clee%' OR email LIKE '%christina%')")
specialists = cursor.fetchall()
print(f"Specialists found: {specialists}")

if specialists:
    specialist_id = specialists[0]['specialist_id']
    print(f"\nDr. Christina Lee's specialist_id: {specialist_id}")
    
    # Check assignments
    print(f"\nChecking assignments for specialist_id {specialist_id}...")
    cursor.execute("SELECT * FROM specialistpatient WHERE specialist_id = %s", (specialist_id,))
    assignments = cursor.fetchall()
    print(f"Assignments found: {assignments}")
    
    # Check Alice's patient_id
    print("\nFinding Alice Johnson's patient_id...")
    cursor.execute("SELECT p.*, u.email FROM patients p JOIN users u ON p.user_id = u.user_id WHERE u.email = 'alice@x.com'")
    alice = cursor.fetchall()
    print(f"Alice's record: {alice}")
    
    if alice:
        alice_patient_id = alice[0]['patient_id']
        print(f"\nAlice's patient_id: {alice_patient_id}")
        
        # Check if assignment exists
        cursor.execute("SELECT * FROM specialistpatient WHERE specialist_id = %s AND patient_id = %s", (specialist_id, alice_patient_id))
        existing = cursor.fetchall()
        
        if existing:
            print(f"✅ Assignment EXISTS: {existing}")
        else:
            print(f"❌ Assignment MISSING - Creating it now...")
            cursor.execute("INSERT INTO specialistpatient (specialist_id, patient_id, assigned_date) VALUES (%s, %s, NOW())", (specialist_id, alice_patient_id))
            conn.commit()
            print("✅ Assignment created!")

cursor.close()
conn.close()
