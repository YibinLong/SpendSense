/**
 * SignalTrendChart Component
 * 
 * Why this exists:
 * - Compares signal metrics between 30d and 180d windows
 * - Line chart shows trends over different time periods
 * - Helps identify short-term vs long-term behavior patterns
 * 
 * Uses Recharts LineChart with gradient fills
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getChartIcon } from '@/lib/iconMap';

interface TrendDataPoint {
  name: string;
  value30d: number;
  value180d: number;
}

interface SignalTrendChartProps {
  data: TrendDataPoint[];
  title?: string;
  description?: string;
  yAxisLabel?: string;
}

export function SignalTrendChart({ 
  data, 
  title = "Signal Trends",
  description = "Comparison of 30-day vs 180-day metrics",
  yAxisLabel = "Value"
}: SignalTrendChartProps) {
  const Icon = getChartIcon('line');
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-5 w-5 text-primary" strokeWidth={2} />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="color30d" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="color180d" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="name" 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 12 }}
              label={{ value: yAxisLabel, angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
            />
            <Tooltip 
              contentStyle={{ 
                background: 'hsl(var(--card))', 
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                padding: '8px 12px'
              }}
            />
            <Legend 
              wrapperStyle={{ fontSize: '14px' }}
              iconType="line"
            />
            <Line 
              type="monotone" 
              dataKey="value30d" 
              name="30 Days"
              stroke="#3B82F6" 
              strokeWidth={2}
              fill="url(#color30d)"
              dot={{ fill: '#3B82F6', r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line 
              type="monotone" 
              dataKey="value180d" 
              name="180 Days"
              stroke="#8B5CF6" 
              strokeWidth={2}
              fill="url(#color180d)"
              dot={{ fill: '#8B5CF6', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

