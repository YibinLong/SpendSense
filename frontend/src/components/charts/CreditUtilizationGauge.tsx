/**
 * CreditUtilizationGauge Component
 * 
 * Why this exists:
 * - Visual gauge/radial chart showing credit utilization percentage
 * - Color changes based on utilization level (green < 30%, yellow < 50%, red >= 50%)
 * - Makes it easy to see at a glance if credit usage is healthy
 * 
 * Uses Recharts RadialBarChart for circular progress indicator
 */

import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CreditCard } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CreditUtilizationGaugeProps {
  utilization: number;
  title?: string;
  description?: string;
  showDetails?: boolean;
}

/**
 * Get color and label based on utilization percentage.
 */
function getUtilizationStatus(utilization: number) {
  if (utilization >= 80) {
    return {
      color: '#EF4444',  // Red
      label: 'Critical',
      textColor: 'text-red-600',
      bgColor: 'bg-red-50',
    };
  } else if (utilization >= 50) {
    return {
      color: '#F59E0B',  // Amber
      label: 'High',
      textColor: 'text-amber-600',
      bgColor: 'bg-amber-50',
    };
  } else if (utilization >= 30) {
    return {
      color: '#3B82F6',  // Blue
      label: 'Moderate',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
    };
  } else {
    return {
      color: '#10B981',  // Green
      label: 'Healthy',
      textColor: 'text-green-600',
      bgColor: 'bg-green-50',
    };
  }
}

export function CreditUtilizationGauge({ 
  utilization, 
  title = "Credit Utilization",
  description = "Current credit card utilization rate",
  showDetails = true
}: CreditUtilizationGaugeProps) {
  const status = getUtilizationStatus(utilization);
  
  const data = [
    {
      name: 'Utilization',
      value: utilization,
      fill: status.color,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" strokeWidth={2} />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center">
          {/* Radial gauge */}
          <ResponsiveContainer width="100%" height={200}>
            <RadialBarChart 
              cx="50%" 
              cy="50%" 
              innerRadius="70%" 
              outerRadius="90%" 
              barSize={20} 
              data={data}
              startAngle={180}
              endAngle={0}
            >
              <PolarAngleAxis
                type="number"
                domain={[0, 100]}
                angleAxisId={0}
                tick={false}
              />
              <RadialBar
                background={{ fill: 'hsl(var(--muted))' }}
                dataKey="value"
                cornerRadius={10}
              />
            </RadialBarChart>
          </ResponsiveContainer>
          
          {/* Center value */}
          <div className="absolute mt-20 text-center">
            <div className="text-4xl font-bold text-foreground">
              {utilization.toFixed(1)}%
            </div>
            <div className={cn("text-sm font-medium mt-1", status.textColor)}>
              {status.label}
            </div>
          </div>
          
          {/* Details */}
          {showDetails && (
            <div className="mt-4 w-full space-y-2">
              <div className={cn("rounded-lg p-3 text-center", status.bgColor)}>
                <p className="text-xs text-muted-foreground mb-1">Status</p>
                <p className={cn("text-sm font-semibold", status.textColor)}>
                  {status.label} - {utilization.toFixed(1)}%
                </p>
              </div>
              
              {/* Utilization guidelines */}
              <div className="grid grid-cols-3 gap-2 text-xs text-center">
                <div className="rounded bg-green-50 p-2">
                  <div className="font-medium text-green-700">&lt; 30%</div>
                  <div className="text-green-600">Healthy</div>
                </div>
                <div className="rounded bg-amber-50 p-2">
                  <div className="font-medium text-amber-700">30-50%</div>
                  <div className="text-amber-600">Monitor</div>
                </div>
                <div className="rounded bg-red-50 p-2">
                  <div className="font-medium text-red-700">&gt; 50%</div>
                  <div className="text-red-600">High Risk</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

