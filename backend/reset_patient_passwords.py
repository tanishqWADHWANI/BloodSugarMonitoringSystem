"""Quick script to reset all patient passwords to password123"""
import mysql.connector
from werkzeug.security import generate_password_hash
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Database connection
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'blood_sugar_db')
)

cursor = conn.cursor(dictionary=True)

print("="*80)
print("RESETTING PATIENT PASSWORDS TO 'password123'")
print("="*80)

# Get all patients
cursor.execute("SELECT user_id, email, first_name, last_name FROM users WHERE role = 'patient'")
patients = cursor.fetchall()

# Reset password to password123
new_password = "password123"
new_hash = generate_password_hash(new_password)

count = 0
for patient in patients:
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE user_id = %s",
        (new_hash, patient['user_id'])
    )
    print(f"[OK] {patient['email']} - {patient['first_name']} {patient['last_name']}")
    count += 1

conn.commit()

print("\n" + "="*80)
print(f"SUCCESS! Reset {count} patient passwords to: password123")
print("="*80)
print("\nYou can now login with any patient email and password: password123")

cursor.close()
conn.close()
