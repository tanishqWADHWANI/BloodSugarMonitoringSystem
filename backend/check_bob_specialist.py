import mysql.connector
from mysql.connector import Error

def check_bob_specialist():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check Bob's data
            cursor.execute("""
                SELECT user_id, email, first_name, last_name, role,
                       LENGTH(profile_image) as img_length
                FROM users 
                WHERE email = 'bob@x.com'
            """)
            
            bob = cursor.fetchone()
            
            if bob:
                print("=" * 60)
                print("BOB'S CURRENT DATA IN DATABASE")
                print("=" * 60)
                print(f"User ID: {bob['user_id']}")
                print(f"Email: {bob['email']}")
                print(f"First Name: {bob['first_name']}")
                print(f"Last Name: {bob['last_name']}")
                print(f"Role: {bob['role']}")
                print(f"Profile Image Length: {bob['img_length']} chars")
                print("=" * 60)
            else:
                print("Bob not found with bob@x.com")
                
            # Also check if there's a specialist Bob
            cursor.execute("""
                SELECT u.user_id, u.email, u.first_name, u.last_name, u.role,
                       s.specialist_id, s.license_id
                FROM users u
                LEFT JOIN specialists s ON u.user_id = s.user_id
                WHERE u.role = 'specialist' AND u.last_name LIKE '%Smith%'
            """)
            
            specialists = cursor.fetchall()
            print("\nSPECIALISTS WITH LAST NAME SMITH:")
            print("=" * 60)
            for spec in specialists:
                print(f"User ID: {spec['user_id']}")
                print(f"Email: {spec['email']}")
                print(f"Name: {spec['first_name']} {spec['last_name']}")
                print(f"Specialist ID: {spec['specialist_id']}")
                print(f"License ID: {spec['license_id']}")
                print("-" * 60)
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_bob_specialist()
