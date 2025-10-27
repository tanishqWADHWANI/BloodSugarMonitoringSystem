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
CORS(app)

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
            phone=data.get('phone')
        )
        
        return jsonify({"userId": user_id, "message": "User registered successfully"}), 201
    
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
        data = request.json
        
        # Check if user exists
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Update user
        db.update_user(user_id, **data)
        
        return jsonify({"message": "User updated successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        # Check if user exists
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Delete user (CASCADE will delete related records)
        db.delete_user(user_id)
        
        return jsonify({"message": "User deleted successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({"error": str(e)}), 500

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