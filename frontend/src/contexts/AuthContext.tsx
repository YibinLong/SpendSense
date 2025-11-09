/**
 * Authentication Context Provider
 * 
 * Why this exists:
 * - Provides global auth state to all components
 * - Handles login/logout logic
 * - Auto-loads token on mount
 * - Provides user info from token
 * 
 * Usage:
 *   import { useAuth } from './contexts/AuthContext';
 *   const { user, isAuthenticated, login, logout } = useAuth();
 */

import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { setToken, getToken, clearToken, decodeToken, isTokenExpired } from '../lib/authUtils';

interface User {
  user_id: string;
  role: 'card_user' | 'operator';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Load and validate token on mount.
   * 
   * Why we do this:
   * - Restore auth state on page refresh
   * - Validate token hasn't expired
   * - Extract user info from token
   */
  useEffect(() => {
    const token = getToken();
    
    if (token && !isTokenExpired(token)) {
      const decoded = decodeToken(token);
      if (decoded) {
        setUser({
          user_id: decoded.user_id,
          role: decoded.role as 'card_user' | 'operator',
        });
      }
    }
    
    setIsLoading(false);
  }, []);

  /**
   * Handle login - store token and extract user info.
   * 
   * @param token - JWT token from login/signup response
   */
  const login = (token: string) => {
    setToken(token);
    
    const decoded = decodeToken(token);
    if (decoded) {
      setUser({
        user_id: decoded.user_id,
        role: decoded.role as 'card_user' | 'operator',
      });
    }
  };

  /**
   * Handle logout - clear token and user state.
   */
  const logout = () => {
    clearToken();
    setUser(null);
  };

  const value = {
    user,
    isAuthenticated: user !== null,
    login,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to access auth context.
 * 
 * @returns AuthContextType
 * @throws Error if used outside AuthProvider
 * 
 * Example:
 *   const { user, isAuthenticated, logout } = useAuth();
 *   if (isAuthenticated) {
 *     console.log(`Logged in as: ${user?.user_id}`);
 *   }
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

