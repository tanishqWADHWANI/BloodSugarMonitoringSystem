#!/usr/bin/env python3
"""
Blood Sugar Monitoring System - Demo User Creator
==================================================
Create missing staff and admin demo users for the system.

Purpose:
- Creates staff user (user_id 106) if not exists
- Creates admin user (user_id 999) if not exists
- Sets up proper role-specific tables (staff table)
- Uses default passwords for demo purposes

Usage:
    python create_demo_users.py

Demo Accounts Created:
- Staff: staff@clinic.com / demo123 (user_id 106)
- Admin: admin@clinic.com / admin123 (user_id 999)

FUNCTIONS SUMMARY (Total: 1 main function)
===========================================

USER CREATION:
--------------
- create_demo_users():
    Create staff and admin demo users if they don't exist
    Process:
        1. Check if staff user 106 exists
        2. If not, create staff user with:
           - Email: staff@clinic.com
           - Password: demo123 (SHA256 hashed)
           - Role: staff
           - License ID: STAFF-106
        3. Check if admin user 999 exists
        4. If not, create admin user with:
           - Email: admin@clinic.com
           - Password: admin123 (SHA256 hashed)
           - Role: admin
           - License ID: ADMIN-999
        5. Insert into users and staff tables
        6. Commit changes or rollback on error
    Returns:
        None (prints status messages)
"""

from models import Database
import hashlib

def create_demo_users():
    db = Database()
    cursor = db.connection.cursor()
    
    # Check and create staff user 106
    staff = db.get_user(106)
    if not staff:
        print("Creating staff user 106...")
        password_hash = hashlib.sha256('demo123'.encode()).hexdigest()
        
        try:
            # Insert staff user
            cursor.execute("""
                INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (106, 'staff', 'Staff', 'Demo', 'staff@clinic.com', '555-0106', '1985-06-15', password_hash))
            
            # Insert into staff table
            cursor.execute("""
                INSERT INTO staff (user_id, license_id)
                VALUES (%s, %s)
            """, (106, 'STAFF-106'))
            
            db.connection.commit()
            print("Staff user created successfully!")
            print("Email: staff@clinic.com")
            print("Password: demo123")
        except Exception as e:
            print(f"Error creating staff: {e}")
            db.connection.rollback()
    else:
        print(f"Staff user 106 already exists: {staff.get('email')}")
    
    # Check and create admin user 999
    admin = db.get_user(999)
    if not admin:
        print("\nCreating admin user 999...")
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        
        try:
            cursor.execute("""
                INSERT INTO users (user_id, role, first_name, last_name, email, phone, date_of_birth, password_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (999, 'admin', 'Admin', 'User', 'admin@clinic.com', '555-0999', '1980-01-01', password_hash))
            
            db.connection.commit()
            print("Admin user created successfully!")
            print("Email: admin@clinic.com")
            print("Password: admin123")
        except Exception as e:
            print(f"Error creating admin: {e}")
            db.connection.rollback()
    else:
        print(f"\nAdmin user 999 already exists: {admin.get('email')}")
    
    cursor.close()
    
    print("\n=== DEMO USERS SUMMARY ===")
    staff_check = db.get_user(106)
    admin_check = db.get_user(999)
    
    if staff_check:
        print(f"STAFF: {staff_check.get('email')} / demo123 (ID: 106)")
    else:
        print("STAFF: NOT CREATED")
        
    if admin_check:
        print(f"ADMIN: {admin_check.get('email')} / admin123 (ID: 999)")
    else:
        print("ADMIN: NOT CREATED")

if __name__ == '__main__':
    create_demo_users()
