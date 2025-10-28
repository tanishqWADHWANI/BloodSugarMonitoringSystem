# Blood Sugar Monitoring System

## Project Overview

A comprehensive health monitoring platform that enables diabetic patients to track blood sugar levels and receive AI-powered insights. Healthcare specialists can monitor their assigned patients, track trends, and receive automated alerts for abnormal readings.

---

## System Architecture

### Backend (Flask REST API)
- **Framework:** Flask 3.0.0
- **Database:** MySQL 8.0 / MariaDB
- **ML Engine:** Scikit-learn (Random Forest / Gradient Boosting)
- **Notifications:** SMTP email service
- **Scheduler:** Background task automation

### Key Components
1. **API Layer** - RESTful endpoints for all operations
2. **Database Layer** - MySQL with triggers and views
3. **ML Service** - AI predictions and insights generation
4. **Notification Service** - Email alerts for abnormal readings
5. **Scheduler Service** - Hourly patient monitoring

---

## Features

### For Patients
- Track blood sugar readings with timestamps
- Automatic AI classification (normal/low/high/prediabetic)
- Personalized insights and recommendations
- Trend analysis and pattern detection
- Email alerts for concerning readings
- Custom threshold settings
- Diet recommendations

### For Specialists
- View all assigned patients
- Monitor patient trends and patterns
- Receive alerts for patients needing attention
- Dashboard with patient statistics
- Access to patient history and reports

### Automated Intelligence
- **AI Predictions:** Real-time blood sugar status classification
- **Pattern Detection:** Identifies meal, activity, and time-based patterns
- **Risk Assessment:** Evaluates diabetes risk based on reading history
- **Smart Alerts:** Triggers notifications for 3+ abnormal readings in 7 days
- **Trend Analysis:** Tracks improvement or deterioration over time

---

## Database Schema

### Core Tables
- **users** - Patient, specialist, staff, and admin accounts
- **bloodsugarreadings** - Blood sugar measurements with metadata
- **aiinsights** - AI-generated patterns and suggestions
- **alerts** - System-generated notifications
- **thresholds** - Custom user-defined ranges
- **specialistpatient** - Patient-specialist assignments
- **dietrecommendations** - Nutrition guidance data

### Kaggle Datasets Integrated
- Diabetes dataset (Pima Indians)
- Heart disease dataset
- Diet recommendations dataset

### Database Features
- **Triggers:** Auto-classify readings, generate alerts
- **Views:** Pre-built queries for specialist dashboards
- **Cascade Deletes:** Maintain referential integrity

---

## Machine Learning Model

### Purpose
Predict blood sugar status and generate personalized health insights.

### Training Data
- Patient readings from database
- Diabetes research datasets
- Synthetic data (fallback)

### Model Features
- **Input:** Blood sugar value, fasting status, food intake, activity, time of day
- **Output:** Status classification, confidence score, actionable insights
- **Algorithms:** Random Forest and Gradient Boosting (best model selected)
- **Accuracy:** ~92% on test data

### Fallback System
If ML model unavailable, system uses clinical rule-based classification.

---

## API Overview

### Base URL
```
http://localhost:5000
```

### Main Endpoints

**User Management**
```
POST   /api/users/register       Register new user
GET    /api/users/{id}           Get user info
PUT    /api/users/{id}           Update user
DELETE /api/users/{id}           Delete user
```

**Blood Sugar Readings**
```
POST   /api/readings             Add reading (with AI prediction)
GET    /api/readings/{user_id}   Get user readings
PUT    /api/readings/{id}        Update reading
DELETE /api/readings/{id}        Delete reading
```

**AI Insights**
```
GET    /api/insights/{user_id}           Generate fresh insights
GET    /api/insights/{user_id}/trends    Trend analysis
GET    /api/insights/{user_id}/patterns  Pattern detection
GET    /api/aiinsights/{user_id}         Saved insights
```

**Alerts & Notifications**
```
GET    /api/alerts/{user_id}     Get user alerts
DELETE /api/alerts/{id}          Dismiss alert
```

**Specialist Features**
```
GET    /api/specialist/{id}/patients    All assigned patients
GET    /api/specialist/{id}/dashboard   Dashboard statistics
GET    /api/specialist/{id}/attention   Patients needing care
```

**Additional**
```
GET    /api/reports/{user_id}    Comprehensive health report
GET    /api/diet/{condition}     Diet recommendations
GET    /api/thresholds/{user_id} Custom thresholds
```

---

## Project Structure

