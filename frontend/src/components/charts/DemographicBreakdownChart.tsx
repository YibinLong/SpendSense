/**
 * Demographic Breakdown Chart Component
 * 
 * Why this exists:
 * - Visualizes demographic distribution across age, gender, ethnicity
 * - Shows persona assignments for each demographic group
 * - Uses stacked bar chart for easy comparison
 * 
 * What it does:
 * - Takes demographic data (age_range, gender, ethnicity)
 * - Displays each group's user count and persona breakdown
 * - Color-codes different personas for visual clarity
 */

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface DemographicData {
  [key: string]: {
    count: number
    pct_of_total: number
    personas: { [persona: string]: number }
    education_recs: number
    offer_recs: number
  }
}

interface DemographicBreakdownChartProps {
  title: string
  description?: string
  data: DemographicData
}

// Color palette for personas
const PERSONA_COLORS: { [key: string]: string } = {
  'high_utilization': '#ef4444', // red
  'savings_builder': '#22c55e', // green
  'insufficient_data': '#94a3b8', // gray
  'subscription_heavy': '#f59e0b', // amber
  'credit_builder': '#3b82f6', // blue
  'stable_saver': '#8b5cf6', // purple
  'debt_manager': '#ec4899', // pink
}

export function DemographicBreakdownChart({ title, description, data }: DemographicBreakdownChartProps) {
  // Transform data for Recharts
  // Each group becomes a data point with persona counts
  const chartData = Object.entries(data).map(([group, info]) => {
    const dataPoint: any = {
      name: group.replace('_', ' '),
      total: info.count,
    }
    
    // Add each persona as a separate key
    Object.entries(info.personas).forEach(([persona, count]) => {
      dataPoint[persona] = count
    })
    
    return dataPoint
  })

  // Get all unique personas across all groups
  const allPersonas = new Set<string>()
  Object.values(data).forEach(info => {
    Object.keys(info.personas).forEach(persona => allPersonas.add(persona))
  })

  // Custom tooltip to show details
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null
    
    const group = payload[0].payload.name
    const groupData = Object.values(data).find((_, idx) => 
      Object.keys(data)[idx].replace('_', ' ') === group
    )
    
    return (
      <div className="bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 space-y-2">
        <p className="font-semibold capitalize text-gray-900 dark:text-white">{group}</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {groupData?.count} users ({groupData?.pct_of_total.toFixed(1)}%)
        </p>
        <div className="space-y-1 pt-2 border-t border-gray-200 dark:border-gray-700">
          {payload.map((entry: any) => (
            entry.dataKey !== 'total' && entry.value > 0 && (
              <div key={entry.dataKey} className="flex justify-between gap-4 text-xs text-gray-700 dark:text-gray-200">
                <span className="capitalize flex items-center gap-1">
                  <div 
                    className="w-3 h-3 rounded" 
                    style={{ backgroundColor: entry.color }}
                  />
                  {entry.dataKey.replace('_', ' ')}
                </span>
                <span className="font-medium">{entry.value}</span>
              </div>
            )
          ))}
        </div>
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-600 dark:text-gray-400">Education recs</span>
            <span className="font-medium text-gray-900 dark:text-white">{groupData?.education_recs}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-600 dark:text-gray-400">Offer recs</span>
            <span className="font-medium text-gray-900 dark:text-white">{groupData?.offer_recs}</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="capitalize">{title}</CardTitle>
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
            <Legend 
              wrapperStyle={{ fontSize: '12px' }}
              formatter={(value) => value.replace('_', ' ')}
            />
            {Array.from(allPersonas).map((persona) => (
              <Bar
                key={persona}
                dataKey={persona}
                stackId="a"
                fill={PERSONA_COLORS[persona] || '#6b7280'}
                name={persona.replace('_', ' ')}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

