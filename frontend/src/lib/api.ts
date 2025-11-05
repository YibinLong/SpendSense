/**
 * API Client for SpendSense Backend
 * 
 * Why this exists:
 * - Centralizes all API calls with TypeScript types matching backend Pydantic schemas
 * - Handles errors consistently (401 auth, 403 consent/forbidden, 404 not found, 500 server errors)
 * - Provides React Query hooks for automatic caching and refetching
 * - Adds Authorization header with JWT token
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { getToken, clearToken } from './authUtils'

// ============================================================================
// TypeScript Interfaces (matching backend Pydantic schemas)
// ============================================================================

export interface User {
  id: number
  user_id: string
  email_masked?: string | null
  phone_masked?: string | null
  created_at: string
}

export interface PersonaAssignment {
  id: number
  user_id: string
  persona_id: string
  window_days: number
  criteria_met?: Record<string, any> | null
  assigned_at: string
}

export interface SubscriptionSignalData {
  recurring_merchant_count: number
  monthly_recurring_spend: number
  subscription_share_pct: number
}

export interface SavingsSignalData {
  savings_net_inflow: number
  savings_growth_rate_pct: number
  emergency_fund_months: number
}

export interface CreditSignalData {
  credit_utilization_max_pct: number
  credit_utilization_avg_pct: number
  credit_util_flag_30: boolean
  credit_util_flag_50: boolean
  credit_util_flag_80: boolean
  has_interest_charges: boolean
  has_minimum_payment_only: boolean
  is_overdue: boolean
}

export interface IncomeSignalData {
  payroll_deposit_count: number
  median_pay_gap_days: number
  pay_gap_variability: number
  avg_payroll_amount: number
  cashflow_buffer_months: number
}

export interface SignalSummary {
  user_id: string
  window_days: number
  subscriptions?: SubscriptionSignalData | null
  savings?: SavingsSignalData | null
  credit?: CreditSignalData | null
  income?: IncomeSignalData | null
}

export interface RecommendationItem {
  id: number
  user_id: string
  persona_id?: string | null
  window_days: number
  item_type: 'education' | 'offer'
  title: string
  description?: string | null
  url?: string | null
  rationale?: string | null
  eligibility_flags?: Record<string, any> | null
  disclosure?: string | null
  status: string
  created_at: string
}

export interface OperatorReview {
  id: number
  recommendation_id: number
  status: 'approved' | 'rejected' | 'flagged'
  reviewer: string
  notes?: string | null
  decided_at: string
}

export interface UserProfile {
  user_id: string
  window_days: number
  persona?: PersonaAssignment | null
  signals: SignalSummary
}

export interface ApprovalRequest {
  status: 'approved' | 'rejected' | 'flagged'
  reviewer: string
  notes?: string | null
}

export interface ApprovalResponse {
  success: boolean
  message: string
  review_id: number
}

export interface ApiError {
  detail: string
}

export interface ConsentRequest {
  user_id: string
  action: 'opt_in' | 'opt_out'
  reason?: string
  by?: string
}

export interface ConsentResponse {
  success: boolean
  user_id: string
  action: 'opt_in' | 'opt_out'
  message: string
}

export interface Transaction {
  id: number
  transaction_id: string
  account_id: string
  amount: number
  currency: string
  transaction_date: string
  posted_date?: string | null
  merchant_name?: string | null
  category?: string | null
  subcategory?: string | null
  transaction_type: string
  pending: boolean
  payment_channel?: string | null
  created_at: string
}

export class HttpError extends Error {
  status: number
  body: unknown
  constructor(status: number, message: string, body?: unknown) {
    super(message)
    this.status = status
    this.body = body
  }
}

// ============================================================================
// API Client Class
// ============================================================================

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  /**
   * Generic fetch wrapper with error handling and auth.
   * 
   * Why this exists:
   * - Centralizes error handling for 401, 403, 404, 500
   * - Automatically adds Authorization header if token exists
   * - Automatically parses JSON responses
   * - Shows toast notifications for errors
   * - Redirects to login on 401 Unauthorized
   */
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {},
    suppressToast: boolean = false
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    // Add Authorization header if token exists
    const token = getToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      // Handle error responses
      if (!response.ok) {
        const errorBody = await response
          .json()
          .catch(() => ({ detail: 'Unknown error' })) as Partial<ApiError> & Record<string, any>

        const message =
          (typeof errorBody.detail === 'string' && errorBody.detail) ||
          (typeof (errorBody as any).error === 'string' && (errorBody as any).error) ||
          `Request failed with status ${response.status}`

        // Handle different error types (unless toast is suppressed)
        if (!suppressToast) {
          if (response.status === 401) {
            // Unauthorized - clear token and redirect to login
            clearToken()
            toast.error('Session Expired', { description: 'Please log in again' })
            window.location.href = '/login'
          } else if (response.status === 403) {
            toast.error('Access Denied', { description: message })
          } else if (response.status === 404) {
            toast.error('Not Found', { description: message })
          } else if (response.status >= 500) {
            toast.error('Server Error', { description: message })
          } else {
            toast.error('Error', { description: message })
          }
        }

        throw new HttpError(response.status, message, errorBody)
      }

      return response.json()
    } catch (error) {
      if (!suppressToast && error instanceof TypeError && error.message.includes('fetch')) {
        toast.error('Network Error', {
          description: 'Cannot connect to the backend. Please ensure the server is running.',
        })
      }
      throw error
    }
  }

  // ========================================================================
  // User Endpoints
  // ========================================================================

  async getUsers(): Promise<User[]> {
    // Suppress 403 toast for regular users (expected error)
    return this.fetch<User[]>('/users', {}, true)
  }

  async createUser(userData: { user_id: string; email_masked?: string; phone_masked?: string }): Promise<User> {
    return this.fetch<User>('/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  // ========================================================================
  // Profile Endpoint
  // ========================================================================

  async getUserProfile(userId: string, windowDays: number = 30): Promise<UserProfile> {
    return this.fetch<UserProfile>(`/profile/${userId}?window=${windowDays}`)
  }

  // ========================================================================
  // Recommendations Endpoint
  // ========================================================================

  async getRecommendations(userId: string, windowDays: number = 30): Promise<RecommendationItem[]> {
    return this.fetch<RecommendationItem[]>(`/recommendations/${userId}?window=${windowDays}`)
  }

  // ========================================================================
  // Transactions Endpoint
  // ========================================================================

  async getTransactions(userId: string, limit: number = 100, offset: number = 0): Promise<Transaction[]> {
    return this.fetch<Transaction[]>(`/transactions/${userId}?limit=${limit}&offset=${offset}`)
  }

  // ========================================================================
  // Operator Endpoints
  // ========================================================================

  async getOperatorQueue(): Promise<RecommendationItem[]> {
    return this.fetch<RecommendationItem[]>('/operator/review')
  }

  async approveRecommendation(
    recommendationId: number,
    approval: ApprovalRequest
  ): Promise<ApprovalResponse> {
    return this.fetch<ApprovalResponse>(`/operator/recommendations/${recommendationId}/approve`, {
      method: 'POST',
      body: JSON.stringify(approval),
    })
  }

  // ========================================================================
  // Consent Endpoints
  // ========================================================================

  async postConsent(req: ConsentRequest): Promise<ConsentResponse> {
    const body: ConsentRequest = { ...req, by: req.by ?? 'api' }
    return this.fetch<ConsentResponse>(`/consent`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }
}

// Export singleton instance
export const apiClient = new ApiClient(API_BASE)

// ============================================================================
// React Query Hooks
// ============================================================================

/**
 * Fetch all users (operators only).
 * 
 * Why this exists:
 * - Used in User Dashboard selector and Operator View user list
 * - Only works for operators (regular users get 403)
 * - Automatically caches and refetches
 * 
 * Note: This query will fail with 403 for regular users. That's expected.
 * Use retry: false to avoid retry loops on 403.
 */
export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.getUsers(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry on 403 (regular users can't access this)
  })
}

/**
 * Fetch user profile with signals and persona for a given window.
 * 
 * Why this exists:
 * - Used in User Dashboard to display persona, signals, and recommendations
 * - Supports both 30d and 180d windows
 */
export function useUserProfile(userId: string | undefined, windowDays: number = 30) {
  return useQuery({
    queryKey: ['profile', userId, windowDays],
    queryFn: () => apiClient.getUserProfile(userId!, windowDays),
    enabled: !!userId, // Only fetch if userId is provided
    staleTime: 0, // Don't cache - always check consent status
    retry: false, // Avoid retry loops on 403 before consent
    refetchOnWindowFocus: false,
    refetchOnMount: true, // Always refetch on mount to check consent status
  })
}

/**
 * Fetch recommendations for a user.
 * 
 * Why this exists:
 * - Used in User Dashboard to display education items and offers
 * - Includes rationales and disclosure
 * 
 * @param userId - User ID to fetch recommendations for
 * @param windowDays - Time window (30 or 180 days)
 * @param shouldFetch - Whether to enable fetching (used to control when insights are loaded)
 */
export function useRecommendations(userId: string | undefined, windowDays: number = 30, shouldFetch: boolean = true) {
  return useQuery({
    queryKey: ['recommendations', userId, windowDays],
    queryFn: () => apiClient.getRecommendations(userId!, windowDays),
    enabled: !!userId && shouldFetch, // Only fetch if userId is provided AND we should fetch
    staleTime: 2 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: true, // Always refetch on mount to check consent status
  })
}

/**
 * Grant consent for a user (opt-in) and refresh related queries.
 */
export function useGrantConsent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, reason, by }: { userId: string; reason?: string; by?: string }) =>
      apiClient.postConsent({ user_id: userId, action: 'opt_in', reason, by: by ?? 'user_dashboard' }),
    onSuccess: (_data, variables) => {
      toast.success('Consent granted', {
        description: 'You can now view this dashboard.',
      })
      // Invalidate profile and recommendations for this user (all windows)
      queryClient.invalidateQueries({ queryKey: ['profile', variables.userId] })
      queryClient.invalidateQueries({ queryKey: ['recommendations', variables.userId] })
      // Broadly invalidate to catch any cache variants
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      queryClient.invalidateQueries({ queryKey: ['recommendations'] })
    },
    onError: (error: Error) => {
      toast.error('Failed to grant consent', {
        description: error.message,
      })
    },
  })
}

