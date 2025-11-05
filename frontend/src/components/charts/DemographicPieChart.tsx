/**
 * Demographic Pie Chart Component
 * 
 * Why this exists:
 * - Shows proportional distribution of demographic groups at a glance
 * - Makes it easy to spot over/under-represented groups
 * - Provides a quick visual summary before diving into details
 * 
 * What it does:
 * - Takes demographic data and converts to pie chart format
 * - Shows percentage and count for each group
 * - Color-codes segments for easy identification
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface DemographicData {
  [key: string]: {
    count: number
    pct_of_total: number
  }
}

interface DemographicPieChartProps {
  title: string
  description?: string
  data: DemographicData
}

// Color palette for pie segments
const COLORS = [
  '#3b82f6', // blue
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
  '#94a3b8', // gray
]

export function DemographicPieChart({ title, description, data }: DemographicPieChartProps) {
  // Transform data for Recharts
  const chartData = Object.entries(data).map(([group, info]) => ({
    name: group.replace('_', ' '),
    value: info.count,
    percentage: info.pct_of_total,
  }))

  // Custom label to show percentage on chart
  const renderLabel = (entry: any) => {
    return `${entry.percentage.toFixed(1)}%`
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null
    
    const data = payload[0].payload
    
    return (
      <div className="bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 space-y-1">
        <p className="font-semibold capitalize text-gray-900 dark:text-white">{data.name}</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {data.value} users
        </p>
        <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
          {data.percentage.toFixed(1)}%
        </p>
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
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderLabel}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ fontSize: '12px' }}
              formatter={(value) => value}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

