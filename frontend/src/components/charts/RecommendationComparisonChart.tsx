/**
 * Recommendation Comparison Chart Component
 * 
 * Why this exists:
 * - Compares education vs offer recommendations across demographic groups
 * - Helps identify potential bias in recommendation types
 * - Makes it easy to see if certain groups get more educational content vs offers
 * 
 * What it does:
 * - Takes demographic data with recommendation counts
 * - Creates grouped bar chart comparing education vs offer recommendations
 * - Shows distribution across demographic groups
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface DemographicData {
  [key: string]: {
    count: number
    pct_of_total: number
    education_recs: number
    offer_recs: number
  }
}

interface RecommendationComparisonChartProps {
  title: string
  description?: string
  data: DemographicData
}

export function RecommendationComparisonChart({ title, description, data }: RecommendationComparisonChartProps) {
  // Transform data for Recharts
  const chartData = Object.entries(data).map(([group, info]) => ({
    name: group.replace('_', ' '),
    education: info.education_recs,
    offers: info.offer_recs,
    total: info.education_recs + info.offer_recs,
    users: info.count,
  }))

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null
    
    const data = payload[0].payload
    const eduPct = data.total > 0 ? ((data.education / data.total) * 100).toFixed(1) : 0
    const offerPct = data.total > 0 ? ((data.offers / data.total) * 100).toFixed(1) : 0
    
    return (
      <div className="bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 space-y-2">
        <p className="font-semibold capitalize text-gray-900 dark:text-white">{data.name}</p>
        <p className="text-xs text-gray-600 dark:text-gray-300">{data.users} users</p>
        <div className="space-y-1 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between gap-4 text-sm text-gray-700 dark:text-gray-200">
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-blue-500" />
              Education
            </span>
            <span className="font-medium">{data.education} ({eduPct}%)</span>
          </div>
          <div className="flex justify-between gap-4 text-sm text-gray-700 dark:text-gray-200">
            <span className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500" />
              Offers
            </span>
            <span className="font-medium">{data.offers} ({offerPct}%)</span>
          </div>
          <div className="flex justify-between gap-4 text-sm pt-1 border-t border-gray-200 dark:border-gray-700 font-medium text-gray-900 dark:text-white">
            <span>Total</span>
            <span>{data.total}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="name" 
              tick={{ fontSize: 12 }}
              className="capitalize"
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Bar 
              dataKey="education" 
              fill="#3b82f6" 
              name="Education Recommendations"
            />
            <Bar 
              dataKey="offers" 
              fill="#22c55e" 
              name="Offer Recommendations"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

