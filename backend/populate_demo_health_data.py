"""
Blood Sugar Monitoring System - Demo Health Data Populator
===========================================================
Populate health history data for all demo patients in the database.
Creates 8 entries per patient with varying blood sugar readings including abnormal values.

Purpose:
- Populates comprehensive health data for 5 demo patient accounts
- Creates realistic blood sugar patterns based on health profiles
- Includes abnormal readings for testing alert systems
- Generates time-series data for testing charts and trends

Usage:
    python populate_demo_health_data.py

Demo Patients:
- Alice (user_id 315): Diabetic with strict monitoring, occasional spikes
- Bob (user_id 316): Prediabetic, borderline readings
- Sarah (user_id 317): Type 2 diabetes, moderate control
- Michael (user_id 318): Well controlled diabetes
- Emma (user_id 319): Newly diagnosed, learning patterns

FUNCTIONS SUMMARY (Total: 6 data population functions)
=======================================================

DATA GENERATION:
----------------
- generate_reading_for_day(profile, day_number, is_abnormal_day):
    Generate blood sugar reading for specific day based on health profile
    Args:
        profile (dict): Health profile with blood sugar ranges
        day_number (int): Day number (1-8)
        is_abnormal_day (bool): Whether to generate abnormal reading
    Returns:
        float: Blood sugar value in mg/dL

- get_meal_type_for_day(day_number):
    Determine meal type based on day number (rotating pattern)
    Args:
        day_number (int): Day number (1-8)
    Returns:
        str: Meal type (Breakfast/Lunch/Dinner/Snack/Fasting)

- get_food_intake(meal_type):
    Get appropriate food description for meal type
    Args:
        meal_type (str): Type of meal
    Returns:
        str: Food description

- get_activity(day_number):
    Get activity description for day
    Args:
        day_number (int): Day number
    Returns:
        str: Activity description

DATABASE OPERATIONS:
--------------------
- populate_patient_data(connection, patient):
    Populate 8 days of health data for single patient
    Args:
        connection: MySQL database connection
        patient (dict): Patient info with user_id, name, profile
    Returns:
        None (commits to database)

MAIN EXECUTION:
---------------
- main():
    Main function to populate data for all demo patients
    Process:
        1. Connect to MySQL database
        2. Delete existing readings for demo patients (clean slate)
        3. Populate 8 entries per patient with realistic patterns
        4. Include abnormal readings for testing
        5. Commit all changes
        6. Display summary
"""

import mysql.connector
from datetime import datetime, timedelta
import random

# Database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'blood_sugar_db'
}

# Demo patients to populate (from @x.com domain - the active demo accounts)
DEMO_PATIENTS = [
    {'user_id': 315, 'name': 'Alice', 'profile': 'diabetic_strict'},
    {'user_id': 316, 'name': 'Bob', 'profile': 'prediabetic'},
    {'user_id': 317, 'name': 'Sarah', 'profile': 'diabetic_moderate'},
    {'user_id': 318, 'name': 'Michael', 'profile': 'well_controlled'},
    {'user_id': 319, 'name': 'Emma', 'profile': 'newly_diagnosed'}
]

# Health profiles with different patterns
HEALTH_PROFILES = {
    'diabetic_strict': {
        'blood_sugar_range': (85, 185),  # Wide range with spikes
        'abnormal_days': [3, 4],  # Days with high readings
        'medications': 'Metformin 500mg',
        'description': 'Strict monitoring with occasional spikes'
    },
    'prediabetic': {
        'blood_sugar_range': (95, 150),  # Extended range to allow abnormal readings
        'abnormal_days': [5],
        'medications': 'Diet and exercise only',
        'description': 'Prediabetic - borderline readings'
    },
    'diabetic_moderate': {
        'blood_sugar_range': (90, 165),
        'abnormal_days': [2, 4],
        'medications': 'Metformin 850mg + Glipizide',
        'description': 'Type 2 diabetes - moderate control'
    },
    'well_controlled': {
        'blood_sugar_range': (85, 145),  # Slightly extended to allow occasional high readings
        'abnormal_days': [],
        'medications': 'Metformin 500mg',
        'description': 'Well controlled diabetes'
    },
    'newly_diagnosed': {
        'blood_sugar_range': (100, 180),  # Extended range for higher readings
        'abnormal_days': [1, 2, 3],
        'medications': 'Metformin 500mg (new)',
        'description': 'Newly diagnosed - adjusting to treatment'
    }
}

# Food options for variety
BREAKFAST_OPTIONS = [
    'Oatmeal with berries and nuts',
    'Scrambled eggs with whole wheat toast',
    'Greek yogurt with granola',
    'Vegetable omelet with avocado',
    'Steel-cut oats with cinnamon'
]

LUNCH_OPTIONS = [
    'Grilled chicken salad with olive oil',
    'Turkey sandwich on whole grain bread',
    'Quinoa bowl with vegetables',
    'Lentil soup with mixed greens',
    'Baked salmon with brown rice'
]

