"""
Blood Sugar Monitoring System - Demo Data Generator
====================================================
This script populates the database with realistic demo blood sugar readings.

Purpose:
- Creates sample blood sugar readings for existing patients in the database
- Generates 90 days of historical data (2-4 readings per day per patient)
- Includes realistic variations based on meal types, food, and activities
- Useful for testing, demonstrations, and UI development

Usage:
    python add_demo_data.py

Note: Requires patients to exist in the database first.
Use this after running the main database setup and creating demo accounts.
"""

from models import Database  # Import Database class for MySQL operations
from datetime import datetime, timedelta  # Date/time manipulation
import random  # Random number generation for realistic data variation

# Initialize database connection
db = Database()

print("Adding demo blood sugar readings...")

# Get all patient user IDs from database (limit to 5 for demo purposes)
cursor = db._get_cursor()  # Get database cursor for SQL queries
cursor.execute("SELECT user_id FROM users WHERE role = 'patient' LIMIT 5")
patients = cursor.fetchall()  # Fetch all patient records

# Check if any patients exist
if not patients:
    print("No patients found in database!")
    cursor.close()  # Close cursor before exiting
    exit(1)  # Exit with error code

print(f"Found {len(patients)} patients")

# Define date range for historical data (past 3 months)
end_date = datetime.now()  # Current date/time
start_date = end_date - timedelta(days=90)  # 90 days ago

# Define realistic meal types for blood sugar readings
meal_types = ['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Fasting']

# List of common food items to associate with readings
food_items = [
    'Rice with chicken', 'Pasta with vegetables', 'Salad with fish',
    'Oatmeal with fruits', 'Sandwich', 'Yogurt', 'Apple', 'Banana',
    'Grilled chicken', 'Steamed vegetables', 'Brown rice', 'Whole wheat bread'
]

# Physical activities that might affect blood sugar
activities = ['Walking', 'Running', 'Cycling', 'Swimming', 'Gym', 'Yoga', 'None']

readings_added = 0  # Counter for total readings added

# Generate readings for each patient
for patient in patients:
    user_id = patient['user_id']  # Extract patient's user ID
    print(f"\nAdding readings for patient {user_id}...")
    
    # Add 2-4 readings per day for the past 90 days
    current_date = start_date  # Start from 90 days ago
    while current_date <= end_date:  # Loop through each day
        # Random number of readings per day (simulates real patient behavior)
        num_readings = random.randint(2, 4)
        
        # Generate each reading for this day
        for i in range(num_readings):
            # Generate random time of day based on typical meal times
            hour = random.choice([7, 12, 18, 21])  # 7am, 12pm, 6pm, 9pm
            minute = random.randint(0, 59)  # Random minute
            reading_time = current_date.replace(hour=hour, minute=minute, second=0)
            
            # Generate glucose level based on meal type (realistic ranges)
            meal_type = meal_types[i % len(meal_types)]  # Cycle through meal types
            
            if meal_type == 'Fasting':
                # Fasting glucose: 70-100 normal, 101-125 borderline, >125 abnormal
                glucose = random.randint(70, 150)  # Generate value with some variation
            else:
                # Post-meal glucose: 70-140 normal, 141-180 borderline, >180 abnormal
                glucose = random.randint(80, 220)  # Higher range after eating
            
            # Determine status based on glucose value and meal type (medical thresholds)
            if meal_type == 'Fasting':
                # Apply fasting glucose thresholds
                if glucose <= 100:
                    status = 'normal'  # Normal fasting glucose
                elif glucose <= 125:
                    status = 'borderline'  # Pre-diabetes range
                else:
                    status = 'abnormal'  # Diabetes range
            else:
                # Apply post-meal glucose thresholds
                if glucose <= 140:
                    status = 'normal'  # Normal post-meal glucose
                elif glucose <= 180:
                    status = 'borderline'  # Elevated but not diabetic
                else:
                    status = 'abnormal'  # Diabetes range
            
            try:
                # Insert blood sugar reading into database
                cursor.execute("""
                    INSERT INTO bloodsugarreadings 
                    (user_id, value, date_time, meal_type, food_consumed, activity, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,  # Patient's user ID
                    glucose,  # Blood glucose level (mg/dL)
                    reading_time,  # Date and time of reading
                    meal_type,  # Type of meal (Breakfast, Lunch, Dinner, etc.)
                    random.choice(food_items),  # Random food item from list
                    random.choice(activities),  # Random activity from list
                    status  # Status classification (normal, borderline, abnormal)
                ))
                readings_added += 1  # Increment counter for successful insert
            except Exception as e:
                # Log any errors that occur during insertion
                print(f"Error adding reading: {e}")
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Commit transaction after each patient (saves all readings for this patient to database)
    db.connection.commit()
    print(f"Added readings for patient {user_id}")

# Close database cursor to free resources
cursor.close()

# Print summary of data generation
print(f"\n✅ Successfully added {readings_added} demo blood sugar readings!")
print(f"   Readings span from {start_date.date()} to {end_date.date()}")
