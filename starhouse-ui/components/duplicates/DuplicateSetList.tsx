'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ChevronRight, Mail } from 'lucide-react'
import type { DuplicateSet } from '@/app/(dashboard)/contacts/duplicates/page'

interface DuplicateSetListProps {
  duplicateSets: DuplicateSet[]
  onSelectSet: (set: DuplicateSet) => void
}

export function DuplicateSetList({ duplicateSets, onSelectSet }: DuplicateSetListProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Duplicate Sets</CardTitle>
        <CardDescription>
          Click a set to review and merge contacts. Sets are sorted by contact count (most duplicates first).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-slate-100">
          {duplicateSets.map((set) => (
            <button
              key={set.normalized_name}
              onClick={() => onSelectSet(set)}
              className="w-full text-left px-4 py-4 hover:bg-slate-50 transition-colors flex items-center gap-4 group first:rounded-t-lg last:rounded-b-lg"
            >
              {/* Contact count badge */}
              <div className="flex-shrink-0">
                <Badge variant="secondary" className="h-10 w-10 rounded-full flex items-center justify-center text-lg font-semibold">
                  {set.contact_count}
                </Badge>
              </div>

              {/* Main content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-slate-900 capitalize">
                    {set.normalized_name}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {set.contact_count} contacts
                  </Badge>
                </div>

                {/* Emails preview */}
                <div className="flex items-center gap-1 text-sm text-slate-500">
                  <Mail className="h-3.5 w-3.5 flex-shrink-0" />
                  <span className="truncate">
                    {set.emails.slice(0, 2).join(', ')}
                    {set.emails.length > 2 && ` +${set.emails.length - 2} more`}
                  </span>
                </div>

                {/* Oldest created date */}
                <div className="text-xs text-slate-400 mt-1">
                  Oldest record: {new Date(set.oldest_created).toLocaleDateString()}
                </div>
              </div>

              {/* Chevron indicator */}
              <ChevronRight className="h-5 w-5 text-slate-400 flex-shrink-0 group-hover:text-slate-600 transition-colors" />
            </button>
          ))}
        </div>

        {duplicateSets.length > 20 && (
          <div className="text-center text-sm text-slate-500 mt-4 pt-4 border-t">
            Showing all {duplicateSets.length} duplicate sets
          </div>
        )}
      </CardContent>
    </Card>
  )
}
