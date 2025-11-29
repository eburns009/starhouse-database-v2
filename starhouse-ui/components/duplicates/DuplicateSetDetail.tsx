'use client'

import { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Check,
  Crown,
  Calendar,
  Mail,
  DollarSign,
  Receipt,
  Tag,
  StickyNote,
  Link as LinkIcon,
  GitMerge
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { MergeConfirmationDialog } from './MergeConfirmationDialog'
import type { DuplicateSet } from '@/app/(dashboard)/contacts/duplicates/page'

interface ContactStats {
  contact_id: string
  email: string
  first_name: string
  last_name: string
  created_at: string
  transaction_count: number
  donation_total: number
  subscription_count: number
  tags_count: number
  notes_count: number
  external_ids_count: number
}

interface DuplicateSetDetailProps {
  duplicateSet: DuplicateSet
  onBack: () => void
  onMergeComplete: () => void
}

export function DuplicateSetDetail({ duplicateSet, onBack, onMergeComplete }: DuplicateSetDetailProps) {
  const [contacts, setContacts] = useState<ContactStats[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedWinnerId, setSelectedWinnerId] = useState<string | null>(null)
  const [showMergeDialog, setShowMergeDialog] = useState(false)

  const fetchContactStats = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data, error: fetchError } = await supabase
        .rpc('get_contact_merge_stats', { p_contact_ids: duplicateSet.contact_ids })

      if (fetchError) throw fetchError

      setContacts(data || [])

      // Auto-select recommended winner (oldest created_at or most transactions)
      if (data && data.length > 0) {
        const recommended = [...data].sort((a, b) => {
          // Primary: most transactions
          if (b.transaction_count !== a.transaction_count) {
            return b.transaction_count - a.transaction_count
          }
          // Secondary: oldest created_at
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        })[0]
        setSelectedWinnerId(recommended.contact_id)
      }
    } catch (err) {
      console.error('Error fetching contact stats:', err)
      setError(err instanceof Error ? err.message : 'Failed to load contact details')
    } finally {
      setLoading(false)
    }
  }, [duplicateSet.contact_ids])

  useEffect(() => {
    fetchContactStats()
  }, [fetchContactStats])

  const selectedWinner = contacts.find(c => c.contact_id === selectedWinnerId)
  const losers = contacts.filter(c => c.contact_id !== selectedWinnerId)

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading contact details...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <CardTitle>Failed to Load Details</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-600 mb-4">{error}</p>
          <div className="flex gap-2">
            <Button onClick={onBack} variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to List
            </Button>
            <Button onClick={fetchContactStats} variant="outline">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold capitalize">{duplicateSet.normalized_name}</h2>
            <p className="text-slate-500">
              {contacts.length} duplicate contacts to merge
            </p>
          </div>
        </div>

        <Button
          onClick={() => setShowMergeDialog(true)}
          disabled={!selectedWinnerId || contacts.length < 2}
          className="gap-2"
        >
          <GitMerge className="h-4 w-4" />
          Merge Contacts
        </Button>
      </div>

      {/* Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <Crown className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Select the winner contact</p>
              <p className="text-blue-700">
                Click a contact card to select it as the winner. All data from other contacts
                will be merged into the winner. The contact with the most activity is recommended.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contact Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {contacts.map((contact) => {
          const isWinner = contact.contact_id === selectedWinnerId
          const isRecommended = contacts.length > 0 &&
            [...contacts].sort((a, b) => {
              if (b.transaction_count !== a.transaction_count) {
                return b.transaction_count - a.transaction_count
              }
              return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            })[0].contact_id === contact.contact_id

          return (
            <Card
              key={contact.contact_id}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md',
                isWinner
                  ? 'ring-2 ring-primary border-primary bg-primary/5'
                  : 'hover:border-slate-300'
              )}
              onClick={() => setSelectedWinnerId(contact.contact_id)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base flex items-center gap-2">
                      {contact.first_name} {contact.last_name}
                      {isWinner && (
                        <Check className="h-4 w-4 text-primary flex-shrink-0" />
                      )}
                    </CardTitle>
                    <CardDescription className="truncate flex items-center gap-1 mt-1">
                      <Mail className="h-3 w-3" />
                      {contact.email}
                    </CardDescription>
                  </div>
                  {isRecommended && (
                    <Badge variant="secondary" className="flex-shrink-0 ml-2 gap-1">
                      <Crown className="h-3 w-3" />
                      <span className="hidden sm:inline">Recommended</span>
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  {/* Created date */}
                  <div className="flex items-center gap-2 text-slate-600">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span>Created {new Date(contact.created_at).toLocaleDateString()}</span>
                  </div>

                  {/* Stats grid */}
                  <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                    <StatItem
                      icon={Receipt}
                      label="Transactions"
                      value={contact.transaction_count}
                      highlight={contact.transaction_count > 0}
                    />
                    <StatItem
                      icon={DollarSign}
                      label="Donations"
                      value={`$${contact.donation_total.toLocaleString()}`}
                      highlight={contact.donation_total > 0}
                    />
                    <StatItem
                      icon={Tag}
                      label="Tags"
                      value={contact.tags_count}
                      highlight={contact.tags_count > 0}
                    />
                    <StatItem
                      icon={StickyNote}
                      label="Notes"
                      value={contact.notes_count}
                      highlight={contact.notes_count > 0}
                    />
                    <StatItem
                      icon={LinkIcon}
                      label="External IDs"
                      value={contact.external_ids_count}
                      highlight={contact.external_ids_count > 0}
                    />
                    <StatItem
                      icon={Receipt}
                      label="Subscriptions"
                      value={contact.subscription_count}
                      highlight={contact.subscription_count > 0}
                    />
                  </div>
                </div>

                {/* Winner indicator */}
                {isWinner && (
                  <div className="mt-3 pt-3 border-t border-primary/20">
                    <Badge className="w-full justify-center">
                      <Crown className="h-3 w-3 mr-1" />
                      Selected as Winner
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Merge Preview */}
      {selectedWinner && losers.length > 0 && (
        <Card className="bg-slate-50">
          <CardHeader>
            <CardTitle className="text-lg">Merge Preview</CardTitle>
            <CardDescription>
              What will happen when you merge these contacts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <Badge variant="default" className="gap-1">
                  <Crown className="h-3 w-3" />
                  Winner
                </Badge>
                <span className="font-medium">{selectedWinner.email}</span>
                <span className="text-slate-500">will be kept</span>
              </div>

              <div className="border-l-2 border-slate-300 pl-4 ml-3 space-y-2">
                {losers.map((loser) => (
                  <div key={loser.contact_id} className="flex items-center gap-2 text-slate-600">
                    <GitMerge className="h-3.5 w-3.5 text-slate-400" />
                    <span>{loser.email}</span>
                    <span className="text-slate-400">will be merged</span>
                    {loser.transaction_count > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {loser.transaction_count} transactions
                      </Badge>
                    )}
                  </div>
                ))}
              </div>

              <div className="pt-2 text-slate-500">
                <strong>After merge:</strong> All transactions, tags, notes, and external IDs
                from merged contacts will be transferred to the winner.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Merge Confirmation Dialog */}
      <MergeConfirmationDialog
        open={showMergeDialog}
        onOpenChange={setShowMergeDialog}
        winner={selectedWinner || null}
        losers={losers}
        onMergeComplete={onMergeComplete}
      />
    </div>
  )
}

interface StatItemProps {
  icon: React.ElementType
  label: string
  value: number | string
  highlight?: boolean
}

function StatItem({ icon: Icon, label, value, highlight }: StatItemProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-1.5 text-xs',
        highlight ? 'text-slate-700 font-medium' : 'text-slate-500'
      )}
      title={label}
    >
      <Icon className={cn(
        'h-3 w-3',
        highlight ? 'text-primary' : 'text-slate-400'
      )} />
      <span>{value}</span>
    </div>
  )
}
