"""
Blood Sugar Monitoring System - Fix Profile Image Column Script
================================================================
Migrate profile_image column from VARCHAR(255) to MEDIUMTEXT.

Purpose:
- Fix profile_image column size limitation
- Change from VARCHAR(255) (255 bytes) to MEDIUMTEXT (16MB)
- Allow storing larger base64-encoded images
- Prevent image upload failures due to size constraints

Usage:
    python fix_profile_image_column.py

Database Migration:
- Table: users
- Column: profile_image
- Before: VARCHAR(255) - max 255 bytes
- After: MEDIUMTEXT - max 16MB

FUNCTIONS SUMMARY (Total: 1 migration function)
================================================

MIGRATION FUNCTIONS:
-------------------
- fix_profile_image_column():
    Alter profile_image column to support larger images
    Process:
        1. Connect to MySQL database
        2. Execute ALTER TABLE statement:
           ALTER TABLE users MODIFY COLUMN profile_image MEDIUMTEXT
        3. Commit database changes
        4. Display success message
    Output:
        - Migration status
        - New column capacity (16MB)
    Returns:
        None (prints status messages)
"""

import mysql.connector
from mysql.connector import Error

def fix_profile_image_column():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("=" * 60)
            print("FIXING profile_image COLUMN SIZE")
            print("=" * 60)
            
            # Change VARCHAR(255) to MEDIUMTEXT (16MB max)
            sql = """
                ALTER TABLE users 
                MODIFY COLUMN profile_image MEDIUMTEXT
            """
            
            cursor.execute(sql)
            connection.commit()
            
            print("✅ Successfully changed profile_image column to MEDIUMTEXT")
            print("   This can now store images up to 16MB")
            print("=" * 60)
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_profile_image_column()
