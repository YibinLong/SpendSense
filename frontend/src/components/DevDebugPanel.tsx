/**
 * DevDebugPanel Component
 * 
 * Why this exists:
 * - Shows decision traces and raw API data for debugging
 * - Only visible when import.meta.env.DEV && VITE_SHOW_DEBUG is true
 * - Helps developers understand recommendation logic
 */

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { isDevMode } from '@/lib/utils'

interface DevDebugPanelProps {
  title?: string
  data: any
}

export function DevDebugPanel({ title = 'Debug Data', data }: DevDebugPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Only render in dev mode
  if (!isDevMode()) {
    return null
  }

  return (
    <Card className="border-dashed border-2 border-yellow-500 bg-yellow-50/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm text-yellow-900">🔧 {title}</CardTitle>
            <CardDescription className="text-yellow-700">
              Dev mode only - hidden in production
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </Button>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent>
          <pre className="text-xs overflow-auto max-h-96 bg-white p-4 rounded border">
            {JSON.stringify(data, null, 2)}
          </pre>
        </CardContent>
      )}
    </Card>
  )
}


