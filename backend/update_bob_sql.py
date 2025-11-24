"""
Direct SQL update to add profile picture for Bob
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
