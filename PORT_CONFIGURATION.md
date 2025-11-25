# Port Configuration Guide

## Overview
This document explains the port architecture for the Blood Sugar Monitoring System to prevent configuration errors.

## Port Architecture

### Backend API Server (Flask)
- **Port**: 5000
- **Host**: 127.0.0.1 (localhost)
- **Full URL**: `http://127.0.0.1:5000`
- **Purpose**: REST API endpoints for frontend communication
- **Configuration**: Set in `backend/app.py` line 1535

### Database Server (MySQL/MariaDB)
- **Port**: 3306 (default, not explicitly set)
- **Host**: 127.0.0.1 (localhost)
- **Database Name**: `blood_sugar_db`
- **Purpose**: Data storage
- **Configuration**: Uses default MySQL port, no need to specify

## Common Mistakes to Avoid

### ❌ WRONG: Using port 5000 for database
```python
connection = mysql.connector.connect(
    host='127.0.0.1',
    port=5000,  # WRONG! This is the Flask API port
    database='blood_sugar_db'
)
```

### ✅ CORRECT: Use default MySQL port (3306)
```python
connection = mysql.connector.connect(
    host='127.0.0.1',
    # No port specified - uses default 3306
    database='blood_sugar_db',
    user='root',
    password=''
)
```

## Port Usage Summary

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| Flask API | 5000 | HTTP | Frontend → Backend API |
| MySQL Database | 3306 | MySQL Protocol | Backend → Database |
| Frontend | N/A | File:// or HTTP | Browser → HTML files |

## How Frontend Communicates

```
Browser (HTML/JS)
    ↓ HTTP requests to port 5000
Flask API Server (port 5000)
    ↓ MySQL queries to port 3306
MySQL Database (port 3306)
```

## Troubleshooting

### Issue: "Can't connect to MySQL server on port 5000"
**Cause**: Trying to connect to MySQL using Flask API port  
**Solution**: Remove port parameter or use port 3306

### Issue: "Frontend can't reach API"
**Cause**: Wrong API URL in frontend  
**Solution**: Verify all fetch() calls use `http://127.0.0.1:5000`

### Issue: "Profile images truncated"
**Cause**: Database column too small (VARCHAR(255))  
**Solution**: Already fixed - column is now MEDIUMTEXT

## Files Using Port Configuration

### Backend Files (Port 5000 for API)
- `backend/app.py` - Flask server configuration
- `backend/test_assignment.py` - API testing
- `backend/assign_alice_to_christina.py` - API scripts

### Frontend Files (Port 5000 for API calls)
- `frontend/js/api.js` - Centralized API configuration
- All dashboard HTML files - Direct fetch() calls
- All edit profile HTML files - API endpoints

### Database Files (Port 3306, usually implicit)
- `backend/models.py` - Database class
- `backend/check_alice_profile_image.py` - Database queries
- `backend/fix_profile_image_column.py` - Schema modifications

## Environment Variables

For production deployment, use environment variables:

```bash
# Backend API
export API_HOST=127.0.0.1
export API_PORT=5000

# Database
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_NAME=blood_sugar_db
export DB_USER=root
export DB_PASSWORD=
```

## Quick Reference

**Need to call an API?** → Use port 5000  
**Need to query database?** → Don't specify port (uses 3306 by default)  
**Seeing port errors?** → Check if you're mixing up API port with database port
