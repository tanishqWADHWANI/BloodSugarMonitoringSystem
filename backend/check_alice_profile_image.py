import mysql.connector
from mysql.connector import Error

def check_profile_image():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Check Alice's profile image
            cursor.execute("""
                SELECT user_id, email, first_name, last_name, 
                       LENGTH(profile_image) as image_length,
                       SUBSTRING(profile_image, 1, 50) as image_preview
                FROM users 
                WHERE email = 'alice@x.com'
            """)
            
            result = cursor.fetchone()
            
            if result:
                print("=" * 60)
                print("ALICE'S PROFILE IMAGE STATUS")
                print("=" * 60)
                print(f"User ID: {result['user_id']}")
                print(f"Email: {result['email']}")
                print(f"Name: {result['first_name']} {result['last_name']}")
                print(f"Image Length: {result['image_length']} characters")
                print(f"Image Preview: {result['image_preview']}")
                print("=" * 60)
                
                if result['image_length'] and result['image_length'] > 0:
                    print("✅ Profile image EXISTS in database")
                    if result['image_preview'] and result['image_preview'].startswith('data:image'):
                        print("✅ Image data format looks correct (base64)")
                    else:
                        print("❌ Image data format looks WRONG")
                else:
                    print("❌ NO profile image in database")
            else:
                print("User alice@x.com not found!")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_profile_image()
