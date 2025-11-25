import mysql.connector
from mysql.connector import Error

def fix_profile_image_column():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='blood_sugar_db',
            user='root',
            password=''
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("=" * 60)
            print("FIXING profile_image COLUMN SIZE")
            print("=" * 60)
            
            # Change VARCHAR(255) to MEDIUMTEXT (16MB max)
            sql = """
                ALTER TABLE users 
                MODIFY COLUMN profile_image MEDIUMTEXT
            """
            
            cursor.execute(sql)
            connection.commit()
            
            print("✅ Successfully changed profile_image column to MEDIUMTEXT")
            print("   This can now store images up to 16MB")
            print("=" * 60)
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_profile_image_column()