```
blood-sugar-backend/
├── app.py                      # Main Flask application
├── models.py                   # Database operations
├── ml_service.py               # AI/ML predictions
├── notification_service.py     # Email service
├── scheduler_service.py        # Background tasks
├── train_model.py             # Model training script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── models/                    # Trained ML models
│   ├── blood_sugar_model.joblib
│   └── scaler.joblib
└── README.md                  # This file
```

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL 8.0 or MariaDB
- pip (Python package manager)

### Installation

1. **Clone repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   
   Create `.env` file:
   ```env
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=blood_sugar_db
   
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

5. **Import database**
   ```bash
   mysql -u root -p < database_schema.sql
   ```

6. **Train ML model** (optional)
   ```bash
   python train_model.py
   ```

7. **Start server**
   ```bash
   python app.py
   ```

Server runs on `http://localhost:5000`

---

## Testing

### Test Credentials
- **Patient:** `demo.patient@example.com` / `demo1234`
- **Specialist:** `alex.smith@example.com` / `spec123`
- **Staff:** `lana.reed@clinic.com` / `staff123`

### Quick Test
```bash
curl http://localhost:5000/health
curl http://localhost:5000/api/readings/1
```

---

## Frontend Integration

### Request Format
```javascript
// Add reading
const response = await fetch('http://localhost:5000/api/readings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    userId: 1,
    value: 145,
    unit: 'mg/dL',
    fasting: false,
    foodIntake: 'pasta',
    activity: 'walking'
  })
});
const data = await response.json();
```

### Response Format
```json
{
  "readingId": 6,
  "status": "prediabetic",
  "severity": "medium",
  "confidence": 0.90,
  "insights": [
    {
      "type": "warning",
      "message": "Your reading is in the prediabetic range.",
      "priority": "medium"
    }
  ]
}
```

### Error Handling
All errors return:
```json
{ "error": "Error description" }
```

HTTP codes: 200 (OK), 201 (Created), 400 (Bad Request), 404 (Not Found), 500 (Server Error)

---

## Data Flow

1. **Patient adds reading** → API receives request
2. **ML model predicts** → Classifies status (normal/high/low)
3. **Database triggers** → Auto-generate alerts if abnormal
4. **Insights generated** → Personalized recommendations
5. **Scheduler checks** → Hourly monitoring for all patients
6. **Email sent** → Alerts for 3+ abnormal readings in 7 days
7. **Specialist notified** → Dashboard updates automatically

---

## Key Features Explanation

### Automated Alerts
- System monitors all patients hourly
- Triggers when 3+ abnormal readings in 7 days
- Emails sent to patient and assigned specialist
- Alerts stored in database for tracking

### AI Insights
- **Summary:** Total readings, averages, abnormal percentage
- **Recommendations:** Personalized based on patterns
- **Risk Assessment:** Low/moderate/high risk level
- **Statistics:** Mean, median, standard deviation
- **Trends:** Increasing/decreasing/stable detection
- **Patterns:** Time of day, meal impact, activity effects

### Specialist Dashboard
- Total patients assigned
- Active alerts count
- Inactive patients (no recent readings)
- Patients with abnormal readings
- Individual patient trends

---

## Security Notes

**Current Status:**
- No authentication implemented
- All endpoints publicly accessible
- Passwords stored as plain text

**TODO for Production:**
- Implement JWT authentication
- Add role-based access control
- Hash passwords with bcrypt
- Add rate limiting
- Enable HTTPS

---

## Known Limitations

1. No user authentication currently
2. Email requires Gmail app password setup
3. ML model requires training with sufficient data
4. Single-server deployment (no load balancing)
5. No data backup automation

---

## Troubleshooting

**Server won't start:**
- Check MySQL is running
- Verify `.env` credentials
- Ensure port 5000 is available

**No insights generated:**
- Verify ML model trained (`models/` folder exists)
- Check sufficient readings in database
- System falls back to rule-based classification

**Emails not sending:**
- Configure Gmail app password
- Check SMTP settings in `.env`
- Verify internet connection

**Database errors:**
- Confirm database imported correctly
- Check user permissions in MySQL
- Verify table structures match schema

---

## Dependencies

```
Flask==3.0.0
flask-cors==4.0.0
mysql-connector-python==8.2.0
scikit-learn==1.3.2
joblib==1.3.2
pandas==2.1.4
numpy==1.26.2
python-dotenv==1.0.0
APScheduler==3.10.4
```

---

## Team

**Backend Development:** ML model, API endpoints, database design, automation, Schema design, triggers, views, test data


**Frontend Development:** User interface, API integration, data visualization

---


## Contact

For backend issues or questions, check console logs or review `app.py` for endpoint details.# BloodSugarMonitoringSystem
