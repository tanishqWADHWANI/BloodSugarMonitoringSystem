/**
 * Blood Sugar Monitoring System - API Client Library
 * ===================================================
 * This file provides a centralized JavaScript API client for all frontend pages.
 * It handles HTTP communication with the Flask backend REST API.
 * 
 * Features:
 * - Centralized API base URL configuration
 * - Generic HTTP request wrapper with error handling
 * - User authentication helpers (login, role verification, session storage)
 * - Semantic wrapper functions for all backend endpoints
 * - Type-safe error handling and JSON parsing
 * 
 * Usage:
 *   Include this file in HTML: <script src="js/api.js"></script>
 *   Then call functions like: await loginUser(email, password)
 * 
 * Backend: Flask API running on http://127.0.0.1:5000
 */

// ========== Configuration ==========

/**
 * Base URL for the Flask API backend server
 * Dynamically determined based on current page location
 * Supports both localhost and network access
 */
const API_BASE_URL = (() => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // If accessing from localhost/127.0.0.1, use those addresses
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
    return 'http://127.0.0.1:5000';
  }
  
  // Otherwise, use the current hostname/IP with port 5000
  return `${protocol}//${hostname}:5000`;
})();

// Log the API URL for debugging
console.log('[Blood Sugar Monitoring System] Backend API URL:', API_BASE_URL);

// ========== Core HTTP Request Handler ==========

/**
 * Generic HTTP request wrapper that all API calls use.
 * Handles JSON serialization, error responses, and consistent headers.
 * 
 * @param {string} path - API endpoint path (e.g., '/api/users/1')
 * @param {Object} options - Request configuration
 * @param {string} options.method - HTTP method (GET, POST, PUT, DELETE)
 * @param {Object} options.headers - Additional HTTP headers
 * @param {string|null} options.body - Request body (pre-stringified JSON)
 * @returns {Promise<Object>} Parsed JSON response from server
 * @throws {Error} If request fails or server returns error status
 */
async function apiRequest(
  path,
  { method = 'GET', headers = {}, body = null } = {}
) {
  // Make fetch request to backend API
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,  // HTTP verb (GET, POST, PUT, DELETE)
    headers: { 'Content-Type': 'application/json', ...headers },  // Merge default + custom headers
    body,  // Request body (already JSON stringified by caller)
  });

  // Try to parse response as JSON
  let data = null;
  try {
    data = await res.json();  // Parse JSON response body
  } catch (_) {
    // Allow empty response bodies (e.g., 204 No Content)
  }

  // Check if request was successful (status 200-299)
  if (!res.ok) {
    // Extract error message from response or use generic message
    const msg =
      (data && data.error) || `Request failed with status ${res.status}`;
    throw new Error(msg);  // Throw error to be caught by caller
  }
  return data;  // Return parsed JSON data
}

// ========== User Management Endpoints ==========

/**
 * Get user details by user ID
 * @param {number} id - User ID
 * @returns {Promise<Object>} User object with all details
 */
const getUser = (id) => apiRequest(`/api/users/${encodeURIComponent(id)}`);

/**
 * Register a new user account (patient, specialist, staff, or admin)
 * @param {Object} payload - User registration data
 * @param {string} payload.email - User email (must be unique)
 * @param {string} payload.password - User password
 * @param {string} payload.first_name - First name
 * @param {string} payload.last_name - Last name
 * @param {string} payload.role - User role (patient, specialist, staff, admin)
 * @returns {Promise<Object>} Created user object
 */
const registerUser = (payload) =>
  apiRequest('/api/users/register', {
    method: 'POST',
    body: JSON.stringify(payload),  // Convert object to JSON string
  });

/**
 * Update existing user details
 * @param {number} id - User ID to update
 * @param {Object} payload - Fields to update
 * @returns {Promise<Object>} Updated user object
 */
