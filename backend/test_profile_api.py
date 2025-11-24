"""
Test script to verify profile API returns health_care_number and working_id
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_get_user(user_id, expected_role):
    """Test getting user data"""
    print(f"\n{'='*60}")
    print(f"Testing GET /api/users/{user_id} (Expected role: {expected_role})")
    print('='*60)
    
    try:
        response = requests.get(f'{BASE_URL}/api/users/{user_id}')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - User data retrieved:")
            print(json.dumps(data, indent=2))
            
            # Check role-specific fields
            if expected_role == 'patient':
                if 'health_care_number' in data:
                    print(f"\n✅ health_care_number found: {data['health_care_number']}")
                else:
                    print("\n❌ health_care_number NOT found")
            elif expected_role in ['specialist', 'staff']:
                if 'working_id' in data:
                    print(f"\n✅ working_id found: {data['working_id']}")
                else:
                    print("\n❌ working_id NOT found")
            
            return data
        else:
            print(f"❌ FAILED - {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_update_user(user_id, update_data):
    """Test updating user data"""
    print(f"\n{'='*60}")
    print(f"Testing PUT /api/users/{user_id}")
    print('='*60)
    print(f"Update data: {json.dumps(update_data, indent=2)}")
    
    try:
        response = requests.put(
            f'{BASE_URL}/api/users/{user_id}',
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - User updated:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"❌ FAILED - {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

if __name__ == '__main__':
    print("\n" + "="*60)
    print("PROFILE API TEST SUITE")
    print("="*60)
    
    # Test patient user (user_id might vary, using 316 from logs)
    print("\n📋 TEST 1: Get Patient User Data")
    patient_data = test_get_user(316, 'patient')
    
    # Test specialist user
    print("\n📋 TEST 2: Get Specialist User Data")
    specialist_data = test_get_user(102, 'specialist')
    
    # Test staff user
    print("\n📋 TEST 3: Get Staff User Data")
    staff_data = test_get_user(105, 'staff')
    
    # Test updating patient profile
    if patient_data:
        print("\n📋 TEST 4: Update Patient Profile")
        update_result = test_update_user(316, {
            'firstName': patient_data.get('first_name', 'Test'),
            'lastName': patient_data.get('last_name', 'Patient'),
            'email': patient_data.get('email', 'test@example.com'),
            'phone': '555-1234',
            'healthCareNumber': patient_data.get('health_care_number', 'HC123456')
        })
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60 + "\n")
