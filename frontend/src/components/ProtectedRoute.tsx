/**
 * Protected Route Component
 * 
 * Why this exists:
 * - Prevents unauthorized access to protected pages
 * - Redirects unauthenticated users to login
 * - Optionally checks user role (operator vs card_user)
 * - Shows loading state while checking auth
 * 
 * Usage:
 *   <ProtectedRoute>
 *     <UserDashboard />
 *   </ProtectedRoute>
 * 
 *   <ProtectedRoute requiredRole="operator">
 *     <OperatorView />
 *   </ProtectedRoute>
 */

import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'card_user' | 'operator';
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  /**
   * Show loading state while checking authentication.
   * 
   * Why: Prevents flash of redirect before auth state loads
   */
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  /**
   * Redirect to login if not authenticated.
   * 
   * Why: User must be logged in to access protected routes
   */
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  /**
   * Check role if specified.
   * 
   * Why: Some routes (like /operator) require specific roles
   * If role doesn't match, redirect to appropriate dashboard
   */
  if (requiredRole && user?.role !== requiredRole) {
    // If operator tries to access card_user route, send to operator view
    if (user?.role === 'operator') {
      return <Navigate to="/operator" replace />;
    }
    // If card_user tries to access operator route, send to user dashboard
    return <Navigate to="/dashboard" replace />;
  }

  // User is authenticated and has required role (if specified)
  return <>{children}</>;
}

