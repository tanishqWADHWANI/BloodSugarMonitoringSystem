"""
Blood Sugar Monitoring System - Test Login Script
==================================================
Test login API endpoint for staff and admin accounts.

Purpose:
- Verify staff login credentials work
- Verify admin login credentials work
- Test /api/login endpoint functionality
- Display API responses for debugging

Usage:
    python test_login.py

Test Accounts:
- Staff: staff@clinic.com / demo123
- Admin: admin@clinic.com / admin123

Output:
- HTTP status codes
- API response messages
- Login success/failure status
- JWT tokens if successful

NOTE: This is a test script with inline code, no functions.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Test staff login
print("Testing staff login...")
staff_response = requests.post(f"{BASE_URL}/api/login", json={
    "email": "staff@clinic.com",
    "password": "demo123"
})
print(f"Staff Status: {staff_response.status_code}")
print(f"Staff Response: {staff_response.text}\n")

# Test admin login
print("Testing admin login...")
admin_response = requests.post(f"{BASE_URL}/api/login", json={
    "email": "admin@clinic.com",
    "password": "admin123"
})
print(f"Admin Status: {admin_response.status_code}")
print(f"Admin Response: {admin_response.text}")
