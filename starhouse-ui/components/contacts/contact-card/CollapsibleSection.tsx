'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface CollapsibleSectionProps {
  title: string
  count?: number
  icon: React.ReactNode
  defaultOpen?: boolean
  children: React.ReactNode
  emptyMessage?: string
  isEmpty?: boolean
}

/**
 * Collapsible section for contact card
 * FAANG Standard: Reusable component following research recommendations
 */
export function CollapsibleSection({
  title,
  count,
  icon,
  defaultOpen = false,
  children,
  emptyMessage = 'No data available',
  isEmpty = false,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <Card className="shadow-sm">
      <CardHeader
        className="cursor-pointer select-none py-3 px-4"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <span className="text-muted-foreground">{icon}</span>
            {title}
            {count !== undefined && count > 0 && (
              <Badge variant="secondary" className="text-xs">
                {count}
              </Badge>
            )}
          </CardTitle>
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </div>
      </CardHeader>
      {isOpen && (
        <CardContent className="pt-0 pb-4 px-4">
          {isEmpty ? (
            <p className="text-sm text-muted-foreground italic text-center py-4">
              {emptyMessage}
            </p>
          ) : (
            children
          )}
        </CardContent>
      )}
    </Card>
  )
}
