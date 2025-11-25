"""
Blood Sugar Monitoring System - Assignment API Test Script
===========================================================
Test patient-to-specialist assignment API functionality.

Purpose:
- Test assignment API endpoint
- Verify Alice (user_id 315) can be assigned to Dr. Christina Lee
- Test database assignment operations
- Validate API responses

Usage:
    python test_assignment.py

Test Cases:
- Assign patient to specialist via API
- Verify assignment in database
- Test GET endpoint for retrieving assignments

FUNCTIONS SUMMARY (Total: 1 test function)
===========================================

TEST FUNCTIONS:
---------------
- test_assign_alice_to_christina():
    Test assigning Alice (user_id 315) to Dr. Christina Lee
    Process:
        1. Connect to MySQL database directly
        2. Find Christina's user_id from specialists table
        3. Create assignment record
        4. Test API endpoint to verify assignment
        5. Print results and status
    Returns:
        None (prints test results)
"""

import requests
import json

# Test the assignment API
BASE_URL = 'http://127.0.0.1:5000'

# Get token (using admin login if needed) - for now test without auth
def test_assign_alice_to_christina():
    """Test assigning Alice (user_id 315) to Dr. Christina Lee"""
    
    # Alice's user_id
    alice_user_id = 315
    
    # Need to find Christina's user_id
    # From database: clee@clinic should be user_id for specialist
    # Let's try finding the user_id first
    
    print("Testing assignment API...")
    
    # Assign Alice (user_id 315) to Christina
    # We need Christina's user_id - let's check the database first
    # For now, let's manually insert and then test the GET endpoint
    
    import mysql.connector
    
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="blood_sugar_db"
    )
    cursor = conn.cursor(dictionary=True)
    
    # Find Christina's user_id
    cursor.execute("SELECT s.user_id, s.specialist_id FROM specialists s JOIN users u ON s.user_id = u.user_id WHERE u.email = 'clee@clinic'")
    christina = cursor.fetchone()
    print(f"Dr. Christina Lee: {christina}")
    
    # Find Alice's patient_id
    cursor.execute("SELECT p.user_id, p.patient_id FROM patients p JOIN users u ON p.user_id = u.user_id WHERE u.email = 'alice@x.com'")
    alice = cursor.fetchone()
    print(f"Alice Johnson: {alice}")
    
    if not christina or not alice:
        print("ERROR: Could not find Christina or Alice")
        return
    
    # Check current assignments
    cursor.execute("SELECT * FROM specialistpatient WHERE specialist_id = %s", (christina['specialist_id'],))
    current = cursor.fetchall()
    print(f"\nCurrent assignments for Christina (specialist_id {christina['specialist_id']}): {current}")
    
    # Test the POST API
    print(f"\nTesting POST /api/assignments/assign...")
    print(f"Assigning patient user_id {alice['user_id']} to specialist user_id {christina['user_id']}")
    
    response = requests.post(
        f"{BASE_URL}/api/assignments/assign",
        json={
            'patientId': alice['user_id'],
            'specialistId': christina['user_id']
        },
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    # Check assignments again
    cursor.execute("SELECT * FROM specialistpatient WHERE specialist_id = %s", (christina['specialist_id'],))
    after = cursor.fetchall()
    print(f"\nAssignments after API call: {after}")
    
    # Test the GET endpoint
    print(f"\nTesting GET /api/specialist/{christina['specialist_id']}/patients...")
    response = requests.get(f"{BASE_URL}/api/specialist/{christina['specialist_id']}/patients")
    print(f"Response status: {response.status_code}")
    print(f"Patients returned: {json.dumps(response.json(), indent=2)}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    test_assign_alice_to_christina()
