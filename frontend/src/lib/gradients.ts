/**
 * Gradient Utilities
 * 
 * Why this file exists:
 * - Provides reusable gradient styles for consistent design across components
 * - Makes it easy to apply gradient backgrounds, text, and borders
 * - Centralizes gradient definitions that match our design tokens
 * 
 * Usage:
 * - Import the getGradientClasses function and apply to className
 * - Use type-safe variants for consistency
 */

export type GradientVariant = 
  | 'primary'        // Blue to purple (default brand gradient)
  | 'success'        // Green gradient (savings, approvals)
  | 'danger'         // Red gradient (high utilization, errors)
  | 'warning'        // Orange gradient (warnings, variable income)
  | 'info'           // Blue gradient (informative, subscriptions)
  | 'purple'         // Purple gradient (cash flow optimizer)
  | 'gray';          // Gray gradient (insufficient data, neutral)

export type GradientType = 'background' | 'text' | 'border';

/**
 * Get Tailwind classes for a gradient.
 * 
 * Why: This function provides a consistent way to apply gradients across the app.
 * Instead of writing long gradient strings in every component, we use this helper.
 * 
 * @param variant - The color variant for the gradient
 * @param type - Whether to apply to background, text, or border
 * @returns CSS class string to apply to an element
 */
export function getGradientClasses(
  variant: GradientVariant = 'primary',
  type: GradientType = 'background'
): string {
  const baseClasses = {
    primary: {
      background: 'bg-gradient-primary',
      text: 'text-gradient-primary',
      border: 'border-gradient-primary',
    },
    success: {
      background: 'bg-gradient-success',
      text: 'text-gradient-success',
      border: 'border-gradient-success',
    },
    danger: {
      background: 'bg-gradient-danger',
      text: 'text-gradient-danger',
      border: 'border-gradient-danger',
    },
    warning: {
      background: 'bg-gradient-warning',
      text: 'text-gradient-warning',
      border: 'border-gradient-warning',
    },
    info: {
      background: 'bg-gradient-info',
      text: 'text-gradient-info',
      border: 'border-gradient-info',
    },
    purple: {
      background: 'bg-gradient-to-r from-purple-600 to-purple-400',
      text: 'bg-gradient-to-r from-purple-600 to-purple-400 bg-clip-text text-transparent',
      border: 'border-gradient-purple',
    },
    gray: {
      background: 'bg-gradient-to-r from-gray-500 to-gray-400',
      text: 'bg-gradient-to-r from-gray-500 to-gray-400 bg-clip-text text-transparent',
      border: 'border-gradient-gray',
    },
  };

  return baseClasses[variant][type];
}

/**
 * Get inline CSS gradient style for more control.
 * 
 * Why: Sometimes we need inline styles instead of classes (e.g., in Recharts components).
 * This function returns the actual gradient CSS value.
 * 
 * @param variant - The color variant for the gradient
 * @returns CSS gradient string
 */
export function getGradientStyle(variant: GradientVariant = 'primary'): string {
  const gradients = {
    primary: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
    success: 'linear-gradient(135deg, #059669 0%, #10B981 100%)',
    danger: 'linear-gradient(135deg, #DC2626 0%, #EF4444 100%)',
    warning: 'linear-gradient(135deg, #EA580C 0%, #F59E0B 100%)',
    info: 'linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)',
    purple: 'linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%)',
    gray: 'linear-gradient(135deg, #6B7280 0%, #9CA3AF 100%)',
  };

  return gradients[variant];
}

/**
 * Get solid color from gradient variant (uses the end color).
 * 
 * Why: For simple use cases where we need a single color that matches the gradient theme.
 * Useful for chart data points, borders, etc.
 * 
 * @param variant - The color variant
 * @returns Hex color code
 */
export function getGradientColor(variant: GradientVariant = 'primary'): string {
  const colors = {
    primary: '#8B5CF6',    // Purple end of gradient
    success: '#10B981',    // Green
    danger: '#EF4444',     // Red
    warning: '#F59E0B',    // Orange
    info: '#3B82F6',       // Blue
    purple: '#8B5CF6',     // Purple
    gray: '#9CA3AF',       // Gray
  };

  return colors[variant];
}

/**
 * Get an array of gradient colors for multi-color charts.
 * 
 * Why: Charts often need multiple colors. This provides a harmonious set
 * that matches our design system.
 * 
 * @returns Array of hex color codes
 */
export function getChartColors(): string[] {
  return [
    '#3B82F6',  // Blue
    '#10B981',  // Green
    '#8B5CF6',  // Purple
    '#F59E0B',  // Orange
    '#EF4444',  // Red
    '#06B6D4',  // Cyan
  ];
}

/**
 * Get persona-specific gradient variant.
 * 
 * Why: Each persona has its own color scheme based on priority and meaning.
 * This maps persona IDs to the appropriate gradient variant.
 * 
 * @param personaId - The persona identifier
 * @returns Gradient variant for the persona
 */
export function getPersonaGradient(personaId: string): GradientVariant {
  const personaMap: Record<string, GradientVariant> = {
    'high_utilization': 'danger',           // Red - urgent, high priority
    'variable_income_budgeter': 'warning',  // Orange - caution
    'subscription_heavy': 'info',           // Blue - informative
    'savings_builder': 'success',           // Green - positive
    'cash_flow_optimizer': 'purple',        // Purple - strategic
    'insufficient_data': 'gray',            // Gray - neutral
  };

  return personaMap[personaId] || 'primary';
}

