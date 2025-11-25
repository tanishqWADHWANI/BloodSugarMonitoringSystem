"""
Populate comprehensive health history for 16 patients
Creates blood sugar readings spanning multiple months with varied patterns
"""
import mysql.connector
from datetime import datetime, timedelta
import random

def get_db_connection():
    """Establish database connection"""
    return mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='blood_sugar_db'
    )

def create_health_history():
    """Create comprehensive health records for all patients"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Patient IDs to populate
    patient_ids = [1, 3, 4, 301, 302, 303, 304, 305, 306, 307, 308, 314, 315, 316, 317, 318]
    
    # Get user_id for each patient
    patient_user_ids = {}
    for patient_id in patient_ids:
        cursor.execute("SELECT user_id FROM patients WHERE patient_id = %s", (patient_id,))
        result = cursor.fetchone()
        if result:
            patient_user_ids[patient_id] = result['user_id']
    
    print(f"Found {len(patient_user_ids)} patients to populate")
    
    # Define health patterns for variety
    patterns = {
        'well_controlled': {'base': 110, 'variance': 15, 'spike_chance': 0.1},
        'moderate': {'base': 135, 'variance': 25, 'spike_chance': 0.2},
        'poor_control': {'base': 160, 'variance': 35, 'spike_chance': 0.3},
        'improving': {'base': 150, 'variance': 30, 'spike_chance': 0.25}
    }
    
    # Meal types and activities
    meals = ['Oatmeal with berries', 'Grilled chicken salad', 'Rice with vegetables', 
             'Pasta with tomato sauce', 'Sandwich', 'Eggs and toast', 'Fish with quinoa',
             'Stir fry', 'Soup and bread', 'Yogurt and fruit', 'Pizza slice', 'Burger']
    
    activities = ['Walking 30 min', 'Jogging 20 min', 'Yoga session', 'Gym workout',
                 'Cycling', 'Swimming', 'Light exercise', 'Sedentary', 'Running']
    
    symptoms = ['Feeling great', 'Slightly tired', 'Hungry', 'Thirsty', 'Headache',
               'Dizzy', 'Normal', 'Energetic', 'Fatigued', '']
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)  # 4 months of history
    
    total_readings = 0
    
    for patient_id, user_id in patient_user_ids.items():
        # Assign a pattern to each patient
        pattern_name = random.choice(list(patterns.keys()))
        pattern = patterns[pattern_name]
        
        print(f"\nProcessing Patient {patient_id} (user_id: {user_id}) - Pattern: {pattern_name}")
        
        # Generate readings over 4 months (3-5 readings per day)
        current_date = start_date
        patient_readings = 0
        
        while current_date <= end_date:
            # Random number of readings per day (3-5)
            daily_readings = random.randint(3, 5)
            
            for reading_num in range(daily_readings):
                # Generate time of day
                hour = random.choice([7, 8, 12, 13, 18, 19, 22])  # Morning, lunch, dinner, bedtime
                minute = random.randint(0, 59)
                reading_time = current_date.replace(hour=hour, minute=minute, second=0)
                
                # Skip if in future
                if reading_time > end_date:
                    continue
                
                # Generate blood sugar value based on pattern
                base_value = pattern['base']
                variance = pattern['variance']
                
                # Time of day adjustments
                if hour in [7, 8]:  # Fasting morning
                    base_value -= 10
                elif hour in [12, 13, 18, 19]:  # Post-meal
                    base_value += 20
                
                # Random spike
                if random.random() < pattern['spike_chance']:
                    base_value += random.randint(30, 60)
                
                blood_sugar = max(70, min(300, base_value + random.randint(-variance, variance)))
                
                # Determine status
                if blood_sugar < 100:
                    status = 'normal'
                elif blood_sugar < 140:
                    status = 'borderline'
                else:
                    status = 'abnormal'
                
                # Fasting flag (morning readings)
                fasting = 1 if hour in [7, 8] else 0
                
                # Random meal, activity, symptoms
                food = random.choice(meals) if random.random() > 0.2 else None
                activity = random.choice(activities) if random.random() > 0.3 else None
                symptom = random.choice(symptoms)
                
                try:
                    cursor.execute("""
                        INSERT INTO bloodsugarreadings 
                        (user_id, date_time, value, unit, fasting, food_intake, activity, 
                         symptoms_notes, status, created_at, updated_at)
                        VALUES (%s, %s, %s, 'mg/dL', %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (user_id, reading_time, blood_sugar, fasting, food, activity, symptom, status))
                    
                    patient_readings += 1
                    
                except mysql.connector.IntegrityError:
                    # Skip if duplicate
                    pass
            
            current_date += timedelta(days=1)
        
        conn.commit()
        total_readings += patient_readings
        print(f"  Created {patient_readings} readings for Patient {patient_id}")
    
    print(f"\n✅ Total readings created: {total_readings}")
    print(f"✅ Successfully populated health history for {len(patient_user_ids)} patients")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("Populating Patient Health History")
    print("=" * 70)
    create_health_history()
    print("\n✅ Health history population complete!")
