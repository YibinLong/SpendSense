/**
 * PersonaBadge Component
 * 
 * Why this exists:
 * - Displays assigned persona with gradient backgrounds and icons
 * - Shows time window (30d/180d)
 * - Visual indicator of user's financial behavior category
 * - Modern design with hover effects for interactive feel
 */

import { cn } from '@/lib/utils'
import { getPersonaIcon } from '@/lib/iconMap'
import { getPersonaGradient, getGradientClasses } from '@/lib/gradients'
import type { PersonaAssignment } from '@/lib/api'

interface PersonaBadgeProps {
  persona: PersonaAssignment | null | undefined
  className?: string
  /** Whether to show in compact mode (smaller, no window days) */
  compact?: boolean
}

/**
 * Get display name for persona ID.
 * 
 * Why this exists:
 * - Converts snake_case persona_id to readable labels
 * - Centralizes persona naming logic
 */
function getPersonaLabel(personaId: string): string {
  const labels: Record<string, string> = {
    'high_utilization': 'High Utilization',
    'variable_income_budgeter': 'Variable Income',
    'subscription_heavy': 'Subscription Heavy',
    'savings_builder': 'Savings Builder',
    'cash_flow_optimizer': 'Cash Flow Optimizer',
    'insufficient_data': 'Insufficient Data',
  }
  return labels[personaId] || personaId
}

export function PersonaBadge({ persona, className, compact = false }: PersonaBadgeProps) {
  if (!persona) {
    return (
      <div className={cn(
        "inline-flex items-center gap-2 rounded-lg border-2 border-dashed border-muted-foreground/30 px-4 py-2 text-sm text-muted-foreground",
        className
      )}>
        <span>No Persona Assigned</span>
      </div>
    )
  }

  const Icon = getPersonaIcon(persona.persona_id)
  const gradientVariant = getPersonaGradient(persona.persona_id)
  const gradientClass = getGradientClasses(gradientVariant, 'background')

  return (
    <div className={cn(
      "inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-white shadow-md transition-all duration-200 hover:shadow-lg hover:scale-105",
      gradientClass,
      className
    )}>
      {/* Icon */}
      <Icon className="h-5 w-5" strokeWidth={2} />
      
      {/* Label */}
      <span className="font-semibold text-sm">
        {getPersonaLabel(persona.persona_id)}
      </span>
      
      {/* Window days (if not compact) */}
      {!compact && (
        <span className="text-xs opacity-90 ml-1">
          ({persona.window_days}d)
        </span>
      )}
    </div>
  )
}