/**
 * Fetch operator review queue (all pending recommendations).
 * 
 * Why this exists:
 * - Used in Operator View to show recommendations needing review
 */
export function useOperatorQueue() {
  return useQuery({
    queryKey: ['operatorQueue'],
    queryFn: () => apiClient.getOperatorQueue(),
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

/**
 * Approve, reject, or flag a recommendation.
 * 
 * Why this exists:
 * - Used in Operator View for approve/reject/flag actions
 * - Invalidates operator queue to show updated status
 * - Shows success/error toasts
 */
export function useApproveRecommendation() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ recommendationId, approval }: { recommendationId: number; approval: ApprovalRequest }) =>
      apiClient.approveRecommendation(recommendationId, approval),
    onSuccess: (data) => {
      toast.success('Success', {
        description: data.message,
      })
      // Invalidate and refetch operator queue
      queryClient.invalidateQueries({ queryKey: ['operatorQueue'] })
    },
    onError: (error: Error) => {
      toast.error('Failed to process recommendation', {
        description: error.message,
      })
    },
  })
}

/**
 * Fetch transactions for a user.
 * 
 * Why this exists:
 * - Used in User Dashboard to display transaction history
 * - Supports pagination with limit and offset
 */
export function useTransactions(userId: string | undefined, limit: number = 100, offset: number = 0) {
  return useQuery({
    queryKey: ['transactions', userId, limit, offset],
    queryFn: () => apiClient.getTransactions(userId!, limit, offset),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: false,
  })
}

/**
 * Revoke consent for a user (opt-out) and refresh related queries.
 */
export function useRevokeConsent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, reason, by }: { userId: string; reason?: string; by?: string }) =>
      apiClient.postConsent({ user_id: userId, action: 'opt_out', reason, by: by ?? 'user_dashboard' }),
    onSuccess: (_data, variables) => {
      toast.success('Consent revoked', {
        description: 'Your data will no longer be processed.',
      })
      // Remove cached data for profile and recommendations to force 403 on next access
      // Why: We don't want to invalidate (refetch immediately), we want to clear the cache
      // so that when the user tries to access Insights tab again, it will fetch fresh and get 403
      queryClient.removeQueries({ queryKey: ['profile', variables.userId] })
      queryClient.removeQueries({ queryKey: ['recommendations', variables.userId] })
    },
    onError: (error: Error) => {
      toast.error('Failed to revoke consent', {
        description: error.message,
      })
    },
  })
}

