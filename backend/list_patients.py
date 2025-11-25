"""
Blood Sugar Monitoring System - List Patients Script
=====================================================
Display all patient accounts with email addresses.

Purpose:
- List all users with role='patient'
- Display user ID, name, and email
- Order by user_id
- Verify patient accounts exist

Usage:
    python list_patients.py

FUNCTIONS SUMMARY (Total: 1 listing function)
==============================================

LISTING FUNCTIONS:
------------------
- list_all_patient_emails():
    Display all patient accounts from database
    Process:
        1. Connect to MySQL database
        2. Query all users with role='patient'
        3. Order results by user_id
        4. Display formatted list with:
           - User ID
           - Full name
           - Email address
        5. Show total count
    Output:
        - Formatted patient list
        - User details per patient
    Returns:
        None (prints to console)
"""

import mysql.connector
from mysql.connector import Error

def list_all_patient_emails():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT user_id, email, first_name, last_name, role 
                FROM users 
                WHERE role = 'patient'
                ORDER BY user_id
            """)
            
            users = cursor.fetchall()
            
            print("=" * 60)
            print("ALL PATIENT ACCOUNTS")
            print("=" * 60)
            for user in users:
                print(f"ID: {user['user_id']} | {user['first_name']} {user['last_name']} | {user['email']}")
            print("=" * 60)
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_all_patient_emails()
