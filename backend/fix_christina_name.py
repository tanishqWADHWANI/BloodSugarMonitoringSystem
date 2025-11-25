#!/usr/bin/env python3
"""
Blood Sugar Monitoring System - Fix Christina Name Script
==========================================================
Remove 'Dr.' prefix from Christina Lee's first name in database.

Purpose:
- Fix data entry error where 'Dr.' was included in first_name
- Update Christina Lee's first_name from 'Dr. Christina' to 'Christina'
- Verify the update was successful

Usage:
    python fix_christina_name.py

User Affected:
- Dr. Christina Lee (user_id 103)
- Before: first_name = 'Dr. Christina', last_name = 'Lee'
- After: first_name = 'Christina', last_name = 'Lee'

FUNCTIONS SUMMARY (Total: 1 fix function)
==========================================

DATA FIX FUNCTIONS:
-------------------
- fix_christina_name():
    Remove 'Dr.' prefix from Christina's first name
    Process:
        1. Get current user record for user_id 103
        2. Display current name
        3. Update first_name to 'Christina' (removing 'Dr.')
        4. Commit database changes
        5. Verify update successful
        6. Display updated name
    Returns:
        None (prints status messages)
"""

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
