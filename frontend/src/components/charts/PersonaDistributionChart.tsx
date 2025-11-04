/**
 * PersonaDistributionChart Component
 * 
 * Why this exists:
 * - Shows distribution of users across different personas in a donut chart
 * - Color-coded by persona type for easy visual identification
 * - Useful in operator view to see persona balance across user base
 * 
 * Uses Recharts PieChart for responsive, interactive visualization
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getChartIcon } from '@/lib/iconMap';
import { getGradientColor, getPersonaGradient } from '@/lib/gradients';

interface PersonaData {
  persona_id: string;
  count: number;
  label: string;
}

interface PersonaDistributionChartProps {
  data: PersonaData[];
  title?: string;
  description?: string;
}

/**
 * Get display label for persona ID.
 */
function getPersonaLabel(personaId: string): string {
  const labels: Record<string, string> = {
    'high_utilization': 'High Utilization',
    'variable_income_budgeter': 'Variable Income',
    'subscription_heavy': 'Subscription Heavy',
    'savings_builder': 'Savings Builder',
    'cash_flow_optimizer': 'Cash Flow Optimizer',
    'insufficient_data': 'Insufficient Data',
  };
  return labels[personaId] || personaId;
}

/**
 * Custom label for pie chart showing percentage.
 */
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
  const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);

  // Only show label if percentage is > 5%
  if (percent < 0.05) return null;

  return (
    <text 
      x={x} 
      y={y} 
      fill="white" 
      textAnchor={x > cx ? 'start' : 'end'} 
      dominantBaseline="central"
      className="text-xs font-semibold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export function PersonaDistributionChart({ 
  data, 
  title = "Persona Distribution",
  description = "User distribution across behavioral personas"
}: PersonaDistributionChartProps) {
  const Icon = getChartIcon('pie');
  
  // Transform data and add colors
  const chartData = data.map(item => ({
    name: item.label || getPersonaLabel(item.persona_id),
    value: item.count,
    personaId: item.persona_id,
    color: getGradientColor(getPersonaGradient(item.persona_id)),
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
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomLabel}
              outerRadius={100}
              innerRadius={60}
              fill="#8884d8"
              dataKey="value"
              paddingAngle={2}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                background: 'hsl(var(--card))', 
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                padding: '8px 12px'
              }}
              formatter={(value: number, name: string) => [value, name]}
            />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              iconType="circle"
              formatter={(value) => <span className="text-sm">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

