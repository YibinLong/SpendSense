/**
 * Recommendation Distribution Chart Component
 * 
 * Why this exists:
 * - Shows education vs offer recommendation distribution across demographics
 * - Helps identify if certain groups receive disproportionate types of recommendations
 * - Part of fairness analysis to ensure equitable treatment
 * 
 * What it does:
 * - Takes demographic data with education_recs and offer_recs counts
 * - Displays grouped bar chart comparing the two types
 * - Shows hover tooltips with exact counts and user information
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface DemographicData {
  [key: string]: {
    count: number
    pct_of_total: number
    personas?: { [persona: string]: number }
    education_recs: number
    offer_recs: number
  }
}

interface RecommendationDistributionChartProps {
  title: string
  description: string
  data: DemographicData
}

export function RecommendationDistributionChart({ 
  title, 
  description, 
  data 
}: RecommendationDistributionChartProps) {
  // Transform data for Recharts
  const chartData = Object.entries(data).map(([group, info]) => ({
    name: group.replace(/_/g, ' '),
    'Education Recommendations': info.education_recs,
    'Offer Recommendations': info.offer_recs,
    users: info.count,
    total: info.education_recs + info.offer_recs,
  }))

  // Custom tooltip to show details
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null
    
    const data = payload[0].payload
    
    return (
      <div className="bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 space-y-2">
        <p className="font-semibold capitalize text-gray-900 dark:text-white">{data.name}</p>
        <p className="text-xs text-muted-foreground">{data.users} users</p>
        <div className="space-y-1 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-blue-500" />
              <span>Education</span>
            </div>
            <span className="font-medium">
              {data['Education Recommendations']} ({data.total > 0 ? ((data['Education Recommendations'] / data.total) * 100).toFixed(1) : 0}%)
            </span>
          </div>
          <div className="flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500" />
              <span>Offers</span>
            </div>
            <span className="font-medium">
              {data['Offer Recommendations']} ({data.total > 0 ? ((data['Offer Recommendations'] / data.total) * 100).toFixed(1) : 0}%)
            </span>
          </div>
        </div>
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between text-xs font-medium">
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
        <CardDescription>{description}</CardDescription>
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
            <Legend 
              wrapperStyle={{ fontSize: '12px' }}
            />
            <Bar
              dataKey="Education Recommendations"
              fill="#3b82f6"
              name="Education"
            />
            <Bar
              dataKey="Offer Recommendations"
              fill="#22c55e"
              name="Offers"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

