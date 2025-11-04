/**
 * Operator View Page - Modern UI Redesign
 * 
 * Why this exists:
 * - Allows operators to review recommendations for all users with modern interface
 * - View fairness metrics and demographic analysis with charts
 * - Access evaluation reports
 * - Drill into user details (signals, persona, recommendations)
 * - Approve/reject/flag recommendations with intuitive workflow
 * - Client-side pagination with modern controls
 * 
 * Modern Features:
 * - Enhanced table design with striped rows and hover effects
 * - Color-coded status indicators (green, yellow, red)
 * - Icons for all actions
 * - Charts for fairness metrics
 * - Better pagination controls
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
import { TableSkeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/EmptyState'
import { PersonaDistributionChart } from '@/components/charts/PersonaDistributionChart'
import { getStatusIcon } from '@/lib/iconMap'
import { CommonIcons } from '@/lib/iconMap'
import { 
  useUsers, 
  useUserProfile, 
  useRecommendations, 
  useApproveRecommendation,
  type User,
  type RecommendationItem,
  apiClient
} from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { ChevronLeft, ChevronRight, Search } from 'lucide-react'

const ITEMS_PER_PAGE = 10

export function OperatorView() {
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

  // User list columns
  const userColumns = [
    {
      header: 'User ID',
      accessor: (user: User) => <span className="font-medium">{user.user_id}</span>,
    },
    {
      header: 'Email',
      accessor: (user: User) => (
        <span className="text-muted-foreground">{user.email_masked || 'N/A'}</span>
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

  // Recommendation columns with status colors
  const recommendationColumns = [
    {
      header: 'Title',
      accessor: (rec: RecommendationItem) => (
        <div>
          <div className="font-medium">{rec.title}</div>
          <div className="text-xs text-muted-foreground capitalize">{rec.item_type}</div>
        </div>
      ),
    },
    {
      header: 'Status',
      accessor: (rec: RecommendationItem) => {
        const StatusIcon = getStatusIcon(rec.status || 'pending')
        const statusColors = {
          approved: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
          rejected: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
          flagged: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
        }
        return (
          <Badge 
            variant="secondary" 
            className={cn(
              'flex items-center gap-1 w-fit',
              statusColors[rec.status as keyof typeof statusColors] || statusColors.pending
            )}
          >
            <StatusIcon className="h-3 w-3" />
            {rec.status || 'pending'}
          </Badge>
        )
      },
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
          className="flex items-center gap-1"
        >
          <CommonIcons.Eye className="h-3 w-3" />
          Review
        </Button>
      ),
    },
  ]

  // Fetch fairness metrics
  const { data: fairnessMetrics, isLoading: fairnessLoading } = useQuery({
    queryKey: ['fairness'],
    queryFn: async () => {
      const response = await apiClient['fetch']<any>('/operator/fairness')
      return response
    },
    staleTime: 5 * 60 * 1000,
  })

  // Fetch latest report
  const { data: reportData, isLoading: reportLoading } = useQuery({
    queryKey: ['report'],
    queryFn: async () => {
      const response = await apiClient['fetch']<any>('/operator/reports/latest')
      return response
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header with gradient */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 p-8 shadow-lg">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="relative z-10">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <CommonIcons.Users className="h-8 w-8" />
            Operator View
          </h1>
          <p className="text-white/90">
            Review user profiles, approve recommendations, and monitor system fairness
          </p>
        </div>
      </div>

      {/* Review dialog with modern styling */}
      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Recommendation</DialogTitle>
            <DialogDescription>
              Approve, reject, or flag this recommendation for the user
            </DialogDescription>
          </DialogHeader>

          {selectedRecommendation && (
            <div className="space-y-4 py-4">
              <div className="rounded-lg border bg-muted/50 p-4">
                <h4 className="font-semibold mb-1">{selectedRecommendation.title}</h4>
                <p className="text-sm text-muted-foreground">{selectedRecommendation.description}</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Decision</label>
                <Select value={reviewStatus} onValueChange={(v: any) => setReviewStatus(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="approved">
                      <span className="flex items-center gap-2">
                        <CommonIcons.CheckCircle className="h-4 w-4 text-green-600" />
                        Approve
                      </span>
                    </SelectItem>
                    <SelectItem value="rejected">
                      <span className="flex items-center gap-2">
                        <CommonIcons.XCircle className="h-4 w-4 text-red-600" />
                        Reject
                      </span>
                    </SelectItem>
                    <SelectItem value="flagged">
                      <span className="flex items-center gap-2">
                        <CommonIcons.Flag className="h-4 w-4 text-orange-600" />
                        Flag for Review
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Notes (optional)</label>
                <textarea
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Add any notes or reasoning..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setReviewDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="gradient" onClick={handleSubmitReview}>
              Submit Review
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Main tabs */}
      <Tabs defaultValue="review">
        <TabsList className="grid w-full max-w-md grid-cols-3 h-11">
          <TabsTrigger value="review" className="flex items-center gap-2">
            <CommonIcons.CheckCircle className="h-4 w-4" />
            Review
          </TabsTrigger>
          <TabsTrigger value="fairness" className="flex items-center gap-2">
            <CommonIcons.BarChart3 className="h-4 w-4" />
            Fairness
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center gap-2">
            <CommonIcons.Activity className="h-4 w-4" />
            Reports
          </TabsTrigger>
        </TabsList>

        {/* Review Tab */}
        <TabsContent value="review" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* User list */}
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CommonIcons.Users className="h-5 w-5 text-primary" />
                    Users
                  </CardTitle>
                  <CardDescription>
                    {filteredUsers.length} user{filteredUsers.length !== 1 ? 's' : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Search */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users..."
                      value={searchQuery}
                      onChange={(e) => {
                        setSearchQuery(e.target.value)
                        setCurrentPage(1)
                      }}
                      className="pl-9"
                    />
                  </div>

                  {/* User list with modern styling */}
                  {usersLoading ? (
                    <TableSkeleton rows={5} />
                  ) : paginatedUsers.length > 0 ? (
                    <div className="space-y-2">
                      {paginatedUsers.map((user) => (
                        <button
                          key={user.user_id}
                          onClick={() => handleUserClick(user)}
                          className={cn(
                            "w-full text-left p-3 rounded-lg border transition-all hover:shadow-md",
                            selectedUser?.user_id === user.user_id
                              ? "border-primary bg-primary/5 shadow-sm"
                              : "border-border hover:border-primary/50"
                          )}
                        >
                          <div className="font-medium text-sm">{user.user_id}</div>
                          {user.email_masked && (
                            <div className="text-xs text-muted-foreground">{user.email_masked}</div>
                          )}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={CommonIcons.Search}
                      title="No users found"
                      description="Try adjusting your search query"
                    />
                  )}

                  {/* Pagination controls */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between pt-2 border-t">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        Page {currentPage} of {totalPages}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* User details */}
            <div className="lg:col-span-2">
              {selectedUser ? (
                <div className="space-y-6">
                  <Card>
                    <div className="h-2 bg-gradient-primary rounded-t-lg" />
                    <CardHeader>
                      <CardTitle>Profile: {selectedUser.user_id}</CardTitle>
                      <CardDescription>
                        Behavioral signals and assigned persona
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <PersonaBadge persona={profile?.persona} />
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        {profile?.signals && (
                          <>
                            <SignalCard
                              title="Credit"
                              description="Utilization & behavior"
                              data={profile.signals.credit}
                              type="credit"
                            />
                            <SignalCard
                              title="Savings"
                              description="Growth & emergency fund"
                              data={profile.signals.savings}
                              type="savings"
                            />
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Recommendations table */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <CommonIcons.Gift className="h-5 w-5 text-primary" />
                        Recommendations
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {recommendations && recommendations.length > 0 ? (
                        <DataTable
                          data={recommendations}
                          columns={recommendationColumns}
                          onRowClick={(rec) => handleReviewClick(rec)}
                        />
                      ) : (
                        <EmptyState
                          icon={CommonIcons.Inbox}
                          title="No recommendations"
                          description="This user has no recommendations yet"
                        />
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <EmptyState
                  icon={CommonIcons.Users}
                  title="Select a user"
                  description="Choose a user from the list to view their profile and recommendations"
                />
              )}
            </div>
          </div>
        </TabsContent>

        {/* Fairness Tab with Charts */}
        <TabsContent value="fairness" className="space-y-6 mt-6">
          {fairnessLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-muted-foreground">Loading fairness metrics...</p>
            </div>
          ) : fairnessMetrics ? (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-primary">
                      {fairnessMetrics.total_users || 'N/A'}
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-muted-foreground">Demographics Tracked</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-primary">
                      {fairnessMetrics.demographics ? Object.keys(fairnessMetrics.demographics).length : 0}
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-muted-foreground">Personas Assigned</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-primary">
                      {fairnessMetrics.total_personas || 'N/A'}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Demographics Breakdown */}
              {fairnessMetrics.demographics && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(fairnessMetrics.demographics).map(([key, value]: [string, any]) => (
                    <Card key={key}>
                      <CardHeader>
                        <CardTitle className="capitalize">{key.replace('_', ' ')}</CardTitle>
                        <CardDescription>Distribution and persona breakdown</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {Object.entries(value).map(([subKey, subValue]: [string, any]) => (
                          <div key={subKey} className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium capitalize">{subKey.replace('_', ' ')}</span>
                              <span className="text-sm text-muted-foreground">
                                {subValue.count} users ({subValue.pct_of_total?.toFixed(1)}%)
                              </span>
                            </div>
                            
                            {subValue.personas && (
                              <div className="pl-4 space-y-1">
                                {Object.entries(subValue.personas).map(([persona, count]: [string, any]) => (
                                  <div key={persona} className="flex justify-between text-xs">
                                    <span className="text-muted-foreground capitalize">
                                      {persona.replace('_', ' ')}
                                    </span>
                                    <span className="font-medium">{count}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                            
                            {subValue.education_recs !== undefined && (
                              <div className="flex justify-between text-xs pt-1 border-t">
                                <span className="text-muted-foreground">Education recommendations</span>
                                <span className="font-medium">{subValue.education_recs}</span>
                              </div>
                            )}
                            
                            {subValue.offer_recs !== undefined && (
                              <div className="flex justify-between text-xs">
                                <span className="text-muted-foreground">Offer recommendations</span>
                                <span className="font-medium">{subValue.offer_recs}</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <EmptyState
              icon={CommonIcons.BarChart3}
              title="No fairness data"
              description="Fairness metrics are not yet available"
            />
          )}
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-6 mt-6">
          {reportLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-muted-foreground">Loading latest report...</p>
            </div>
          ) : reportData ? (
            <div className="space-y-6">
              {/* Report Header */}
              <Card>
                <CardHeader>
                  <CardTitle>Latest Evaluation Report</CardTitle>
                  <CardDescription>
                    Generated: {reportData.timestamp ? new Date(reportData.timestamp).toLocaleString() : 'N/A'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {reportData.content && (
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap bg-muted p-4 rounded-lg text-sm leading-relaxed">
                        {reportData.content}
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Additional metrics if available */}
              {reportData.exists !== undefined && (
                <Card>
                  <CardHeader>
                    <CardTitle>Report Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        "h-3 w-3 rounded-full",
                        reportData.exists ? "bg-green-500" : "bg-gray-400"
                      )} />
                      <span className="text-sm">
                        {reportData.exists ? "Report exists and is valid" : "Report not found"}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <EmptyState
              icon={CommonIcons.Activity}
              title="No reports available"
              description="Evaluation reports will appear here once generated"
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Dev Debug Panel */}
      <DevDebugPanel
        title="Operator Debug Data"
        data={{ selectedUser, profile, recommendations, fairnessMetrics }}
      />
    </div>
  )
}
