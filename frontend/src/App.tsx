/**
 * App Component - Main Router
 * 
 * Why this exists:
 * - Sets up routing for User Dashboard and Operator View
 * - Provides shared layout with navigation
 * - Redirects root path to /dashboard
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { UserDashboard } from './pages/UserDashboard'
import { OperatorView } from './pages/OperatorView'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* User Dashboard - supports both with and without userId */}
          <Route path="/dashboard" element={<UserDashboard />} />
          <Route path="/dashboard/:userId" element={<UserDashboard />} />
          
          {/* Operator View */}
          <Route path="/operator" element={<OperatorView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
