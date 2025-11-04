/**
 * Shared Layout Component
 * 
 * Why this exists:
 * - Provides consistent navigation between User Dashboard and Operator View
 * - Shows current user info and role
 * - Provides logout functionality
 * - Wraps all pages with a responsive container
 * - Shows app branding (SpendSense title)
 * 
 * Features:
 * - Role-based navigation (shows only appropriate links)
 * - User info display (user_id and role badge)
 * - Logout button
 */

import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

export function Layout() {
  const location = useLocation()
  const { user, logout } = useAuth()
  
  /**
   * Handle logout.
   * 
   * Why: Clears token and redirects to login
   */
  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }
  
  return (
    <div className="min-h-screen bg-background">
      {/* Header with Navigation */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">SpendSense</h1>
            
            <div className="flex items-center gap-6">
              {/* Navigation Links */}
              <nav className="flex gap-4">
                {/* User Dashboard - show for all authenticated users */}
                <Link
                  to="/dashboard"
                  className={cn(
                    "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    location.pathname.startsWith('/dashboard')
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-secondary"
                  )}
                >
                  User Dashboard
                </Link>
                
                {/* Operator View - show only for operators */}
                {user?.role === 'operator' && (
                  <Link
                    to="/operator"
                    className={cn(
                      "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                      location.pathname.startsWith('/operator')
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-secondary"
                    )}
                  >
                    Operator View
                  </Link>
                )}
              </nav>
              
              {/* User Info and Logout */}
              {user && (
                <div className="flex items-center gap-4 border-l pl-6">
                  <div className="text-sm">
                    <div className="font-medium">{user.user_id}</div>
                    <div className="text-xs text-muted-foreground">
                      {user.role === 'operator' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          Operator
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          Card User
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleLogout}
                  >
                    Logout
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}


