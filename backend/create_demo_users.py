#!/usr/bin/env python3
"""Create missing staff and admin demo users"""

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
