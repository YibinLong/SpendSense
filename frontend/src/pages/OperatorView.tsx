/**
 * Operator View Page
 * 
 * Why this exists:
 * - Allows operators to review recommendations for all users
 * - View fairness metrics and demographic analysis
 * - Access evaluation reports (markdown and PDF)
 * - Drill into user details (signals, persona, recommendations)
 * - Approve/reject/flag recommendations with notes
 * - Client-side pagination for ~100 users
 * 
 * Tabs:
 * 1. Review - User review queue and approval workflow
 * 2. Fairness - Demographic analysis and disparity detection
 * 3. Reports - System performance reports and metrics
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
    retry: false, // Don't retry if report doesn't exist
  })

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Operator View</h1>
        <p className="text-muted-foreground">
          Review users, analyze fairness, and view system reports
        </p>
      </div>

      <Tabs defaultValue="review" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="review">Review Queue</TabsTrigger>
          <TabsTrigger value="fairness">Fairness Analysis</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* TAB 1: Review Queue */}
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
        <Card>
          <CardHeader>
            <CardTitle>User Details</CardTitle>
            <CardDescription>
              {selectedUser ? `Viewing ${selectedUser.user_id}` : 'Select a user to view details'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedUser ? (
              <p className="text-center text-muted-foreground py-8">
                Click on a user from the list to view their profile
              </p>
            ) : (
              <div className="space-y-4">
                {/* Persona */}
                <div>
                  <h3 className="font-semibold mb-2">Persona (30d)</h3>
                  <PersonaBadge persona={profile?.persona} />
                </div>

                {/* Quick Signals Overview */}
                <div>
                  <h3 className="font-semibold mb-2">Key Signals</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {profile?.signals?.credit && (
                      <div className="p-2 bg-muted rounded">
                        <span className="text-muted-foreground">Max Util:</span>{' '}
                        <span className="font-medium">
                          {Number(profile.signals.credit.credit_utilization_max_pct).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {profile?.signals?.savings && (
                      <div className="p-2 bg-muted rounded">
                        <span className="text-muted-foreground">Emergency:</span>{' '}
                        <span className="font-medium">
                          {Number(profile.signals.savings.emergency_fund_months).toFixed(1)}mo
                        </span>
                      </div>
                    )}
                    {profile?.signals?.subscriptions && (
                      <div className="p-2 bg-muted rounded">
                        <span className="text-muted-foreground">Subscriptions:</span>{' '}
                        <span className="font-medium">
                          {profile.signals.subscriptions.recurring_merchant_count}
                        </span>
                      </div>
                    )}
                    {profile?.signals?.income && (
                      <div className="p-2 bg-muted rounded">
                        <span className="text-muted-foreground">Cash Buffer:</span>{' '}
                        <span className="font-medium">
                          {Number(profile.signals.income.cashflow_buffer_months).toFixed(1)}mo
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recommendations Section */}
      {selectedUser && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendations for {selectedUser.user_id}</CardTitle>
            <CardDescription>Review and approve/reject recommendations</CardDescription>
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

        {/* TAB 2: Fairness Analysis */}
        <TabsContent value="fairness" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Fairness Metrics</CardTitle>
              <CardDescription>
                Demographic analysis to detect potential bias in persona assignment and recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              {fairnessLoading ? (
                <p className="text-muted-foreground">Loading fairness metrics...</p>
              ) : !fairnessMetrics ? (
                <p className="text-muted-foreground">No fairness metrics available</p>
              ) : (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Total Users</p>
                      <p className="text-2xl font-bold">{fairnessMetrics.total_users_analyzed}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Disparities</p>
                      <p className="text-2xl font-bold">{fairnessMetrics.disparities?.length || 0}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Threshold</p>
                      <p className="text-2xl font-bold">{fairnessMetrics.threshold_pct}%</p>
                    </div>
                  </div>

                  {/* Warnings */}
                  {fairnessMetrics.warnings && fairnessMetrics.warnings.length > 0 && (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                      <h3 className="font-semibold text-amber-900 mb-2">⚠️ Fairness Warnings</h3>
                      <ul className="space-y-1">
                        {fairnessMetrics.warnings.map((warning: string, i: number) => (
                          <li key={i} className="text-sm text-amber-800">• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Demographics Tables */}
                  {fairnessMetrics.demographics && (
                    <div className="space-y-4">
                      {/* Age Range */}
                      {fairnessMetrics.demographics.age_range && (
                        <div>
                          <h3 className="font-semibold mb-2">Age Range Distribution</h3>
                          <div className="border rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                              <thead className="bg-muted">
                                <tr>
                                  <th className="text-left p-2">Age Range</th>
                                  <th className="text-right p-2">Count</th>
                                  <th className="text-right p-2">% of Total</th>
                                  <th className="text-right p-2">Education Recs</th>
                                  <th className="text-right p-2">Offer Recs</th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(fairnessMetrics.demographics.age_range).map(([age, data]: [string, any]) => (
                                  <tr key={age} className="border-t">
                                    <td className="p-2">{age}</td>
                                    <td className="text-right p-2">{data.count}</td>
                                    <td className="text-right p-2">{data.pct_of_total}%</td>
                                    <td className="text-right p-2">{data.education_recs}</td>
                                    <td className="text-right p-2">{data.offer_recs}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Gender */}
                      {fairnessMetrics.demographics.gender && (
                        <div>
                          <h3 className="font-semibold mb-2">Gender Distribution</h3>
                          <div className="border rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                              <thead className="bg-muted">
                                <tr>
                                  <th className="text-left p-2">Gender</th>
                                  <th className="text-right p-2">Count</th>
                                  <th className="text-right p-2">% of Total</th>
                                  <th className="text-right p-2">Education Recs</th>
                                  <th className="text-right p-2">Offer Recs</th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(fairnessMetrics.demographics.gender).map(([gender, data]: [string, any]) => (
                                  <tr key={gender} className="border-t">
                                    <td className="p-2">{gender}</td>
                                    <td className="text-right p-2">{data.count}</td>
                                    <td className="text-right p-2">{data.pct_of_total}%</td>
                                    <td className="text-right p-2">{data.education_recs}</td>
                                    <td className="text-right p-2">{data.offer_recs}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB 3: Reports */}
        <TabsContent value="reports" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Evaluation Reports</CardTitle>
              <CardDescription>
                System performance metrics and executive summaries
              </CardDescription>
            </CardHeader>
            <CardContent>
              {reportLoading ? (
                <p className="text-muted-foreground">Loading report...</p>
              ) : !reportData ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">
                    No report available. Generate one by running:
                  </p>
                  <code className="bg-muted px-3 py-1 rounded text-sm">
                    python run_metrics.py --report
                  </code>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Report metadata */}
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium">Latest Report</p>
                      <p className="text-sm text-muted-foreground">
                        Generated: {new Date(reportData.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <Button
                      onClick={() => {
                        window.open(`${import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'}/operator/reports/latest/pdf`, '_blank')
                      }}
                    >
                      Download PDF
                    </Button>
                  </div>

                  {/* Markdown content (simplified rendering) */}
                  <div className="border rounded-lg p-6 prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap font-sans text-sm">
                      {reportData.content}
                    </pre>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
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

