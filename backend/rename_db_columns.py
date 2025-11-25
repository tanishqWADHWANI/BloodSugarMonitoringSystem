"""
Blood Sugar Monitoring System - Rename DB Columns Script
=========================================================
Migrate database columns from working_id to license_id.

Purpose:
- Rename column working_id to license_id in multiple tables
- Update specialists table schema
- Update staff table schema
- Verify column rename successful
- Maintain data integrity during migration

Usage:
    python rename_db_columns.py

Tables Updated:
1. specialists:
   - working_id → license_id (VARCHAR(50))

2. staff:
   - working_id → license_id (VARCHAR(50))

Migration Steps:
1. ALTER TABLE specialists CHANGE COLUMN working_id license_id
2. ALTER TABLE staff CHANGE COLUMN working_id license_id
3. Verify column structure
4. Display updated schema

NOTE: This is a database migration script with inline code, no functions.
"""

import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor()

print("=" * 80)
print("RENAMING working_id TO license_id IN DATABASE")
print("=" * 80)

try:
    # Rename column in specialists table
    print("\n1. Renaming working_id to license_id in specialists table...")
    cursor.execute("ALTER TABLE specialists CHANGE COLUMN working_id license_id VARCHAR(50) DEFAULT NULL")
    print("   ✓ specialists table updated")
    
    # Rename column in staff table
    print("\n2. Renaming working_id to license_id in staff table...")
    cursor.execute("ALTER TABLE staff CHANGE COLUMN working_id license_id VARCHAR(50) DEFAULT NULL")
    print("   ✓ staff table updated")
    
    conn.commit()
    
    # Verify changes
    print("\n3. Verifying changes...")
    print("\n   Specialists table structure:")
    cursor.execute("DESCRIBE specialists")
    for col in cursor.fetchall():
        if 'license' in col[0] or 'working' in col[0]:
            print(f"      {col[0]:20} {col[1]:20}")
    
    print("\n   Staff table structure:")
    cursor.execute("DESCRIBE staff")
    for col in cursor.fetchall():
        if 'license' in col[0] or 'working' in col[0]:
            print(f"      {col[0]:20} {col[1]:20}")
    
    print("\n" + "=" * 80)
    print("✅ DATABASE SCHEMA SUCCESSFULLY UPDATED")
    print("   working_id → license_id")
    print("=" * 80)
    
except mysql.connector.Error as err:
    print(f"\n❌ Error: {err}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
