/**
 * RecommendationCard Component
 * 
 * Why this exists:
 * - Displays education items and partner offers with modern card design
 * - Shows rationale with concrete data points
 * - Always displays mandatory disclosure (PRD requirement)
 * - Type-specific icons and gradient accents
 * - Hover effects for better interactivity
 */

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getItemTypeIcon } from '@/lib/iconMap'
import { cn } from '@/lib/utils'
import type { RecommendationItem } from '@/lib/api'

interface RecommendationCardProps {
  recommendation: RecommendationItem
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const Icon = getItemTypeIcon(recommendation.item_type);
  const isOffer = recommendation.item_type === 'offer';
  
  return (
    <Card className={cn(
      "hover-lift overflow-hidden transition-all duration-200",
      isOffer && "border-primary/50"
    )}>
      {/* Gradient accent bar at top - different color for offers */}
      <div className={cn(
        "h-1",
        isOffer ? "bg-gradient-to-r from-purple-500 to-pink-500" : "bg-gradient-primary"
      )} />
      
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1">
            {/* Icon with gradient background */}
            <div className={cn(
              "rounded-lg p-2.5 mt-0.5",
              isOffer 
                ? "bg-gradient-to-br from-purple-100 to-pink-100" 
                : "bg-gradient-to-br from-blue-100 to-purple-100"
            )}>
              <Icon className={cn(
                "h-5 w-5",
                isOffer ? "text-purple-600" : "text-blue-600"
              )} strokeWidth={2} />
            </div>
            
            <div className="flex-1">
              <CardTitle className="text-lg leading-tight">{recommendation.title}</CardTitle>
              {recommendation.description && (
                <CardDescription className="mt-1.5 line-clamp-2">{recommendation.description}</CardDescription>
              )}
            </div>
          </div>
          
          {/* Type badge */}
          <Badge 
            variant={isOffer ? 'default' : 'secondary'}
            className={cn(
              "capitalize shrink-0",
              isOffer && "bg-gradient-to-r from-purple-600 to-pink-600 text-white border-none"
            )}
          >
            {recommendation.item_type}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Rationale - the "because" with concrete data */}
        {recommendation.rationale && (
          <div className="rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 p-3.5 border border-blue-100 dark:border-blue-900/30">
            <p className="text-sm font-semibold mb-1.5 text-foreground">Why this recommendation:</p>
            <p className="text-sm text-muted-foreground leading-relaxed">{recommendation.rationale}</p>
          </div>
        )}

        {/* Mandatory Disclosure - PRD requirement */}
        {recommendation.disclosure && (
          <div className="border-t pt-3">
            <p className="text-xs text-muted-foreground italic leading-relaxed">{recommendation.disclosure}</p>
          </div>
        )}
      </CardContent>

      {/* Call-to-action if URL provided */}
      {recommendation.url && (
        <CardFooter className="pt-4">
          <Button 
            asChild 
            variant={isOffer ? "gradient" : "outline"}
            className="w-full"
            size="default"
          >
            <a href={recommendation.url} target="_blank" rel="noopener noreferrer">
              {isOffer ? "View Offer" : "Learn More"}
            </a>
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}


