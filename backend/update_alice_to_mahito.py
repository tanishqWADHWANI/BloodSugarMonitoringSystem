"""
Blood Sugar Monitoring System - Update Alice to Mahito Script
==============================================================
Change Alice's email address from alice@x.com to mahito@x.com.

Purpose:
- Update demo patient email address
- Test email change functionality
- Verify database update successful

Usage:
    python update_alice_to_mahito.py

Email Change:
- User: Alice Johnson (user_id 315)
- Before: alice@x.com
- After: mahito@x.com

FUNCTIONS SUMMARY (Total: 1 update function)
=============================================

UPDATE FUNCTIONS:
-----------------
- update_alice_email():
    Change Alice's email from alice@x.com to mahito@x.com
    Process:
        1. Connect to MySQL database
        2. Find user with email 'alice@x.com'
        3. Display current user information
        4. Execute UPDATE query to change email to 'mahito@x.com'
        5. Commit changes to database
        6. Verify update successful
        7. Display updated user information
    Returns:
        None (prints status messages)
"""

import mysql.connector
from mysql.connector import Error

def update_alice_email():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # First check if Alice exists
            cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE email = 'alice@x.com'")
            user = cursor.fetchone()
            
            if user:
                print("=" * 60)
                print("FOUND USER TO UPDATE")
                print("=" * 60)
                print(f"User ID: {user['user_id']}")
                print(f"Current Email: {user['email']}")
                print(f"Name: {user['first_name']} {user['last_name']}")
                print("=" * 60)
                
                # Update email to mahito@x.com
                cursor.execute(
                    "UPDATE users SET email = 'mahito@x.com' WHERE email = 'alice@x.com'"
                )
                connection.commit()
                
                print("✅ Email updated successfully!")
                print(f"New Email: mahito@x.com")
                print("=" * 60)
                
                # Verify the update
                cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE email = 'mahito@x.com'")
                updated_user = cursor.fetchone()
                if updated_user:
                    print("VERIFIED UPDATE:")
                    print(f"User ID: {updated_user['user_id']}")
                    print(f"Email: {updated_user['email']}")
                    print(f"Name: {updated_user['first_name']} {updated_user['last_name']}")
                else:
                    print("⚠️ Could not verify update")
            else:
                print("❌ User with email 'alice@x.com' not found!")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_alice_email()
