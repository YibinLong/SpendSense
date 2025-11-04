/**
 * Shared Layout Component
 * 
 * Why this exists:
 * - Provides consistent navigation between User Dashboard and Operator View
 * - Wraps all pages with a responsive container
 * - Shows app branding (SpendSense title)
 */

import { Link, Outlet, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'

export function Layout() {
  const location = useLocation()
  
  return (
    <div className="min-h-screen bg-background">
      {/* Header with Navigation */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">SpendSense</h1>
            
            <nav className="flex gap-4">
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
            </nav>
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


