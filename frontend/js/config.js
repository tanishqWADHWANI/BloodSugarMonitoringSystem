/**
 * Global API Configuration
 * =========================
 * Provides dynamic backend URL for all API calls
 * Supports both localhost and network access
 */

(function() {
  'use strict';
  
  // Determine the backend URL dynamically based on current page location
  function getBackendUrl() {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // If accessing from localhost/127.0.0.1, use those addresses
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
      return 'http://127.0.0.1:5000';
    }
    
    // Otherwise, use the current hostname/IP with port 5000
    return `${protocol}//${hostname}:5000`;
  }
  
  // Make the backend URL available globally
  window.API_BASE_URL = getBackendUrl();
  window.API_CONFIG = {
    baseUrl: window.API_BASE_URL,
    timeout: 10000, // 10 seconds
    
    /**
     * Helper function to build API endpoint URLs
     * @param {string} endpoint - API endpoint path (e.g., '/api/login')
     * @returns {string} - Full API URL
     */
    getUrl: function(endpoint) {
      return window.API_BASE_URL + endpoint;
    },
    
    /**
     * Helper function for fetch requests with error handling
     * @param {string} url - Full URL or endpoint
     * @param {object} options - Fetch options
     * @returns {Promise}
     */
    fetch: async function(url, options = {}) {
      const fullUrl = url.startsWith('http') ? url : this.getUrl(url);
      const timeout = options.timeout || this.timeout;
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      try {
        const response = await fetch(fullUrl, {
          ...options,
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
      } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
          throw new Error('Request timeout: The server took too long to respond');
        }
        throw error;
      }
    }
  };
  
  // Log configuration for debugging
  console.log('[API Config] Backend URL:', window.API_BASE_URL);
})();
