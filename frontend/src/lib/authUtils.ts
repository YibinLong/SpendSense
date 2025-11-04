/**
 * Authentication utility functions for token management.
 * 
 * Why this exists:
 * - Centralizes token storage logic
 * - Provides type-safe token operations
 * - Handles localStorage safely
 * - Simple JWT decoding for client-side use
 * 
 * Storage key: 'spendsense_token'
 */

const TOKEN_KEY = 'spendsense_token';

/**
 * Store JWT token in localStorage.
 * 
 * @param token - JWT access token from login/signup
 * 
 * Why we use localStorage:
 * - Persists across browser sessions
 * - Simple API
 * - Works for local-only demo app
 */
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Retrieve JWT token from localStorage.
 * 
 * @returns JWT token or null if not found
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Remove JWT token from localStorage (logout).
 */
export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Decode JWT token to extract payload data.
 * 
 * WARNING: This does NOT verify the signature!
 * Only use for extracting user info on the client side.
 * The backend MUST verify the token signature.
 * 
 * @param token - JWT token string
 * @returns Decoded payload with user_id, role, exp
 * 
 * Why we decode client-side:
 * - Extract user info for UI display
 * - Check expiration before making requests
 * - No signature verification needed (backend does that)
 */
export const decodeToken = (token: string): {
  user_id: string;
  role: string;
  exp: number;
} | null => {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.error('Invalid JWT format');
      return null;
    }

    // Decode payload (base64url)
    const payload = parts[1];
    // Replace URL-safe chars and add padding if needed
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padding = '='.repeat((4 - (base64.length % 4)) % 4);
    const decoded = atob(base64 + padding);
    
    return JSON.parse(decoded);
  } catch (error) {
    console.error('Failed to decode token:', error);
    return null;
  }
};

/**
 * Check if token is expired.
 * 
 * @param token - JWT token string
 * @returns true if token is expired or invalid
 */
export const isTokenExpired = (token: string): boolean => {
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) {
    return true;
  }
  
  // exp is in seconds, Date.now() is in milliseconds
  return decoded.exp * 1000 < Date.now();
};

/**
 * Check if user has a valid token.
 * 
 * @returns true if valid token exists and is not expired
 */
export const isAuthenticated = (): boolean => {
  const token = getToken();
  if (!token) {
    return false;
  }
  
  return !isTokenExpired(token);
};

