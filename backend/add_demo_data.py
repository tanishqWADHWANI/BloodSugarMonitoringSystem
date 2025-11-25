"""Add demo blood sugar readings to the database"""
from models import Database
from datetime import datetime, timedelta
import random

db = Database()

print("Adding demo blood sugar readings...")

# Get patient user IDs
cursor = db._get_cursor()
cursor.execute("SELECT user_id FROM users WHERE role = 'patient' LIMIT 5")
patients = cursor.fetchall()

if not patients:
    print("No patients found in database!")
    cursor.close()
    exit(1)

print(f"Found {len(patients)} patients")

# Generate readings for the past 3 months
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Fasting']
food_items = [
    'Rice with chicken', 'Pasta with vegetables', 'Salad with fish',
    'Oatmeal with fruits', 'Sandwich', 'Yogurt', 'Apple', 'Banana',
    'Grilled chicken', 'Steamed vegetables', 'Brown rice', 'Whole wheat bread'
]
activities = ['Walking', 'Running', 'Cycling', 'Swimming', 'Gym', 'Yoga', 'None']

readings_added = 0

for patient in patients:
    user_id = patient['user_id']
    print(f"\nAdding readings for patient {user_id}...")
    
    # Add 2-3 readings per day for the past 90 days
    current_date = start_date
    while current_date <= end_date:
        # Random number of readings per day (2-4)
        num_readings = random.randint(2, 4)
        
        for i in range(num_readings):
            # Generate random time of day
            hour = random.choice([7, 12, 18, 21])  # Morning, Noon, Evening, Night
            minute = random.randint(0, 59)
            reading_time = current_date.replace(hour=hour, minute=minute, second=0)
            
            # Generate glucose level based on meal type
            meal_type = meal_types[i % len(meal_types)]
            
            if meal_type == 'Fasting':
                # Fasting: 70-100 normal, 101-125 borderline, >125 abnormal
                glucose = random.randint(70, 150)
            else:
                # After meal: 70-140 normal, 141-180 borderline, >180 abnormal
                glucose = random.randint(80, 220)
            
            # Determine status
            if meal_type == 'Fasting':
                if glucose <= 100:
                    status = 'normal'
                elif glucose <= 125:
                    status = 'borderline'
                else:
                    status = 'abnormal'
            else:
                if glucose <= 140:
                    status = 'normal'
                elif glucose <= 180:
                    status = 'borderline'
                else:
                    status = 'abnormal'
            
            try:
                cursor.execute("""
                    INSERT INTO bloodsugarreadings 
                    (user_id, value, date_time, meal_type, food_consumed, activity, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    glucose,
                    reading_time,
                    meal_type,
                    random.choice(food_items),
                    random.choice(activities),
                    status
                ))
                readings_added += 1
            except Exception as e:
                print(f"Error adding reading: {e}")
        
        current_date += timedelta(days=1)
    
    # Commit after each patient
    db.connection.commit()
    print(f"Added readings for patient {user_id}")

cursor.close()

print(f"\n✅ Successfully added {readings_added} demo blood sugar readings!")
print(f"   Readings span from {start_date.date()} to {end_date.date()}")
