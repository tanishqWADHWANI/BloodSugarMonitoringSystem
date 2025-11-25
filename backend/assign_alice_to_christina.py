"""
Blood Sugar Monitoring System - Assign Alice to Dr. Christina Script
======================================================================
Manually assign Alice Johnson as patient to Dr. Christina Lee.

Purpose:
- Test assignment API endpoint
- Assign Alice (user_id 315) to Dr. Christina Lee (user_id 103)
- Verify assignment in database
- Display assignment results

Usage:
    python assign_alice_to_christina.py

Process:
1. Call POST /api/assignments/assign endpoint
2. Send Alice's patientId (315) and Christina's specialistId (103)
3. Verify API response
4. Query database to confirm assignment
5. Display all of Dr. Christina Lee's patients
6. Show assignment details

Output:
- API response status and message
- Assignment verification status
- List of all Dr. Christina Lee's patients
- Alice's assignment details

NOTE: This is a setup script with inline code, no functions.
"""

import requests
import json

# Manually assign Alice to Dr. Christina Lee
BASE_URL = 'http://127.0.0.1:5000'

# Alice's user_id: 315
# Dr. Christina Lee's user_id: 103

print("Assigning Alice (user_id 315) to Dr. Christina Lee (user_id 103)...")

response = requests.post(
    f"{BASE_URL}/api/assignments/assign",
    json={
        'patientId': '315',  # Alice's user_id
        'specialistId': '103'  # Christina's user_id
    },
    headers={'Content-Type': 'application/json'}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✅ Assignment successful!")
    
    # Verify by checking the specialist's patients
    print("\nVerifying assignment - Getting Dr. Christina Lee's patients...")
    
    import mysql.connector
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="blood_sugar_db"
    )
    cursor = conn.cursor(dictionary=True)
    
    # Find Christina's specialist_id
    cursor.execute("SELECT s.specialist_id FROM specialists s JOIN users u ON s.user_id = u.user_id WHERE u.user_id = 103")
    christina = cursor.fetchone()
    
    if christina:
        specialist_id = christina['specialist_id']
        print(f"Dr. Christina Lee's specialist_id: {specialist_id}")
        
        # Check assignments
        cursor.execute("""
            SELECT sp.*, p.patient_id, u.first_name, u.last_name, u.email
            FROM specialistpatient sp
            JOIN patients p ON sp.patient_id = p.patient_id
            JOIN users u ON p.user_id = u.user_id
            WHERE sp.specialist_id = %s
        """, (specialist_id,))
        
        patients = cursor.fetchall()
        print(f"\nPatients assigned to Dr. Christina Lee:")
        for patient in patients:
            print(f"  - {patient['first_name']} {patient['last_name']} ({patient['email']}) - patient_id: {patient['patient_id']}")
    
    cursor.close()
    conn.close()
else:
    print(f"\n❌ Assignment failed: {response.json()}")
