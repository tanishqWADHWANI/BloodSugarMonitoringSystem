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
