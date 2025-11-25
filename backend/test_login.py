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
