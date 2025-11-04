/**
 * SignalCard Component
 * 
 * Why this exists:
 * - Displays behavioral signals (Subscriptions, Savings, Credit, Income)
 * - Shows key metrics in an easy-to-read card format with visual progress bars
 * - Handles empty states when signals aren't available
 * - Modern design with icons, gradients, and hover effects
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getSignalIcon } from '@/lib/iconMap'
import { cn } from '@/lib/utils'
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
 * Progress bar component for visual metrics.
 * 
 * Why: Visual progress bars make it easier to quickly understand metrics
 * at a glance compared to just numbers.
 */
function ProgressBar({ value, max, variant = 'primary' }: { value: number; max: number; variant?: 'primary' | 'success' | 'warning' | 'danger' }) {
  const percentage = Math.min((value / max) * 100, 100);
  
  const variantClasses = {
    primary: 'bg-gradient-to-r from-blue-500 to-purple-500',
    success: 'bg-gradient-to-r from-emerald-500 to-green-500',
    warning: 'bg-gradient-to-r from-orange-500 to-amber-500',
    danger: 'bg-gradient-to-r from-red-500 to-rose-500',
  };
  
  return (
    <div className="progress-bar">
      <div 
        className={cn('progress-fill', variantClasses[variant])}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

/**
 * Render signal data based on type.
 * 
 * Why this exists:
 * - Each signal type has different metrics
 * - Provides consistent formatting across signal types
 * - Highlights important flags and thresholds
 * - Adds visual progress bars for better UX
 */
function renderSignalContent(
  type: string,
  data: SubscriptionSignalData | SavingsSignalData | CreditSignalData | IncomeSignalData
) {
  if (type === 'subscriptions') {
    const sub = data as SubscriptionSignalData
    const subShare = Number(sub.subscription_share_pct);
    
    return (
      <div className="space-y-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Recurring Merchants</span>
            <span className="font-semibold">{sub.recurring_merchant_count}</span>
          </div>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Monthly Recurring</span>
            <span className="font-semibold">{formatCurrency(Number(sub.monthly_recurring_spend))}</span>
          </div>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Subscription Share</span>
            <span className="font-semibold">{formatPercent(subShare)}</span>
          </div>
          <ProgressBar value={subShare} max={100} variant={subShare >= 20 ? 'warning' : 'primary'} />
        </div>
      </div>
    )
  }

  if (type === 'savings') {
    const sav = data as SavingsSignalData
    const growthRate = Number(sav.savings_growth_rate_pct);
    const emergencyMonths = Number(sav.emergency_fund_months);
    
    return (
      <div className="space-y-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Net Inflow</span>
            <span className={cn("font-semibold", Number(sav.savings_net_inflow) > 0 ? 'text-green-600' : 'text-red-600')}>
              {formatCurrency(Number(sav.savings_net_inflow))}
            </span>
          </div>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Growth Rate</span>
            <span className="font-semibold">{formatPercent(growthRate)}</span>
          </div>
          <ProgressBar value={Math.abs(growthRate)} max={10} variant={growthRate >= 0 ? 'success' : 'danger'} />
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Emergency Fund</span>
            <span className="font-semibold">{emergencyMonths.toFixed(1)} months</span>
          </div>
          <ProgressBar value={emergencyMonths} max={6} variant={emergencyMonths >= 3 ? 'success' : emergencyMonths >= 1 ? 'warning' : 'danger'} />
        </div>
      </div>
    )
  }

  if (type === 'credit') {
    const cred = data as CreditSignalData
    const maxUtil = Number(cred.credit_utilization_max_pct);
    const avgUtil = Number(cred.credit_utilization_avg_pct);
    
    return (
      <div className="space-y-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Max Utilization</span>
            <span className="font-semibold">{formatPercent(maxUtil)}</span>
          </div>
          <ProgressBar 
            value={maxUtil} 
            max={100} 
            variant={maxUtil >= 80 ? 'danger' : maxUtil >= 50 ? 'warning' : maxUtil >= 30 ? 'primary' : 'success'} 
          />
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Avg Utilization</span>
            <span className="font-semibold">{formatPercent(avgUtil)}</span>
          </div>
          <ProgressBar 
            value={avgUtil} 
            max={100} 
            variant={avgUtil >= 50 ? 'warning' : avgUtil >= 30 ? 'primary' : 'success'} 
          />
        </div>
        
        {/* Flags */}
        <div className="space-y-1.5 pt-2 border-t">
          {cred.credit_util_flag_50 && (
            <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-500">
              <div className="h-1.5 w-1.5 rounded-full bg-amber-600" />
              High utilization (≥50%)
            </div>
          )}
          {cred.has_interest_charges && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
              Interest charges present
            </div>
          )}
          {cred.is_overdue && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-500">
              <div className="h-1.5 w-1.5 rounded-full bg-red-600" />
              Overdue payments
            </div>
          )}
          {!cred.credit_util_flag_50 && !cred.has_interest_charges && !cred.is_overdue && (
            <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-500">
              <div className="h-1.5 w-1.5 rounded-full bg-green-600" />
              No critical flags
            </div>
          )}
        </div>
      </div>
    )
  }

  if (type === 'income') {
    const inc = data as IncomeSignalData
    const cashBuffer = Number(inc.cashflow_buffer_months);
    
    return (
      <div className="space-y-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Payroll Deposits</span>
            <span className="font-semibold">{inc.payroll_deposit_count}</span>
          </div>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Median Pay Gap</span>
            <span className="font-semibold">{Number(inc.median_pay_gap_days).toFixed(0)} days</span>
          </div>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Avg Payroll</span>
            <span className="font-semibold">{formatCurrency(Number(inc.avg_payroll_amount))}</span>
          </div>
        </div>
        
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Cash Buffer</span>
            <span className="font-semibold">{cashBuffer.toFixed(1)} months</span>
          </div>
          <ProgressBar value={cashBuffer} max={3} variant={cashBuffer >= 2 ? 'success' : cashBuffer >= 1 ? 'primary' : 'danger'} />
        </div>
      </div>
    )
  }

  return null
}

export function SignalCard({ title, description, data, type }: SignalCardProps) {
  const Icon = getSignalIcon(type);
  
  return (
    <Card className="hover-lift overflow-hidden transition-shadow">
      {/* Gradient accent bar at top */}
      <div className="h-1 bg-gradient-primary" />
      
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2">
              <Icon className="h-5 w-5 text-primary" strokeWidth={2} />
              {title}
            </CardTitle>
            <CardDescription className="mt-1">{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {data ? (
          renderSignalContent(type, data)
        ) : (
          <div className="text-center py-6">
            <Icon className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" strokeWidth={1.5} />
            <p className="text-sm text-muted-foreground">No data available for this window</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}


