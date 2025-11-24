"""
Blood Sugar Monitoring System - Backend (Flask API)

This file defines all REST API endpoints for:
- User & admin management
- Patient / specialist dashboards
- Blood sugar readings CRUD
- AI insights, trends, and patterns
- Alerts, thresholds, diet recommendations
- Admin reports (monthly / annual)
- Patient–specialist assignments

The app relies on:
- models.Database
- ml_service.MLService
- notification_service.NotificationService
- scheduler_service.SchedulerService
"""

from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, date
import logging

# Local imports (your own modules)
from models import Database
from ml_service import MLService
from notification_service import NotificationService
from scheduler_service import SchedulerService

# ========================================
# 1. Environment, Logging, Flask App Setup
# ========================================

# Load environment variables from .env
load_dotenv()

# Configure logging once, at module load
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
# Serve the frontend folder as static files so frontend and backend can be
# same-origin in development (recommended). The static_folder path is set
# relative to this file's parent directory.
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Configure CORS so your front-end can call this API.
# Allow configuration via environment variable `CORS_ORIGINS`.
# Example:
#   export CORS_ORIGINS="https://my-preview.domain,https://localhost:5500"
# By default (development) we allow all origins to avoid preview friction.
cors_origins = os.environ.get("CORS_ORIGINS", "*")
if cors_origins.strip() == "":
    cors_origins = "*"

if cors_origins == "*":
    CORS(app, resources={r"/*": {"origins": "*"}})
else:
    origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
    CORS(app, resources={r"/*": {"origins": origins_list}})

logger.info(f"CORS configured. Origins={cors_origins}")

# ========================================
# 2. Service Initialization (DB, ML, etc.)
# ========================================

# Database connection
try:
    db = Database()
    logger.info("Database initialized successfully.")
except Exception as e:
    # Do NOT crash the app if DB fails; just log it
    logger.error(f"Database connection failed during startup: {e}", exc_info=True)
    db = None

# ML and notification services
ml_service = MLService()
notification_service = NotificationService()

# Scheduler for background / periodic tasks
try:
    scheduler_service = SchedulerService(db, notification_service)
    logger.info("SchedulerService initialized successfully.")
except Exception as e:
    logger.error(f"SchedulerService disabled because DB is not available: {e}", exc_info=True)
    scheduler_service = None


# ========================================
# 3. Health & Test Endpoints
# ========================================

@app.route("/health", methods=["GET"])
def health_check():
    """
    Simple health check for uptime monitoring.
    Does NOT check database or other services.
    """
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
        }
    ), 200


@app.route("/api/server/mode", methods=["GET"])
def server_mode():
    """
    Return runtime mode info for the frontend (helpful in dev):
      - demo_mode: whether DEMO_AUTH is enabled
      - db_available: whether the DB connection appears usable
    The endpoint is safe to call from the browser and returns a small JSON.
    """
    demo_env = os.environ.get("DEMO_AUTH", "0").lower() in ("1", "true", "yes")

    db_available = False
    if db is not None:
        try:
            # lightweight check
            cursor = db._get_cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            db_available = True
        except Exception:
            db_available = False

    return jsonify({
        "demo_mode": demo_env,
        "db_available": db_available,
    }), 200