const updateUser = (id, payload) =>
  apiRequest(`/api/users/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

/**
 * Delete a user account
 * @param {number} id - User ID to delete
 * @returns {Promise<Object>} Deletion confirmation
 */
const deleteUser = (id) =>
  apiRequest(`/api/users/${encodeURIComponent(id)}`, { method: 'DELETE' });

// ========== Authentication Endpoints ==========

/**
 * Login user with email and password (works for all roles)
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {string} role - User role (patient, specialist, staff, admin)
 * @returns {Promise<Object>} User object with token
 */
const loginUser = (email, password, role) =>
  apiRequest('/api/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

/**
 * Alternative login function (mainly used for patient pages)
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {string} role - User role
 * @returns {Promise<Object>} User object with authentication token
 */
const login = (email, password, role) =>
  apiRequest('/api/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });

// ========== Local Storage Authentication Helpers ==========

/**
 * LocalStorage key for storing authenticated user data
 * Used to persist login session across page reloads
 */
const AUTH_KEY = 'authUser';

/**
 * Save authenticated user data to browser localStorage
 * Called after successful login to persist session
 * @param {Object} user - User object to save (includes user_id, role, email, token)
 */
function saveAuthUser(user) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));  // Store as JSON string
}

/**
 * Load authenticated user data from browser localStorage
 * Called on page load to restore login session
 * @returns {Object|null} User object if logged in, null otherwise
 */
function loadAuthUser() {
  const raw = localStorage.getItem(AUTH_KEY);  // Get JSON string from storage
  if (!raw) return null;  // Not logged in
  try {
    return JSON.parse(raw);  // Parse JSON string to object
  } catch {
    return null;  // Invalid JSON, treat as not logged in
  }
}

/**
 * Verify user is logged in with expected role, or redirect to login page
 * Call this at the top of protected pages to enforce authentication
 * @param {string} expectedRole - Required role (patient, specialist, staff, admin)
 * @returns {Object} User object if authenticated with correct role
 * @throws {Error} If not logged in or wrong role (after redirecting)
 */
function requireRole(expectedRole) {
  const user = loadAuthUser();  // Try to load user from localStorage
  // Check if user is logged in and has the correct role
  if (!user || (expectedRole && user.role !== expectedRole)) {
    // Not logged in or wrong role → redirect to appropriate login page
    if (expectedRole === 'patient') window.location.href = 'patient.html';
    else if (expectedRole === 'specialist') window.location.href = 'specialist.html';
    else if (expectedRole === 'staff') window.location.href = 'staff.html';
    else if (expectedRole === 'admin') window.location.href = 'admin.html';
    else window.location.href = 'index.html';  // Default to home page
    throw new Error('Not logged in');  // Throw error (page will redirect anyway)
  }
  return user;  // Return authenticated user object { user_id, role, email, ... }
}

// ========== Blood Sugar Readings Endpoints ==========

/**
 * Add a new blood sugar reading for a patient
 * @param {Object} payload - Reading data
 * @param {number} payload.user_id - Patient user ID
 * @param {number} payload.value - Blood glucose level (mg/dL)
 * @param {string} payload.meal_type - Type of meal (Breakfast, Lunch, Dinner, etc.)
 * @param {string} payload.food_consumed - Food items consumed
 * @param {string} payload.activity - Physical activity performed
 * @returns {Promise<Object>} Created reading object
 */
const addReading = (payload) =>
  apiRequest('/api/readings', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

/**
 * Get blood sugar readings for a user within specified time period
 * @param {number} userId - User ID to get readings for
 * @param {number} days - Number of days to look back (default: 30)
 * @returns {Promise<Array>} Array of reading objects
 */
const getReadings = async (userId, days = 30) => {
  const path = `/api/readings/${encodeURIComponent(
    userId
  )}?days=${encodeURIComponent(days)}`;

  // Make API request and extract readings array from response
  const json = await apiRequest(path);
  
  // Return readings array, or empty array if none found
  return Array.isArray(json.readings) ? json.readings : [];
};

/**
 * Update an existing blood sugar reading
 * @param {number} readingId - Reading ID to update
 * @param {Object} payload - Fields to update
 * @returns {Promise<Object>} Updated reading object
 */
const updateReading = (readingId, payload) =>
  apiRequest(`/api/readings/${encodeURIComponent(readingId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

/**
 * Delete a blood sugar reading
 * @param {number} readingId - Reading ID to delete
 * @returns {Promise<Object>} Deletion confirmation
 */
const deleteReading = (readingId) =>
  apiRequest(`/api/readings/${encodeURIComponent(readingId)}`, {
    method: 'DELETE',
  });

// ========== AI Insights & Analytics Endpoints ==========

/**
 * Get AI-powered insights for a patient's blood sugar data
 * Includes patterns, trends, and recommendations
 * @param {number} userId - Patient user ID
 * @returns {Promise<Object>} Insights object with analysis
 */
const getInsights = (userId) =>
  apiRequest(`/api/insights/${encodeURIComponent(userId)}`);

/**
 * Get blood sugar trend analysis for a patient
 * @param {number} userId - Patient user ID
 * @returns {Promise<Object>} Trend data (improving, stable, declining)
 */
const getTrends = (userId) =>
  apiRequest(`/api/insights/${encodeURIComponent(userId)}/trends`);

/**
 * Get pattern analysis (food triggers, activity effects)
 * @param {number} userId - Patient user ID
 * @returns {Promise<Object>} Pattern analysis data
 */
const getPatterns = (userId) =>
  apiRequest(`/api/insights/${encodeURIComponent(userId)}/patterns`);

/**
 * Get previously saved AI insights for a patient
 * @param {number} userId - Patient user ID
 * @returns {Promise<Array>} Array of saved insight objects
 */
const getSavedInsights = (userId) =>
  apiRequest(`/api/aiinsights/${encodeURIComponent(userId)}`);

// ========== Alerts & Notifications Endpoints ==========

/**
 * Get active alerts for a user (abnormal readings, threshold breaches)
 * @param {number} userId - User ID
 * @returns {Promise<Array>} Array of alert objects
 */
const getAlerts = (userId) =>
  apiRequest(`/api/alerts/${encodeURIComponent(userId)}`);

/**
 * Dismiss/acknowledge an alert
 * @param {number} alertId - Alert ID to dismiss
 * @returns {Promise<Object>} Dismissal confirmation
 */
const dismissAlert = (alertId) =>
  apiRequest(`/api/alerts/${encodeURIComponent(alertId)}`, {
    method: 'DELETE',
  });

// ========== Admin Endpoints ==========

/**
 * Get list of all users in the system (admin only)
 * @returns {Promise<Array>} Array of all user objects
 */
const getAllUsers = () => apiRequest('/api/admin/users/all');

/**
 * Get monthly report with aggregated statistics (admin only)
 * @param {string} month - Month string in YYYY-MM format (e.g., '2025-11')
 * @param {number} year - Year (e.g., 2025)
 * @returns {Promise<Object>} Monthly report with patient statistics
 */
const getAdminMonthlyReport = (month, year) =>
  apiRequest(`/api/admin/reports/monthly?month=${month}&year=${year}`);

// ========== Patient Management Endpoints (Staff/Admin) ==========

/**
 * Get list of all patients in the system
 * @returns {Promise<Array>} Array of patient objects
 */
const getAllPatients = () => apiRequest('/api/patients');

/**
 * Assign a patient to a specialist for monitoring
 * @param {number} patientUserId - Patient's user ID
 * @param {number} specialistUserId - Specialist's user ID
 * @returns {Promise<Object>} Assignment confirmation
 */
const assignPatientToSpecialist = (patientUserId, specialistUserId) =>
  apiRequest('/api/assignments/assign', {
    method: 'POST',
    body: JSON.stringify({
      patientId: patientUserId,
      specialistId: specialistUserId,
    }),
  });

// ========== Specialist Endpoints ==========

/**
 * Get list of patients assigned to a specialist
 * @param {number} specId - Specialist user ID
 * @returns {Promise<Array>} Array of assigned patient objects
 */
const getSpecialistPatients = (specId) =>
  apiRequest(`/api/specialist/${encodeURIComponent(specId)}/patients`);

/**
 * Get specialist dashboard data (statistics, alerts)
 * @param {number} specId - Specialist user ID
 * @returns {Promise<Object>} Dashboard data object
 */
const getSpecialistDashboard = (specId) =>
  apiRequest(`/api/specialist/${encodeURIComponent(specId)}/dashboard`);

/**
 * Get patients requiring specialist attention (abnormal readings, alerts)
 * @param {number} specId - Specialist user ID
 * @returns {Promise<Array>} Array of patients needing attention
 */
const getSpecialistAttention = (specId) =>
  apiRequest(`/api/specialist/${encodeURIComponent(specId)}/attention`);

// ========== Additional Utility Endpoints ==========

/**
 * Get comprehensive report for a patient
 * @param {number} userId - Patient user ID
 * @returns {Promise<Object>} Patient report with detailed analytics
 */
const getReport = (userId) =>
  apiRequest(`/api/reports/${encodeURIComponent(userId)}`);

/**
 * Get diet recommendations for a specific condition
 * @param {string} condition - Medical condition (e.g., 'diabetes', 'prediabetes')
 * @returns {Promise<Object>} Diet recommendations object
 */
const getDiet = (condition) =>
  apiRequest(`/api/diet/${encodeURIComponent(condition)}`);

/**
 * Get personalized thresholds for a patient
 * @param {number} userId - Patient user ID
 * @returns {Promise<Object>} Threshold values (normal, borderline, abnormal ranges)
 */
const getThresholds = (userId) =>
  apiRequest(`/api/thresholds/${encodeURIComponent(userId)}`);
