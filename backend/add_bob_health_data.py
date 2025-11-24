import mysql.connector
from datetime import datetime, timedelta
import random

# Connect to database
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='blood_sugar_db'
)

cursor = conn.cursor()

# Bob's user_id
bob_user_id = 202

# Generate 8 days of health data for Bob (prediabetic profile)
print(f"Creating 8 days of health data for Bob (user_id: {bob_user_id})...")

base_date = datetime.now() - timedelta(days=7)

for day_offset in range(8):
    date = base_date + timedelta(days=day_offset)
    
    # Morning reading (fasting)
    morning_value = random.randint(100, 115)  # Prediabetic fasting range
    morning_status = 'normal'
    
    cursor.execute("""
        INSERT INTO bloodsugarreadings 
        (user_id, value, date_time, fasting, food_intake, activity, event, symptoms_notes, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        bob_user_id,
        morning_value,
        date.replace(hour=7, minute=0, second=0),
        1,  # fasting
        'None',
        'Just woke up',
        'Morning reading',
        'Feeling good',
        morning_status
    ))
    
    # Afternoon reading (2 hours after lunch)
    afternoon_value = random.randint(130, 155)  # Slightly elevated
    afternoon_status = 'abnormal' if day_offset == 5 else 'normal'  # One abnormal reading
    
    cursor.execute("""
        INSERT INTO bloodsugarreadings 
        (user_id, value, date_time, fasting, food_intake, activity, event, symptoms_notes, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        bob_user_id,
        afternoon_value,
        date.replace(hour=14, minute=30, second=0),
        0,  # not fasting
        'Sandwich and salad',
        'Light walk',
        'Post-lunch reading',
        'Feeling okay' if afternoon_status == 'normal' else 'Slightly tired',
        afternoon_status
    ))
    
    print(f"  Day {day_offset + 1}: Morning {morning_value} ({morning_status}), Afternoon {afternoon_value} ({afternoon_status})")

conn.commit()
cursor.close()
conn.close()

print(f"\n✓ Successfully created 16 health entries for Bob!")
print(f"  - 8 morning readings (fasting)")
print(f"  - 8 afternoon readings (post-lunch)")
print(f"  - 1 abnormal reading on day 6")
