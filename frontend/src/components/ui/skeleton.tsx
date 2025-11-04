/**
 * Skeleton Component
 * 
 * Why this exists:
 * - Shows loading placeholders instead of blank spaces or "Loading..." text
 * - Provides better UX by indicating content is coming
 * - Maintains layout stability while data loads
 * 
 * Usage:
 * - Use <Skeleton /> for simple loading states
 * - Use predefined skeletons (CardSkeleton, TableSkeleton) for common patterns
 */

import { cn } from "@/lib/utils"

/**
 * Basic skeleton component for loading states.
 * 
 * Why: A simple animated placeholder that can be sized to match any content.
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

/**
 * Card skeleton for loading card-based content.
 * 
 * Why: Cards are used throughout the app. This provides a consistent
 * loading state that matches the card structure.
 */
function CardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={cn("rounded-lg border bg-card p-6 space-y-4", className)}>
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-5 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      
      {/* Content */}
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
    </div>
  );
}

/**
 * Table skeleton for loading tabular data.
 * 
 * Why: The operator view uses tables. This skeleton maintains the
 * table structure while data loads.
 */
function TableSkeleton({ rows = 5, className = '' }: { rows?: number; className?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {/* Table header */}
      <div className="flex gap-4">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 w-20" />
      </div>
      
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <Skeleton className="h-12 flex-1" />
          <Skeleton className="h-12 flex-1" />
          <Skeleton className="h-12 flex-1" />
          <Skeleton className="h-12 w-20" />
        </div>
      ))}
    </div>
  );
}

/**
 * Chart skeleton for loading data visualizations.
 * 
 * Why: Charts take time to render. This skeleton indicates
 * where the chart will appear.
 */
function ChartSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={cn("rounded-lg border bg-card p-6", className)}>
      <div className="space-y-4">
        {/* Title */}
        <Skeleton className="h-6 w-1/3" />
        
        {/* Chart area */}
        <div className="space-y-3">
          <Skeleton className="h-64 w-full" />
          
          {/* Legend */}
          <div className="flex gap-4 justify-center">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Dashboard skeleton for loading the full dashboard view.
 * 
 * Why: The dashboard has a specific layout with hero section and cards.
 * This skeleton matches that structure.
 */
function DashboardSkeleton() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Hero section */}
      <div className="rounded-xl bg-gradient-to-br from-blue-50 to-purple-50 p-8">
        <Skeleton className="h-8 w-1/3 mb-4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
      
      {/* Signal cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
}

export { Skeleton, CardSkeleton, TableSkeleton, ChartSkeleton, DashboardSkeleton }

