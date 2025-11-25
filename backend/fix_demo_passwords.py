# This script will update all demo patient passwords to werkzeug hashes for Flask login compatibility
import mysql.connector
from werkzeug.security import generate_password_hash

# Database connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)
cursor = conn.cursor()

# Demo patient emails
emails = [
    'newemail@test.com',
    'test@example.com',
    'tanishq@gmail.com',
    'patient1@test.com',
    'john.doe@example.com'
]

# New password
new_password = 'password123'
hash_pw = generate_password_hash(new_password)

for email in emails:
    cursor.execute("UPDATE users SET password_hash=%s WHERE email=%s", (hash_pw, email))
    print(f"Updated {email}")

conn.commit()
cursor.close()
conn.close()
print("All demo patient passwords updated to werkzeug hash.")
