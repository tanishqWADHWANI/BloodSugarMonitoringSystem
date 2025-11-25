import mysql.connector
from mysql.connector import Error

def check_specialists():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check all specialists
            cursor.execute("""
                SELECT u.user_id, u.email, u.first_name, u.last_name, u.role,
                       s.specialist_id, s.license_id,
                       LENGTH(u.profile_image) as img_length
                FROM users u
                LEFT JOIN specialists s ON u.user_id = s.user_id
                WHERE u.role = 'specialist'
                ORDER BY u.user_id
            """)
            
            specialists = cursor.fetchall()
            
            print("=" * 80)
            print("ALL SPECIALISTS IN DATABASE")
            print("=" * 80)
            for spec in specialists:
                print(f"User ID: {spec['user_id']}")
                print(f"Email: {spec['email']}")
                print(f"Name: {spec['first_name']} {spec['last_name']}")
                print(f"Specialist ID: {spec.get('specialist_id', 'N/A')}")
                print(f"License ID: {spec.get('license_id', 'N/A')}")
                print(f"Profile Image: {spec['img_length']} chars" if spec['img_length'] else "No image")
                print("-" * 80)
            
            # Check if jsmith email exists
            cursor.execute("""
                SELECT user_id, email, first_name, last_name 
                FROM users 
                WHERE email LIKE '%jsmith%' OR email LIKE '%smith%'
            """)
            
            smiths = cursor.fetchall()
            if smiths:
                print("\nUSERS WITH 'SMITH' IN EMAIL:")
                print("=" * 80)
                for user in smiths:
                    print(f"ID: {user['user_id']} | {user['first_name']} {user['last_name']} | {user['email']}")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_specialists()
