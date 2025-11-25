"""
Blood Sugar Monitoring System - Check Alice Profile Image Script
=================================================================
Verify Alice's profile image data in database.

Purpose:
- Check if Alice (alice@x.com) has profile image stored
- Display profile image data length (size)
- Show preview of image data (first 50 characters)
- Verify image column type and storage

Usage:
    python check_alice_profile_image.py

FUNCTIONS SUMMARY (Total: 1 check function)
============================================

DIAGNOSTIC FUNCTIONS:
--------------------
- check_profile_image():
    Verify Alice's profile image status
    Process:
        1. Connect to MySQL database
        2. Query Alice's user record (email='alice@x.com')
        3. Get profile_image column length
        4. Get preview of image data (first 50 chars)
        5. Display results with formatting
    Output:
        - User ID and name
        - Image data length in bytes
        - Image data preview
        - Storage status
    Returns:
        None (prints to console)
"""

import mysql.connector
from mysql.connector import Error

def check_profile_image():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check Alice's profile image
            cursor.execute("""
                SELECT user_id, email, first_name, last_name, 
                       LENGTH(profile_image) as image_length,
                       SUBSTRING(profile_image, 1, 50) as image_preview
                FROM users 
                WHERE email = 'alice@x.com'
            """)
            
            result = cursor.fetchone()
            
            if result:
                print("=" * 60)
                print("ALICE'S PROFILE IMAGE STATUS")
                print("=" * 60)
                print(f"User ID: {result['user_id']}")
                print(f"Email: {result['email']}")
                print(f"Name: {result['first_name']} {result['last_name']}")
                print(f"Image Length: {result['image_length']} characters")
                print(f"Image Preview: {result['image_preview']}")
                print("=" * 60)
                
                if result['image_length'] and result['image_length'] > 0:
                    print("✅ Profile image EXISTS in database")
                    if result['image_preview'] and result['image_preview'].startswith('data:image'):
                        print("✅ Image data format looks correct (base64)")
                    else:
                        print("❌ Image data format looks WRONG")
                else:
                    print("❌ NO profile image in database")
            else:
                print("User alice@x.com not found!")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_profile_image()
