/**
 * App Component - Main Router
 * 
 * Why this exists:
 * - Sets up routing for User Dashboard and Operator View
 * - Provides shared layout with navigation
 * - Wraps app with AuthProvider for global auth state
 * - Protects routes with authentication guards
 * - Provides public routes for login/signup
 * 
 * Route Structure:
 * - /login, /signup: Public routes (no auth required)
 * - /dashboard: Protected route (requires auth, card_user or operator)
 * - /operator: Protected route (requires auth, operator role only)
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { Layout } from './components/Layout'
import { UserDashboard } from './pages/UserDashboard'
import { OperatorView } from './pages/OperatorView'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes (no layout, no auth required) */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Protected routes (with layout) */}
          <Route element={<Layout />}>
            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* User Dashboard - protected, any authenticated user */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <UserDashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/dashboard/:userId" 
              element={
                <ProtectedRoute>
                  <UserDashboard />
                </ProtectedRoute>
              } 
            />
            
            {/* Operator View - protected, operator role only */}
            <Route 
              path="/operator" 
              element={
                <ProtectedRoute requiredRole="operator">
                  <OperatorView />
                </ProtectedRoute>
              } 
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
