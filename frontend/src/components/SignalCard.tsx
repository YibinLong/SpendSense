/**
 * SignalCard Component
 * 
 * Why this exists:
 * - Displays behavioral signals (Subscriptions, Savings, Credit, Income)
 * - Shows key metrics in an easy-to-read card format
 * - Handles empty states when signals aren't available
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { 
  SubscriptionSignalData,
  SavingsSignalData,
  CreditSignalData,
  IncomeSignalData 
} from '@/lib/api'

interface SignalCardProps {
  title: string
  description: string
  data: SubscriptionSignalData | SavingsSignalData | CreditSignalData | IncomeSignalData | null | undefined
  type: 'subscriptions' | 'savings' | 'credit' | 'income'
}

/**
 * Format currency values for display.
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Format percentage values for display.
 */
function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}

/**
 * Render signal data based on type.
 * 
 * Why this exists:
 * - Each signal type has different metrics
 * - Provides consistent formatting across signal types
 * - Highlights important flags and thresholds
 */
function renderSignalContent(
  type: string,
  data: SubscriptionSignalData | SavingsSignalData | CreditSignalData | IncomeSignalData
) {
  if (type === 'subscriptions') {
    const sub = data as SubscriptionSignalData
    return (
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Recurring Merchants:</span>
          <span className="font-medium">{sub.recurring_merchant_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Monthly Recurring:</span>
          <span className="font-medium">{formatCurrency(Number(sub.monthly_recurring_spend))}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Subscription Share:</span>
          <span className="font-medium">{formatPercent(Number(sub.subscription_share_pct))}</span>
        </div>
      </div>
    )
  }

  if (type === 'savings') {
    const sav = data as SavingsSignalData
    return (
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Net Inflow:</span>
          <span className="font-medium">{formatCurrency(Number(sav.savings_net_inflow))}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Growth Rate:</span>
          <span className="font-medium">{formatPercent(Number(sav.savings_growth_rate_pct))}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Emergency Fund:</span>
          <span className="font-medium">{Number(sav.emergency_fund_months).toFixed(1)} months</span>
        </div>
      </div>
    )
  }

  if (type === 'credit') {
    const cred = data as CreditSignalData
    return (
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Max Utilization:</span>
          <span className={`font-medium ${Number(cred.credit_utilization_max_pct) >= 50 ? 'text-destructive' : ''}`}>
            {formatPercent(Number(cred.credit_utilization_max_pct))}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Avg Utilization:</span>
          <span className="font-medium">{formatPercent(Number(cred.credit_utilization_avg_pct))}</span>
        </div>
        <div className="space-y-1 pt-2 border-t">
          {cred.credit_util_flag_50 && (
            <div className="text-sm text-destructive">⚠️ High utilization (≥50%)</div>
          )}
          {cred.has_interest_charges && (
            <div className="text-sm text-muted-foreground">Interest charges present</div>
          )}
          {cred.is_overdue && (
            <div className="text-sm text-destructive">⚠️ Overdue payments</div>
          )}
          {!cred.credit_util_flag_50 && !cred.has_interest_charges && !cred.is_overdue && (
            <div className="text-sm text-muted-foreground">No critical flags</div>
          )}
        </div>
      </div>
    )
  }

  if (type === 'income') {
    const inc = data as IncomeSignalData
    return (
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Payroll Deposits:</span>
          <span className="font-medium">{inc.payroll_deposit_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Median Pay Gap:</span>
          <span className="font-medium">{Number(inc.median_pay_gap_days).toFixed(0)} days</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Avg Payroll:</span>
          <span className="font-medium">{formatCurrency(Number(inc.avg_payroll_amount))}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Cash Buffer:</span>
          <span className="font-medium">{Number(inc.cashflow_buffer_months).toFixed(1)} months</span>
        </div>
      </div>
    )
  }

  return null
}

export function SignalCard({ title, description, data, type }: SignalCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {data ? (
          renderSignalContent(type, data)
        ) : (
          <p className="text-sm text-muted-foreground">No data available for this window</p>
        )}
      </CardContent>
    </Card>
  )
}


