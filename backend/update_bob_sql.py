"""
Blood Sugar Monitoring System - Update Bob Profile Picture Script
==================================================================
Add profile picture URL to Bob's account via direct SQL update.

Purpose:
- Add profile image to Bob's user record (user_id 316)
- Use external image URL (Minion character)
- Test profile_image column functionality
- Verify image URL storage

Usage:
    python update_bob_sql.py

Profile Image:
- User: Bob (user_id 316)
- Image: Minion character from Despicable Me
- URL: https://i.pinimg.com/736x/8b/16/7a/8b167af653c2399dd93b952a48740620.jpg

FUNCTIONS SUMMARY (Total: 1 update function)
=============================================

UPDATE FUNCTIONS:
-----------------
- update_bob_profile_picture():
    Add profile picture to Bob's account
    Process:
        1. Connect to MySQL database
        2. Prepare Minion image URL
        3. Execute UPDATE query: SET profile_image = URL WHERE user_id = 316
        4. Commit changes
        5. Display success message with URL
        6. Show rows affected count
    Returns:
        None (prints status messages)
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'blood_sugar_db'
}

MINION_IMAGE_URL = 'https://i.pinimg.com/736x/8b/16/7a/8b167af653c2399dd93b952a48740620.jpg'

def update_bob_profile_picture():
    """Add profile picture to Bob's account (user_id 316)"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Update Bob's profile image
        sql = "UPDATE users SET profile_image = %s WHERE user_id = 316"
        cursor.execute(sql, (MINION_IMAGE_URL,))
        connection.commit()
        
        print(f"✅ SUCCESS - Profile picture added to Bob (user_id 316)!")
        print(f"Image URL: {MINION_IMAGE_URL}")
        print(f"Rows affected: {cursor.rowcount}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ DATABASE ERROR: {e}")
        return False

if __name__ == '__main__':
    update_bob_profile_picture()
