"""
Check Bob's profile image in database
"""
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'blood_sugar_db'
}

def check_bob_profile():
    """Check Bob's profile image"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Get Bob's data
        sql = "SELECT user_id, first_name, last_name, email, profile_image FROM users WHERE user_id = 316"
        cursor.execute(sql)
        bob = cursor.fetchone()
        
        if bob:
            print("✅ Bob's Profile Data:")
            print(f"   User ID: {bob['user_id']}")
            print(f"   Name: {bob['first_name']} {bob['last_name']}")
            print(f"   Email: {bob['email']}")
            print(f"   Profile Image: {bob['profile_image']}")
        else:
            print("❌ Bob not found in database")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"❌ DATABASE ERROR: {e}")

if __name__ == '__main__':
    check_bob_profile()