# Serve frontend static files (development convenience)
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_frontend(path):
    """
    Serve frontend static files from the top-level `frontend/` directory.
    If the requested file does not exist, fall back to `index.html`.
    This enables opening `http://127.0.0.1:5000/specialist.html` and other
    frontend files directly without a separate static server.
    """
    try:
        full_path = os.path.join(frontend_dir, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(frontend_dir, path)
    except Exception:
        # swallow file system errors and fallback to index
        pass

    # Default fallback
    return send_from_directory(frontend_dir, 'index.html')


@app.route("/api/db/health", methods=["GET"])
def db_health_check():
    """
    Run a set of lightweight DB integrity checks and return a concise JSON report.
    Checks performed:
      - table row counts for core tables
      - orphaned records counts (patients/specialists/readings)
      - existence of key triggers
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        cursor = db._get_cursor()

        core_tables = [
            'users', 'patients', 'specialists', 'bloodsugarreadings',
            'alerts', 'thresholds', 'specialistpatient', 'specialist_feedback'
        ]

        counts = {}
        for t in core_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) AS c FROM `{t}`")
                counts[t] = cursor.fetchone()['c']
            except Exception:
                counts[t] = None

        # Orphan checks
        cursor.execute(
            "SELECT COUNT(*) AS orphan_patients FROM patients p LEFT JOIN users u ON p.user_id=u.user_id WHERE u.user_id IS NULL"
        )
        orphan_patients = cursor.fetchone()['orphan_patients']

        cursor.execute(
            "SELECT COUNT(*) AS orphan_specialists FROM specialists s LEFT JOIN users u ON s.user_id=u.user_id WHERE u.user_id IS NULL"
        )
        orphan_specialists = cursor.fetchone()['orphan_specialists']

        cursor.execute(
            "SELECT COUNT(*) AS orphan_readings FROM bloodsugarreadings r LEFT JOIN users u ON r.user_id=u.user_id WHERE u.user_id IS NULL"
        )
        orphan_readings = cursor.fetchone()['orphan_readings']

        # Trigger existence (names known from dump)
        cursor.execute("SHOW TRIGGERS")
        triggers = [r['Trigger'] for r in cursor.fetchall()]

        cursor.close()

        report = {
            'counts': counts,
            'orphans': {
                'patients': orphan_patients,
                'specialists': orphan_specialists,
                'readings': orphan_readings,
            },
            'triggers': triggers,
        }

        return jsonify(report), 200

    except Exception as e:
        logger.error(f"DB health check failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/test/database", methods=["GET"])
def test_database():
    """
    Test database connection and show a small snapshot.
    This is mainly for debugging in development.
    """
    if db is None:
        return jsonify({"error": "Database object not initialized"}), 500

    try:
        # Get a sample user (ID 1 by convention for testing)
        sample_user = db.get_user(1)

        # Recent readings
        recent_readings = db.get_user_readings(1, days=7)

        # Recent AI insights
        recent_insights = db.get_user_insights(1, limit=3)

        return jsonify(
            {
                "status": "Database connected successfully",
                "sample_user": sample_user,
                "recent_readings_count": len(recent_readings),
                "recent_insights_count": len(recent_insights),
                "message": "All database tables accessible",
            }
        ), 200

    except Exception as e:
        logger.error(f"Database test failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 4. Authentication & Login
# ========================================

@app.route("/api/auth/login", methods=["POST"])
def handle_auth_login():
    """
    Generic auth login (likely used by admin dashboard).
    Uses db.get_user_by_email and db.verify_password.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.get_user_by_email(email)
    if not user or not db.verify_password(user, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Return minimal info required by front-end
    # Normalize user id key (DB uses `user_id`)
    uid = user.get('user_id') or user.get('id')
    return jsonify({"userId": uid, "role": user.get("role")}), 200


@app.route("/api/login", methods=["POST"])
def login():
    """
    Simple user login using plain password comparison
    (legacy / student version). Uses password_hash column directly.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.get_user_by_email(email)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Verify using db helper which supports hashed and legacy plain-text passwords
    if not db.verify_password(user, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Do not expose password hash in response
    user.pop("password_hash", None)

    return jsonify({"message": "Login successful", "user": user}), 200


@app.route("/api/specialist/login", methods=["POST"])
def specialist_login():
    """
    Demo login for specialists using hard-coded demo accounts.
    This bypasses the real database and is typically for UI demo only.
    """
    data = request.get_json() or {}
    username = (data.get("username") or data.get('email') or "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username/email and password required"}), 400

    # Demo mode override: if DEMO_AUTH is explicitly enabled, use demo-only auth
    demo_env = os.environ.get("DEMO_AUTH", "0").lower() in ("1", "true", "yes")

    DEMO_CREDS = {
        'jsmith': {'password': 'smith123', 'full_name': 'Dr. John Smith', 'email': 'jsmith@demo'},
        'ajones': {'password': 'jones123', 'full_name': 'Dr. Alex Jones', 'email': 'ajones@demo'},
        'clee': {'password': 'lee123', 'full_name': 'Dr. Christina Lee', 'email': 'clee@demo'},
    }

    # If developer explicitly forced demo mode, bypass DB entirely.
    if demo_env:
        key = username.split('@')[0].lower()
        demo = DEMO_CREDS.get(key)
        if demo and demo['password'] == password:
            return jsonify({
                "success": True,
                "token": f"spec-demo-{key}",
                "specialist": {
                    "id": 0,
                    "user_id": 0,
                    "username": key,
                    "full_name": demo['full_name'],
                    "email": demo['email'],
                }
            }), 200
        else:
            return jsonify({"success": False, "message": "Invalid username or password"}), 401

    # Normal mode: prefer DB-backed authentication. Only if DB is unavailable
    # will we attempt the demo fallback.
    if db is not None:
        try:
            cursor = db._get_cursor()

            working_id = data.get('working_id') or data.get('workingId')
            if working_id:
                cursor.execute(
                    "SELECT u.* FROM users u JOIN specialists s ON u.user_id = s.user_id WHERE s.working_id = %s LIMIT 1",
                    (working_id,)
                )
                account = cursor.fetchone()
            else:
                sql = """
                    SELECT u.* FROM users u
                    JOIN specialists s ON u.user_id = s.user_id
                    WHERE LOWER(u.email) = LOWER(%s)
                       OR LOWER(SUBSTRING_INDEX(u.email, '@', 1)) = LOWER(%s)
                       OR LOWER(CONCAT(u.first_name, '.', u.last_name)) = LOWER(%s)
                    LIMIT 1
                """
                cursor.execute(sql, (username, username, username))
                account = cursor.fetchone()

            cursor.close()

            if not account:
                # DB is available but account not found — do NOT fall back to demo.
                return jsonify({"success": False, "message": "Invalid username or password"}), 401

            if not db.verify_password(account, password):
                return jsonify({"success": False, "message": "Invalid username or password"}), 401

            return jsonify({
                "success": True,
                "token": f"spec-{account.get('user_id')}",
                "specialist": {
                    "id": account.get('user_id'),
                    "user_id": account.get('user_id'),
                    "username": working_id or username,
                    "full_name": f"{account.get('first_name','')} {account.get('last_name','')}",
                    "email": account.get('email'),
                }
            }), 200

        except Exception as e:
            logger.exception("Specialist login DB error: %s", e)
            # Fall through to demo fallback only if DB operation failed

    # If we reach here, DB is unavailable or errored. Try demo fallback.
    key = username.split('@')[0].lower()
    demo = DEMO_CREDS.get(key)
    if demo and demo['password'] == password:
        return jsonify({
            "success": True,
            "token": f"spec-demo-{key}",
            "specialist": {
                "id": 0,
                "user_id": 0,
                "username": key,
                "full_name": demo['full_name'],
                "email": demo['email'],
            }
        }), 200

    # DB is down (or errored) and demo did not match
    return jsonify({"success": False, "message": "Invalid username or password"}), 401


# ========================================
# 5. User Management (Admin + General)
# ========================================

@app.route("/api/users/register", methods=["POST"])
def register_user():
    """
    Public endpoint: Register a new user (patient, specialist, etc.)
    Expected JSON fields:
      - email, password, firstName, lastName, role
      - Optional: dateOfBirth, phone, healthCareNumber
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}
        required_fields = ["email", "password", "firstName", "lastName", "role"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        user_id = db.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            role=data["role"],
            date_of_birth=data.get("dateOfBirth"),
            phone=data.get("phone"),
            health_care_number=data.get("healthCareNumber"),
        )

        return jsonify({"userId": user_id, "message": "User registered successfully"}), 201

    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/users/all", methods=["GET"])
def get_all_users():
    """
    Admin: Get list of all users for admin dashboard.
    Relies on db.get_all_users() to return a list of dicts.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        users = db.get_all_users()
        return jsonify({"users": users}), 200

    except Exception as e:
        # Show full traceback in terminal logs for debugging
        logger.error("CRASH REPORT: Database query failed.", exc_info=True)
        return jsonify({"error": "Failed to fetch users. CHECK TERMINAL LOGS."}), 500


@app.route("/api/admin/users", methods=["POST"])
def create_user_admin():
    """
    Admin: Create a user (patient / specialist / staff).
    Accepts:
      - email, password, firstName, lastName, role  (required)
      - phone, dateOfBirth, workingId, healthCareNumber (optional)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    data = request.json or {}

    try:
        email = data.get("email")
        password = data.get("password")
        first_name = data.get("firstName")
        last_name = data.get("lastName")
        role = data.get("role")
        phone = data.get("phone")
        date_of_birth = data.get("dateOfBirth")
        working_id = data.get("workingId")  # for specialists/staff
        health_care_number = data.get("healthCareNumber")  # for patients

        if not all([email, password, first_name, last_name, role]):
            return jsonify({"error": "Missing required fields"}), 400

        user_id = db.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            date_of_birth=date_of_birth,
            phone=phone,
            health_care_number=health_care_number,
            working_id=working_id,
        )

        return jsonify(
            {
                "success": True,
                "userId": user_id,
                "message": "User created successfully",
            }
        ), 201

    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Get a single user's details by ID.
    Removes password_hash before returning.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        user = db.get_user(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.pop("password_hash", None)
        return jsonify(user), 200

    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """
    Update user details (email, password, names, role, etc.).
    Only fields present in JSON are updated.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}

        # Ensure user exists
        existing = db.get_user(user_id)
        if not existing:
            return jsonify({"error": "User not found"}), 404

        updated = db.update_user(
            user_id,
            email=data.get("email"),
            password=data.get("password"),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            role=data.get("role"),
            date_of_birth=data.get("dateOfBirth"),
            phone=data.get("phone"),
            health_care_number=data.get("healthCareNumber"),
        )

        if not updated:
            return jsonify({"error": "No changes made or user not found"}), 400

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update user"}), 500


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """
    Delete a user by ID.
    Relies on DB foreign key CASCADE to clean up related data.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        existing = db.get_user(user_id)
        if not existing:
            return jsonify({"error": "User not found"}), 404

        deleted = db.delete_user(user_id)
        if not deleted:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete user"}), 500


# ========================================
# 6. Staff & Specialist: Patient Lists / Details
# ========================================

@app.route("/api/staff/patients", methods=["GET"])
def api_staff_patients():
    """
    Staff view: list ALL patients for patient_records.html.
    Joins: patients + users + latest bloodsugarreadings per user.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    cursor = None
    try:
        conn = db.connection
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT
                p.patient_id,
                p.health_care_number,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                u.date_of_birth,
                last_r.last_value,
                last_r.last_status,
                last_r.last_date_time
            FROM patients p
            JOIN users u
              ON u.user_id = p.user_id
            LEFT JOIN (
                SELECT
                    r.user_id,
                    r.value     AS last_value,
                    r.status    AS last_status,
                    r.date_time AS last_date_time
                FROM bloodsugarreadings r
                JOIN (
                    SELECT user_id, MAX(date_time) AS max_dt
                    FROM bloodsugarreadings
                    GROUP BY user_id
                ) x
                  ON x.user_id = r.user_id
                 AND x.max_dt  = r.date_time
            ) AS last_r
              ON last_r.user_id = u.user_id
            ORDER BY
                u.last_name,
                u.first_name
        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        patients = []
        for row in rows:
            full_name = f"{row['first_name']} {row['last_name']}".strip()
            patient_number = row["health_care_number"] or f"P{row['patient_id']}"

            # Date of birth -> age
            dob = row.get("date_of_birth")
            if isinstance(dob, date):
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                dob_str = dob.isoformat()
            else:
                age = None
                dob_str = None

            # Last checked
            last_dt = row.get("last_date_time")
            if isinstance(last_dt, datetime):
                last_checked_str = last_dt.strftime("%Y-%m-%d %H:%M")
            else:
                last_checked_str = None

            last_value = row.get("last_value")
            if last_value is not None:
                last_value = float(last_value)

            patients.append(
                {
                    "id": row["patient_id"],
                    "patient_number": patient_number,
                    "full_name": full_name,
                    "email": row.get("email"),
                    "phone": row.get("phone"),
                    "date_of_birth": dob_str,
                    "age": age,
                    "gender": None,  # No gender column in schema
                    "last_value": last_value,
                    "last_status": row.get("last_status"),
                    "last_checked": last_checked_str,
                }
            )

        return jsonify({"patients": patients}), 200

    except Exception as e:
        logger.error(f"Error in /api/staff/patients: {e}", exc_info=True)
        return jsonify({"error": "Failed to load patients"}), 500

    finally:
        if cursor is not None:
            cursor.close()


@app.route("/api/staff/patients/<patient_number>", methods=["GET"])
def api_staff_patient_detail(patient_number):
    """
    Staff view: detailed info for a single patient.

    patient_number can be:
      - health_care_number (e.g., 'P001')
      - or numeric patient_id
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    cursor = None
    try:
        conn = db.connection
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT
                p.patient_id,
                p.health_care_number,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                u.date_of_birth,
                last_r.last_value,
                last_r.last_status,
                last_r.last_date_time,
                last_r.last_unit
            FROM patients p
            JOIN users u
              ON u.user_id = p.user_id
            LEFT JOIN (
                SELECT
                    r.user_id,
                    r.value     AS last_value,
                    r.status    AS last_status,
                    r.date_time AS last_date_time,
                    r.unit      AS last_unit
                FROM bloodsugarreadings r
                JOIN (
                    SELECT user_id, MAX(date_time) AS max_dt
                    FROM bloodsugarreadings
                    GROUP BY user_id
                ) x
                  ON x.user_id = r.user_id
                 AND x.max_dt  = r.date_time
            ) AS last_r
              ON last_r.user_id = u.user_id
            WHERE p.health_care_number = %s
               OR p.patient_id = %s
            LIMIT 1
        """

        cursor.execute(sql, (patient_number, patient_number))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Patient not found"}), 404

        full_name = f"{row['first_name']} {row['last_name']}".strip()
        patient_number = row["health_care_number"] or f"P{row['patient_id']}"

        dob = row.get("date_of_birth")
        if isinstance(dob, date):
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            dob_str = dob.isoformat()
        else:
            age = None
            dob_str = None

        last_dt = row.get("last_date_time")
        if isinstance(last_dt, datetime):
            last_checked_str = last_dt.strftime("%Y-%m-%d %H:%M")
        else:
            last_checked_str = None

        last_value = row.get("last_value")
        if last_value is not None:
            last_value = float(last_value)

        unit = row.get("last_unit") or "mg/dL"
        status = row.get("last_status")

        if last_value is not None and last_checked_str:
            last_results_str = (
                f"Last blood sugar: {last_value:.1f} {unit} "
                f"on {last_checked_str} ({status or 'normal'})."
            )
        else:
            last_results_str = "No blood sugar readings recorded yet."

        patient_obj = {
            "id": row["patient_id"],
            "patient_number": patient_number,
            "full_name": full_name,
            "email": row.get("email"),
            "phone": row.get("phone"),
            "date_of_birth": dob_str,
            "age": age,
            "gender": None,
            "medical_history": "No detailed medical history stored in the system.",
            "last_results": last_results_str,
            "last_value": last_value,
            "last_status": status,
            "last_checked": last_checked_str,
        }

        return jsonify({"patient": patient_obj}), 200

    except Exception as e:
        logger.error(f"Error in /api/staff/patients/<patient_number>: {e}", exc_info=True)
        return jsonify({"error": "Failed to load patient detail"}), 500

    finally:
        if cursor is not None:
            cursor.close()


@app.route("/api/staff/patients/<patient_number>/summary", methods=["GET"])
def api_staff_patient_summary(patient_number):
    """
    Staff view: summary statistics for a single patient.
    Returns:
      - total readings, abnormal count, avg value
      - latest reading summary string
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    cursor = None
    try:
        conn = db.connection
        cursor = conn.cursor(dictionary=True)

        # Resolve patient_number -> user_id
        cursor.execute(
            """
            SELECT u.user_id, u.first_name, u.last_name
            FROM patients p
            JOIN users u ON u.user_id = p.user_id
            WHERE p.health_care_number = %s
               OR p.patient_id = %s
            LIMIT 1
            """,
            (patient_number, patient_number),
        )
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"error": "Patient not found"}), 404

        user_id = user_row["user_id"]
        full_name = f"{user_row['first_name']} {user_row['last_name']}".strip()

        # Aggregate stats for this user
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_readings,
                SUM(CASE WHEN status = 'abnormal' THEN 1 ELSE 0 END) AS abnormal_count,
                AVG(value) AS avg_value
            FROM bloodsugarreadings
            WHERE user_id = %s
            """,
            (user_id,),
        )
        stats = cursor.fetchone() or {}

        total_readings = stats.get("total_readings") or 0
        abnormal_count = stats.get("abnormal_count") or 0
        avg_value = stats.get("avg_value")
        if avg_value is not None:
            avg_value = float(avg_value)

        # Latest reading
        cursor.execute(
            """
            SELECT value, status, unit, date_time
            FROM bloodsugarreadings
            WHERE user_id = %s
            ORDER BY date_time DESC
            LIMIT 1
            """,
            (user_id,),
        )
        last = cursor.fetchone()

        if last:
            last_dt = last["date_time"]
            if isinstance(last_dt, datetime):
                last_dt_str = last_dt.strftime("%Y-%m-%d %H:%M")
            else:
                last_dt_str = None

            last_value = float(last["value"])
            last_status = last["status"]
            unit = last["unit"] or "mg/dL"

            last_results_str = (
                f"Latest reading: {last_value:.1f} {unit} at {last_dt_str} "
                f"({last_status})."
            )
        else:
            last_results_str = "No readings yet."

        history_str = (
            f"{full_name} has {total_readings} recorded blood sugar reading(s), "
            f"with {abnormal_count} abnormal result(s)."
        )
        if avg_value is not None:
            history_str += f" Average value so far is {avg_value:.1f} mg/dL."

        return jsonify(
            {
                "medical_history": history_str,
                "last_results": last_results_str,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error in /api/staff/patients/<patient_number>/summary: {e}", exc_info=True)
        return jsonify({"error": "Failed to load summary"}), 500

    finally:
        if cursor is not None:
            cursor.close()


@app.route("/api/specialist/patients", methods=["GET"])
def api_specialist_patients():
    """
    Specialist dashboard: list patients assigned to a given specialist.

    Front-end calls:
      /api/specialist/patients?working_id=jsmith
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    working_id = request.args.get("working_id", "").strip()
    if not working_id:
        return jsonify({"error": "working_id is required"}), 400

    cursor = None
    try:
        conn = db.connection
        cursor = conn.cursor(dictionary=True)

        # First: fetch basic patient + user info for this specialist.
        sql = """
            SELECT
                p.patient_id,
                p.health_care_number,
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                u.date_of_birth
            FROM specialists s
            JOIN specialistpatient sp ON s.specialist_id = sp.specialist_id
            JOIN patients p ON p.patient_id = sp.patient_id
            JOIN users u ON u.user_id = p.user_id
            WHERE s.working_id = %s
            ORDER BY u.last_name, u.first_name
        """

        logger.debug("Fetching patients for specialist %s", working_id)
        cursor.execute(sql, (working_id,))
        rows = cursor.fetchall()

        # For each patient, fetch their latest reading (if any) via a simple query.
        for row in rows:
            # default last fields
            row['last_value'] = None
            row['last_status'] = None
            row['last_date_time'] = None

            try:
                cursor.execute(
                    "SELECT value, status, date_time FROM bloodsugarreadings WHERE user_id = %s ORDER BY date_time DESC LIMIT 1",
                    (row['user_id'],),
                )
                last = cursor.fetchone()
                if last:
                    row['last_value'] = last.get('value')
                    row['last_status'] = last.get('status')
                    row['last_date_time'] = last.get('date_time')
            except Exception:
                # ignore per-patient read errors, leave last_* as None
                pass

        patients = []
        for row in rows:
            full_name = f"{row['first_name']} {row['last_name']}".strip()
            patient_number = row["health_care_number"] or f"P{row['patient_id']}"

            dob = row.get("date_of_birth")
            if isinstance(dob, date):
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            else:
                age = None

            last_dt = row.get("last_date_time")
            if isinstance(last_dt, datetime):
                last_checked_str = last_dt.strftime("%Y-%m-%d %H:%M")
            else:
                last_checked_str = None

            last_value = row.get("last_value")
            if last_value is not None:
                last_value = float(last_value)

            patients.append(
                {
                    "id": row["patient_id"],
                    "patient_number": patient_number,
                    "full_name": full_name,
                    "email": row.get("email"),
                    "phone": row.get("phone"),
                    "age": age,
                    "gender": None,
                    "address": None,
                    "last_value": last_value,
                    "last_status": row.get("last_status"),
                    "last_checked": last_checked_str,
                }
            )

        return jsonify({"patients": patients}), 200

    except Exception as e:
        logger.error(f"Error in /api/specialist/patients: {e}", exc_info=True)
        return jsonify({"error": "Failed to load specialist patients"}), 500

    finally:
        if cursor is not None:
            cursor.close()


