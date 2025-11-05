/**
 * TransactionList Component
 * 
 * Why this exists:
 * - Displays user's transaction history in a beautiful, modern design
 * - Shows newest transactions first
 * - Includes details like merchant, amount, date, category
 * - Uses card-based layout for better UX on all screen sizes
 */

import type { Transaction } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CommonIcons } from '@/lib/iconMap'
import { ArrowUpRight, ArrowDownRight, Calendar, Tag } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TransactionListProps {
  transactions: Transaction[]
}

/**
 * Format currency for display
 * Why: We want to show amounts in a user-friendly way with $ sign and 2 decimals
 */
function formatCurrency(amount: number, currency: string = 'USD'): string {
  const absAmount = Math.abs(amount)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(absAmount)
}

/**
 * Format date for display
 * Why: Convert ISO date strings to readable format like "Nov 4, 2025"
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

/**
 * Get category color
 * Why: Different categories get different colors for visual distinction
 */
function getCategoryColor(category: string | null | undefined): string {
  if (!category) return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
  
  const colorMap: Record<string, string> = {
    'Food and Drink': 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
    'Shopping': 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
    'Transportation': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    'Transfer': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    'Subscription': 'bg-pink-100 text-pink-800 dark:bg-pink-900/20 dark:text-pink-400',
    'Bills': 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    'Healthcare': 'bg-teal-100 text-teal-800 dark:bg-teal-900/20 dark:text-teal-400',
    'Entertainment': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400',
  }
  
  return colorMap[category] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
}

export function TransactionList({ transactions }: TransactionListProps) {
  if (transactions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="rounded-full bg-muted p-6 mb-4">
          <CommonIcons.Inbox className="h-12 w-12 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">No transactions found</h3>
        <p className="text-muted-foreground text-sm">
          Transactions will appear here once they are available
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {transactions.map((transaction) => {
        // Determine if this is a credit (money in) or debit (money out)
        // Why: We only check transaction_type, not amount sign, because amount sign can vary
        // Credits = money IN (income, refunds), Debits = money OUT (spending)
        const isCredit = transaction.transaction_type === 'credit'
        const amount = Math.abs(transaction.amount)
        
        return (
          <Card
            key={transaction.transaction_id}
            className={cn(
              "transition-all hover:shadow-md",
              transaction.pending && "opacity-60"
            )}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                {/* Left section: Icon and details */}
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  {/* Icon */}
                  <div className={cn(
                    "rounded-full p-2 shrink-0",
                    isCredit 
                      ? "bg-green-100 dark:bg-green-900/20" 
                      : "bg-gray-100 dark:bg-gray-900/20"
                  )}>
                    {isCredit ? (
                      <ArrowDownRight className="h-5 w-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <ArrowUpRight className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                    )}
                  </div>
                  
                  {/* Transaction details */}
                  <div className="flex-1 min-w-0">
                    {/* Merchant name */}
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold truncate">
                        {transaction.merchant_name || 'Unknown Merchant'}
                      </h4>
                      {transaction.pending && (
                        <Badge variant="outline" className="text-xs">
                          Pending
                        </Badge>
                      )}
                    </div>
                    
                    {/* Metadata row */}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                      {/* Date */}
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(transaction.transaction_date)}</span>
                      </div>
                      
                      {/* Category */}
                      {transaction.category && (
                        <Badge 
                          variant="secondary" 
                          className={cn("text-xs", getCategoryColor(transaction.category))}
                        >
                          <Tag className="h-3 w-3 mr-1" />
                          {transaction.category}
                        </Badge>
                      )}
                      
                      {/* Subcategory */}
                      {transaction.subcategory && (
                        <span className="text-xs text-muted-foreground">
                          {transaction.subcategory}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Right section: Amount */}
                <div className="text-right shrink-0">
                  <div className={cn(
                    "text-lg font-bold",
                    isCredit 
                      ? "text-green-600 dark:text-green-400" 
                      : "text-foreground"
                  )}>
                    {isCredit ? '+' : '-'}{formatCurrency(amount, transaction.currency)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {transaction.payment_channel || 'Online'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

