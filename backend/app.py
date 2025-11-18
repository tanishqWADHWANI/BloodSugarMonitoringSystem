from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime
import logging
from models import Database
from ml_service import MLService
from notification_service import NotificationService
from scheduler_service import SchedulerService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://127.0.0.1:5500",
            "http://localhost:5500"
        ]
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

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Check if the service is running"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

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
            health_care_number=data.get('healthCareNumber')

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
            health_care_number=data.get('healthCareNumber')
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
        working_id = data.get('workingId')  # For specialists/staff
        health_care_number = data.get('healthCareNumber')  # For patients
        
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
            working_id=working_id
        )
        
        return jsonify({
            'success': True,
            'userId': user_id,
            'message': 'User created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
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
        
        # Get AI prediction and insights
        prediction_result = ml_service.predict_status(
            value=data['value'],
            fasting=data.get('fasting', False),
            food_intake=data.get('foodIntake', ''),
            activity=data.get('activity', ''),
            time_of_day=datetime.now().hour
        )
        
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
            status=prediction_result['status']
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
    data = request.json
    
    user = db.get_user_by_email(data['email'])
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Simple password check (improve with hashing later)
    if user['password_hash'] != data['password']:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Remove password from response
    del user['password_hash']
    
    return jsonify({
        "message": "Login successful",
        "user": user
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
@app.route('/api/specialist/<int:specialist_id>/patients', methods=['GET'])
def get_specialist_patients(specialist_id):
    """Get all patients assigned to a specialist"""
    try:
        patients = db.get_specialist_patients(specialist_id)
        
        return jsonify({
            "specialistId": specialist_id,
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
                SUM(CASE WHEN r.status IN ('abnormal', 'borderline') THEN 1 ELSE 0 END) as abnormal_count
            FROM users u
            LEFT JOIN bloodsugarreadings r ON u.user_id = r.user_id AND {date_filter}
            WHERE u.role = 'patient'
            GROUP BY u.user_id
        """
        cursor.execute(sql)
        patient_stats = cursor.fetchall()
        
        # Convert Decimal to float
        for stat in patient_stats:
            if stat.get('avg_value'):
                stat['avg_value'] = float(stat['avg_value'])
            if stat.get('max_value'):
                stat['max_value'] = float(stat['max_value'])
            if stat.get('min_value'):
                stat['min_value'] = float(stat['min_value'])
            if stat.get('total_readings'):
                stat['total_readings'] = int(stat['total_readings'])
            if stat.get('abnormal_count'):
                stat['abnormal_count'] = int(stat['abnormal_count'])
                
        # Get top food triggers
        sql = f"""
            SELECT 
                food_intake,
                COUNT(*) as trigger_count,
                AVG(value) as avg_value
            FROM bloodsugarreadings
            WHERE {date_filter}
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
        
        # Get top activity triggers
        sql = f"""
            SELECT 
                activity,
                COUNT(*) as trigger_count,
                AVG(value) as avg_value
            FROM bloodsugarreadings
            WHERE {date_filter}
                AND status IN ('abnormal', 'borderline')
                AND activity IS NOT NULL
                AND activity != ''
            GROUP BY activity
            ORDER BY trigger_count DESC
            LIMIT 10
        """
        cursor.execute(sql)
        activity_triggers = cursor.fetchall()
        
        for trigger in activity_triggers:
            if trigger.get('avg_value'):
                trigger['avg_value'] = float(trigger['avg_value'])
        
        cursor.close()
        
        return jsonify({
            "period": month or year,
            "total_active_patients": total_patients,
            "patient_statistics": patient_stats,
            "top_food_triggers": food_triggers,
            "top_activity_triggers": activity_triggers,
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