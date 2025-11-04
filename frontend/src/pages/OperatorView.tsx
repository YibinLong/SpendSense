/**
 * Operator View Page
 * 
 * Why this exists:
 * - Allows operators to review recommendations for all users
 * - Drill into user details (signals, persona, recommendations)
 * - Approve/reject/flag recommendations with notes
 * - Client-side pagination for ~100 users
 * - Dev-only decision traces
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
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
  type RecommendationItem
} from '@/lib/api'

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

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Operator View</h1>
        <p className="text-muted-foreground">
          Review user profiles and approve recommendations
        </p>
      </div>

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

