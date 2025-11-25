import mysql.connector
from mysql.connector import Error

def update_alice_email():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # First check if Alice exists
            cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE email = 'alice@x.com'")
            user = cursor.fetchone()
            
            if user:
                print("=" * 60)
                print("FOUND USER TO UPDATE")
                print("=" * 60)
                print(f"User ID: {user['user_id']}")
                print(f"Current Email: {user['email']}")
                print(f"Name: {user['first_name']} {user['last_name']}")
                print("=" * 60)
                
                # Update email to mahito@x.com
                cursor.execute(
                    "UPDATE users SET email = 'mahito@x.com' WHERE email = 'alice@x.com'"
                )
                connection.commit()
                
                print("✅ Email updated successfully!")
                print(f"New Email: mahito@x.com")
                print("=" * 60)
                
                # Verify the update
                cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE email = 'mahito@x.com'")
                updated_user = cursor.fetchone()
                if updated_user:
                    print("VERIFIED UPDATE:")
                    print(f"User ID: {updated_user['user_id']}")
                    print(f"Email: {updated_user['email']}")
                    print(f"Name: {updated_user['first_name']} {updated_user['last_name']}")
                else:
                    print("⚠️ Could not verify update")
            else:
                print("❌ User with email 'alice@x.com' not found!")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_alice_email()
