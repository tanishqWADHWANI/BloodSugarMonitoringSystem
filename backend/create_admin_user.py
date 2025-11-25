#!/usr/bin/env python3
"""
Blood Sugar Monitoring System - Create Admin User Script
=========================================================
Create or verify demo admin user in database.

Purpose:
- Create demo admin user (user_id 999) if not exists
- Set up admin credentials for testing
- Avoid duplicate admin creation

Usage:
    python create_admin_user.py

Admin Account Created:
- User ID: 999
- Email: admin@clinic.com
- Password: demo123 (SHA256 hashed)
- Role: admin
- Name: Admin User

FUNCTIONS SUMMARY (Total: 1 creation function)
===============================================

USER CREATION FUNCTIONS:
------------------------
- create_demo_admin():
    Create demo admin user if not exists
    Process:
        1. Check if admin user 999 already exists
        2. If exists, display message and exit
        3. If not exists, create new admin user with:
           - User ID: 999
           - Email: admin@clinic.com
           - Password: demo123 (SHA256 hashed)
           - Role: admin
           - First name: Admin
           - Last name: User
        4. Insert into users table
        5. Commit transaction or rollback on error
        6. Display success/failure message
    Returns:
        None (prints status messages)
"""

from models import Database
import hashlib

def create_demo_admin():
    db = Database()
    
    # Check if admin with user_id 999 exists
    admin = db.get_user(999)
    
    if admin:
        print(f"Admin user 999 already exists: {admin.get('email')}")
        return
    
    print("Creating demo admin user with ID 999...")
    
    # Create password hash
    password = 'demo123'
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Insert admin user
    cursor = db.connection.cursor()
    query = """
        INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
    """
    
    try:
        cursor.execute(query, (
            999,
            'admin',
            'Demo',
            'Admin',
            'demo@admin.com',
            '555-9999',
            '1980-01-01',
            password_hash
        ))
        db.connection.commit()
        print("Admin user created successfully!")
        cursor.close()
        
        # Verify creation
        admin = db.get_user(999)
        if admin:
            print(f"Verified: {admin.get('email')}")
            print(f"Name: {admin.get('first_name')} {admin.get('last_name')}")
            print("Login credentials: demo@admin.com / demo123")
        else:
            print("ERROR: Failed to verify admin user")
    except Exception as e:
        print(f"ERROR: {e}")
        db.connection.rollback()
        cursor.close()

if __name__ == '__main__':
    create_demo_admin()
