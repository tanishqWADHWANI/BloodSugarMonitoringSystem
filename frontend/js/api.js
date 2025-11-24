// frontend/js/api.js

// 1) Base URL of your Flask API
// Behavior:
// - If `window.API_BASE` is defined by the page, use it (explicit override).
// - If the page is served from the backend port (5000), prefer a relative
//   base (empty string) so requests are same-origin: `fetch('/api/...')`.
// - Otherwise default to assuming backend is at port 5000 on the current host.
const API_BASE_URL = (function() {
  try {
    if (typeof window !== 'undefined' && window.API_BASE) {
      return window.API_BASE;
    }
    const loc = (typeof window !== 'undefined' && window.location) ? window.location : null;
    if (loc && String(loc.port) === '5000') {
      // same-origin (backend serving frontend)
      return '';
    }
    const host = loc && loc.hostname ? loc.hostname : '127.0.0.1';
    const proto = loc && loc.protocol ? loc.protocol : 'http:';
    return `${proto}//${host}:5000`;
  } catch (e) {
    return 'http://127.0.0.1:5000';
  }
})();

// 2) Core helper: all HTTP calls pass through here
async function apiRequest(path, { method = 'GET', headers = {}, body = null } = {}) {
  // Attach auth token automatically if available
  const token = (typeof localStorage !== 'undefined') ? localStorage.getItem('bsm_token') : null;
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeaders, ...headers },
  };

  if (body != null) {
    opts.body = (typeof body === 'string') ? body : JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, opts);

  let data = null;
  try { data = await res.json(); } catch (_) { /* allow empty bodies */ }

  if (!res.ok) {
    const msg = (data && (data.error || data.message)) || `Request failed with status ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

// 3) Semantic wrappers (match README endpoints)  ────────────────
// Users
const getUser = (id) => apiRequest(`/api/users/${encodeURIComponent(id)}`);

// NEW: Generic login function for all roles with hybrid behavior
// Try the backend first; on network/error/failure, fall back to a local demo response.
const loginUser = async (email, password) => {
  try {
    const data = await apiRequest('/api/login', { method: 'POST', body: { email, password } });
    return data;
  } catch (err) {
    // Fallback: create a local demo session similar to patient.html behavior
    try {
      const key = (email || '').split('@')[0] || 'demo';
      const cap = (s) => s.replace(/[_\.-]/g, ' ').split(' ').map(p => p.charAt(0).toUpperCase()+p.slice(1)).join(' ');
      const name = cap(key);
      const token = 'local-demo-' + key;
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('bsm_token', token);
        localStorage.setItem('loggedInPatient', key);
      }
      return { token, user: { id: `local-${key}`, email, firstName: name.split(' ')[0] || key, lastName: name.split(' ')[1] || '', role: 'patient' }, _localDemo: true };
    } catch (e) {
      throw err;
    }
  }
};

// Specialist login wrapper (calls /api/specialist/login) with hybrid fallback
const specialistLogin = async (username, password, workingId=null) => {
  try {
    const body = workingId ? { username, password, working_id: workingId } : { username, password };
    const data = await apiRequest('/api/specialist/login', { method: 'POST', body });
    return data;
  } catch (err) {
    // Fallback: create a local demo specialist session
    try {
      const key = (username || '').split('@')[0] || 'specialist';
      const cap = (s) => s.replace(/[_\.-]/g, ' ').split(' ').map(p => p.charAt(0).toUpperCase()+p.slice(1)).join(' ');
      const name = cap(key);
      const token = 'local-demo-' + key;
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('bsm_token', token);
        localStorage.setItem('specialistUsername', key);
        localStorage.setItem('specialistFullName', name);
        localStorage.setItem('specialistId', '0');
      }
      return { token, user: { id: `local-spec-${key}`, username: key, fullName: name, role: 'specialist' }, _localDemo: true };
    } catch (e) {
      throw err;
    }
  }
};


const registerUser = (payload) => apiRequest('/api/users/register', {
  method: 'POST', body: JSON.stringify(payload)
});
const updateUser = (id, payload) => apiRequest(`/api/users/${encodeURIComponent(id)}`, {
  method: 'PUT', body: JSON.stringify(payload)
});
const deleteUser = (id) => apiRequest(`/api/users/${encodeURIComponent(id)}`, { method: 'DELETE' });

// Readings with offline caching and write-queue support
const READINGS_CACHE_KEY = (userId) => `readings_${userId}`;
const PENDING_READINGS_KEY = 'pending_readings';

const getCachedReadings = (userId) => {
  try {
    const raw = localStorage.getItem(READINGS_CACHE_KEY(userId));
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) { return null; }
};

const setCachedReadings = (userId, readings) => {
  try {
    localStorage.setItem(READINGS_CACHE_KEY(userId), JSON.stringify(readings || []));
  } catch (e) { /* ignore storage errors */ }
};

const enqueuePendingReading = (payload) => {
  try {
    const raw = localStorage.getItem(PENDING_READINGS_KEY) || '[]';
    const arr = JSON.parse(raw);
    arr.push(payload);
    localStorage.setItem(PENDING_READINGS_KEY, JSON.stringify(arr));
  } catch (e) { /* ignore */ }
};

const getPendingReadings = () => {
  try { return JSON.parse(localStorage.getItem(PENDING_READINGS_KEY) || '[]'); } catch (e) { return []; }
};

const clearPendingReadings = () => {
  try { localStorage.removeItem(PENDING_READINGS_KEY); } catch (e) { /* ignore */ }
};

const syncPendingReadings = async () => {
  const pending = getPendingReadings();
  if (!Array.isArray(pending) || pending.length === 0) return { synced: 0 };

  let synced = 0;
  const remaining = [];
  for (const p of pending) {
    try {
      await apiRequest('/api/readings', { method: 'POST', body: JSON.stringify(p) });
      synced += 1;
    } catch (e) {
      remaining.push(p);
    }
  }

  try {
    if (remaining.length === 0) localStorage.removeItem(PENDING_READINGS_KEY);
    else localStorage.setItem(PENDING_READINGS_KEY, JSON.stringify(remaining));
  } catch (e) { /* ignore */ }

  return { synced, remaining: remaining.length };
};

const addReading = async (payload) => {
  try {
    const res = await apiRequest('/api/readings', { method: 'POST', body: JSON.stringify(payload) });
    // If successful, update cached readings for the user (prepend newest)
    try {
      const userId = payload.userId || payload.user_id;
      if (userId) {
        const cached = getCachedReadings(userId) || [];
        const readingObj = Object.assign({}, res, { date_time: new Date().toISOString() });
        cached.unshift(readingObj);
        setCachedReadings(userId, cached);
      }
    } catch (e) { /* ignore cache update errors */ }
    return res;
  } catch (err) {
    // On failure, enqueue the reading locally to be synced later
    try { enqueuePendingReading(payload); } catch (e) { /* ignore */ }
    // Return a local acknowledgement so UI can reflect the new reading
    return { _localQueued: true, message: 'Reading queued locally and will be synced when online.' };
  }
};

const getReadings = async (userId, days = 30) => {
  const path = `/api/readings/${encodeURIComponent(userId)}?days=${encodeURIComponent(days)}`;
  try {
    // Try network first
    const json = await apiRequest(path);
    const readings = Array.isArray(json.readings) ? json.readings : [];
    // Cache the successful response for offline fallback
    try { setCachedReadings(userId, readings); } catch (e) { /* ignore */ }
    return readings;
  } catch (err) {
    // Network or server error — fall back to cached readings if available
    const cached = getCachedReadings(userId);
    if (Array.isArray(cached)) return cached;
    // No cached data — rethrow original error so callers can handle
    throw err;
  }
};
const updateReading = (readingId, payload) => apiRequest(`/api/readings/${encodeURIComponent(readingId)}`, {
  method: 'PUT', body: JSON.stringify(payload)
});
const deleteReading = (readingId) => apiRequest(`/api/readings/${encodeURIComponent(readingId)}`, { method: 'DELETE' });

// Insights
const getInsights = (userId) => apiRequest(`/api/insights/${encodeURIComponent(userId)}`);
const getTrends = (userId) => apiRequest(`/api/insights/${encodeURIComponent(userId)}/trends`);
const getPatterns = (userId) => apiRequest(`/api/insights/${encodeURIComponent(userId)}/patterns`);
const getSavedInsights = (userId) => apiRequest(`/api/aiinsights/${encodeURIComponent(userId)}`);

// Alerts
const getAlerts = (userId) => apiRequest(`/api/alerts/${encodeURIComponent(userId)}`);
const dismissAlert = (alertId) => apiRequest(`/api/alerts/${encodeURIComponent(alertId)}`, { method: 'DELETE' });

// Admin
// In api.js
const getAllUsers = () => apiRequest('/api/admin/users/all'); 
const getAdminMonthlyReport = (month, year) => apiRequest(`/api/admin/reports/monthly?month=${month}&year=${year}`);

// Staff Dashboard - Assign Patients to Doctors
const assignPatientToSpecialist = (patientUserId, specialistUserId) => apiRequest('/api/assignments/assign', {
    method: 'POST', 
    body: JSON.stringify({ 
        patientId: patientUserId, 
        specialistId: specialistUserId 
    })
});

// Specialist
const getSpecialistPatients = (specId) => apiRequest(`/api/specialist/${encodeURIComponent(specId)}/patients`);
const getSpecialistDashboard = (specId) => apiRequest(`/api/specialist/${encodeURIComponent(specId)}/dashboard`);
const getSpecialistAttention = (specId) => apiRequest(`/api/specialist/${encodeURIComponent(specId)}/attention`);

// Additional
const getReport = (userId) => apiRequest(`/api/reports/${encodeURIComponent(userId)}`);
const getDiet = (condition) => apiRequest(`/api/diet/${encodeURIComponent(condition)}`);
const getThresholds = (userId) => apiRequest(`/api/thresholds/${encodeURIComponent(userId)}`);

// Server runtime mode (demo vs DB availability)
const getServerMode = () => apiRequest('/api/server/mode');

// Notifications / Email
const sendEmail = (payload) => apiRequest('/api/notify/email', { method: 'POST', body: JSON.stringify(payload) });
const sendEmailBatch = (emails) => apiRequest('/api/notify/batch', { method: 'POST', body: JSON.stringify({ emails }) });

// Exported for other modules (if using bundler) - keep global for now in browser
window.bsm_api = window.bsm_api || {};
window.bsm_api.getServerMode = getServerMode;
window.bsm_api.specialistLogin = specialistLogin;
window.bsm_api.loginUser = loginUser;
window.bsm_api.sendEmail = sendEmail;
window.bsm_api.sendEmailBatch = sendEmailBatch;