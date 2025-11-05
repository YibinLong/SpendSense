/**
 * Operator View Page
 * 
 * Why this exists:
 * - Allows operators to review recommendations for all users
 * - Monitor fairness metrics across demographics
 * - View system performance reports
 * - Approve/reject/flag recommendations with notes
 * - Client-side pagination for ~100 users
 * - Dev-only decision traces
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { DataTable } from '@/components/DataTable'
import { PersonaBadge } from '@/components/PersonaBadge'
import { SignalCard } from '@/components/SignalCard'
import { DevDebugPanel } from '@/components/DevDebugPanel'
import { DemographicPieChart } from '@/components/charts/DemographicPieChart'
import { DemographicBreakdownChart } from '@/components/charts/DemographicBreakdownChart'
import { RecommendationDistributionChart } from '@/components/charts/RecommendationDistributionChart'
import { 
  useUsers, 
  useUserProfile, 
  useRecommendations, 
  useApproveRecommendation,
  useFairnessMetrics,
  useOperatorMetrics,
  type User,
  type RecommendationItem
} from '@/lib/api'
import { CheckCircle2, AlertCircle } from 'lucide-react'

const ITEMS_PER_PAGE = 10

export function OperatorView() {
  const [activeTab, setActiveTab] = useState('review')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedRecommendation, setSelectedRecommendation] = useState<RecommendationItem | null>(null)
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false)
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'rejected' | 'flagged'>('approved')
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewerName, setReviewerName] = useState('operator_default')

  // Fetch all users
  const { data: users, isLoading: usersLoading } = useUsers()

  // Fetch selected user's profile (30d by default for operator view)
  const { data: profile } = useUserProfile(selectedUser?.user_id, 30)
  const { data: recommendations } = useRecommendations(selectedUser?.user_id, 30)

  // Fetch fairness and metrics data
  const { data: fairnessMetrics, isLoading: fairnessLoading } = useFairnessMetrics()
  const { data: operatorMetrics, isLoading: metricsLoading } = useOperatorMetrics()

  // Mutation for approving/rejecting recommendations
  const approveRecommendation = useApproveRecommendation()

  // Filter and paginate users
  const filteredUsers = users?.filter((user) =>
    user.user_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email_masked?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const totalPages = Math.ceil(filteredUsers.length / ITEMS_PER_PAGE)
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  // Handle user selection
  const handleUserClick = (user: User) => {
    setSelectedUser(user)
  }

  // Handle opening review dialog
  const handleReviewClick = (recommendation: RecommendationItem) => {
    setSelectedRecommendation(recommendation)
    setReviewDialogOpen(true)
    setReviewStatus('approved')
    setReviewNotes('')
  }

  // Handle submitting review
  const handleSubmitReview = async () => {
    if (!selectedRecommendation) return

    await approveRecommendation.mutateAsync({
      recommendationId: selectedRecommendation.id,
      approval: {
        status: reviewStatus,
        reviewer: reviewerName,
        notes: reviewNotes || undefined,
      },
    })

    setReviewDialogOpen(false)
    setSelectedRecommendation(null)
  }

  // Helper function to convert user_id to display name
  const formatUserName = (userId: string) => {
    return userId
      .split('.')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  // User list columns
  const userColumns = [
    {
      header: 'User ID',
      accessor: (user: User) => <span className="font-medium">{formatUserName(user.user_id)}</span>,
    },
    {
      header: 'Email',
      accessor: (user: User) => (
        <span className="text-muted-foreground">{user.user_id}@example.com</span>
      ),
    },
    {
      header: 'Created',
      accessor: (user: User) => (
        <span className="text-sm text-muted-foreground">
          {new Date(user.created_at).toLocaleDateString()}
        </span>
      ),
    },
  ]

  // Recommendation columns
  const recommendationColumns = [
    {
      header: 'Title',
      accessor: (rec: RecommendationItem) => (
        <div>
          <div className="font-medium">{rec.title}</div>
          <div className="text-xs text-muted-foreground">{rec.item_type}</div>
        </div>
      ),
    },
    {
      header: 'Status',
      accessor: (rec: RecommendationItem) => (
        <Badge variant={rec.status === 'approved' ? 'default' : 'secondary'}>
          {rec.status}
        </Badge>
      ),
    },
    {
      header: 'Actions',
      accessor: (rec: RecommendationItem) => (
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => {
            e.stopPropagation()
            handleReviewClick(rec)
          }}
          disabled={rec.status !== 'pending'}
        >
          Review
        </Button>
      ),
    },
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-500 text-white p-8 rounded-lg">
        <div className="flex items-center gap-3 mb-2">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h1 className="text-3xl font-bold">Operator View</h1>
        </div>
        <p className="text-purple-100">
          Review user profiles, approve recommendations, and monitor system fairness
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="review" className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Review
          </TabsTrigger>
          <TabsTrigger value="fairness" className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Fairness
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Reports
          </TabsTrigger>
        </TabsList>

        {/* Review Tab */}
        <TabsContent value="review" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Panel: User List */}
            <Card>
              <CardHeader>
                <CardTitle>Users ({filteredUsers.length})</CardTitle>
                <CardDescription>Select a user to view details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Search */}
                <Input
                  placeholder="Search by user ID or email..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setCurrentPage(1)
                  }}
                />

                {/* User Table */}
                {usersLoading ? (
                  <p className="text-muted-foreground">Loading users...</p>
                ) : (
                  <>
                    <DataTable
                      data={paginatedUsers}
                      columns={userColumns}
                      onRowClick={handleUserClick}
                      emptyMessage="No users found"
                    />

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-between pt-4">
                        <p className="text-sm text-muted-foreground">
                          Page {currentPage} of {totalPages}
                        </p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                          >
                            Previous
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                          >
                            Next
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Right Panel: User Details */}
            <div className="space-y-6">
              {/* Profile Card */}
              <Card>
                <CardHeader>
                  <CardTitle>
                    Profile: {selectedUser ? formatUserName(selectedUser.user_id) : 'Select a user'}
                  </CardTitle>
                  <CardDescription>
                    Behavioral signals and assigned persona
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!selectedUser ? (
                    <p className="text-center text-muted-foreground py-8">
                      Click on a user from the list to view their profile
                    </p>
                  ) : (
                    <div className="space-y-6">
                      {/* Persona */}
                      <div>
                        <h3 className="text-sm font-semibold mb-3">Persona (30d)</h3>
                        <PersonaBadge persona={profile?.persona} />
                      </div>

                      {/* Key Signals - Card Grid */}
                      <div>
                        <h3 className="text-sm font-semibold mb-3">Key Signals</h3>
                        <div className="grid grid-cols-2 gap-3">
                          {profile?.signals?.credit && (
                            <div className="p-4 border rounded-lg bg-background">
                              <div className="text-xs text-muted-foreground mb-1">Max Util</div>
                              <div className="text-2xl font-bold">
                                {Number(profile.signals.credit.credit_utilization_max_pct).toFixed(1)}%
                              </div>
                            </div>
                          )}
                          {profile?.signals?.savings && (
                            <div className="p-4 border rounded-lg bg-background">
                              <div className="text-xs text-muted-foreground mb-1">Emergency</div>
                              <div className="text-2xl font-bold">
                                {Number(profile.signals.savings.emergency_fund_months).toFixed(1)}mo
                              </div>
                            </div>
                          )}
                          {profile?.signals?.subscriptions && (
                            <div className="p-4 border rounded-lg bg-background">
                              <div className="text-xs text-muted-foreground mb-1">Subscriptions</div>
                              <div className="text-2xl font-bold">
                                {profile.signals.subscriptions.recurring_merchant_count}
                              </div>
                            </div>
                          )}
                          {profile?.signals?.income && (
                            <div className="p-4 border rounded-lg bg-background">
                              <div className="text-xs text-muted-foreground mb-1">Cash Buffer</div>
                              <div className="text-2xl font-bold">
                                {Number(profile.signals.income.cashflow_buffer_months).toFixed(1)}mo
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recommendations Card */}
              {selectedUser && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <CardTitle>Recommendations</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {!recommendations || recommendations.length === 0 ? (
                      <p className="text-center text-muted-foreground py-4">
                        No recommendations available for this user
                      </p>
                    ) : (
                      <DataTable
                        data={recommendations}
                        columns={recommendationColumns}
                        emptyMessage="No recommendations"
                      />
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Full Signal Details (collapsible) */}
          {selectedUser && profile && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold">Detailed Signals</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SignalCard
                  title="Subscriptions"
                  description="Recurring payment patterns"
                  data={profile.signals?.subscriptions}
                  type="subscriptions"
                />
                <SignalCard
                  title="Savings"
                  description="Savings growth and emergency fund"
                  data={profile.signals?.savings}
                  type="savings"
                />
                <SignalCard
                  title="Credit"
                  description="Credit utilization and behavior"
                  data={profile.signals?.credit}
                  type="credit"
                />
                <SignalCard
                  title="Income Stability"
                  description="Payroll frequency and cash buffer"
                  data={profile.signals?.income}
                  type="income"
                />
              </div>
            </div>
          )}

          {/* Dev Debug Panel */}
          {selectedUser && (
            <DevDebugPanel
              title="Operator Debug Data"
              data={{ user: selectedUser, profile, recommendations }}
            />
          )}
        </TabsContent>

        {/* Fairness Tab */}
        <TabsContent value="fairness" className="space-y-6">
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Total Users</CardDescription>
                  <CardTitle className="text-3xl">
                    {fairnessMetrics?.total_users_analyzed || 0}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    {fairnessMetrics?.total_users_analyzed || 0} with full coverage
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Demographics Tracked</CardDescription>
                  <CardTitle className="text-3xl">
                    {fairnessMetrics?.demographics ? Object.keys(fairnessMetrics.demographics).length : 0}
                  </CardTitle>
                </CardHeader>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Personas Assigned</CardDescription>
                  <CardTitle className="text-3xl">
                    {fairnessMetrics?.total_users_analyzed || 0}
                  </CardTitle>
                </CardHeader>
              </Card>
            </div>

            {/* Demographic Pie Charts */}
            {fairnessLoading ? (
              <p className="text-center text-muted-foreground py-8">Loading fairness metrics...</p>
            ) : fairnessMetrics?.demographics ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {fairnessMetrics.demographics.age_range && (
                  <DemographicPieChart
                    title="Age Distribution"
                    description="User distribution by age range"
                    data={fairnessMetrics.demographics.age_range}
                  />
                )}
                {fairnessMetrics.demographics.gender && (
                  <DemographicPieChart
                    title="Gender Distribution"
                    description="User distribution by gender"
                    data={fairnessMetrics.demographics.gender}
                  />
                )}
                {fairnessMetrics.demographics.ethnicity && (
                  <DemographicPieChart
                    title="Ethnicity Distribution"
                    description="User distribution by ethnicity"
                    data={fairnessMetrics.demographics.ethnicity}
                  />
                )}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">No fairness data available</p>
            )}

            {/* Demographic Breakdown Charts with Personas */}
            {fairnessMetrics?.demographics && (
              <div className="space-y-6">
                {fairnessMetrics.demographics.age_range && (
                  <DemographicBreakdownChart
                    title="Age Range Breakdown"
                    description="Persona distribution across age groups"
                    data={fairnessMetrics.demographics.age_range}
                  />
                )}
                {fairnessMetrics.demographics.gender && (
                  <DemographicBreakdownChart
                    title="Gender Breakdown"
                    description="Persona distribution across genders"
                    data={fairnessMetrics.demographics.gender}
                  />
                )}
                {fairnessMetrics.demographics.ethnicity && (
                  <DemographicBreakdownChart
                    title="Ethnicity Breakdown"
                    description="Persona distribution across ethnicities"
                    data={fairnessMetrics.demographics.ethnicity}
                  />
                )}
              </div>
            )}

            {/* Recommendation Distribution by Demographics */}
            {fairnessMetrics?.demographics && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold">Recommendation Distribution</h2>
                <p className="text-sm text-muted-foreground -mt-4">
                  Education vs offer recommendations by demographic group
                </p>
                
                {fairnessMetrics.demographics.age_range && (
                  <RecommendationDistributionChart
                    title="Age - Recommendations"
                    description="Education vs offer recommendations by age"
                    data={fairnessMetrics.demographics.age_range}
                  />
                )}
                {fairnessMetrics.demographics.gender && (
                  <RecommendationDistributionChart
                    title="Gender - Recommendations"
                    description="Education vs offer recommendations by gender"
                    data={fairnessMetrics.demographics.gender}
                  />
                )}
                {fairnessMetrics.demographics.ethnicity && (
                  <RecommendationDistributionChart
                    title="Ethnicity - Recommendations"
                    description="Education vs offer recommendations by ethnicity"
                    data={fairnessMetrics.demographics.ethnicity}
                  />
                )}
              </div>
            )}

            {/* Disparity Warnings */}
            {fairnessMetrics?.disparities && fairnessMetrics.disparities.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-600">
                    <AlertCircle className="w-5 h-5" />
                    Disparity Warnings
                  </CardTitle>
                  <CardDescription>
                    Groups with potential under/over-representation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {fairnessMetrics.disparities.map((disparity: any, idx: number) => (
                      <div key={idx} className="p-3 bg-orange-50 dark:bg-orange-950 border border-orange-200 dark:border-orange-800 rounded">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-orange-600 mt-0.5" />
                          <div>
                            <p className="font-medium text-sm capitalize">
                              {disparity.demographic}: {disparity.group}
                            </p>
                            <p className="text-xs text-muted-foreground">{disparity.issue}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-6">
          {metricsLoading ? (
            <p className="text-center text-muted-foreground py-8">Loading metrics...</p>
          ) : operatorMetrics ? (
            <>
              {/* Coverage Metrics */}
              {operatorMetrics.coverage && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      <CardTitle>Coverage Metrics</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <CardDescription>Total Users</CardDescription>
                            {operatorMetrics.coverage.total_users >= 50 && (
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                            )}
                          </div>
                          <CardTitle className="text-3xl">
                            {operatorMetrics.coverage.total_users || 0}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-xs text-muted-foreground">
                            {operatorMetrics.coverage.users_with_full_coverage || 0} with full coverage
                          </p>
                        </CardContent>
                      </Card>

                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <CardDescription>Users with Persona</CardDescription>
                            {operatorMetrics.coverage.coverage_persona_pct >= 80 && (
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                            )}
                          </div>
                          <CardTitle className="text-3xl">
                            {operatorMetrics.coverage.users_with_persona || 0}/{operatorMetrics.coverage.total_users || 0}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-xs text-muted-foreground">
                            {operatorMetrics.coverage.coverage_persona_pct?.toFixed(1) || 0}%
                          </p>
                        </CardContent>
                      </Card>

                      <Card className="border-2">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <CardDescription>Users with ≥3 Signals</CardDescription>
                            {operatorMetrics.coverage.coverage_signals_pct >= 80 && (
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                            )}
                          </div>
                          <CardTitle className="text-3xl">
                            {operatorMetrics.coverage.users_with_3plus_signals || 0}/{operatorMetrics.coverage.total_users || 0}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-xs text-muted-foreground">
                            {operatorMetrics.coverage.coverage_signals_pct?.toFixed(1) || 0}%
                          </p>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Coverage Breakdown */}
                    <div className="space-y-4">
                      <h3 className="font-semibold">Coverage Breakdown</h3>
                      
                      {/* Persona Coverage */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm">Persona Coverage</span>
                          <span className="text-sm font-medium">
                            {operatorMetrics.coverage.coverage_persona_pct?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${(operatorMetrics.coverage.coverage_persona_pct || 0) >= 80 ? 'bg-green-500' : 'bg-orange-500'}`}
                            style={{ width: `${operatorMetrics.coverage.coverage_persona_pct || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Target: ≥80%</p>
                      </div>

                      {/* Signal Coverage */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm">Signal Coverage</span>
                          <span className="text-sm font-medium">
                            {operatorMetrics.coverage.coverage_signals_pct?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${(operatorMetrics.coverage.coverage_signals_pct || 0) >= 80 ? 'bg-green-500' : 'bg-orange-500'}`}
                            style={{ width: `${operatorMetrics.coverage.coverage_signals_pct || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Target: ≥80%</p>
                      </div>

                      {/* Full Coverage */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm">Full Coverage</span>
                          <span className="text-sm font-medium">
                            {operatorMetrics.coverage.full_coverage_pct?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${operatorMetrics.coverage.full_coverage_pct >= 80 ? 'bg-green-500' : 'bg-orange-500'}`}
                            style={{ width: `${operatorMetrics.coverage.full_coverage_pct || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Target: ≥80%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Explainability & Auditability */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <CardTitle>Explainability & Auditability</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Explainability */}
                    {operatorMetrics.explainability && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                          <h3 className="font-semibold">Explainability</h3>
                        </div>
                        <div className="text-center p-6 bg-muted rounded-lg">
                          <div className="text-5xl font-bold">
                            {operatorMetrics.explainability.explainability_pct?.toFixed(1) || 0}%
                          </div>
                          <p className="text-sm text-muted-foreground mt-2">
                            {operatorMetrics.explainability.recommendations_with_rationale || 0}/{operatorMetrics.explainability.total_recommendations || 0} recommendations with rationale
                          </p>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${(operatorMetrics.explainability.explainability_pct || 0) >= 90 ? 'bg-green-500' : 'bg-orange-500'}`}
                            style={{ width: `${operatorMetrics.explainability.explainability_pct || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">Target: ≥90%</p>
                      </div>
                    )}

                    {/* Auditability */}
                    {operatorMetrics.auditability && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                          </svg>
                          <h3 className="font-semibold">Auditability</h3>
                        </div>
                        <div className="text-center p-6 bg-muted rounded-lg">
                          <div className="text-5xl font-bold">
                            {operatorMetrics.auditability.auditability_pct?.toFixed(1) || 0}%
                          </div>
                          <p className="text-sm text-muted-foreground mt-2">
                            {operatorMetrics.auditability.recommendations_with_traces || 0}/{operatorMetrics.auditability.total_recommendations || 0} with decision traces
                          </p>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${(operatorMetrics.auditability.auditability_pct || 0) >= 90 ? 'bg-green-500' : 'bg-orange-500'}`}
                            style={{ width: `${operatorMetrics.auditability.auditability_pct || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">Target: ≥90%</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Latency Metrics */}
              {operatorMetrics.latency && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <CardTitle>Latency Metrics</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Latency Statistics Chart */}
                      <div className="space-y-3">
                        <h3 className="font-semibold">Latency Statistics</h3>
                        <p className="text-xs text-muted-foreground">
                          Sample size: {operatorMetrics.latency.sample_size || 0} users
                        </p>
                        <div className="h-48 flex items-end justify-around gap-2 px-4">
                          <div className="flex flex-col items-center gap-2 flex-1">
                            <div 
                              className="w-full bg-green-500 rounded-t"
                              style={{ height: `${((operatorMetrics.latency.min_latency_s || 0) / (operatorMetrics.latency.max_latency_s || 1)) * 100}%`, minHeight: '20px' }}
                            />
                            <div className="text-center">
                              <div className="text-xs text-muted-foreground">Min</div>
                              <div className="text-sm font-medium">{((operatorMetrics.latency.min_latency_s || 0) * 1000).toFixed(1)}ms</div>
                            </div>
                          </div>
                          <div className="flex flex-col items-center gap-2 flex-1">
                            <div 
                              className="w-full bg-blue-500 rounded-t"
                              style={{ height: `${((operatorMetrics.latency.avg_latency_s || 0) / (operatorMetrics.latency.max_latency_s || 1)) * 100}%`, minHeight: '30px' }}
                            />
                            <div className="text-center">
                              <div className="text-xs text-muted-foreground">Avg</div>
                              <div className="text-sm font-medium">{((operatorMetrics.latency.avg_latency_s || 0) * 1000).toFixed(1)}ms</div>
                            </div>
                          </div>
                          <div className="flex flex-col items-center gap-2 flex-1">
                            <div 
                              className="w-full bg-purple-500 rounded-t"
                              style={{ height: `${((operatorMetrics.latency.median_latency_s || 0) / (operatorMetrics.latency.max_latency_s || 1)) * 100}%`, minHeight: '30px' }}
                            />
                            <div className="text-center">
                              <div className="text-xs text-muted-foreground">Median</div>
                              <div className="text-sm font-medium">{((operatorMetrics.latency.median_latency_s || 0) * 1000).toFixed(1)}ms</div>
                            </div>
                          </div>
                          <div className="flex flex-col items-center gap-2 flex-1">
                            <div 
                              className="w-full bg-red-500 rounded-t"
                              style={{ height: '100%' }}
                            />
                            <div className="text-center">
                              <div className="text-xs text-muted-foreground">Max</div>
                              <div className="text-sm font-medium">{((operatorMetrics.latency.max_latency_s || 0) * 1000).toFixed(1)}ms</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Performance Target */}
                      <div className="space-y-4">
                        <h3 className="font-semibold">Performance Target</h3>
                        <div className="text-center p-6 bg-muted rounded-lg">
                          <div className="text-5xl font-bold">
                            {operatorMetrics.latency.users_under_5s_pct?.toFixed(1) || 0}%
                          </div>
                          <p className="text-sm text-muted-foreground mt-2">
                            {operatorMetrics.latency.users_under_5s || 0}/{operatorMetrics.latency.sample_size || 0} users under 5s
                          </p>
                        </div>
                        
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm">Target: ≥90% under 5s</span>
                            <span className="text-sm font-medium">
                              {operatorMetrics.latency.users_under_5s_pct?.toFixed(1) || 0}%
                            </span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${(operatorMetrics.latency.users_under_5s_pct || 0) >= 90 ? 'bg-green-500' : 'bg-orange-500'}`}
                              style={{ width: `${operatorMetrics.latency.users_under_5s_pct || 0}%` }}
                            />
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">Target: ≥90%</p>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-4">
                          <div className="text-center">
                            <div className="text-xs text-muted-foreground mb-1">Avg Latency</div>
                            <div className="text-xl font-bold">{((operatorMetrics.latency.avg_latency_s || 0) * 1000).toFixed(1)}ms</div>
                          </div>
                          <div className="text-center">
                            <div className="text-xs text-muted-foreground mb-1">Max Latency</div>
                            <div className="text-xl font-bold">{((operatorMetrics.latency.max_latency_s || 0) * 1000).toFixed(1)}ms</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Metadata */}
              {operatorMetrics.metadata && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Report Metadata</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground">Generated:</span>{' '}
                        <span className="font-medium">
                          {operatorMetrics.metadata.computed_at || 'Invalid Date'}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Latency Sample Size:</span>{' '}
                        <span className="font-medium">{operatorMetrics.metadata.latency_sample_size || 0} users</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-8">
                <p className="text-center text-muted-foreground">
                  No metrics available. Run evaluation first.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Recommendation</DialogTitle>
            <DialogDescription>
              {selectedRecommendation?.title}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Reviewer Name */}
            <div>
              <label className="text-sm font-medium">Reviewer</label>
              <Input
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                placeholder="Enter your operator ID"
              />
            </div>

            {/* Status Selection */}
            <div>
              <label className="text-sm font-medium">Decision</label>
              <Select
                value={reviewStatus}
                onValueChange={(v) => setReviewStatus(v as 'approved' | 'rejected' | 'flagged')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="approved">Approve</SelectItem>
                  <SelectItem value="rejected">Reject</SelectItem>
                  <SelectItem value="flagged">Flag for Follow-up</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Notes */}
            <div>
              <label className="text-sm font-medium">Notes (optional)</label>
              <Input
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add notes about your decision..."
              />
            </div>

            {/* Rationale Preview */}
            {selectedRecommendation?.rationale && (
              <div className="p-3 bg-muted rounded">
                <p className="text-sm font-medium mb-1">Rationale:</p>
                <p className="text-sm text-muted-foreground">
                  {selectedRecommendation.rationale}
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setReviewDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitReview}
              disabled={!reviewerName || approveRecommendation.isPending}
            >
              {approveRecommendation.isPending ? 'Submitting...' : 'Submit Review'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
