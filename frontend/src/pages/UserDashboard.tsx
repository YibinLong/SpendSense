/**
 * User Dashboard Page
 * 
 * Why this exists:
 * - Shows users their behavioral persona and financial signals
 * - Displays personalized recommendations with rationales
 * - Supports both URL routing (/dashboard/:userId) and dropdown selection
 * - Tabs for 30d and 180d windows
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
import { useUsers, useUserProfile, useRecommendations, useGrantConsent, HttpError } from '@/lib/api'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

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

  // If no user selected, show selector
  if (!urlUserId) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>User Dashboard</CardTitle>
            <CardDescription>
              Select a user to view their financial profile and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {usersLoading ? (
              <p className="text-muted-foreground">Loading users...</p>
            ) : (
              <Select onValueChange={handleUserSelect}>
                <SelectTrigger className="w-full">
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

  // Loading state
  if (profileLoading) {
    return (
      <div className="max-w-6xl mx-auto">
        <p className="text-center text-muted-foreground">Loading profile...</p>
      </div>
    )
  }

  // Error state (exclude 403 so we can show consent dialog instead)
  if (profileError && !(profileError instanceof HttpError && profileError.status === 403)) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Profile</CardTitle>
            <CardDescription>
              {profileError.message || 'Unable to load user profile. Please try again.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select onValueChange={handleUserSelect} value={urlUserId}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Choose a different user" />
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
          </CardContent>
        </Card>
      </div>
    )
  }

  // Main dashboard view
  const signals = profile?.signals
  const persona = profile?.persona
  const selectedUser = users?.find(u => u.user_id === urlUserId)

  // Split recommendations into education and offers
  const educationItems = recommendations?.filter(r => r.item_type === 'education') || []
  const offerItems = recommendations?.filter(r => r.item_type === 'offer') || []

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Consent dialog shown when backend blocks with 403 */}
      <Dialog open={(
        (profileError instanceof HttpError && profileError.status === 403) ||
        (recsError instanceof HttpError && recsError.status === 403)
      )}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Consent required</DialogTitle>
            <DialogDescription>
              To view this user's profile and recommendations, you need to grant consent for data processing.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              onClick={() => urlUserId && grantConsent.mutate({ userId: urlUserId, reason: 'Accessing dashboard', by: 'user_dashboard' })}
              disabled={grantConsent.isPending}
            >
              {grantConsent.isPending ? 'Granting…' : 'Grant consent'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Header with user selector */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">User Dashboard</h1>
          <p className="text-muted-foreground">
            Viewing: {urlUserId}
            {selectedUser?.email_masked ? ` (${selectedUser.email_masked})` : ''}
          </p>
        </div>
        <Select onValueChange={handleUserSelect} value={urlUserId}>
          <SelectTrigger className="w-64">
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

      {/* Window tabs (30d vs 180d) */}
      <Tabs value={activeWindow} onValueChange={(v) => setActiveWindow(v as '30' | '180')}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="30">30 Days</TabsTrigger>
          <TabsTrigger value="180">180 Days</TabsTrigger>
        </TabsList>

        <TabsContent value={activeWindow} className="space-y-6 mt-6">
          {/* Persona Badge */}
          <Card>
            <CardHeader>
              <CardTitle>Assigned Persona</CardTitle>
              <CardDescription>
                Based on behavioral patterns over the last {windowDays} days
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PersonaBadge persona={persona} />
              {persona?.criteria_met && (
                <div className="mt-4 text-sm">
                  <p className="font-medium mb-2">Why this persona was assigned:</p>
                  <pre className="bg-muted p-3 rounded text-xs overflow-auto">
                    {JSON.stringify(persona.criteria_met, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Behavioral Signals */}
          <div>
            <h2 className="text-2xl font-bold mb-4">Behavioral Signals</h2>
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
            <h2 className="text-2xl font-bold mb-4">Recommendations</h2>
            
            {recsLoading ? (
              <p className="text-muted-foreground">Loading recommendations...</p>
            ) : (
              <div className="space-y-6">
                {/* Education Items */}
                {educationItems.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold mb-3">Educational Content</h3>
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
                    <h3 className="text-xl font-semibold mb-3">Partner Offers</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {offerItems.slice(0, 3).map((item) => (
                        <RecommendationCard key={item.id} recommendation={item} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty state */}
                {educationItems.length === 0 && offerItems.length === 0 && (
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-center text-muted-foreground">
                        No recommendations available for this window. Check back later.
                      </p>
                    </CardContent>
                  </Card>
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

