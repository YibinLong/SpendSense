/**
 * API Client for SpendSense Backend
 * 
 * Why this exists:
 * - Centralizes all API calls with TypeScript types matching backend Pydantic schemas
 * - Handles errors consistently (403 consent, 404 not found, 500 server errors)
 * - Provides React Query hooks for automatic caching and refetching
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

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
   * Generic fetch wrapper with error handling.
   * 
   * Why this exists:
   * - Centralizes error handling for 403 consent errors, 404, 500
   * - Automatically parses JSON responses
   * - Shows toast notifications for errors
   */
  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
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

        if (response.status === 404) {
          toast.error('Not Found', { description: message })
        } else if (response.status >= 500) {
          toast.error('Server Error', { description: message })
        } else {
          toast.error('Error', { description: message })
        }

        throw new HttpError(response.status, message, errorBody)
      }

      return response.json()
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
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
    return this.fetch<User[]>('/users')
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
 * Fetch all users.
 * 
 * Why this exists:
 * - Used in User Dashboard selector and Operator View user list
 * - Automatically caches and refetches
 */
export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.getUsers(),
    staleTime: 5 * 60 * 1000, // 5 minutes
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
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: false, // Avoid retry loops on 403 before consent
    refetchOnWindowFocus: false,
  })
}

/**
 * Fetch recommendations for a user.
 * 
 * Why this exists:
 * - Used in User Dashboard to display education items and offers
 * - Includes rationales and disclosure
 */
export function useRecommendations(userId: string | undefined, windowDays: number = 30) {
  return useQuery({
    queryKey: ['recommendations', userId, windowDays],
    queryFn: () => apiClient.getRecommendations(userId!, windowDays),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000,
    retry: false,
    refetchOnWindowFocus: false,
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

