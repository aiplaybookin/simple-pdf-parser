/**
 * API Configuration
 *
 * In Docker: Uses relative path '/api' (proxied by nginx to backend)
 * In Development: Uses 'http://localhost:8000' (direct connection)
 */

// Detect environment
const isDocker = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

export const API_BASE_URL = isDocker ? '/api' : 'http://localhost:8000';
