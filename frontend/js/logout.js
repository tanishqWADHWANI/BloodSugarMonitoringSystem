// logout.js - Universal logout functionality

function performLogout(redirectPage = 'index.html') {
  // Clear all possible session storage keys
  const keysToRemove = [
    'bsm_token',
    'userId',
    'patientId',
    'patientUsername',
    'patientFullName',
    'specialistId',
    'specialistUserId',
    'specialistUsername',
    'specialistFullName',
    'specialistSpecialty',
    'staffId',
    'staffUserId',
    'loggedInStaff',
    'staffName',
    'adminId',
    'adminUserId',
    'loggedInAdmin',
    'adminName',
    'authUser'
  ];
  
  keysToRemove.forEach(key => localStorage.removeItem(key));
  
  // Optional: Clear everything for a complete logout
  // localStorage.clear();
  
  console.log('Logout complete - all session data cleared');
  
  // Redirect to login page
  window.location.href = redirectPage;
}

// Session timeout check (30 minutes of inactivity)
let inactivityTimer;
const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes

function resetInactivityTimer() {
  clearTimeout(inactivityTimer);
  inactivityTimer = setTimeout(() => {
    alert('Your session has expired due to inactivity. Please log in again.');
    performLogout();
  }, INACTIVITY_TIMEOUT);
}

// Track user activity
function setupActivityTracking() {
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
  
  events.forEach(event => {
    document.addEventListener(event, resetInactivityTimer, true);
  });
  
  // Start the timer
  resetInactivityTimer();
}

// Validate session on page load
function validateSession() {
  const token = localStorage.getItem('bsm_token');
  if (!token) {
    console.warn('No valid session found');
    return false;
  }
  return true;
}
