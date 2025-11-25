// frontend/js/api.js

// 1) Base URL of your Flask API
const API_BASE_URL = 'http://127.0.0.1:5000';  // change if your backend host/port changes

// 2) Core helper: all HTTP calls pass through here
async function apiRequest(
  path,
  { method = 'GET', headers = {}, body = null } = {}
) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...headers },
    body,
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    // allow empty bodies
  }

  if (!res.ok) {
    const msg =
      (data && data.error) || `Request failed with status ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

// 3) Semantic wrappers (match README endpoints)  ────────────────

// Users
const getUser = (id) => apiRequest(`/api/users/${encodeURIComponent(id)}`);

const registerUser = (payload) =>
  apiRequest('/api/users/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

const updateUser = (id, payload) =>
  apiRequest(`/api/users/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

const deleteUser = (id) =>
  apiRequest(`/api/users/${encodeURIComponent(id)}`, { method: 'DELETE' });

// Login (generic for all roles)
const loginUser = (email, password, role) =>
  apiRequest('/api/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

// shared login helper (mainly used for patient pages)
const login = (email, password, role) =>
  apiRequest('/api/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });

// Shared auth storage 
const AUTH_KEY = 'authUser';

function saveAuthUser(user) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

function loadAuthUser() {
  const raw = localStorage.getItem(AUTH_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function requireRole(expectedRole) {
  const user = loadAuthUser();
  if (!user || (expectedRole && user.role !== expectedRole)) {
    // Not logged in as expected role → kick back to the appropriate login page
    if (expectedRole === 'patient') window.location.href = 'patient.html';
    else if (expectedRole === 'specialist') window.location.href = 'specialist.html';
    else if (expectedRole === 'staff') window.location.href = 'staff.html';
    else if (expectedRole === 'admin') window.location.href = 'admin.html';
    else window.location.href = 'index.html';
    throw new Error('Not logged in');
  }
  return user; // { user_id, role, email, ... }
}

// Readings
const addReading = (payload) =>
  apiRequest('/api/readings', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

const getReadings = async (userId, days = 30) => {
  const path = `/api/readings/${encodeURIComponent(
    userId
  )}?days=${encodeURIComponent(days)}`;

// apiRequest will give us the full JSON object:
const json = await apiRequest(path);
  
return Array.isArray(json.readings) ? json.readings : [];
};

const updateReading = (readingId, payload) =>
  apiRequest(`/api/readings/${encodeURIComponent(readingId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

const deleteReading = (readingId) =>
  apiRequest(`/api/readings/${encodeURIComponent(readingId)}`, {
    method: 'DELETE',
  });

// Insights
const getInsights = (userId) =>
  apiRequest(`/api/insights/${encodeURIComponent(userId)}`);

const getTrends = (userId) =>
  apiRequest(`/api/insights/${encodeURIComponent(userId)}/trends`);

const getPatterns = (userId) =>
  apiRequest(`/api/insights/${encodeURIComponent(userId)}/patterns`);

const getSavedInsights = (userId) =>
  apiRequest(`/api/aiinsights/${encodeURIComponent(userId)}`);

// Alerts
const getAlerts = (userId) =>
  apiRequest(`/api/alerts/${encodeURIComponent(userId)}`);

const dismissAlert = (alertId) =>
  apiRequest(`/api/alerts/${encodeURIComponent(alertId)}`, {
    method: 'DELETE',
  });

// Admin
const getAllUsers = () => apiRequest('/api/admin/users/all');

const getAdminMonthlyReport = (month, year) =>
  apiRequest(`/api/admin/reports/monthly?month=${month}&year=${year}`);

// Patients (for staff/admin)
const getAllPatients = () => apiRequest('/api/patients');

// Staff Dashboard - Assign Patients to Doctors
const assignPatientToSpecialist = (patientUserId, specialistUserId) =>
  apiRequest('/api/assignments/assign', {
    method: 'POST',
    body: JSON.stringify({
      patientId: patientUserId,
      specialistId: specialistUserId,
    }),
  });

// Specialist
const getSpecialistPatients = (specId) =>
  apiRequest(`/api/specialist/${encodeURIComponent(specId)}/patients`);

const getSpecialistDashboard = (specId) =>
  apiRequest(`/api/specialist/${encodeURIComponent(specId)}/dashboard`);

const getSpecialistAttention = (specId) =>
  apiRequest(`/api/specialist/${encodeURIComponent(specId)}/attention`);

// Additional
const getReport = (userId) =>
  apiRequest(`/api/reports/${encodeURIComponent(userId)}`);

const getDiet = (condition) =>
  apiRequest(`/api/diet/${encodeURIComponent(condition)}`);

const getThresholds = (userId) =>
  apiRequest(`/api/thresholds/${encodeURIComponent(userId)}`);
