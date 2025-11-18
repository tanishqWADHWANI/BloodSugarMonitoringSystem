import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', '127.0.0.1'),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'blood_sugar_db'),
                autocommit=False
            )
            if self.connection.is_connected():
                logger.info("Database connection established")
        except Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _get_cursor(self):
        """Get a cursor, reconnecting if necessary"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)
    
    # User Management
    def get_user(self, user_id):
        """Get user by ID"""
        cursor = self._get_cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        cursor = self._get_cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cursor.fetchone()
        finally:
            cursor.close()
    
    def create_user(self, email, password, first_name, last_name, role, date_of_birth=None, phone=None, health_care_number =None):
        """Create a new user (password stored as-is for demo, hash in production)"""
        cursor = self._get_cursor()
        try:
            sql = """
                INSERT INTO users (email, password_hash, first_name, last_name, role, date_of_birth, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (email, password, first_name, last_name, role, date_of_birth, phone)
            cursor.execute(sql, values)
            self.connection.commit()
            user_id = cursor.lastrowid
            
            # Create patient record if role is patient
            if role == 'patient':
                cursor.execute(
                    "INSERT INTO patients (user_id, health_care_number) VALUES (%s,%s)",
                    (user_id,health_care_number)
                )
                self.connection.commit()
            # Create specialist record if role is specialist
            elif role == 'specialist':
                cursor.execute(
                    "INSERT INTO specialists (user_id) VALUES (%s)",
                    (user_id,)
                )
                self.connection.commit()
            # Create staff record if role is staff
            elif role == 'staff':
                cursor.execute(
                    "INSERT INTO staff (user_id) VALUES (%s)",
                    (user_id,)
                )
                self.connection.commit()
            
            return user_id
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            cursor.close()

    def update_user(self, user_id, *, email: str | None = None, password: str | None = None, first_name: str | None = None, last_name: str | None = None, role: str | None = None, date_of_birth: str | None = None, phone: str | None = None, health_care_number: str | None = None)-> bool:
        """
        Update user. Only provided fields are updated.
        Password is stored in plain text (demo only).
        """
        cursor = self._get_cursor()
        try:
            # Build updates for `users` table
            updates = {}
            if email is not None:          updates["email"] = email
            if password is not None:       updates["password_hash"] = password  # plain text
            if first_name is not None:     updates["first_name"] = first_name
            if last_name is not None:      updates["last_name"] = last_name
            if role is not None:           updates["role"] = role
            if date_of_birth is not None:  updates["date_of_birth"] = date_of_birth
            if phone is not None:          updates["phone"] = phone

            if not updates:
                return False  # nothing to update

            set_clause = ", ".join(f"{col} = %s" for col in updates)
            values = list(updates.values())
            values.append(user_id)

            sql = f"UPDATE users SET {set_clause} WHERE user_id = %s"
            cursor.execute(sql, values)

            if cursor.rowcount == 0:
                return False  # user not found

            # === Role-specific logic ===
            if role is not None:
                # Get old role
                cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
                old_role = cursor.fetchone()[0]

                # Clean up old role table
                if old_role == "patient":
                    cursor.execute("DELETE FROM patients WHERE user_id = %s", (user_id,))
                elif old_role == "specialist":
                    cursor.execute("DELETE FROM specialists WHERE user_id = %s", (user_id,))
                elif old_role == "staff":
                    cursor.execute("DELETE FROM staff WHERE user_id = %s", (user_id,))

                # Insert into new role table
                if role == "patient":
                    cursor.execute(
                        "INSERT INTO patients (user_id, health_care_number) VALUES (%s, %s)",
                        (user_id, health_care_number)
                    )
                elif role == "specialist":
                    cursor.execute("INSERT INTO specialists (user_id) VALUES (%s)", (user_id,))
                elif role == "staff":
                    cursor.execute("INSERT INTO staff (user_id) VALUES (%s)", (user_id,))

            # === Update health care number (even if role didn't change) ===
            elif health_care_number is not None:
                cursor.execute(
                    "UPDATE patients SET health_care_number = %s WHERE user_id = %s",
                    (health_care_number, user_id)
                )

            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise
        finally:
            cursor.close()

    def delete_user(self,user_id)-> bool:
            
        """
        Delete a user and all associated records.
        Relies on ON DELETE CASCADE in the database.

        Returns
        -------
        bool
            True if user was deleted, False if user not found.
        """

        cursor = self._get_cursor()
        try:

            # Delete from users table (CASCADE handles patients/specialists/staff)
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            self.connection.commit()

            return cursor.rowcount > 0 # True if a row is deleted
        except Exception as e:
            self.connection.rollback()
            logger.error("Error Deleting the user {user_id}: {e} ")
            raise
        finally:
            cursor.close()

    def get_specialist_feedback(self, patient_id):
        """Get all feedback for a patient"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT 
                    sf.*, 
                    s.user_id, 
                    u.first_name, 
                    u.last_name
                FROM specialist_feedback sf
                JOIN specialists s ON sf.specialist_id = s.specialist_id
                JOIN users u ON s.user_id = u.user_id
                WHERE sf.patient_id = %s
                ORDER BY sf.created_at DESC
            """
            cursor.execute(sql, (patient_id,))
            rows = cursor.fetchall()

            feedback = []
            for row in rows:
                r = dict(row)
                if 'created_at' in r and r['created_at']:
                    r['createdAt'] = r['created_at'].isoformat()
                feedback.append(r)
            return feedback
        finally:
            cursor.close()




    
    # Blood Sugar Readings
    def create_reading(self, user_id, value, unit='mg/dL', fasting=None, food_intake=None, 
                      activity=None, event=None, symptoms_notes=None, additional_note=None, 
                      status=None, confidence=None, date_time=None):
        """Create a new blood sugar reading - triggers will auto-classify status"""
        cursor = self._get_cursor()
        try:
            sql = """
                INSERT INTO bloodsugarreadings 
                (user_id, date_time, value, unit, fasting, food_intake, activity, 
                 event, symptoms_notes, additional_note, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # if caller did not pass a date_time, fall back to "now"
            effective_dt = date_time or datetime.now()

            values = (user_id, datetime.now(), value, unit, fasting, food_intake, 
                     activity, event, symptoms_notes, additional_note, status)
            cursor.execute(sql, values)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error creating reading: {e}")
            raise
        finally:
            cursor.close()
    
    def get_user_readings(self, user_id, days=30):
        """Get blood sugar readings for a user"""
        cursor = self._get_cursor()
        try:
            start_date = datetime.now() - timedelta(days=days)
            sql = """
                SELECT * FROM bloodsugarreadings 
                WHERE user_id = %s AND date_time >= %s 
                ORDER BY date_time DESC
            """
            cursor.execute(sql, (user_id, start_date))
            readings = cursor.fetchall()
            
            # Convert datetime objects to strings
            for reading in readings:
                if reading.get('date_time'):
                    reading['date_time'] = reading['date_time'].isoformat()
                if reading.get('created_at'):
                    reading['created_at'] = reading['created_at'].isoformat()
                if reading.get('updated_at'):
                    reading['updated_at'] = reading['updated_at'].isoformat()
                # Convert Decimal to float
                if reading.get('value'):
                    reading['value'] = float(reading['value'])
            
            return readings
        finally:
            cursor.close()
    
    def get_all_readings_for_training(self):
        """Get all blood sugar readings for ML training"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT 
                    reading_id,
                    user_id,
                    date_time,
                    value,
                    unit,
                    fasting,
                    food_intake,
                    activity,
                    status
                FROM bloodsugarreadings
                ORDER BY date_time DESC
            """
            cursor.execute(sql)
            readings = cursor.fetchall()
            
            # Convert to proper format
            for reading in readings:
                if reading.get('date_time'):
                    reading['dateTime'] = reading['date_time'].isoformat()
                if reading.get('value'):
                    reading['value'] = float(reading['value'])
            
            return readings
        finally:
            cursor.close()
    
    def update_reading(self, reading_id, **kwargs):
        """Update a blood sugar reading"""
        cursor = self._get_cursor()
        try:
            update_fields = []
            values = []
            
            allowed_fields = ['value', 'unit', 'fasting', 'food_intake', 'activity', 
                            'event', 'symptoms_notes', 'additional_note', 'status']
            
            for key, value in kwargs.items():
                if key in allowed_fields:
                    update_fields.append(f"{key} = %s")
                    values.append(value)
            
            if not update_fields:
                return
            
            values.append(reading_id)
            sql = f"UPDATE bloodsugarreadings SET {', '.join(update_fields)} WHERE reading_id = %s"
            cursor.execute(sql, values)
            self.connection.commit()
            
            logger.info(f"Updated reading {reading_id}")
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error updating reading: {e}")
            raise
        finally:
            cursor.close()
    
    def delete_reading(self, reading_id):
        """Delete a blood sugar reading"""
        cursor = self._get_cursor()
        try:
            cursor.execute("DELETE FROM bloodsugarreadings WHERE reading_id = %s", (reading_id,))
            self.connection.commit()
            logger.info(f"Deleted reading {reading_id}")
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error deleting reading: {e}")
            raise
        finally:
            cursor.close()
    
    def get_reading_by_id(self, reading_id):
        """Get a specific reading by ID"""
        cursor = self._get_cursor()
        try:
            cursor.execute("SELECT * FROM bloodsugarreadings WHERE reading_id = %s", (reading_id,))
            reading = cursor.fetchone()
            
            if reading:
                if reading.get('date_time'):
                    reading['date_time'] = reading['date_time'].isoformat()
                if reading.get('created_at'):
                    reading['created_at'] = reading['created_at'].isoformat()
                if reading.get('updated_at'):
                    reading['updated_at'] = reading['updated_at'].isoformat()
                if reading.get('value'):
                    reading['value'] = float(reading['value'])
            
            return reading
        finally:
            cursor.close()
    
    def get_abnormal_count(self, user_id, days=7):
        """Count abnormal readings in the past N days"""
        cursor = self._get_cursor()
        try:
            start_date = datetime.now() - timedelta(days=days)
            sql = """
                SELECT COUNT(*) as count FROM bloodsugarreadings 
                WHERE user_id = %s AND date_time >= %s 
                AND status IN ('abnormal', 'borderline')
            """
            cursor.execute(sql, (user_id, start_date))
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            cursor.close()
    
    # AI Insights
    def create_ai_insight(self, user_id, pattern, suggestion, confidence):
        """Create an AI insight"""
        cursor = self._get_cursor()
        try:
            sql = """
                INSERT INTO aiinsights (user_id, pattern, suggestion, confidence)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, pattern, suggestion, confidence))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error creating insight: {e}")
            raise
        finally:
            cursor.close()
    
    def get_user_insights(self, user_id, limit=10):
        """Get AI insights for a user"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT * FROM aiinsights 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """
            cursor.execute(sql, (user_id, limit))
            insights = cursor.fetchall()
            
            for insight in insights:
                if insight.get('created_at'):
                    insight['created_at'] = insight['created_at'].isoformat()
                if insight.get('confidence'):
                    insight['confidence'] = float(insight['confidence'])
            
            return insights
        finally:
            cursor.close()
    
    # Alerts
    def create_alert(self, user_id, reason, specialist_id=None):
        """Create a new alert - typically done by triggers"""
        cursor = self._get_cursor()
        try:
            sql = """
                INSERT INTO alerts (user_id, specialist_id, reason, date_sent)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, specialist_id, reason, datetime.now()))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
        finally:
            cursor.close()
    
    def get_user_alerts(self, user_id, days=30):
        """Get alerts for a user"""
        cursor = self._get_cursor()
        try:
            start_date = datetime.now() - timedelta(days=days)
            sql = """
                SELECT * FROM alerts 
                WHERE user_id = %s AND date_sent >= %s 
                ORDER BY date_sent DESC
            """
            cursor.execute(sql, (user_id, start_date))
            alerts = cursor.fetchall()
            
            for alert in alerts:
                if alert.get('date_sent'):
                    alert['date_sent'] = alert['date_sent'].isoformat()
                if alert.get('created_at'):
                    alert['created_at'] = alert['created_at'].isoformat()
            
            return alerts
        finally:
            cursor.close()
    
    # Thresholds
    def get_user_thresholds(self, user_id):
        """Get custom thresholds for a user"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT * FROM thresholds 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (user_id,))
            thresholds = cursor.fetchall()
            
            for threshold in thresholds:
                if threshold.get('min_value'):
                    threshold['min_value'] = float(threshold['min_value'])
                if threshold.get('max_value'):
                    threshold['max_value'] = float(threshold['max_value'])
            
            return thresholds
        finally:
            cursor.close()
    
    def set_user_threshold(self, user_id, status, min_value, max_value):
        """Set or update a user's threshold"""
        cursor = self._get_cursor()
        try:
            # Check if threshold exists
            cursor.execute(
                "SELECT threshold_id FROM thresholds WHERE user_id = %s AND status = %s",
                (user_id, status)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update
                sql = """
                    UPDATE thresholds 
                    SET min_value = %s, max_value = %s 
                    WHERE threshold_id = %s
                """
                cursor.execute(sql, (min_value, max_value, existing['threshold_id']))
            else:
                # Insert
                sql = """
                    INSERT INTO thresholds (user_id, status, min_value, max_value)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, status, min_value, max_value))
            
            self.connection.commit()
            return cursor.lastrowid if not existing else existing['threshold_id']
        except Error as e:
            self.connection.rollback()
            logger.error(f"Error setting threshold: {e}")
            raise
        finally:
            cursor.close()
    
    # Diet Recommendations
    def get_diet_recommendations(self, condition_name, meal_type=None):
        """Get diet recommendations for a condition"""
        cursor = self._get_cursor()
        try:
            if meal_type:
                sql = """
                    SELECT * FROM dietrecommendations 
                    WHERE condition_name = %s AND meal_type = %s
                """
                cursor.execute(sql, (condition_name, meal_type))
            else:
                sql = """
                    SELECT * FROM dietrecommendations 
                    WHERE condition_name = %s
                """
                cursor.execute(sql, (condition_name,))
            
            recommendations = cursor.fetchall()
            
            for rec in recommendations:
                if rec.get('protein_g'):
                    rec['protein_g'] = float(rec['protein_g'])
                if rec.get('carbs_g'):
                    rec['carbs_g'] = float(rec['carbs_g'])
                if rec.get('fat_g'):
                    rec['fat_g'] = float(rec['fat_g'])
            
            return recommendations
        finally:
            cursor.close()
    
    # Specialist Functions
    def get_patient_specialist(self, patient_user_id):
        """Get the specialist assigned to a patient"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT s.specialist_id, u.* 
                FROM patients p
                JOIN specialistpatient sp ON p.patient_id = sp.patient_id
                JOIN specialists s ON sp.specialist_id = s.specialist_id
                JOIN users u ON s.user_id = u.user_id
                WHERE p.user_id = %s
                LIMIT 1
            """
            cursor.execute(sql, (patient_user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
    
    def get_specialist_patients(self, specialist_id):
        """Get all patients assigned to a specialist"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT p.patient_id, u.* 
                FROM specialistpatient sp
                JOIN patients p ON sp.patient_id = p.patient_id
                JOIN users u ON p.user_id = u.user_id
                WHERE sp.specialist_id = %s
            """
            cursor.execute(sql, (specialist_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def get_specialist_dashboard(self, specialist_id):
        """Get dashboard data for specialist using pre-built view"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT * FROM v_specialist_dashboard
                WHERE specialist_id = %s
            """
            cursor.execute(sql, (specialist_id,))
            result = cursor.fetchone()
            
            if result:
                # Convert to int where needed
                for key in ['total_patients', 'total_alerts', 'alerts_last_7d', 
                           'inactive_patients', 'abnormal_patients']:
                    if result.get(key):
                        result[key] = int(result[key])
            
            return result
        finally:
            cursor.close()
    
    def get_specialist_attention_list(self, specialist_id):
        """Get patients requiring attention using pre-built view"""
        cursor = self._get_cursor()
        try:
            sql = """
                SELECT * FROM v_specialist_attention
                WHERE specialist_id = %s
                ORDER BY last_date_time DESC
            """
            cursor.execute(sql, (specialist_id,))
            patients = cursor.fetchall()
            
            for patient in patients:
                if patient.get('last_value'):
                    patient['last_value'] = float(patient['last_value'])
                if patient.get('avg_value_total'):
                    patient['avg_value_total'] = float(patient['avg_value_total'])
                if patient.get('last_date_time'):
                    patient['last_date_time'] = patient['last_date_time'].isoformat()
            
            return patients
        finally:
            cursor.close()
    
    # Kaggle Datasets for ML Training
    def get_diabetes_dataset(self):
        """Get diabetes analysis data for ML training"""
        cursor = self._get_cursor()
        try:
            sql = "SELECT * FROM diabetesdataanalysis WHERE Pregnancies > 0"
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def get_heart_disease_dataset(self):
        """Get heart disease data for ML training"""
        cursor = self._get_cursor()
        try:
            sql = "SELECT * FROM heart_disease_raw WHERE Age > 0"
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")