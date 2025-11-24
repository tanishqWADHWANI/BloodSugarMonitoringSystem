from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import logging
import os
from werkzeug.utils import secure_filename

from models import Database
from ml_service import MLService
from notification_service import NotificationService
from scheduler_service import SchedulerService
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# ===== File upload config =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Allow frontend from anywhere (file://, localhost, etc.)
CORS(app, resources={
    r"/api/*": {
        "origins": "*"
    }
})




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
db = Database()
ml_service = MLService()
notification_service = NotificationService()
scheduler_service = SchedulerService(db, notification_service)

# Helper function to extract user from token
def get_user_from_token():
    """Extract user info from authorization token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    # Simple token format: token_{user_id}_{role}
    try:
        parts = token.split('_')
        if len(parts) >= 2 and parts[0] == 'token':
            user_id = int(parts[1])
            return {'user_id': user_id}
    except:
        pass
    return None

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Check if the service is running"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

# Get current user profile (from token)
@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user's profile using token"""
    user_info = get_user_from_token()
    if not user_info:
        return jsonify({"error": "Unauthorized - Invalid or missing token"}), 401
    
    user = db.get_user(user_info['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Remove sensitive data
    if 'password_hash' in user:
        del user['password_hash']
    
    return jsonify(user), 200

# User Management
@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.json
        required_fields = ['email', 'password', 'firstName', 'lastName', 'role']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        user_id = db.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['firstName'],
            last_name=data['lastName'],
            role=data['role'],
            date_of_birth=data.get('dateOfBirth'),
            phone=data.get('phone'),
            health_care_number=data.get('healthCareNumber'),
            profile_image=data.get('profileImage')
        )
        
        return jsonify({"userId": user_id, "message": "User registered successfully"}), 201
    
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": str(e)}), 500



# for admin to view all users 
@app.route('/api/admin/users/all', methods=['GET'])
def get_all_users():
    """Get all users for the Admin Dashboard."""
    
    try:
        # Assumes db.get_all_users() method exists in models.py
        users = db.get_all_users() 
        
        return jsonify({"users": users}), 200
    except Exception as e:
        # CRITICAL FIX: Add exc_info=True to print the full traceback
        logger.error(f"CRASH REPORT: Database query failed.", exc_info=True) 
        return jsonify({"error": "Failed to fetch users. CHECK TERMINAL LOGS."}), 500
    

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user information"""
    try:
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Remove sensitive data
        if 'password_hash' in user:
            del user['password_hash']
        
        return jsonify(user), 200
    
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    try:
        data = request.json or {}
        
        # Check if user exists
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Only pass known fields
        updated = db.update_user(
            user_id,
            email=data.get('email'),
            password=data.get('password'),
            first_name=data.get('firstName'),
            last_name=data.get('lastName'),
            role=data.get('role'),
            date_of_birth=data.get('dateOfBirth'),
            phone=data.get('phone'),
            health_care_number=data.get('healthCareNumber'),
            license_id=data.get('licenseId')  # Province/state professional license
        )

        if not updated:
            return jsonify({"error": "No changes made or user not found"}), 400

        return jsonify({"message": "User updated successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({"error": "Failed to update user"}), 500
    
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        # Check if user exists
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Delete user (CASCADE handles related tables)
        deleted = db.delete_user(user_id)
        if not deleted:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({"error": "Failed to delete user"}), 500

# Admin login
@app.route('/api/auth/login', methods=['POST'])
def handle_auth_login():
    data = request.json
    user = db.get_user_by_email(data['email'])
    if not user or not db.verify_password(user, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"userId": user['id'], "role": user['role']}), 200

    
# Admin creates Specialist/Staff
@app.route('/api/admin/users', methods=['POST'])
def create_user_admin():
    """Admin endpoint to create users"""
    data = request.json
    
    try:
        # Extract data
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        role = data.get('role')
        phone = data.get('phone')
        date_of_birth = data.get('dateOfBirth')
        license_id = data.get('licenseId')  # For specialists/staff - province/state license
        health_care_number = data.get('healthCareNumber')  # For patients
        profile_image = data.get('profileImage')  # Optional profile image
        
        # Validate required fields
        if not all([email, password, first_name, last_name, role]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create user
        user_id = db.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            date_of_birth=date_of_birth,
            phone=phone,
            health_care_number=health_care_number,
            license_id=license_id,  # Province/state professional license number
            profile_image=profile_image
        )
        
        return jsonify({
            'success': True,
            'userId': user_id,
            'message': 'User created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user_admin(user_id):
    """Admin endpoint to delete a user"""
    try:
        cursor = db._get_cursor()
        try:
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            # Get user role to determine cleanup needed
            cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            role = user['role']
            
            # Delete related records based on role
            if role == 'patient':
                # Get patient_id
                cursor.execute("SELECT patient_id FROM patients WHERE user_id = %s", (user_id,))
                patient = cursor.fetchone()
                if patient:
                    patient_id = patient['patient_id']
                    # Delete assignments
                    cursor.execute("DELETE FROM specialistpatient WHERE patient_id = %s", (patient_id,))
                    # Delete readings
                    cursor.execute("DELETE FROM bloodsugarreadings WHERE user_id = %s", (user_id,))
                    # Delete alerts
                    cursor.execute("DELETE FROM alerts WHERE user_id = %s", (user_id,))
                    # Delete insights
                    cursor.execute("DELETE FROM aiinsights WHERE user_id = %s", (user_id,))
                    # Delete patient record
                    cursor.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
            
            elif role == 'specialist':
                # Get specialist_id
                cursor.execute("SELECT specialist_id FROM specialists WHERE user_id = %s", (user_id,))
                specialist = cursor.fetchone()
                if specialist:
                    specialist_id = specialist['specialist_id']
                    # Delete assignments
                    cursor.execute("DELETE FROM specialistpatient WHERE specialist_id = %s", (specialist_id,))
                    # Delete feedback
                    cursor.execute("DELETE FROM specialist_feedback WHERE specialist_id = %s", (specialist_id,))
                    # Delete specialist record
                    cursor.execute("DELETE FROM specialists WHERE specialist_id = %s", (specialist_id,))
            
            elif role == 'staff':
                # Get staff_id if exists
                cursor.execute("SELECT staff_id FROM staff WHERE user_id = %s", (user_id,))
                staff = cursor.fetchone()
                if staff:
                    staff_id = staff['staff_id']
                    cursor.execute("DELETE FROM staff WHERE staff_id = %s", (staff_id,))
            
            # Finally delete the user
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            
            # Commit transaction
            db.connection.commit()
            
            return jsonify({
                'success': True,
                'message': f'User {user_id} deleted successfully'
            }), 200
            
        except Exception as e:
            db.connection.rollback()
            raise e
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500
    
# Blood Sugar Readings
@app.route('/api/readings', methods=['POST'])
def add_reading():
    """Add a new blood sugar reading with AI prediction"""
    try:
        data = request.json
        required_fields = ['userId', 'value']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Determine the effective measurement datetime (from client, or now)
        date_time = datetime.now()
        date_time_str = data.get('date_time')
        if date_time_str:
            try:
                # Expecting e.g. "2025-11-20T12:30"
                date_time = datetime.fromisoformat(date_time_str)
            except ValueError:
                logger.warning("Invalid date_time '%s', falling back to now()", date_time_str)

        # Get AI prediction and insights
        prediction_result = ml_service.predict_status(
            value=data['value'],
            fasting=data.get('fasting', False),
            food_intake=data.get('foodIntake', ''),
            activity=data.get('activity', ''),
            time_of_day=date_time.hour
        )
        ai_status = prediction_result['status']
        if ai_status in ('low', 'high'):
            db_status = 'abnormal'
        elif ai_status == 'prediabetic':
            db_status = 'borderline'
        else:
            db_status = 'normal'
        # Store reading in database (triggers will auto-classify and create alerts)
        reading_id = db.create_reading(
            user_id=data['userId'],
            value=data['value'],
            unit=data.get('unit', 'mg/dL'),
            fasting=data.get('fasting'),
            food_intake=data.get('foodIntake'),
            activity=data.get('activity'),
            event=data.get('event'),
            symptoms_notes=data.get('symptomsNotes'),
            additional_note=data.get('additionalNote'),
            date_time=date_time,
            status=db_status 
        )
        
        # Save AI insight if significant
        if prediction_result['insights']:
            insight_text = "; ".join([i['message'] for i in prediction_result['insights'][:2]])
            suggestion = prediction_result['insights'][0]['message'] if prediction_result['insights'] else "Continue monitoring"
            
            db.create_ai_insight(
                user_id=data['userId'],
                pattern=f"Reading: {data['value']} mg/dL - {prediction_result['status']}",
                suggestion=suggestion,
                confidence=prediction_result['confidence']
            )
        
        return jsonify({
            "readingId": reading_id,
            "status": prediction_result['status'],
            "severity": prediction_result['severity'],
            "confidence": prediction_result['confidence'],
            "insights": prediction_result['insights'],
            "message": "Reading added successfully. Database triggers have auto-classified the reading."
        }), 201
    
    except Exception as e:
        logger.error(f"Error adding reading: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/readings/<int:user_id>', methods=['GET'])
def get_readings(user_id):
    """Get blood sugar readings for a user"""
    try:
        days = request.args.get('days', default=30, type=int)
        readings = db.get_user_readings(user_id, days)
        
        return jsonify({
            "userId": user_id,
            "readings": readings,
            "count": len(readings)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching readings: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
# Update readings
@app.route('/api/readings/<int:reading_id>', methods=['PUT'])
def update_readings(reading_id):
    """Update blood sugar readings for a user"""
    try:
        data = request.json
            
        # Check if reading exists
        reading = db.get_reading_by_id(reading_id)
        if not reading:
            return jsonify({"error": "Reading not found"}), 404
            
        # Update reading
        db.update_reading(reading_id, **data)
            
        return jsonify({
            "readingId": reading_id,
            "message": "Reading updated successfully"
        }), 200
           
        
    except Exception as e:
        logger.error(f"Error updating reading: {str(e)}")
        return jsonify({"error": "Failed to update reading"}), 500


# Delete reading
@app.route('/api/readings/<int:reading_id>', methods=['DELETE'])
def delete_reading(reading_id):
    """Delete a blood sugar reading"""
    try:
        # Check if reading exists
        reading = db.get_reading_by_id(reading_id)
        if not reading:
            return jsonify({"error": "Reading not found"}), 404
        
        # Delete reading
        db.delete_reading(reading_id)
        
        return jsonify({
            "message": "Reading deleted successfully",
            "readingId": reading_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error deleting reading: {str(e)}")
        return jsonify({"error": "Failed to delete reading"}), 500


# User login
@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    from werkzeug.security import check_password_hash
    
    data = request.json
    
    user = db.get_user_by_email(data['email'])
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Verify password using proper hashing
    if not check_password_hash(user['password_hash'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Remove password from response
    del user['password_hash']
    
    # Generate a simple token (in production, use JWT)
    token = f"token_{user['user_id']}_{user['role']}"
    
    # Get patient_id if user is a patient
    patient_id = None
    if user['role'] == 'patient':
        cursor = db._get_cursor()
        cursor.execute("SELECT patient_id FROM patients WHERE user_id = %s", (user['user_id'],))
        patient_record = cursor.fetchone()
        cursor.close()
        if patient_record:
            patient_id = patient_record['patient_id']
    
    return jsonify({
        "message": "Login successful",
        "user": user,
        "token": token,
        "user_id": user['user_id'],
        "patient_id": patient_id,
        "name": f"{user['first_name']} {user['last_name']}"
    }), 200

@app.route('/api/specialist/<int:specialist_id>/readings/search', methods=['GET'])
def specialist_search_readings(specialist_id):
    """Specialist search and filter patient readings"""
    try:
        # Get query parameters
        patient_name = request.args.get('patientName')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        status_filter = request.args.get('status')  # 'normal' or 'abnormal'
        
        # Get all patients for this specialist
        patients = db.get_specialist_patients(specialist_id)
        
        all_readings = []
        for patient in patients:
            # Filter by patient name if provided
            if patient_name:
                full_name = f"{patient['first_name']} {patient['last_name']}"
                if patient_name.lower() not in full_name.lower():
                    continue
            
            # Get readings
            readings = db.get_user_readings(patient['user_id'], days=365)
            
            for reading in readings:
                # Add patient info
                reading['patient_name'] = f"{patient['first_name']} {patient['last_name']}"
                reading['patient_id'] = patient['user_id']
                
                # Filter by date range
                if start_date and reading['date_time'] < start_date:
                    continue
                if end_date and reading['date_time'] > end_date:
                    continue
                
                # Filter by status
                if status_filter:
                    if status_filter == 'abnormal' and reading['status'] not in ['abnormal', 'borderline']:
                        continue
                    if status_filter == 'normal' and reading['status'] != 'normal':
                        continue
                
                all_readings.append(reading)
        
        return jsonify({
            "specialistId": specialist_id,
            "readings": all_readings,
            "count": len(all_readings)
        }), 200
    
    except Exception as e:
        logger.error(f"Error searching readings: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Specialist Feedback
@app.route('/api/specialist/feedback', methods=['POST'])
def add_specialist_feedback():
    """Specialist provides feedback to patient"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('specialistId') or not data.get('patientId') or not data.get('feedbackText'):
            return jsonify({"error": "Missing required fields"}), 400
        
        cursor = db._get_cursor()
        
        # Get patient_id from user_id
        cursor.execute(
            "SELECT patient_id FROM patients WHERE user_id = %s", 
            (data['patientId'],)
        )
        patient = cursor.fetchone()
        
        # If patient record doesn't exist, create it
        if not patient:
            logger.info(f"Creating patient record for user_id {data['patientId']}")
            cursor.execute(
                "INSERT INTO patients (user_id) VALUES (%s)",
                (data['patientId'],)
            )
            db.connection.commit()
            patient_id = cursor.lastrowid
        else:
            patient_id = patient['patient_id']
        
        # Insert feedback
        sql = """
            INSERT INTO specialist_feedback 
            (specialist_id, patient_id, reading_id, feedback_text)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data['specialistId'],
            patient_id,
            data.get('readingId'),
            data['feedbackText']
        ))
        db.connection.commit()
        feedback_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            "feedbackId": feedback_id,
            "message": "Feedback added successfully"
        }), 201
    
    except Exception as e:
        logger.error(f"Error adding feedback: {str(e)}")
        return jsonify({"error": str(e)}), 500



# patient get feedback
@app.route('/api/patient/<int:patient_id>/feedback', methods=['GET'])
def get_patient_feedback(patient_id):
    """Get all feedback for a patient"""
    try:
        feedback = db.get_specialist_feedback(patient_id)

        return jsonify({
            "patientId": patient_id,
            "feedback": feedback,
            "count": len(feedback)
        }), 200

    except Exception as e:
        logger.error(f"Error in get_patient_feedback({patient_id}): {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/patient/<int:patient_id>/specialist', methods=['GET'])
def get_patient_specialist(patient_id):
    """Get the assigned specialist for a patient"""
    try:
        cursor = db._get_cursor()
        try:
            sql = """
                SELECT s.specialist_id, u.user_id, u.first_name, u.last_name, u.email
                FROM specialistpatient sp
                JOIN specialists s ON sp.specialist_id = s.specialist_id
                JOIN users u ON s.user_id = u.user_id
                WHERE sp.patient_id = %s
                LIMIT 1
            """
            cursor.execute(sql, (patient_id,))
            specialist = cursor.fetchone()
            
            if specialist:
                return jsonify({
                    "patientId": patient_id,
                    "specialist": specialist
                }), 200
            else:
                return jsonify({
                    "patientId": patient_id,
                    "specialist": None,
                    "message": "No specialist assigned"
                }), 200
        finally:
            cursor.close()

    except Exception as e:
        logger.error(f"Error in get_patient_specialist({patient_id}): {e}")
        return jsonify({"error": "Internal server error"}), 500
    
# AI Insights
@app.route('/api/insights/<int:user_id>', methods=['GET'])
def get_insights(user_id):
    """Generate fresh AI-powered insights for a user"""
    try:
        days = request.args.get('days', default=30, type=int)
        
        # Get user readings
        readings = db.get_user_readings(user_id, days)
        
        if not readings:
            return jsonify({"error": "No readings found for this user"}), 404
        
        # Generate comprehensive insights
        insights = ml_service.generate_insights(readings)
        
        return jsonify({
            "userId": user_id,
            "period": f"Last {days} days",
            "insights": insights
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/aiinsights/<int:user_id>', methods=['GET'])
def get_saved_insights(user_id):
    """Get saved AI insights from database"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        insights = db.get_user_insights(user_id, limit)
        
        return jsonify({
            "userId": user_id,
            "insights": insights,
            "count": len(insights)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching insights: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/insights/<int:user_id>/trends', methods=['GET'])
def get_trends(user_id):
    """Get trend analysis for a user"""
    try:
        readings = db.get_user_readings(user_id, days=90)
        
        if not readings:
            return jsonify({"error": "No readings found"}), 404
        
        trends = ml_service.analyze_trends(readings)
        
        return jsonify({
            "userId": user_id,
            "trends": trends
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/insights/<int:user_id>/patterns', methods=['GET'])
def get_patterns(user_id):
    """Identify patterns in blood sugar readings"""
    try:
        readings = db.get_user_readings(user_id, days=60)
        
        if not readings:
            return jsonify({"error": "No readings found"}), 404
        
        patterns = ml_service.identify_patterns(readings)
        
        return jsonify({
            "userId": user_id,
            "patterns": patterns
        }), 200
    
    except Exception as e:
        logger.error(f"Error identifying patterns: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Alerts and Notifications
@app.route('/api/alerts/<int:user_id>', methods=['GET'])
def get_alerts(user_id):
    """Get alerts for a user"""
    try:
        days = request.args.get('days', default=30, type=int)
        alerts = db.get_user_alerts(user_id, days)
        
        return jsonify({
            "userId": user_id,
            "alerts": alerts,
            "count": len(alerts)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Thresholds
@app.route('/api/thresholds/<int:user_id>', methods=['GET'])
def get_thresholds(user_id):
    """Get user's custom thresholds"""
    try:
        thresholds = db.get_user_thresholds(user_id)
        
        return jsonify({
            "userId": user_id,
            "thresholds": thresholds
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching thresholds: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/thresholds/<int:user_id>', methods=['POST'])
def set_threshold(user_id):
    """Set or update user's threshold"""
    try:
        data = request.json
        required_fields = ['status', 'minValue', 'maxValue']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        threshold_id = db.set_user_threshold(
            user_id=user_id,
            status=data['status'],
            min_value=data['minValue'],
            max_value=data['maxValue']
        )
        
        return jsonify({
            "thresholdId": threshold_id,
            "message": "Threshold set successfully"
        }), 200
    
    except Exception as e:
        logger.error(f"Error setting threshold: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/thresholds', methods=['GET'])
def get_all_thresholds():
    """Get all thresholds (for staff management)"""
    try:
        thresholds = db.get_all_thresholds()
        
        return jsonify({
            "thresholds": thresholds,
            "count": len(thresholds)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching all thresholds: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/thresholds/<int:threshold_id>', methods=['DELETE'])
def delete_threshold(threshold_id):
    """Delete a threshold by ID"""
    try:
        success = db.delete_threshold(threshold_id)
        
        if success:
            return jsonify({
                "message": "Threshold deleted successfully"
            }), 200
        else:
            return jsonify({"error": "Threshold not found"}), 404
    
    except Exception as e:
        logger.error(f"Error deleting threshold: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Diet Recommendations
@app.route('/api/diet/<condition>', methods=['GET'])
def get_diet_recommendations(condition):
    """Get diet recommendations for a condition"""
    try:
        meal_type = request.args.get('mealType')
        recommendations = db.get_diet_recommendations(condition, meal_type)
        
        return jsonify({
            "condition": condition,
            "mealType": meal_type,
            "recommendations": recommendations,
            "count": len(recommendations)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching diet recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Specialist Features
@app.route('/api/patients', methods=['GET'])
def get_all_patients():
    """Get all patients in the system (for staff/admin)"""
    try:
        patients = db.get_all_patients()
        
        return jsonify({
            "patients": patients,
            "count": len(patients)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching all patients: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/specialist/<int:specialist_id>/patients', methods=['GET'])
def get_specialist_patients(specialist_id):
    """Get all patients assigned to a specialist
    
    Args:
        specialist_id: Can be either user_id or specialist_id from specialists table
    """
    try:
        # First check if this is a user_id, and if so, get the specialist_id
        cursor = db._get_cursor()
        try:
            cursor.execute(
                "SELECT specialist_id FROM specialists WHERE user_id = %s OR specialist_id = %s",
                (specialist_id, specialist_id)
            )
            result = cursor.fetchone()
            
            if result:
                actual_specialist_id = result['specialist_id']
            else:
                return jsonify({"error": "Specialist not found"}), 404
                
        finally:
            cursor.close()
        
        # Get patients using the actual specialist_id from specialists table
        patients = db.get_specialist_patients(actual_specialist_id)
        
        return jsonify({
            "specialistId": actual_specialist_id,
            "patients": patients,
            "count": len(patients)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching specialist patients: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/specialist/<int:specialist_id>/dashboard', methods=['GET'])
def get_specialist_dashboard(specialist_id):
    """Get dashboard statistics for specialist"""
    try:
        dashboard = db.get_specialist_dashboard(specialist_id)
        
        if not dashboard:
            return jsonify({"error": "Specialist not found"}), 404
        
        return jsonify({
            "specialistId": specialist_id,
            "dashboard": dashboard
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/specialist/<int:specialist_id>/attention', methods=['GET'])
def get_patients_needing_attention(specialist_id):
    """Get patients requiring immediate attention"""
    try:
        patients = db.get_specialist_attention_list(specialist_id)
        
        return jsonify({
            "specialistId": specialist_id,
            "patientsNeedingAttention": patients,
            "count": len(patients)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching attention list: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/specialist/alerts/<int:specialist_id>', methods=['GET'])
def get_specialist_alerts(specialist_id):
    """Get all alerts for a specialist's patients"""
    try:
        days = request.args.get('days', default=7, type=int)
        
        # Get all patients for this specialist
        patients = db.get_specialist_patients(specialist_id)
        
        all_alerts = []
        for patient in patients:
            alerts = db.get_user_alerts(patient['user_id'], days)
            for alert in alerts:
                alert['patient_name'] = f"{patient['first_name']} {patient['last_name']}"
                alert['patient_id'] = patient['patient_id']
            all_alerts.extend(alerts)
        
        # Sort by date
        all_alerts.sort(key=lambda x: x['date_sent'], reverse=True)
        
        return jsonify({
            "specialistId": specialist_id,
            "alerts": all_alerts,
            "count": len(all_alerts)
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching specialist alerts: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Reports
@app.route('/api/reports/<int:user_id>', methods=['GET'])
def generate_report(user_id):
    """Generate a comprehensive health report"""
    try:
        days = request.args.get('days', default=30, type=int)
        
        readings = db.get_user_readings(user_id, days)
        if not readings:
            return jsonify({"error": "No readings found"}), 404
        
        report = ml_service.generate_report(user_id, readings)
        
        # Add saved insights
        report['saved_insights'] = db.get_user_insights(user_id, limit=5)
        
        # Add thresholds
        report['thresholds'] = db.get_user_thresholds(user_id)
        
        return jsonify(report), 200
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
# Admin Reports Annually/ Monthly
# Add to app.py

@app.route('/api/admin/reports/monthly', methods=['GET'])
def get_monthly_report():
    """Generate monthly report for admin"""
    try:
        month = request.args.get('month')  # Format: YYYY-MM
        year = request.args.get('year')
        
        if not month and not year:
            return jsonify({"error": "Month or year parameter required"}), 400
        
        cursor = db._get_cursor()
        
        # Get active patients count
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'patient'")
        total_patients = cursor.fetchone()['count']
        
        # Get readings for the period
        if month:
            date_filter = f"DATE_FORMAT(date_time, '%Y-%m') = '{month}'"
        else:
            date_filter = f"YEAR(date_time) = {year}"
        
        # Get patient statistics
        sql = f"""
            SELECT 
                u.user_id,
                u.first_name,
                u.last_name,
                COUNT(r.reading_id) as total_readings,
                AVG(r.value) as avg_value,
                MAX(r.value) as max_value,
                MIN(r.value) as min_value,
                SUM(CASE WHEN r.status = 'normal' THEN 1 ELSE 0 END) as normal_count,
                SUM(CASE WHEN r.status = 'borderline' THEN 1 ELSE 0 END) as borderline_count,
                SUM(CASE WHEN r.status = 'abnormal' THEN 1 ELSE 0 END) as abnormal_count
            FROM users u
            LEFT JOIN bloodsugarreadings r ON u.user_id = r.user_id AND {date_filter}
            WHERE u.role = 'patient'
            GROUP BY u.user_id
        """
        cursor.execute(sql)
        patient_stats = cursor.fetchall()
        
        # Convert Decimal to float and add patient_name
        for stat in patient_stats:
            # Combine first_name and last_name into patient_name
            stat['patient_name'] = f"{stat.get('first_name', '')} {stat.get('last_name', '')}".strip()
            
            # Convert Decimal/None to proper types (always convert, even if 0 or None)
            stat['avg_value'] = float(stat.get('avg_value') or 0)
            stat['max_value'] = float(stat.get('max_value') or 0)
            stat['min_value'] = float(stat.get('min_value') or 0)
            stat['total_readings'] = int(stat.get('total_readings') or 0)
            stat['normal_count'] = int(stat.get('normal_count') or 0)
            stat['borderline_count'] = int(stat.get('borderline_count') or 0)
            stat['abnormal_count'] = int(stat.get('abnormal_count') or 0)
                
        # Get top food triggers with patient names
        sql = f"""
            SELECT 
                r.food_intake,
                COUNT(*) as trigger_count,
                AVG(r.value) as avg_value,
                GROUP_CONCAT(DISTINCT CONCAT(u.first_name, ' ', u.last_name) SEPARATOR ', ') as patients
            FROM bloodsugarreadings r
            LEFT JOIN users u ON r.user_id = u.user_id
            WHERE {date_filter}
                AND r.status IN ('abnormal', 'borderline')
                AND r.food_intake IS NOT NULL
                AND r.food_intake != ''
            GROUP BY r.food_intake
            ORDER BY trigger_count DESC
            LIMIT 10
        """
        cursor.execute(sql)
        food_triggers = cursor.fetchall()
        
        for trigger in food_triggers:
            if trigger.get('avg_value'):
                trigger['avg_value'] = float(trigger['avg_value'])
        
        # Get top activity triggers with patient names
        sql = f"""
            SELECT 
                r.activity,
                COUNT(*) as trigger_count,
                AVG(r.value) as avg_value,
                GROUP_CONCAT(DISTINCT CONCAT(u.first_name, ' ', u.last_name) SEPARATOR ', ') as patients
            FROM bloodsugarreadings r
            LEFT JOIN users u ON r.user_id = u.user_id
            WHERE {date_filter}
                AND r.status IN ('abnormal', 'borderline')
                AND r.activity IS NOT NULL
                AND r.activity != ''
            GROUP BY r.activity
            ORDER BY trigger_count DESC
            LIMIT 10
        """
        cursor.execute(sql)
        activity_triggers = cursor.fetchall()
        
        for trigger in activity_triggers:
            if trigger.get('avg_value'):
                trigger['avg_value'] = float(trigger['avg_value'])
        
        # Convert triggers to dictionary format with patient names
        food_triggers_dict = {
            item['food_intake']: {
                'count': item['trigger_count'],
                'patients': item.get('patients', '')
            } for item in food_triggers
        }
        activity_triggers_dict = {
            item['activity']: {
                'count': item['trigger_count'],
                'patients': item.get('patients', '')
            } for item in activity_triggers
        }
        
        cursor.close()
        
        return jsonify({
            "period": month or year,
            "total_active_patients": total_patients,
            "patient_statistics": patient_stats,
            "food_triggers": food_triggers_dict,
            "activity_triggers": activity_triggers_dict,
            "generated_at": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reports/annual', methods=['GET'])
def get_annual_report():
    """Generate annual report for admin"""
    try:
        year = request.args.get('year')
        
        if not year:
            return jsonify({"error": "Year parameter required"}), 400
        
        cursor = db._get_cursor()
        
        # Get monthly trends
        sql = f"""
            SELECT 
                DATE_FORMAT(date_time, '%Y-%m') as month,
                COUNT(DISTINCT user_id) as active_patients,
                COUNT(*) as total_readings,
                AVG(value) as avg_value,
                SUM(CASE WHEN status IN ('abnormal', 'borderline') THEN 1 ELSE 0 END) as abnormal_count
            FROM bloodsugarreadings
            WHERE YEAR(date_time) = {year}
            GROUP BY DATE_FORMAT(date_time, '%Y-%m')
            ORDER BY month
        """
        cursor.execute(sql)
        monthly_trends = cursor.fetchall()
        
        for trend in monthly_trends:
            if trend.get('avg_value'):
                trend['avg_value'] = float(trend['avg_value'])
        
        # Get overall statistics
        sql = f"""
            SELECT 
                COUNT(DISTINCT user_id) as total_patients,
                COUNT(*) as total_readings,
                AVG(value) as avg_value,
                MAX(value) as max_value,
                MIN(value) as min_value
            FROM bloodsugarreadings
            WHERE YEAR(date_time) = {year}
        """
        cursor.execute(sql)
        overall_stats = cursor.fetchone()
        
        if overall_stats.get('avg_value'):
            overall_stats['avg_value'] = float(overall_stats['avg_value'])
        if overall_stats.get('max_value'):
            overall_stats['max_value'] = float(overall_stats['max_value'])
        if overall_stats.get('min_value'):
            overall_stats['min_value'] = float(overall_stats['min_value'])
        
        # Get top food triggers for the year
        sql = f"""
            SELECT 
                food_intake,
                COUNT(*) as trigger_count,
                AVG(value) as avg_value
            FROM bloodsugarreadings
            WHERE YEAR(date_time) = {year}
                AND status IN ('abnormal', 'borderline')
                AND food_intake IS NOT NULL
                AND food_intake != ''
            GROUP BY food_intake
            ORDER BY trigger_count DESC
            LIMIT 10
        """
        cursor.execute(sql)
        food_triggers = cursor.fetchall()
        
        for trigger in food_triggers:
            if trigger.get('avg_value'):
                trigger['avg_value'] = float(trigger['avg_value'])
        
        cursor.close()
        
        return jsonify({
            "year": year,
            "overall_statistics": overall_stats,
            "monthly_trends": monthly_trends,
            "top_food_triggers": food_triggers,
            "generated_at": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating annual report: {str(e)}")
        return jsonify({"error": str(e)}), 500

# patient assignment to doctor api route
# In app.py

@app.route('/api/assignments/assign', methods=['POST'])
def assign_patient_api():
    """API endpoint to assign a patient user_id to a specialist user_id."""
    try:
        data = request.json
        patient_user_id = data.get('patientId')
        specialist_user_id = data.get('specialistId')

        if not patient_user_id or not specialist_user_id:
            return jsonify({"error": "Missing patientId or specialistId"}), 400

        db.assign_patient_to_specialist(patient_user_id, specialist_user_id)

        return jsonify({"message": "Assignment successful"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error in assignment API: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to complete assignment."}), 500

@app.route('/api/assignments', methods=['GET'])
def get_all_assignments_api():
    """API endpoint to get all patient-specialist assignments from database."""
    try:
        cursor = db._get_cursor()
        try:
            cursor.execute("""
                SELECT 
                    sp.specialist_id,
                    sp.patient_id,
                    sp.created_at,
                    p.user_id as patient_user_id,
                    s.user_id as specialist_user_id,
                    CONCAT(pu.first_name, ' ', pu.last_name) as patient_name,
                    pu.email as patient_email,
                    CONCAT(su.first_name, ' ', su.last_name) as specialist_name,
                    su.email as specialist_email
                FROM specialistpatient sp
                JOIN patients p ON sp.patient_id = p.patient_id
                JOIN specialists s ON sp.specialist_id = s.specialist_id
                JOIN users pu ON p.user_id = pu.user_id
                JOIN users su ON s.user_id = su.user_id
                ORDER BY sp.created_at DESC
            """)
            
            assignments = cursor.fetchall()
            
            return jsonify({
                "count": len(assignments),
                "assignments": assignments
            }), 200
            
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Error fetching assignments: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to fetch assignments."}), 500

@app.route('/api/assignments/<int:specialist_id>/<int:patient_id>', methods=['DELETE'])
def remove_assignment_api(specialist_id, patient_id):
    """API endpoint to remove a patient assignment from a specialist."""
    try:
        cursor = db._get_cursor()
        try:
            cursor.execute(
                "DELETE FROM specialistpatient WHERE specialist_id = %s AND patient_id = %s",
                (specialist_id, patient_id)
            )
            db.connection.commit()
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Assignment not found"}), 404
            
            return jsonify({"message": "Assignment removed successfully"}), 200
            
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Error removing assignment: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to remove assignment."}), 500

# Test Endpoints
@app.route('/api/test/database', methods=['GET'])
def test_database():
    """Test database connection and show sample data"""
    try:
        # Get sample user
        user = db.get_user(1)
        
        # Get sample readings
        readings = db.get_user_readings(1, days=7)
        
        # Get sample insights
        insights = db.get_user_insights(1, limit=3)
        
        return jsonify({
            "status": "Database connected successfully",
            "sample_user": user,
            "recent_readings_count": len(readings),
            "recent_insights_count": len(insights),
            "message": "All database tables accessible"
        }), 200
    
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/patients/<int:patient_id>/documents', methods=['POST'])
def upload_documents(patient_id):
    """
    Upload ID picture + medical documents for a patient.
    Stores files in /uploads/patient_<id>/ and returns metadata.
    """
    try:
        # OPTIONAL: verify that patient exists in DB
        cursor = db._get_cursor()
        cursor.execute("SELECT patient_id FROM patients WHERE patient_id = %s", (patient_id,))
        patient = cursor.fetchone()
        cursor.close()

        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Make per-patient folder
        patient_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"patient_{patient_id}")
        os.makedirs(patient_folder, exist_ok=True)

        files_saved = []

        # Single ID picture (optional)
        id_pic = request.files.get('idPicture')
        if id_pic and id_pic.filename and allowed_file(id_pic.filename):
            filename = secure_filename(id_pic.filename)
            save_path = os.path.join(patient_folder, f"id_{filename}")
            id_pic.save(save_path)
            files_saved.append({
                "type": "idPicture",
                "filename": filename,
                "path": f"patient_{patient_id}/id_{filename}"
            })

        # Multiple medical records
        medical_files = request.files.getlist('medicalRecords')
        for f in medical_files:
            if f and f.filename and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = os.path.join(patient_folder, filename)
                f.save(save_path)
                files_saved.append({
                    "type": "medicalRecord",
                    "filename": filename,
                    "path": f"patient_{patient_id}/{filename}"
                })

        if not files_saved:
            return jsonify({"error": "No valid files uploaded"}), 400

        return jsonify({
            "patientId": patient_id,
            "files": files_saved,
            "count": len(files_saved),
            "message": "Documents uploaded successfully"
        }), 201

    except Exception as e:
        logger.error(f"Error uploading documents for patient {patient_id}: {e}")
        return jsonify({"error": "Failed to upload documents"}), 500

@app.route('/api/setup/demo-users', methods=['POST'])
def setup_demo_users():
    """Create demo users including Alice for testing"""
    try:
        from werkzeug.security import generate_password_hash
        
        cursor = db._get_cursor()
        created_users = []
        
        # Demo patients with password123
        demo_patients = [
            {'email': 'alice@x.com', 'first_name': 'Alice', 'last_name': 'Johnson', 'phone': '555-0101'},
            {'email': 'bob@x.com', 'first_name': 'Bob', 'last_name': 'Smith', 'phone': '555-0102'},
            {'email': 'sarah@x.com', 'first_name': 'Sarah', 'last_name': 'Williams', 'phone': '555-0103'},
            {'email': 'michael@x.com', 'first_name': 'Michael', 'last_name': 'Brown', 'phone': '555-0104'},
            {'email': 'emma@x.com', 'first_name': 'Emma', 'last_name': 'Davis', 'phone': '555-0105'}
        ]
        
        password_hash = generate_password_hash('password123')
        
        for patient_data in demo_patients:
            # Check if user already exists
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (patient_data['email'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update password
                cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", 
                             (password_hash, patient_data['email']))
                user_id = existing['user_id']
                created_users.append(f"Updated: {patient_data['email']}")
            else:
                # Create new user
                cursor.execute("""
                    INSERT INTO users (email, password_hash, role, first_name, last_name, phone, date_of_birth)
                    VALUES (%s, %s, 'patient', %s, %s, %s, '1990-01-01')
                """, (patient_data['email'], password_hash, patient_data['first_name'], 
                      patient_data['last_name'], patient_data['phone']))
                user_id = cursor.lastrowid
                
                # Create patient record
                cursor.execute("""
                    INSERT INTO patients (user_id, health_care_number, created_at)
                    VALUES (%s, %s, NOW())
                """, (user_id, f'HCN{user_id}'))
                
                created_users.append(f"Created: {patient_data['email']}")
        
        db.connection.commit()
        cursor.close()
        
        return jsonify({
            "message": "Demo users setup completed",
            "users": created_users,
            "password": "password123"
        }), 201
        
    except Exception as e:
        logger.error(f"Error setting up demo users: {e}")
        if cursor:
            cursor.close()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize scheduler for periodic tasks
    scheduler_service.start()
    
    logger.info("=" * 60)
    logger.info("Blood Sugar Monitoring System - Backend Server")
    logger.info("=" * 60)
    logger.info("Database: Connected")
    logger.info("ML Service: Ready")
    logger.info("Scheduler: Started")
    logger.info("=" * 60)
    logger.info("API Endpoints Available:")
    logger.info("  - POST   /api/readings")
    logger.info("  - GET    /api/readings/<user_id>")
    logger.info("  - GET    /api/insights/<user_id>")
    logger.info("  - GET    /api/aiinsights/<user_id>")
    logger.info("  - GET    /api/alerts/<user_id>")
    logger.info("  - GET    /api/diet/<condition>")
    logger.info("  - GET    /api/specialist/<id>/dashboard")
    logger.info("  - GET    /api/test/database")
    logger.info("=" * 60)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)