/**
 * SpendingBreakdownChart Component
 * 
 * Why this exists:
 * - Shows spending distribution across different categories
 * - Pie chart provides quick visual understanding of where money goes
 * - Helps identify largest spending categories
 * 
 * Uses Recharts PieChart with category-specific colors
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getChartIcon } from '@/lib/iconMap';
import { getChartColors } from '@/lib/gradients';

interface CategoryData {
  category: string;
  amount: number;
}

interface SpendingBreakdownChartProps {
  data: CategoryData[];
  title?: string;
  description?: string;
}

/**
 * Format currency for display.
 */
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Custom tooltip showing category name and amount.
 */
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border bg-card p-3 shadow-lg">
        <p className="text-sm font-semibold">{payload[0].name}</p>
        <p className="text-lg font-bold text-primary">
          {formatCurrency(payload[0].value)}
        </p>
        <p className="text-xs text-muted-foreground">
          {payload[0].payload.percentage}%
        </p>
      </div>
    );
  }
  return null;
};

/**
 * Custom label showing percentage for larger slices.
 */
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
  const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);

  // Only show label if percentage is > 8%
  if (percent < 0.08) return null;

  return (
    <text 
      x={x} 
      y={y} 
      fill="white" 
      textAnchor={x > cx ? 'start' : 'end'} 
      dominantBaseline="central"
      className="text-xs font-semibold drop-shadow"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export function SpendingBreakdownChart({ 
  data, 
  title = "Spending Breakdown",
  description = "Distribution of spending by category"
}: SpendingBreakdownChartProps) {
  const Icon = getChartIcon('pie');
  const colors = getChartColors();
  
  // Calculate total and add percentage
  const total = data.reduce((sum, item) => sum + item.amount, 0);
  const chartData = data.map((item, index) => ({
    name: item.category,
    value: item.amount,
    percentage: ((item.amount / total) * 100).toFixed(1),
    color: colors[index % colors.length],
  }));

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
        {chartData.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  paddingAngle={1}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  verticalAlign="bottom" 
                  height={36}
                  iconType="circle"
                  formatter={(value, entry: any) => (
                    <span className="text-sm">
                      {value} ({formatCurrency(entry.payload.value)})
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
            
            {/* Total */}
            <div className="mt-4 rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 p-4 text-center border border-blue-100 dark:border-blue-900/30">
              <p className="text-sm text-muted-foreground mb-1">Total Spending</p>
              <p className="text-2xl font-bold text-foreground">{formatCurrency(total)}</p>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <Icon className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" strokeWidth={1.5} />
            <p className="text-sm text-muted-foreground">No spending data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

