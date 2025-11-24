"""
Add profile picture for Bob (user 316)
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

# Minion profile picture URL
MINION_IMAGE_URL = 'https://i.pinimg.com/736x/8b/16/7a/8b167af653c2399dd93b952a48740620.jpg'

def add_profile_picture_to_bob():
    """Add profile picture to Bob's account"""
    user_id = 316
    
    print(f"Adding profile picture to user {user_id} (Bob)...")
    
    update_data = {
        'profileImage': MINION_IMAGE_URL
    }
    
    try:
        response = requests.put(
            f'{BASE_URL}/api/users/{user_id}',
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print(f"✅ SUCCESS - Profile picture added to Bob!")
            print(f"Image URL: {MINION_IMAGE_URL}")
            return True
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    add_profile_picture_to_bob()
