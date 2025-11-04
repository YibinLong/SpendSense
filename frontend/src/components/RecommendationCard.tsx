/**
 * RecommendationCard Component
 * 
 * Why this exists:
 * - Displays education items and partner offers
 * - Shows rationale with concrete data points
 * - Always displays mandatory disclosure (PRD requirement)
 * - Type badge differentiates education vs offers
 */

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { RecommendationItem } from '@/lib/api'

interface RecommendationCardProps {
  recommendation: RecommendationItem
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg">{recommendation.title}</CardTitle>
          <Badge variant={recommendation.item_type === 'education' ? 'secondary' : 'default'}>
            {recommendation.item_type}
          </Badge>
        </div>
        {recommendation.description && (
          <CardDescription>{recommendation.description}</CardDescription>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Rationale - the "because" with concrete data */}
        {recommendation.rationale && (
          <div className="rounded-lg bg-muted p-3">
            <p className="text-sm font-medium mb-1">Why this recommendation:</p>
            <p className="text-sm text-muted-foreground">{recommendation.rationale}</p>
          </div>
        )}

        {/* Mandatory Disclosure - PRD requirement */}
        {recommendation.disclosure && (
          <div className="border-t pt-3">
            <p className="text-xs text-muted-foreground italic">{recommendation.disclosure}</p>
          </div>
        )}
      </CardContent>

      {/* Call-to-action if URL provided */}
      {recommendation.url && (
        <CardFooter>
          <Button asChild variant="outline" className="w-full">
            <a href={recommendation.url} target="_blank" rel="noopener noreferrer">
              Learn More
            </a>
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}


