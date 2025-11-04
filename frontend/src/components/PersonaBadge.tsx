/**
 * PersonaBadge Component
 * 
 * Why this exists:
 * - Displays assigned persona with color coding
 * - Shows time window (30d/180d)
 * - Visual indicator of user's financial behavior category
 */

import { Badge } from '@/components/ui/badge'
import type { PersonaAssignment } from '@/lib/api'

interface PersonaBadgeProps {
  persona: PersonaAssignment | null | undefined
  className?: string
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

/**
 * Get color variant for persona.
 * 
 * Why this exists:
 * - Visual differentiation of personas
 * - High Utilization = red (highest priority/concern)
 * - Savings Builder = green (positive behavior)
 * - Others = neutral/blue tones
 */
function getPersonaVariant(personaId: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (personaId === 'high_utilization') return 'destructive'
  if (personaId === 'savings_builder') return 'default'
  if (personaId === 'insufficient_data') return 'outline'
  return 'secondary'
}

export function PersonaBadge({ persona, className }: PersonaBadgeProps) {
  if (!persona) {
    return (
      <Badge variant="outline" className={className}>
        No Persona Assigned
      </Badge>
    )
  }

  return (
    <div className={className}>
      <Badge variant={getPersonaVariant(persona.persona_id)} className="text-sm">
        {getPersonaLabel(persona.persona_id)} ({persona.window_days}d)
      </Badge>
    </div>
  )
}