# ========================================
# 7. Blood Sugar Readings (CRUD + Search)
# ========================================

@app.route("/api/readings", methods=["POST"])
def add_reading():
    """
    Patient: Add a new blood sugar reading.

    Request JSON must include:
      - userId
      - value
    Optional:
      - unit, fasting, foodIntake, activity, event,
        symptomsNotes, additionalNote

    Flow:
      1) MLService.predict_status() to classify the reading
      2) Save reading to DB (db.create_reading)
      3) Optionally create AI insight in DB
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}
        required_fields = ["userId", "value"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Step 1: AI prediction (status, severity, confidence, insights)
        prediction_result = ml_service.predict_status(
            value=data["value"],
            fasting=data.get("fasting", False),
            food_intake=data.get("foodIntake", ""),
            activity=data.get("activity", ""),
            time_of_day=datetime.now().hour,
        )

        # Step 2: Save reading in DB
        reading_id = db.create_reading(
            user_id=data["userId"],
            value=data["value"],
            unit=data.get("unit", "mg/dL"),
            fasting=data.get("fasting"),
            food_intake=data.get("foodIntake"),
            activity=data.get("activity"),
            event=data.get("event"),
            symptoms_notes=data.get("symptomsNotes"),
            additional_note=data.get("additionalNote"),
            status=prediction_result["status"],
        )

        # Step 3: Save AI insight (optional)
        if prediction_result["insights"]:
            # Combine top 1–2 insight messages into one text
            insight_text = "; ".join(
                [i["message"] for i in prediction_result["insights"][:2]]
            )
            suggestion = (
                prediction_result["insights"][0]["message"]
                if prediction_result["insights"]
                else "Continue monitoring"
            )

            db.create_ai_insight(
                user_id=data["userId"],
                pattern=f"Reading: {data['value']} mg/dL - {prediction_result['status']}",
                suggestion=suggestion,
                confidence=prediction_result["confidence"],
            )

        return jsonify(
            {
                "readingId": reading_id,
                "status": prediction_result["status"],
                "severity": prediction_result["severity"],
                "confidence": prediction_result["confidence"],
                "insights": prediction_result["insights"],
                "message": "Reading added successfully. Database triggers have auto-classified the reading.",
            }
        ), 201

    except Exception as e:
        logger.error(f"Error adding reading: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/readings/<int:user_id>", methods=["GET"])
def get_readings(user_id):
    """
    Get blood sugar readings for a user (default last 30 days).
    Query param:
      - days (optional, default 30)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        days = request.args.get("days", default=30, type=int)
        readings = db.get_user_readings(user_id, days)

        return jsonify(
            {
                "userId": user_id,
                "readings": readings,
                "count": len(readings),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching readings: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/readings/<int:reading_id>", methods=["PUT"])
def update_readings(reading_id):
    """
    Update a single reading by ID.
    JSON can include any fields that db.update_reading supports.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}

        # Ensure reading exists
        reading = db.get_reading_by_id(reading_id)
        if not reading:
            return jsonify({"error": "Reading not found"}), 404

        # Update reading with partial data
        db.update_reading(reading_id, **data)

        return jsonify(
            {
                "readingId": reading_id,
                "message": "Reading updated successfully",
            }
        ), 200

    except Exception as e:
        logger.error(f"Error updating reading {reading_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update reading"}), 500


@app.route("/api/readings/<int:reading_id>", methods=["DELETE"])
def delete_reading(reading_id):
    """
    Delete a single reading by ID.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        reading = db.get_reading_by_id(reading_id)
        if not reading:
            return jsonify({"error": "Reading not found"}), 404

        db.delete_reading(reading_id)

        return jsonify(
            {
                "message": "Reading deleted successfully",
                "readingId": reading_id,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error deleting reading {reading_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete reading"}), 500


@app.route("/api/specialist/<int:specialist_id>/readings/search", methods=["GET"])
def specialist_search_readings(specialist_id):
    """
    Specialist: search & filter readings across their patients.

    Query params:
      - patientName (optional substring match)
      - startDate (optional, must be comparable to reading['date_time'])
      - endDate (optional)
      - status (optional: 'normal' or 'abnormal' (includes borderline))
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        patient_name = request.args.get("patientName")
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")
        status_filter = request.args.get("status")  # 'normal' or 'abnormal'

        # Get all patients assigned to this specialist
        patients = db.get_specialist_patients(specialist_id)

        all_readings = []
        for patient in patients:
            # Filter by patient name (if provided)
            if patient_name:
                full_name = f"{patient['first_name']} {patient['last_name']}"
                if patient_name.lower() not in full_name.lower():
                    continue

            # Get up to 1 year of readings for each patient
            readings = db.get_user_readings(patient["user_id"], days=365)

            for reading in readings:
                # Attach patient info to reading
                reading["patient_name"] = f"{patient['first_name']} {patient['last_name']}"
                reading["patient_id"] = patient["user_id"]

                # Filter by date range (string comparison; ensure consistent format in DB)
                if start_date and reading["date_time"] < start_date:
                    continue
                if end_date and reading["date_time"] > end_date:
                    continue

                # Filter by status
                if status_filter:
                    if (
                        status_filter == "abnormal"
                        and reading["status"] not in ["abnormal", "borderline"]
                    ):
                        continue
                    if status_filter == "normal" and reading["status"] != "normal":
                        continue

                all_readings.append(reading)

        return jsonify(
            {
                "specialistId": specialist_id,
                "readings": all_readings,
                "count": len(all_readings),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error searching readings for specialist {specialist_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 8. Specialist Feedback & Patient Feedback
# ========================================

@app.route("/api/specialist/feedback", methods=["POST"])
def add_specialist_feedback():
    """
    Specialist: provide feedback to a patient.

    Expected JSON:
      - specialistId
      - patientId (user_id of patient)
      - feedbackText
      - readingId (optional, link feedback to a specific reading)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}

        if not data.get("specialistId") or not data.get("patientId") or not data.get(
            "feedbackText"
        ):
            return jsonify({"error": "Missing required fields"}), 400

        cursor = db._get_cursor()

        # Ensure patient row exists in patients table
        cursor.execute(
            "SELECT patient_id FROM patients WHERE user_id = %s",
            (data["patientId"],),
        )
        patient = cursor.fetchone()

        if not patient:
            logger.info(f"Creating patient record for user_id {data['patientId']}")
            cursor.execute(
                "INSERT INTO patients (user_id) VALUES (%s)",
                (data["patientId"],),
            )
            db.connection.commit()
            patient_id = cursor.lastrowid
        else:
            patient_id = patient["patient_id"]

        # Insert feedback
        sql = """
            INSERT INTO specialist_feedback
            (specialist_id, patient_id, reading_id, feedback_text)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                data["specialistId"],
                patient_id,
                data.get("readingId"),
                data["feedbackText"],
            ),
        )
        db.connection.commit()
        feedback_id = cursor.lastrowid
        cursor.close()

        return jsonify(
            {
                "feedbackId": feedback_id,
                "message": "Feedback added successfully",
            }
        ), 201

    except Exception as e:
        logger.error(f"Error adding specialist feedback: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/patient/<int:patient_id>/feedback", methods=["GET"])
def get_patient_feedback(patient_id):
    """
    Patient: view all feedback given by specialists.
    patient_id here is the numeric patient_id (not user_id).
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        feedback = db.get_specialist_feedback(patient_id)

        return jsonify(
            {
                "patientId": patient_id,
                "feedback": feedback,
                "count": len(feedback),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error in get_patient_feedback({patient_id}): {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ========================================
# 9. AI Insights, Trends, Patterns
# ========================================

@app.route("/api/insights/<int:user_id>", methods=["GET"])
def get_insights(user_id):
    """
    Generate fresh AI-powered insights over recent readings.
    Query param:
      - days (default 30)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        days = request.args.get("days", default=30, type=int)
        readings = db.get_user_readings(user_id, days)

        if not readings:
            return jsonify({"error": "No readings found for this user"}), 404

        insights = ml_service.generate_insights(readings)

        return jsonify(
            {
                "userId": user_id,
                "period": f"Last {days} days",
                "insights": insights,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error generating insights for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/aiinsights/<int:user_id>", methods=["GET"])
def get_saved_insights(user_id):
    """
    Get saved AI insights from database (historical).
    Query param:
      - limit (default 10)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        limit = request.args.get("limit", default=10, type=int)
        insights = db.get_user_insights(user_id, limit)

        return jsonify(
            {
                "userId": user_id,
                "insights": insights,
                "count": len(insights),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching saved insights for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/insights/<int:user_id>/trends", methods=["GET"])
def get_trends(user_id):
    """
    Analyze medium-term trends (last 90 days) in readings.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        readings = db.get_user_readings(user_id, days=90)

        if not readings:
            return jsonify({"error": "No readings found"}), 404

        trends = ml_service.analyze_trends(readings)

        return jsonify(
            {
                "userId": user_id,
                "trends": trends,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error analyzing trends for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/insights/<int:user_id>/patterns", methods=["GET"])
def get_patterns(user_id):
    """
    Identify patterns between events/food and blood sugar values.
    (Over the last 60 days.)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        readings = db.get_user_readings(user_id, days=60)

        if not readings:
            return jsonify({"error": "No readings found"}), 404

        patterns = ml_service.identify_patterns(readings)

        return jsonify(
            {
                "userId": user_id,
                "patterns": patterns,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error identifying patterns for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 10. Alerts & Thresholds
# ========================================

@app.route("/api/alerts/<int:user_id>", methods=["GET"])
def get_alerts(user_id):
    """
    Get alerts for a user over the last N days (default 30).
    Query param:
      - days (optional, default 30)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        days = request.args.get("days", default=30, type=int)
        alerts = db.get_user_alerts(user_id, days)

        return jsonify(
            {
                "userId": user_id,
                "alerts": alerts,
                "count": len(alerts),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching alerts for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/thresholds/<int:user_id>", methods=["GET"])
def get_thresholds(user_id):
    """
    Get custom thresholds for a user.
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        thresholds = db.get_user_thresholds(user_id)

        return jsonify(
            {
                "userId": user_id,
                "thresholds": thresholds,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching thresholds for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/thresholds/<int:user_id>", methods=["POST"])
def set_threshold(user_id):
    """
    Create or update a threshold range for a given status (e.g., 'normal', 'abnormal').

    Request JSON:
      - status
      - minValue
      - maxValue
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}
        required_fields = ["status", "minValue", "maxValue"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        threshold_id = db.set_user_threshold(
            user_id=user_id,
            status=data["status"],
            min_value=data["minValue"],
            max_value=data["maxValue"],
        )

        return jsonify(
            {
                "thresholdId": threshold_id,
                "message": "Threshold set successfully",
            }
        ), 200

    except Exception as e:
        logger.error(f"Error setting threshold for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 11. Diet Recommendations
# ========================================

@app.route("/api/diet/<condition>", methods=["GET"])
def get_diet_recommendations(condition):
    """
    Get diet recommendations based on a condition
    (e.g., 'diabetes', 'hypertension').

    Optional query param:
      - mealType (breakfast, lunch, dinner, snack, etc.)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        meal_type = request.args.get("mealType")
        recommendations = db.get_diet_recommendations(condition, meal_type)

        return jsonify(
            {
                "condition": condition,
                "mealType": meal_type,
                "recommendations": recommendations,
                "count": len(recommendations),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching diet recommendations for {condition}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 12. Specialist Dashboards & Alerts
# ========================================

@app.route("/api/specialist/<int:specialist_id>/patients", methods=["GET"])
def get_specialist_patients(specialist_id):
    """
    Get all patients assigned to a specialist by numeric specialist_id.
    This endpoint returns data from db.get_specialist_patients().
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        patients = db.get_specialist_patients(specialist_id)

        return jsonify(
            {
                "specialistId": specialist_id,
                "patients": patients,
                "count": len(patients),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching specialist patients for {specialist_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/specialist/<int:specialist_id>/dashboard", methods=["GET"])
def get_specialist_dashboard(specialist_id):
    """
    Get aggregated dashboard statistics for a specialist.
    Uses db.get_specialist_dashboard(specialist_id).
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        dashboard = db.get_specialist_dashboard(specialist_id)
        if not dashboard:
            return jsonify({"error": "Specialist not found"}), 404

        return jsonify(
            {
                "specialistId": specialist_id,
                "dashboard": dashboard,
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching dashboard for specialist {specialist_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/specialist/<int:specialist_id>/attention", methods=["GET"])
def get_patients_needing_attention(specialist_id):
    """
    Get list of patients who need urgent attention
    (e.g., frequent abnormal readings).
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        patients = db.get_specialist_attention_list(specialist_id)

        return jsonify(
            {
                "specialistId": specialist_id,
                "patientsNeedingAttention": patients,
                "count": len(patients),
            }
        ), 200

    except Exception as e:
        logger.error(
            f"Error fetching attention list for specialist {specialist_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/specialist/alerts/<int:specialist_id>", methods=["GET"])
def get_specialist_alerts(specialist_id):
    """
    Get alerts for all patients assigned to a specialist.

    Query param:
      - days (optional, default 7)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        days = request.args.get("days", default=7, type=int)

        # Get all patients for this specialist
        patients = db.get_specialist_patients(specialist_id)

        all_alerts = []
        for patient in patients:
            alerts = db.get_user_alerts(patient["user_id"], days)
            for alert in alerts:
                alert["patient_name"] = (
                    f"{patient['first_name']} {patient['last_name']}"
                )
                alert["patient_id"] = patient["patient_id"]
            all_alerts.extend(alerts)

        # Sort by date_sent descending
        all_alerts.sort(key=lambda x: x["date_sent"], reverse=True)

        return jsonify(
            {
                "specialistId": specialist_id,
                "alerts": all_alerts,
                "count": len(all_alerts),
            }
        ), 200

    except Exception as e:
        logger.error(f"Error fetching specialist alerts for {specialist_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 14. Notification endpoints (email sending)
# ========================================


@app.route('/api/notify/email', methods=['POST'])
def api_send_email():
    """
    Send a single email. Request JSON:
      - to: recipient email (string)
      - subject: subject (string)
      - message: body (string)
      - html: optional boolean (default False)

    Uses backend.notification_service; returns { success: bool }.
    """
    data = request.get_json() or {}
    to = data.get('to')
    subject = data.get('subject')
    message = data.get('message')
    html = bool(data.get('html', False))

    if not to or not subject or not message:
        return jsonify({"error": "to, subject and message are required"}), 400

    try:
        ok = False
        try:
            ok = notification_service.send_email(to, subject, message, html=html)
        except Exception as e:
            logger.error(f"Notification service error: {e}", exc_info=True)
            ok = False

        if ok:
            return jsonify({"success": True, "message": "Email sent"}), 200
        else:
            # Do not expose SMTP details; return generic response
            return jsonify({"success": False, "message": "Email not sent (SMTP may be unconfigured)"}), 502

    except Exception as e:
        logger.error(f"/api/notify/email failed: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/notify/batch', methods=['POST'])
def api_send_email_batch():
    """
    Send a batch of emails. Request JSON: { emails: [ {to, subject, message, html?}, ... ] }
    Returns counts of successes/failures.
    """
    data = request.get_json() or {}
    emails = data.get('emails') or []
    if not isinstance(emails, list) or len(emails) == 0:
        return jsonify({"error": "emails array required"}), 400

    results = {"sent": 0, "failed": 0}
    for e in emails:
        try:
            ok = notification_service.send_email(e.get('to'), e.get('subject'), e.get('message'), html=bool(e.get('html', False)))
            if ok:
                results['sent'] += 1
            else:
                results['failed'] += 1
        except Exception:
            results['failed'] += 1

    return jsonify({"success": True, "results": results}), 200


# ========================================
# 13. Reports (User & Admin)
# ========================================

@app.route("/api/reports/<int:user_id>", methods=["GET"])
def generate_report(user_id):
    """
    Generate a comprehensive health report for a single user.
    Includes:
      - ML-generated report
      - Recent saved insights
      - Thresholds
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        days = request.args.get("days", default=30, type=int)

        readings = db.get_user_readings(user_id, days)
        if not readings:
            return jsonify({"error": "No readings found"}), 404

        report = ml_service.generate_report(user_id, readings)

        # Attach saved insights and thresholds
        report["saved_insights"] = db.get_user_insights(user_id, limit=5)
        report["thresholds"] = db.get_user_thresholds(user_id)

        return jsonify(report), 200

    except Exception as e:
        logger.error(f"Error generating report for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/reports/monthly", methods=["GET"])
def get_monthly_report():
    """
    Admin: generate monthly or yearly report.

    Query params (one of the two is required):
      - month = 'YYYY-MM'
      - year = 'YYYY'
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        month = request.args.get("month")  # e.g. '2025-11'
        year = request.args.get("year")    # e.g. '2025'

        if not month and not year:
            return jsonify({"error": "Month or year parameter required"}), 400

        cursor = db._get_cursor()

        # Count active patients (role='patient')
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'patient'")
        total_patients = cursor.fetchone()["count"]

        # Build date filter for monthly or yearly
        if month:
            date_filter = f"DATE_FORMAT(date_time, '%Y-%m') = '{month}'"
            period_label = month
        else:
            date_filter = f"YEAR(date_time) = {year}"
            period_label = year

        # Per-patient statistics
        sql = f"""
            SELECT
                u.user_id,
                u.first_name,
                u.last_name,
                COUNT(r.reading_id) AS total_readings,
                AVG(r.value)        AS avg_value,
                MAX(r.value)        AS max_value,
                MIN(r.value)        AS min_value,
                SUM(
                    CASE WHEN r.status IN ('abnormal', 'borderline') THEN 1 ELSE 0 END
                ) AS abnormal_count
            FROM users u
            LEFT JOIN bloodsugarreadings r
                ON u.user_id = r.user_id
               AND {date_filter}
            WHERE u.role = 'patient'
            GROUP BY u.user_id
        """
        cursor.execute(sql)
        patient_stats = cursor.fetchall()

        # Convert numeric fields to plain Python types
        for stat in patient_stats:
            if stat.get("avg_value") is not None:
                stat["avg_value"] = float(stat["avg_value"])
            if stat.get("max_value") is not None:
                stat["max_value"] = float(stat["max_value"])
            if stat.get("min_value") is not None:
                stat["min_value"] = float(stat["min_value"])
            if stat.get("total_readings") is not None:
                stat["total_readings"] = int(stat["total_readings"])
            if stat.get("abnormal_count") is not None:
                stat["abnormal_count"] = int(stat["abnormal_count"])

        # Top food triggers for abnormal/borderline
        sql = f"""
            SELECT
                food_intake,
                COUNT(*) AS trigger_count,
                AVG(value) AS avg_value
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
            if trigger.get("avg_value") is not None:
                trigger["avg_value"] = float(trigger["avg_value"])

        # Top activity triggers
        sql = f"""
            SELECT
                activity,
                COUNT(*) AS trigger_count,
                AVG(value) AS avg_value
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
            if trigger.get("avg_value") is not None:
                trigger["avg_value"] = float(trigger["avg_value"])

        cursor.close()

        return jsonify(
            {
                "period": period_label,
                "total_active_patients": total_patients,
                "patient_statistics": patient_stats,
                "top_food_triggers": food_triggers,
                "top_activity_triggers": activity_triggers,
                "generated_at": datetime.now().isoformat(),
            }
        ), 200

    except Exception as e:
        logger.error("Error generating monthly report: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/reports/annual", methods=["GET"])
def get_annual_report():
    """
    Admin: annual report for a given year.

    Query param:
      - year = 'YYYY'
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        year = request.args.get("year")
        if not year:
            return jsonify({"error": "Year parameter required"}), 400

        cursor = db._get_cursor()

        # Monthly trends
        sql = f"""
            SELECT
                DATE_FORMAT(date_time, '%Y-%m') AS month,
                COUNT(DISTINCT user_id) AS active_patients,
                COUNT(*) AS total_readings,
                AVG(value) AS avg_value,
                SUM(
                    CASE WHEN status IN ('abnormal', 'borderline') THEN 1 ELSE 0 END
                ) AS abnormal_count
            FROM bloodsugarreadings
            WHERE YEAR(date_time) = {year}
            GROUP BY DATE_FORMAT(date_time, '%Y-%m')
            ORDER BY month
        """
        cursor.execute(sql)
        monthly_trends = cursor.fetchall()

        for trend in monthly_trends:
            if trend.get("avg_value") is not None:
                trend["avg_value"] = float(trend["avg_value"])

        # Overall annual statistics
        sql = f"""
            SELECT
                COUNT(DISTINCT user_id) AS total_patients,
                COUNT(*) AS total_readings,
                AVG(value) AS avg_value,
                MAX(value) AS max_value,
                MIN(value) AS min_value
            FROM bloodsugarreadings
            WHERE YEAR(date_time) = {year}
        """
        cursor.execute(sql)
        overall_stats = cursor.fetchone()

        if overall_stats.get("avg_value") is not None:
            overall_stats["avg_value"] = float(overall_stats["avg_value"])
        if overall_stats.get("max_value") is not None:
            overall_stats["max_value"] = float(overall_stats["max_value"])
        if overall_stats.get("min_value") is not None:
            overall_stats["min_value"] = float(overall_stats["min_value"])

        # Top food triggers for the year
        sql = f"""
            SELECT
                food_intake,
                COUNT(*) AS trigger_count,
                AVG(value) AS avg_value
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
            if trigger.get("avg_value") is not None:
                trigger["avg_value"] = float(trigger["avg_value"])

        cursor.close()

        return jsonify(
            {
                "year": year,
                "overall_statistics": overall_stats,
                "monthly_trends": monthly_trends,
                "top_food_triggers": food_triggers,
                "generated_at": datetime.now().isoformat(),
            }
        ), 200

    except Exception as e:
        logger.error("Error generating annual report: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ========================================
# 14. Patient–Specialist Assignments
# ========================================

@app.route("/api/assignments/assign", methods=["POST"])
def assign_patient_api():
    """
    Assign a patient user_id to a specialist user_id.

    Expected JSON:
      - patientId   (user_id of patient)
      - specialistId (user_id of specialist)
    """
    if db is None:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.json or {}
        patient_user_id = data.get("patientId")
        specialist_user_id = data.get("specialistId")

        if not patient_user_id or not specialist_user_id:
            return jsonify({"error": "Missing patientId or specialistId"}), 400

        db.assign_patient_to_specialist(patient_user_id, specialist_user_id)

        return jsonify({"message": "Assignment successful"}), 200

    except ValueError as e:
        # Used when assign_patient_to_specialist raises a known error
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error(f"Error in assignment API: {e}", exc_info=True)
        return jsonify({"error": "Failed to complete assignment."}), 500


# ========================================
# 15. Application Entry Point
# ========================================

if __name__ == "__main__":
    # Start scheduler if available
    if scheduler_service is not None:
        scheduler_service.start()
        logger.info("Scheduler: Started")
    else:
        logger.warning("Scheduler: NOT started (scheduler_service is None)")

    logger.info("=" * 60)
    logger.info("Blood Sugar Monitoring System - Backend Server")
    logger.info("=" * 60)
    logger.info("Database: %s", "Connected" if db is not None else "Not available")
    logger.info("ML Service: Ready")
    logger.info("API Endpoints: See app.py for full list")
    logger.info("=" * 60)

    # Run Flask development server (debug disabled to avoid reloader in container)
    # If TLS cert/key are present or provided via env vars, run with SSL to support HTTPS.
    ssl_cert = os.environ.get('SSL_CERT', os.path.join(os.path.dirname(__file__), 'certs', 'server.crt'))
    ssl_key = os.environ.get('SSL_KEY', os.path.join(os.path.dirname(__file__), 'certs', 'server.key'))

    use_ssl = False
    if os.path.isfile(ssl_cert) and os.path.isfile(ssl_key):
        use_ssl = True

    if use_ssl:
        logger.info(f"Starting HTTPS server on 0.0.0.0:5000 using cert={ssl_cert}")
        app.run(debug=False, host="0.0.0.0", port=5000, ssl_context=(ssl_cert, ssl_key))
    else:
        logger.info("Starting HTTP server on 0.0.0.0:5000 (no SSL certificates found).")
        app.run(debug=False, host="0.0.0.0", port=5000)
