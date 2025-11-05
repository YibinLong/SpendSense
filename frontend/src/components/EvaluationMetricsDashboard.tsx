/**
 * Evaluation Metrics Dashboard Component
 * 
 * Why this exists:
 * - Displays evaluation report data in beautiful, visual charts instead of raw markdown
 * - Shows coverage, explainability, latency, and auditability metrics
 * - Uses progress bars, gauge charts, and stat cards for easy comprehension
 * 
 * What it displays:
 * - Coverage metrics (personas, signals)
 * - Explainability percentage
 * - Latency distribution and statistics
 * - Auditability compliance
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CommonIcons } from '@/lib/iconMap'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface MetricsData {
  coverage?: {
    total_users: number
    users_with_persona: number
    users_with_3plus_signals: number
    users_with_full_coverage: number
    coverage_persona_pct: number
    coverage_signals_pct: number
    full_coverage_pct: number
  }
  explainability?: {
    total_recommendations: number
    recommendations_with_rationale: number
    explainability_pct: number
  }
  latency?: {
    sample_size: number
    min_latency_s: number
    max_latency_s: number
    avg_latency_s: number
    median_latency_s: number
    users_under_5s: number
    users_under_5s_pct: number
  }
  auditability?: {
    total_recommendations: number
    recommendations_with_traces: number
    auditability_pct: number
  }
}

interface EvaluationMetricsDashboardProps {
  metrics: MetricsData
  timestamp?: string
}

// Progress bar component
function ProgressBar({ value, label, target = 100 }: { value: number; label: string; target?: number }) {
  const percentage = Math.min(100, (value / target) * 100)
  const isPassing = value >= target * 0.8 // 80% of target
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-gray-700 dark:text-gray-300">{label}</span>
        <span className="font-bold text-gray-900 dark:text-white">{value.toFixed(1)}%</span>
      </div>
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${
            isPassing ? 'bg-green-500' : 'bg-yellow-500'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {target < 100 && (
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Target: ≥{target}%
        </div>
      )}
    </div>
  )
}

// Metric stat card
function MetricCard({ 
  icon: Icon, 
  title, 
  value, 
  subtitle, 
  status 
}: { 
  icon: any
  title: string
  value: string | number
  subtitle?: string
  status?: 'pass' | 'fail' | 'warning'
}) {
  const statusColors = {
    pass: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    fail: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
  }
  
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              <Icon className="h-5 w-5 text-primary" />
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
            )}
          </div>
          {status && (
            <Badge className={statusColors[status]}>
              {status === 'pass' ? '✓ PASS' : status === 'fail' ? '✗ FAIL' : '⚠ WARN'}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function EvaluationMetricsDashboard({ metrics, timestamp }: EvaluationMetricsDashboardProps) {
  // Calculate overall system status
  const isSystemPassing = 
    (metrics.coverage?.full_coverage_pct || 0) >= 80 &&
    (metrics.explainability?.explainability_pct || 0) >= 90 &&
    (metrics.latency?.users_under_5s_pct || 0) >= 90 &&
    (metrics.auditability?.auditability_pct || 0) >= 100

  // Prepare latency chart data
  const latencyChartData = metrics.latency ? [
    { name: 'Min', value: metrics.latency.min_latency_s * 1000, fill: '#22c55e' },
    { name: 'Avg', value: metrics.latency.avg_latency_s * 1000, fill: '#3b82f6' },
    { name: 'Median', value: metrics.latency.median_latency_s * 1000, fill: '#8b5cf6' },
    { name: 'Max', value: metrics.latency.max_latency_s * 1000, fill: '#ef4444' },
  ] : []

  // Custom tooltip for latency chart
  const LatencyTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null
    const data = payload[0].payload
    return (
      <div className="bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3">
        <p className="font-semibold text-gray-900 dark:text-white">{data.name} Latency</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">{data.value.toFixed(1)}ms</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      <Card className={isSystemPassing ? 'border-green-500/50 bg-green-50 dark:bg-green-950/20' : 'border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20'}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${isSystemPassing ? 'bg-green-500' : 'bg-yellow-500'}`}>
                {isSystemPassing ? (
                  <CommonIcons.CheckCircle className="h-6 w-6 text-white" />
                ) : (
                  <CommonIcons.AlertTriangle className="h-6 w-6 text-white" />
                )}
              </div>
              <div>
                <CardTitle className={isSystemPassing ? 'text-green-700 dark:text-green-400' : 'text-yellow-700 dark:text-yellow-400'}>
                  System Status: {isSystemPassing ? 'PASSING' : 'NEEDS ATTENTION'}
                </CardTitle>
                <CardDescription>
                  Generated: {timestamp ? new Date(timestamp).toLocaleString() : 'N/A'}
                </CardDescription>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Coverage Metrics */}
      {metrics.coverage && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <CommonIcons.Users className="h-5 w-5 text-primary" />
            Coverage Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              icon={CommonIcons.Users}
              title="Total Users"
              value={metrics.coverage.total_users}
              subtitle={`${metrics.coverage.users_with_full_coverage} with full coverage`}
              status="pass"
            />
            <MetricCard
              icon={CommonIcons.Shield}
              title="Users with Persona"
              value={`${metrics.coverage.users_with_persona}/${metrics.coverage.total_users}`}
              subtitle={`${metrics.coverage.coverage_persona_pct.toFixed(1)}%`}
              status={metrics.coverage.coverage_persona_pct >= 80 ? 'pass' : 'warning'}
            />
            <MetricCard
              icon={CommonIcons.Activity}
              title="Users with ≥3 Signals"
              value={`${metrics.coverage.users_with_3plus_signals}/${metrics.coverage.total_users}`}
              subtitle={`${metrics.coverage.coverage_signals_pct.toFixed(1)}%`}
              status={metrics.coverage.coverage_signals_pct >= 80 ? 'pass' : 'warning'}
            />
          </div>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Coverage Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ProgressBar value={metrics.coverage.coverage_persona_pct} label="Persona Coverage" target={80} />
              <ProgressBar value={metrics.coverage.coverage_signals_pct} label="Signal Coverage" target={80} />
              <ProgressBar value={metrics.coverage.full_coverage_pct} label="Full Coverage" target={80} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Explainability & Auditability */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <CommonIcons.FileText className="h-5 w-5 text-primary" />
          Explainability & Auditability
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {metrics.explainability && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <CommonIcons.BookOpen className="h-5 w-5" />
                  Explainability
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary mb-2">
                    {metrics.explainability.explainability_pct.toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {metrics.explainability.recommendations_with_rationale}/{metrics.explainability.total_recommendations} recommendations with rationale
                  </p>
                </div>
                <ProgressBar value={metrics.explainability.explainability_pct} label="Target: ≥90%" target={90} />
              </CardContent>
            </Card>
          )}
          
          {metrics.auditability && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <CommonIcons.Shield className="h-5 w-5" />
                  Auditability
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary mb-2">
                    {metrics.auditability.auditability_pct.toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {metrics.auditability.recommendations_with_traces}/{metrics.auditability.total_recommendations} with decision traces
                  </p>
                </div>
                <ProgressBar value={metrics.auditability.auditability_pct} label="Target: 100%" target={100} />
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Latency Metrics */}
      {metrics.latency && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <CommonIcons.Zap className="h-5 w-5 text-primary" />
            Latency Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Latency Statistics</CardTitle>
                <CardDescription>Sample size: {metrics.latency.sample_size} users</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={latencyChartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} label={{ value: 'ms', angle: -90, position: 'insideLeft' }} />
                    <Tooltip content={<LatencyTooltip />} />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {latencyChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Performance Target</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary mb-2">
                    {metrics.latency.users_under_5s_pct.toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {metrics.latency.users_under_5s}/{metrics.latency.sample_size} users under 5s
                  </p>
                </div>
                <ProgressBar value={metrics.latency.users_under_5s_pct} label="Target: ≥90% under 5s" target={90} />
                <div className="grid grid-cols-2 gap-2 pt-4 border-t">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Avg Latency</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">{(metrics.latency.avg_latency_s * 1000).toFixed(1)}ms</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Max Latency</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">{(metrics.latency.max_latency_s * 1000).toFixed(1)}ms</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