DINNER_OPTIONS = [
    'Grilled fish with steamed vegetables',
    'Chicken stir-fry with broccoli',
    'Lean beef with sweet potato',
    'Tofu and vegetable curry',
    'Baked chicken breast with salad'
]

ABNORMAL_MEALS = [
    'Large pasta serving with garlic bread and soda',
    'Pizza (3 slices) with dessert and cola',
    'Fast food burger with fries and milkshake',
    'Chinese buffet - multiple high-carb dishes',
    'Birthday cake and ice cream at party'
]

def generate_health_entries(user_id, profile_name):
    """Generate 8 days of health data for a patient"""
    profile = HEALTH_PROFILES[profile_name]
    entries = []
    today = datetime.now()
    
    for day in range(7, -1, -1):  # Day 7 (oldest) to Day 0 (today)
        entry_date = today - timedelta(days=day)
        
        # Determine if this is an abnormal reading day
        is_abnormal = day in profile['abnormal_days']
        
        if is_abnormal:
            # High reading
            blood_sugar = random.randint(145, profile['blood_sugar_range'][1])
            food = random.choice(ABNORMAL_MEALS)
            activity = f"⚠️ ALERT: High blood sugar! {random.choice(['Forgot medication', 'Stress from work', 'Ate too many carbs', 'Skipped exercise'])}. {random.choice(['Feeling thirsty', 'Feeling tired', 'Slight headache', 'Feel dizzy'])}"
            symptoms = f"BP: {random.randint(130, 145)}/{random.randint(85, 95)}, HR: {random.randint(80, 95)}, Meds: {profile['medications']} - {'Forgot dose' if random.random() > 0.5 else 'taken late'}"
            event = '⚠️ Abnormal Reading'
            status = 'abnormal'
        else:
            # Normal reading
            blood_sugar = random.randint(profile['blood_sugar_range'][0], min(125, profile['blood_sugar_range'][1]))
            
            # Vary meal time
            if day % 3 == 0:
                food = random.choice(BREAKFAST_OPTIONS)
                event = 'Fasting / Before breakfast'
            elif day % 3 == 1:
                food = random.choice(LUNCH_OPTIONS)
                event = '2 hours after lunch'
            else:
                food = random.choice(DINNER_OPTIONS)
                event = 'Before dinner'
            
            activity = random.choice([
                'Feeling good, slept well',
                '30-minute walk after meal',
                'Light exercise - feeling energetic',
                'Rested well, maintaining diet',
                'Morning yoga session'
            ])
            symptoms = f"BP: {random.randint(110, 125)}/{random.randint(70, 82)}, HR: {random.randint(65, 78)}, Meds: {profile['medications']} (morning dose)"
            status = 'normal' if blood_sugar <= 125 else 'borderline'
        
        # Random time for reading
        reading_time = f"{random.randint(7, 22):02d}:{random.choice(['00', '15', '30', '45'])}:00"
        
        entry = {
            'user_id': user_id,
            'value': blood_sugar,
            'date_time': f"{entry_date.strftime('%Y-%m-%d')} {reading_time}",
            'fasting': 1 if 'Fasting' in event else 0,
            'food_intake': food,
            'activity': activity,
            'event': event,
            'symptoms_notes': symptoms,
            'status': status
        }
        entries.append(entry)
    
    return entries

def populate_database():
    """Insert health data for all demo patients"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO bloodsugarreadings 
        (user_id, value, date_time, fasting, food_intake, activity, event, symptoms_notes, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    total_entries = 0
    
    for patient in DEMO_PATIENTS:
        user_id = patient['user_id']
        name = patient['name']
        profile = patient['profile']
        
        # Check if patient already has data
        cursor.execute("SELECT COUNT(*) FROM bloodsugarreadings WHERE user_id = %s", (user_id,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"⚠️  {name} (ID: {user_id}) already has {existing_count} entries - SKIPPING")
            continue
        
        # Generate and insert entries
        entries = generate_health_entries(user_id, profile)
        
        for entry in entries:
            cursor.execute(insert_query, (
                entry['user_id'],
                entry['value'],
                entry['date_time'],
                entry['fasting'],
                entry['food_intake'],
                entry['activity'],
                entry['event'],
                entry['symptoms_notes'],
                entry['status']
            ))
        
        conn.commit()
        total_entries += len(entries)
        
        profile_info = HEALTH_PROFILES[profile]
        print(f"✓ Created {len(entries)} entries for {name} (ID: {user_id}) - {profile_info['description']}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully created {total_entries} total health entries!")
    print(f"{'='*60}")
    print("\nDemo patients now have health history:")
    for patient in DEMO_PATIENTS:
        profile_desc = HEALTH_PROFILES[patient['profile']]['description']
        print(f"  • {patient['name']}: {profile_desc}")
    print("\nYou can now log in as any demo patient and view their health history.")
    print("Abnormal readings (>140 mg/dL) will be highlighted in red with ⚠️ warnings.")

if __name__ == '__main__':
    print("="*60)
    print("Populating Demo Patient Health Data")
    print("="*60)
    print(f"\nCreating 8 days of health history for {len(DEMO_PATIENTS)} demo patients...")
    print()
    
    try:
        populate_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
