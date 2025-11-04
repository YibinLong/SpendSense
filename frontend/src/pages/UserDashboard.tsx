/**
 * User Dashboard Page - Modern UI Redesign
 * 
 * Why this exists:
 * - Shows users their behavioral persona and financial signals with modern design
 * - Displays personalized recommendations with visual hierarchy
 * - Supports both URL routing (/dashboard/:userId) and dropdown selection
 * - Tabs for 30d and 180d windows with data visualization
 * 
 * Modern Features:
 * - Hero section with gradient background and welcome message
 * - Stats cards showing key metrics
 * - Data visualization with charts
 * - Empty states with helpful messaging
 * - Loading skeletons instead of plain text
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PersonaBadge } from '@/components/PersonaBadge'
import { SignalCard } from '@/components/SignalCard'
import { RecommendationCard } from '@/components/RecommendationCard'
import { DevDebugPanel } from '@/components/DevDebugPanel'
import { DashboardSkeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import { CreditUtilizationGauge } from '@/components/charts/CreditUtilizationGauge'
import { useUsers, useUserProfile, useRecommendations, useGrantConsent, HttpError } from '@/lib/api'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { CommonIcons } from '@/lib/iconMap'
import { TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export function UserDashboard() {
  const { userId: urlUserId } = useParams()
  const navigate = useNavigate()
  const [activeWindow, setActiveWindow] = useState<'30' | '180'>('30')

  // Fetch all users for the selector
  const { data: users, isLoading: usersLoading } = useUsers()

  // Fetch profile data for the selected user
  const windowDays = activeWindow === '30' ? 30 : 180
  const { data: profile, isLoading: profileLoading, error: profileError } = useUserProfile(urlUserId, windowDays)

  // Fetch recommendations for the selected user
  const { data: recommendations, isLoading: recsLoading, error: recsError } = useRecommendations(urlUserId, windowDays)

  // Consent grant mutation
  const grantConsent = useGrantConsent()

  // Handle user selection from dropdown
  const handleUserSelect = (userId: string) => {
    navigate(`/dashboard/${userId}`)
  }

  // If no user selected, show selector with modern design
  if (!urlUserId) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="border-2 shadow-lg">
          <div className="h-2 bg-gradient-primary rounded-t-lg" />
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CommonIcons.LayoutDashboard className="h-6 w-6 text-primary" />
              User Dashboard
            </CardTitle>
            <CardDescription>
              Select a user to view their financial profile and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usersLoading ? (
              <div className="space-y-3">
                <div className="h-11 bg-muted animate-pulse rounded-md" />
                <p className="text-sm text-muted-foreground text-center">Loading users...</p>
              </div>
            ) : (
              <Select onValueChange={handleUserSelect}>
                <SelectTrigger className="w-full h-11">
                  <SelectValue placeholder="Choose a user" />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((user) => (
                    <SelectItem key={user.user_id} value={user.user_id}>
                      {user.user_id}
                      {user.email_masked && ` (${user.email_masked})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  // Loading state with skeleton
  if (profileLoading) {
    return <DashboardSkeleton />
  }

  // Error state (exclude 403 so we can show consent dialog instead)
  if (profileError && !(profileError instanceof HttpError && profileError.status === 403)) {
    return (
      <div className="max-w-6xl mx-auto">
        <EmptyState
          icon={AlertCircle}
          title="Error Loading Profile"
          description={profileError.message || 'Unable to load user profile. Please try again.'}
          action={{
            label: "Try Different User",
            onClick: () => navigate('/dashboard')
          }}
        />
      </div>
    )
  }

  // Main dashboard view
  const signals = profile?.signals
  const persona = profile?.persona
  const selectedUser = users?.find(u => u.user_id === urlUserId)

  // Split recommendations into education and offers, and deduplicate by ID
  // Why: Sometimes the API returns duplicates, so we filter by unique IDs
  const deduplicatedRecs = recommendations?.reduce((acc, rec) => {
    if (!acc.find(r => r.id === rec.id)) {
      acc.push(rec);
    }
    return acc;
  }, [] as typeof recommendations) || [];
  
  const educationItems = deduplicatedRecs.filter(r => r.item_type === 'education')
  const offerItems = deduplicatedRecs.filter(r => r.item_type === 'offer')

  // Calculate stats for hero section
  const totalRecommendations = (educationItems.length || 0) + (offerItems.length || 0)
  const signalsDetected = [
    signals?.subscriptions,
    signals?.savings,
    signals?.credit,
    signals?.income
  ].filter(Boolean).length

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Consent dialog shown when backend blocks with 403 */}
      <Dialog open={(
        (profileError instanceof HttpError && profileError.status === 403) ||
        (recsError instanceof HttpError && recsError.status === 403)
      )}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Consent Required</DialogTitle>
            <DialogDescription>
              To view this user's profile and recommendations, you need to grant consent for data processing.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="gradient"
              onClick={() => urlUserId && grantConsent.mutate({ userId: urlUserId, reason: 'Accessing dashboard', by: 'user_dashboard' })}
              disabled={grantConsent.isPending}
            >
              {grantConsent.isPending ? 'Granting…' : 'Grant Consent'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Hero Section with gradient background */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 p-8 shadow-2xl">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
        
        {/* Content */}
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                Welcome back!
              </h1>
              <p className="text-white/90 text-lg">
                {urlUserId}
                {selectedUser?.email_masked ? ` • ${selectedUser.email_masked}` : ''}
              </p>
            </div>
            
            {/* User selector in hero */}
            <Select onValueChange={handleUserSelect} value={urlUserId}>
              <SelectTrigger className="w-full md:w-64 bg-white/10 border-white/20 text-white hover:bg-white/20 backdrop-blur-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {users?.map((user) => (
                  <SelectItem key={user.user_id} value={user.user_id}>
                    {user.user_id}
                    {user.email_masked ? ` (${user.email_masked})` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Stats Cards in Hero */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/70 text-sm">Recommendations</p>
                  <p className="text-white text-2xl font-bold">{totalRecommendations}</p>
                </div>
                <div className="rounded-lg bg-white/20 p-3">
                  <CommonIcons.BookOpen className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/70 text-sm">Signals Detected</p>
                  <p className="text-white text-2xl font-bold">{signalsDetected} / 4</p>
                </div>
                <div className="rounded-lg bg-white/20 p-3">
                  <Activity className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/70 text-sm">Time Window</p>
                  <p className="text-white text-2xl font-bold">{windowDays}d</p>
                </div>
                <div className="rounded-lg bg-white/20 p-3">
                  <CommonIcons.Activity className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Window tabs (30d vs 180d) */}
      <Tabs value={activeWindow} onValueChange={(v) => setActiveWindow(v as '30' | '180')}>
        <TabsList className="grid w-full max-w-md grid-cols-2 h-11">
          <TabsTrigger value="30" className="text-sm font-medium">30 Days</TabsTrigger>
          <TabsTrigger value="180" className="text-sm font-medium">180 Days</TabsTrigger>
        </TabsList>

        <TabsContent value={activeWindow} className="space-y-6 mt-6">
          {/* Persona Section */}
          <Card className="border-2 shadow-lg overflow-hidden">
            <div className="h-2 bg-gradient-primary" />
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CommonIcons.Users className="h-5 w-5 text-primary" />
                Assigned Persona
              </CardTitle>
              <CardDescription>
                Based on behavioral patterns over the last {windowDays} days
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PersonaBadge persona={persona} />
              {persona?.criteria_met && (
                <div className="mt-4">
                  <details className="group cursor-pointer">
                    <summary className="text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2 list-none">
                      <svg className="h-4 w-4 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      View assignment criteria
                    </summary>
                    <div className="mt-3 space-y-2 ml-6">
                      {Object.entries(persona.criteria_met).map(([key, value]) => (
                        <div key={key} className="bg-muted/50 p-3 rounded-lg border">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium capitalize">
                              {key.replace(/_/g, ' ')}
                            </span>
                            <span className={cn(
                              "text-xs px-2 py-1 rounded",
                              typeof value === 'boolean' && value
                                ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                                : typeof value === 'boolean'
                                ? "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400"
                            )}>
                              {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : 
                               Array.isArray(value) ? value.join(', ') : 
                               typeof value === 'object' ? JSON.stringify(value) : 
                               String(value)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Data Visualization Row */}
          {signals?.credit && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <CreditUtilizationGauge 
                utilization={Number(signals.credit.credit_utilization_max_pct || 0)}
                title="Credit Utilization"
                description="Current maximum credit card utilization"
              />
              <Card className="flex items-center justify-center">
                <CardContent className="text-center py-12">
                  <CommonIcons.LineChart className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
                  <p className="text-muted-foreground">Additional charts available</p>
                  <p className="text-sm text-muted-foreground mt-1">Spending trends, signal comparisons, etc.</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Behavioral Signals */}
          <div>
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Activity className="h-6 w-6 text-primary" />
              Behavioral Signals
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SignalCard
                title="Subscriptions"
                description="Recurring payment patterns"
                data={signals?.subscriptions}
                type="subscriptions"
              />
              <SignalCard
                title="Savings"
                description="Savings growth and emergency fund"
                data={signals?.savings}
                type="savings"
              />
              <SignalCard
                title="Credit"
                description="Credit utilization and behavior"
                data={signals?.credit}
                type="credit"
              />
              <SignalCard
                title="Income Stability"
                description="Payroll frequency and cash buffer"
                data={signals?.income}
                type="income"
              />
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <CommonIcons.Gift className="h-6 w-6 text-primary" />
              Recommendations
            </h2>
            
            {recsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="animate-pulse">
                    <CardContent className="p-6 space-y-3">
                      <div className="h-4 bg-muted rounded w-3/4" />
                      <div className="h-3 bg-muted rounded w-full" />
                      <div className="h-3 bg-muted rounded w-2/3" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="space-y-6">
                {/* Education Items */}
                {educationItems.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                      <CommonIcons.BookOpen className="h-5 w-5 text-blue-600" />
                      Educational Content
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {educationItems.slice(0, 5).map((item) => (
                        <RecommendationCard key={item.id} recommendation={item} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Partner Offers */}
                {offerItems.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                      <CommonIcons.Gift className="h-5 w-5 text-purple-600" />
                      Partner Offers
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {offerItems.slice(0, 3).map((item) => (
                        <RecommendationCard key={item.id} recommendation={item} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty state */}
                {educationItems.length === 0 && offerItems.length === 0 && (
                  <EmptyState
                    icon={CommonIcons.Inbox}
                    title="No recommendations yet"
                    description="Check back later for personalized recommendations based on your financial behavior."
                  />
                )}
              </div>
            )}
          </div>

          {/* Dev Debug Panel */}
          <DevDebugPanel
            title={`Profile Data (${windowDays}d)`}
            data={{ profile, signals, persona, recommendations }}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
