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

import { useState, useEffect, useMemo } from 'react'
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
import { SpendingBreakdownChart } from '@/components/charts/SpendingBreakdownChart'
import { TransactionList } from '@/components/TransactionList'
import { useUsers, useUserProfile, useRecommendations, useTransactions, useGrantConsent, useRevokeConsent, HttpError } from '@/lib/api'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { CommonIcons } from '@/lib/iconMap'
import { Activity, AlertCircle, Receipt, ShieldOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import { parseUserInfo, formatSignalCount } from '@/lib/userUtils'
import { useAuth } from '@/contexts/AuthContext'

export function UserDashboard() {
  const { userId: urlUserId } = useParams()
  const navigate = useNavigate()
  const [activeWindow, setActiveWindow] = useState<'30' | '180'>('30')
  const [activeTab, setActiveTab] = useState<'transactions' | 'insights'>('transactions')
  const [showConsentDialog, setShowConsentDialog] = useState(false)
  const { user } = useAuth() // Get the logged-in user to check their role

  // Auto-redirect regular users to their own dashboard
  // Why: Regular users should only see their own data, not a selector
  useEffect(() => {
    if (!urlUserId && user?.role === 'card_user') {
      // Redirect to their own dashboard
      navigate(`/dashboard/${user.user_id}`, { replace: true })
    }
  }, [urlUserId, user, navigate])

  // Fetch all users for the selector (only for operators to avoid 403)
  // Why: Regular users get 403 on /users endpoint, so we skip the query
  const { data: users, isLoading: usersLoading } = useUsers()

  // Fetch profile data for the selected user
  const windowDays = activeWindow === '30' ? 30 : 180
  const { data: profile, isLoading: profileLoading, error: profileError } = useUserProfile(urlUserId, windowDays)

  // Fetch recommendations for the selected user
  const { data: recommendations, isLoading: recsLoading, error: recsError } = useRecommendations(
    urlUserId, 
    windowDays
  )

  // Fetch transactions for the selected user
  const { data: transactions, isLoading: transactionsLoading } = useTransactions(urlUserId, 100, 0)

  // Process transactions for spending breakdown chart
  // Why: We calculate spending by category to show users where their money goes
  // This only includes debit transactions (spending), not credits (income)
  // Now filters by the selected time window (30 or 180 days) to match the toggle
  const spendingByCategory = useMemo(() => {
    if (!transactions || transactions.length === 0) return []
    
    // Calculate the cutoff date based on the active window
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - windowDays)
    
    const categoryMap = new Map<string, number>()
    
    transactions
      .filter(t => {
        // Only spending, not income
        if (t.transaction_type !== 'debit') return false
        
        // Filter by time window - only include transactions within the selected period
        const transactionDate = new Date(t.transaction_date)
        return transactionDate >= cutoffDate
      })
      .forEach(transaction => {
        const category = transaction.category || 'Other'
        const currentAmount = categoryMap.get(category) || 0
        categoryMap.set(category, currentAmount + Math.abs(transaction.amount))
      })
    
    return Array.from(categoryMap.entries())
      .map(([category, amount]) => ({ category, amount }))
      .sort((a, b) => b.amount - a.amount) // Sort by amount descending
      .slice(0, 8) // Top 8 categories
  }, [transactions, windowDays])

  // Parse user info - MUST be before any conditional returns to avoid hook order issues
  // Why: React hooks must be called in the same order every render
  const selectedUser = users?.find(u => u.user_id === urlUserId)
  const userInfo = useMemo(() => {
    if (selectedUser) {
      return parseUserInfo(selectedUser.email_masked, selectedUser.user_id)
    }
    
    // Fallback: Parse user_id to create display name
    // e.g., "alice.martinez" → "Alice Martinez"
    if (urlUserId && urlUserId.includes('.')) {
      const parts = urlUserId.split('.')
      const firstName = parts[0].charAt(0).toUpperCase() + parts[0].slice(1)
      const lastName = parts.slice(1).join(' ').split('').map((c, i) => i === 0 ? c.toUpperCase() : c).join('')
      return {
        displayName: `${firstName} ${lastName}`,
        fullName: `${firstName} ${lastName}`,
        firstName,
        lastName,
        email: ''
      }
    }
    
    return urlUserId 
      ? { displayName: urlUserId, email: '', fullName: urlUserId, firstName: urlUserId, lastName: '' }
      : null
  }, [selectedUser, urlUserId])

  // Consent mutations
  const grantConsent = useGrantConsent()
  const revokeConsent = useRevokeConsent()

  // Check if user needs consent (403 error on profile or recommendations)
  const needsConsent = (profileError instanceof HttpError && profileError.status === 403) ||
                       (recsError instanceof HttpError && recsError.status === 403)

  // Handle tab change - show consent dialog if switching to insights without consent
  const handleTabChange = (newTab: string) => {
    if (newTab === 'insights') {
      // Always check consent status when switching to insights
      // Why: Even if we have cached data, user might have revoked consent
      if (needsConsent) {
        setShowConsentDialog(true)
        // Don't switch tabs yet - wait for consent
        return
      }
    }
    setActiveTab(newTab as 'transactions' | 'insights')
  }

  // Handle consent grant
  const handleGrantConsent = async () => {
    if (!urlUserId) return
    await grantConsent.mutateAsync({ userId: urlUserId, reason: 'Accessing insights', by: 'user_dashboard' })
    setShowConsentDialog(false)
    setActiveTab('insights')
  }

  // Handle consent revoke
  const handleRevokeConsent = async () => {
    if (!urlUserId) return
    await revokeConsent.mutateAsync({ userId: urlUserId, reason: 'User revoked consent', by: 'user_dashboard' })
    setActiveTab('transactions') // Redirect to transactions tab
  }

  // If consent is needed and user switches back to transactions tab, reset
  useEffect(() => {
    if (needsConsent && activeTab === 'insights') {
      setActiveTab('transactions')
    }
  }, [needsConsent])

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
                  {users?.map((user) => {
                    const userInfo = parseUserInfo(user.email_masked, user.user_id)
                    return (
                      <SelectItem key={user.user_id} value={user.user_id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{userInfo.displayName}</span>
                          {userInfo.email && (
                            <span className="text-xs text-muted-foreground">{userInfo.email}</span>
                          )}
                        </div>
                      </SelectItem>
                    )
                  })}
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
      {/* Consent dialog shown when user tries to access insights without consent */}
      <Dialog open={showConsentDialog} onOpenChange={setShowConsentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Consent to Process Financial Data</DialogTitle>
            <DialogDescription className="space-y-3">
              <p>
                To generate behavioral insights and personalized recommendations, we need your explicit consent 
                to <strong>process and analyze</strong> your transaction data.
              </p>
              <p className="text-sm">
                <strong>What we'll do with consent:</strong>
              </p>
              <ul className="text-sm list-disc list-inside space-y-1 ml-2">
                <li>Detect spending patterns (subscriptions, savings, credit usage)</li>
                <li>Assign you to a behavioral persona for personalized content</li>
                <li>Generate educational recommendations tailored to your financial behavior</li>
              </ul>
              <p className="text-sm text-muted-foreground">
                Your raw transaction data is always available to you. You can revoke this consent at any time.
              </p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowConsentDialog(false)
                setActiveTab('transactions')
              }}
            >
              Not Now
            </Button>
            <Button
              variant="gradient"
              onClick={handleGrantConsent}
              disabled={grantConsent.isPending}
            >
              {grantConsent.isPending ? 'Processing…' : 'I Consent'}
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
                {userInfo?.displayName || urlUserId}
              </p>
              {userInfo?.email && (
                <p className="text-white/70 text-sm mt-1">
                  {userInfo.email}
                </p>
              )}
            </div>
            
            {/* User selector in hero - only show for operators */}
            {/* Why: Regular users should only see their own dashboard, not switch between users */}
            {user?.role === 'operator' && (
              <Select onValueChange={handleUserSelect} value={urlUserId}>
                <SelectTrigger className="w-full md:w-64 bg-white/10 border-white/20 text-white hover:bg-white/20 backdrop-blur-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((user) => {
                    const uInfo = parseUserInfo(user.email_masked, user.user_id)
                    return (
                      <SelectItem key={user.user_id} value={user.user_id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{uInfo.displayName}</span>
                          {uInfo.email && (
                            <span className="text-xs text-muted-foreground">{uInfo.email}</span>
                          )}
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            )}
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
                  <p className="text-white/70 text-sm">Behavioral Signals</p>
                  <p className="text-white text-2xl font-bold">{formatSignalCount(signalsDetected)}</p>
                  <p className="text-white/60 text-xs mt-1">Credit, Income, Savings, Subscriptions</p>
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

      {/* Main tabs: Transactions vs Insights */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full max-w-md grid-cols-2 h-11">
          <TabsTrigger value="transactions" className="text-sm font-medium">
            <Receipt className="h-4 w-4 mr-2" />
            Transactions
          </TabsTrigger>
          <TabsTrigger value="insights" className="text-sm font-medium">
            <Activity className="h-4 w-4 mr-2" />
            Insights
          </TabsTrigger>
        </TabsList>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-6 mt-6">
          <Card className="border-2 shadow-lg overflow-hidden">
            <div className="h-2 bg-gradient-primary" />
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-primary" />
                Transaction History
              </CardTitle>
              <CardDescription>
                Your recent transactions, sorted by date (newest first)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {transactionsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Card key={i} className="animate-pulse">
                      <CardContent className="p-4">
                        <div className="h-16 bg-muted rounded" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : transactions && transactions.length > 0 ? (
                <TransactionList transactions={transactions} />
              ) : (
                <EmptyState
                  icon={Receipt}
                  title="No transactions found"
                  description="Transactions will appear here once they are available"
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-6 mt-6">
          {/* Add revoke consent button at the top of insights tab */}
          {!needsConsent && (
            <div className="flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRevokeConsent}
                disabled={revokeConsent.isPending}
                className="gap-2"
              >
                <ShieldOff className="h-4 w-4" />
                {revokeConsent.isPending ? 'Revoking...' : 'Revoke Consent'}
              </Button>
            </div>
          )}

          {/* Window tabs (30d vs 180d) - inside Insights tab */}
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Credit Utilization - only show if user has credit data */}
            {signals?.credit && (
              <CreditUtilizationGauge 
                utilization={Number(signals.credit.credit_utilization_max_pct || 0)}
                title="Credit Utilization"
                description={`Maximum credit card utilization (past ${windowDays} days)`}
              />
            )}
            
            {/* Spending Breakdown - show for all users with transactions */}
            {spendingByCategory.length > 0 ? (
              <SpendingBreakdownChart 
                data={spendingByCategory}
                title="Spending Breakdown"
                description={`Your spending by category (past ${windowDays} days)`}
              />
            ) : (
              <Card className="flex items-center justify-center">
                <CardContent className="text-center py-12">
                  <CommonIcons.PieChart className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
                  <p className="text-muted-foreground">No spending data yet</p>
                  <p className="text-sm text-muted-foreground mt-1">Spending breakdown will appear once you have transactions</p>
                </CardContent>
              </Card>
            )}
          </div>

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
        </TabsContent>
      </Tabs>
    </div>
  )
}
