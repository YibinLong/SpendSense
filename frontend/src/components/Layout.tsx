/**
 * Shared Layout Component
 * 
 * Why this exists:
 * - Provides consistent navigation between User Dashboard and Operator View
 * - Shows current user info and role with modern avatar dropdown
 * - Provides logout functionality
 * - Wraps all pages with a responsive container
 * - Modern gradient header design
 * 
 * Features:
 * - Role-based navigation with gradient active states
 * - User avatar/profile dropdown
 * - Icons for better visual navigation
 * - Gradient header background
 */

import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from './ui/button'
import { getNavIcon } from '@/lib/iconMap'
import { cn } from '@/lib/utils'
import { useState } from 'react'
import { ChevronDown, User } from 'lucide-react'

export function Layout() {
  const location = useLocation()
  const { user, logout } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)
  
  const HomeIcon = getNavIcon('home')
  const DashboardIcon = getNavIcon('dashboard')
  const OperatorIcon = getNavIcon('operator')
  const LogoutIcon = getNavIcon('logout')
  
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
      {/* Header with Navigation - Gradient background */}
      <header className="sticky top-0 z-50 border-b shadow-md bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo/Brand */}
            <Link to="/dashboard" className="flex items-center gap-2 group">
              <div className="rounded-lg bg-white/10 p-2 backdrop-blur-sm group-hover:bg-white/20 transition-colors">
                <HomeIcon className="h-6 w-6 text-white" strokeWidth={2} />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                SpendSense
              </h1>
            </Link>
            
            <div className="flex items-center gap-4">
              {/* Navigation Links */}
              <nav className="flex gap-2">
                {/* User Dashboard - show for all authenticated users */}
                <Link
                  to="/dashboard"
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                    location.pathname.startsWith('/dashboard')
                      ? "bg-white text-blue-600 shadow-lg"
                      : "text-white/90 hover:bg-white/10 hover:text-white"
                  )}
                >
                  <DashboardIcon className="h-4 w-4" strokeWidth={2} />
                  Dashboard
                </Link>
                
                {/* Operator View - show only for operators */}
                {user?.role === 'operator' && (
                  <Link
                    to="/operator"
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                      location.pathname.startsWith('/operator')
                        ? "bg-white text-purple-600 shadow-lg"
                        : "text-white/90 hover:bg-white/10 hover:text-white"
                    )}
                  >
                    <OperatorIcon className="h-4 w-4" strokeWidth={2} />
                    Operator
                  </Link>
                )}
              </nav>
              
              {/* User Info and Dropdown */}
              {user && (
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-3 pl-4 border-l border-white/20 hover:bg-white/10 rounded-lg py-2 pr-3 transition-colors"
                  >
                    {/* User Avatar */}
                    <div className="flex items-center gap-3">
                      <div className="rounded-full bg-white/20 p-2 backdrop-blur-sm">
                        <User className="h-4 w-4 text-white" strokeWidth={2} />
                      </div>
                      <div className="text-left">
                        <div className="text-sm font-medium text-white">{user.user_id}</div>
                        <div className="text-xs text-white/70">
                          {user.role === 'operator' ? 'Operator' : 'Card User'}
                        </div>
                      </div>
                      <ChevronDown className={cn(
                        "h-4 w-4 text-white/70 transition-transform",
                        showUserMenu && "rotate-180"
                      )} />
                    </div>
                  </button>
                  
                  {/* Dropdown Menu */}
                  {showUserMenu && (
                    <>
                      {/* Backdrop */}
                      <div 
                        className="fixed inset-0 z-10" 
                        onClick={() => setShowUserMenu(false)}
                      />
                      
                      {/* Menu */}
                      <div className="absolute right-0 mt-2 w-56 rounded-lg bg-white dark:bg-gray-900 shadow-xl border border-gray-200 dark:border-gray-700 z-20">
                        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                          <p className="text-sm font-medium text-foreground">{user.user_id}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {user.role === 'operator' ? 'Operator Account' : 'Card User Account'}
                          </p>
                        </div>
                        <div className="p-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              handleLogout()
                              setShowUserMenu(false)
                            }}
                            className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <LogoutIcon className="h-4 w-4 mr-2" strokeWidth={2} />
                            Logout
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
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


