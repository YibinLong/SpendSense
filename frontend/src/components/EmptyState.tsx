/**
 * EmptyState Component
 * 
 * Why this exists:
 * - Provides a consistent, helpful UI when there's no data to display
 * - Better UX than showing nothing or just plain text
 * - Includes icon, message, description, and optional action button
 * 
 * Usage:
 * - Use instead of conditional rendering with "No data" text
 * - Can include a call-to-action button for next steps
 */

import type { LucideProps } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import type { FC } from 'react';

interface EmptyStateProps {
  /**
   * Icon to display (from lucide-react).
   * Why: Visual representation helps users understand the context.
   */
  icon: FC<LucideProps>;
  
  /**
   * Main heading text.
   * Why: Clear, concise message about what's missing.
   */
  title: string;
  
  /**
   * Optional description text.
   * Why: Provides additional context or explanation.
   */
  description?: string;
  
  /**
   * Optional action button configuration.
   * Why: Guides users on what to do next.
   */
  action?: {
    label: string;
    onClick: () => void;
  };
  
  /**
   * Optional CSS class name for customization.
   */
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <Card className={className}>
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        {/* Icon with gradient background */}
        <div className="mb-4 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 p-4">
          <Icon className="h-12 w-12 text-blue-600" strokeWidth={1.5} />
        </div>
        
        {/* Title */}
        <h3 className="text-xl font-semibold mb-2 text-foreground">
          {title}
        </h3>
        
        {/* Description */}
        {description && (
          <p className="text-muted-foreground mb-6 max-w-md">
            {description}
          </p>
        )}
        
        {/* Action button */}
        {action && (
          <Button
            onClick={action.onClick}
            variant="gradient"
            size="default"
          >
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

