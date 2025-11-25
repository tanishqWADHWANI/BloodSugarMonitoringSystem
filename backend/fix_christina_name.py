#!/usr/bin/env python3
"""Fix Christina Lee's name - remove Dr. prefix from first_name"""

from models import Database

def fix_christina_name():
    db = Database()
    
    # Check current name
    user = db.get_user(103)
    if user:
        print(f"Current name: {user.get('first_name')} {user.get('last_name')}")
        
        # Update to remove Dr. prefix
        query = "UPDATE users SET first_name = %s WHERE user_id = %s"
        cursor = db.connection.cursor()
        cursor.execute(query, ('Christina', 103))
        db.connection.commit()
        cursor.close()
        
        # Verify update
        user = db.get_user(103)
        print(f"Updated name: {user.get('first_name')} {user.get('last_name')}")
        print("✓ Successfully removed 'Dr.' prefix from Christina's first name")
    else:
        print("✗ User 103 not found")

if __name__ == '__main__':
    fix_christina_name()
