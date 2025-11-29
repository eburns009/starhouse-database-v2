'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Loader2, AlertTriangle, Crown, GitMerge, CheckCircle, ArrowRight } from 'lucide-react'

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

interface MergeConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  winner: ContactStats | null
  losers: ContactStats[]
  onMergeComplete: () => void
}

interface MergeResult {
  success: boolean
  loserEmail: string
  result?: {
    transactions_reassigned: number
    subscriptions_reassigned: number
    tags_reassigned: number
    notes_reassigned: number
    external_ids_reassigned: number
    emails_merged: number
    donors_reassigned: number
  }
  error?: string
}

export function MergeConfirmationDialog({
  open,
  onOpenChange,
  winner,
  losers,
  onMergeComplete,
}: MergeConfirmationDialogProps) {
  const [isMerging, setIsMerging] = useState(false)
  const [mergeResults, setMergeResults] = useState<MergeResult[]>([])
  const [mergeComplete, setMergeComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClose = () => {
    if (mergeComplete) {
      onMergeComplete()
    }
    setMergeResults([])
    setMergeComplete(false)
    setError(null)
    onOpenChange(false)
  }

  const handleMerge = async () => {
    if (!winner || losers.length === 0) return

    setIsMerging(true)
    setError(null)
    const results: MergeResult[] = []

    try {
      const supabase = createClient()

      // Merge each loser into winner
      for (const loser of losers) {
        const { data, error: mergeError } = await supabase.rpc('merge_contacts', {
          p_winner_id: winner.contact_id,
          p_loser_id: loser.contact_id,
        })

        if (mergeError) {
          results.push({
            success: false,
            loserEmail: loser.email,
            error: mergeError.message,
          })
        } else {
          results.push({
            success: true,
            loserEmail: loser.email,
            result: data,
          })
        }
      }

      setMergeResults(results)
      setMergeComplete(true)

      // Check if all merges succeeded
      const allSuccess = results.every((r) => r.success)
      if (!allSuccess) {
        setError('Some merges failed. See details below.')
      }
    } catch (err) {
      console.error('Merge error:', err)
      setError(err instanceof Error ? err.message : 'Failed to merge contacts')
    } finally {
      setIsMerging(false)
    }
  }

  if (!winner) return null

  // Calculate totals being moved
  const totalTransactions = losers.reduce((sum, l) => sum + l.transaction_count, 0)
  const totalTags = losers.reduce((sum, l) => sum + l.tags_count, 0)
  const totalNotes = losers.reduce((sum, l) => sum + l.notes_count, 0)
  const totalDonations = losers.reduce((sum, l) => sum + l.donation_total, 0)

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {mergeComplete ? 'Merge Complete' : 'Confirm Contact Merge'}
          </DialogTitle>
          <DialogDescription>
            {mergeComplete
              ? 'The contacts have been merged successfully.'
              : 'This action cannot be undone. Please review the merge details.'}
          </DialogDescription>
        </DialogHeader>

        {mergeComplete ? (
          // Success state
          <div className="space-y-4">
            <div className="rounded-md bg-green-50 p-4 text-green-800">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="font-medium">Merge Successful</span>
              </div>
              <p className="text-sm text-green-700">
                {losers.length} contact{losers.length > 1 ? 's' : ''} merged into{' '}
                <strong>{winner.email}</strong>
              </p>
            </div>

            {/* Results detail */}
            <div className="space-y-2">
              {mergeResults.map((result, idx) => (
                <div
                  key={idx}
                  className={`rounded-md p-3 text-sm ${
                    result.success ? 'bg-slate-50' : 'bg-red-50'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {result.success ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                    )}
                    <span className="font-medium">{result.loserEmail}</span>
                    <ArrowRight className="h-3 w-3 text-slate-400" />
                    <span className="text-slate-600">{winner.email}</span>
                  </div>
                  {result.success && result.result && (
                    <div className="flex flex-wrap gap-2 mt-2 ml-6">
                      {result.result.transactions_reassigned > 0 && (
                        <Badge variant="secondary">
                          {result.result.transactions_reassigned} transactions
                        </Badge>
                      )}
                      {result.result.tags_reassigned > 0 && (
                        <Badge variant="secondary">
                          {result.result.tags_reassigned} tags
                        </Badge>
                      )}
                      {result.result.notes_reassigned > 0 && (
                        <Badge variant="secondary">
                          {result.result.notes_reassigned} notes
                        </Badge>
                      )}
                      {result.result.subscriptions_reassigned > 0 && (
                        <Badge variant="secondary">
                          {result.result.subscriptions_reassigned} subscriptions
                        </Badge>
                      )}
                      {result.result.external_ids_reassigned > 0 && (
                        <Badge variant="secondary">
                          {result.result.external_ids_reassigned} external IDs
                        </Badge>
                      )}
                      {result.result.emails_merged > 0 && (
                        <Badge variant="secondary">
                          {result.result.emails_merged} email aliases
                        </Badge>
                      )}
                    </div>
                  )}
                  {!result.success && (
                    <p className="text-red-600 ml-6">{result.error}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          // Confirmation state
          <div className="space-y-4">
            {/* Warning */}
            <div className="flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium">This action cannot be undone</div>
                <p className="mt-1">
                  The merged contacts will be soft-deleted and their data transferred to the winner.
                </p>
              </div>
            </div>

            {/* Winner */}
            <div className="rounded-md bg-green-50 p-4">
              <div className="flex items-center gap-2 text-green-800 mb-2">
                <Crown className="h-4 w-4" />
                <span className="font-medium">Winner (will be kept)</span>
              </div>
              <div className="text-sm text-green-700">
                <p className="font-medium">{winner.first_name} {winner.last_name}</p>
                <p>{winner.email}</p>
                <p className="text-green-600 mt-1">
                  {winner.transaction_count} transactions, ${winner.donation_total.toLocaleString()} donations
                </p>
              </div>
            </div>

            {/* Losers */}
            <div className="rounded-md bg-slate-100 p-4">
              <div className="flex items-center gap-2 text-slate-700 mb-2">
                <GitMerge className="h-4 w-4" />
                <span className="font-medium">
                  To be merged ({losers.length} contact{losers.length > 1 ? 's' : ''})
                </span>
              </div>
              <div className="space-y-2">
                {losers.map((loser) => (
                  <div key={loser.contact_id} className="text-sm text-slate-600">
                    <p className="font-medium">{loser.email}</p>
                    <p className="text-slate-500">
                      {loser.transaction_count} transactions, {loser.tags_count} tags, {loser.notes_count} notes
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Summary of what will be moved */}
            {(totalTransactions > 0 || totalTags > 0 || totalNotes > 0) && (
              <div className="rounded-md bg-blue-50 p-4 text-sm text-blue-800">
                <p className="font-medium mb-1">Data to be transferred:</p>
                <div className="flex flex-wrap gap-2">
                  {totalTransactions > 0 && (
                    <Badge variant="secondary">{totalTransactions} transactions</Badge>
                  )}
                  {totalDonations > 0 && (
                    <Badge variant="secondary">${totalDonations.toLocaleString()} donations</Badge>
                  )}
                  {totalTags > 0 && (
                    <Badge variant="secondary">{totalTags} tags</Badge>
                  )}
                  {totalNotes > 0 && (
                    <Badge variant="secondary">{totalNotes} notes</Badge>
                  )}
                </div>
              </div>
            )}

            {/* API Error */}
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                {error}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          {mergeComplete ? (
            <Button onClick={handleClose}>
              Done
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isMerging}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                onClick={handleMerge}
                disabled={isMerging}
                className="gap-2"
              >
                {isMerging && <Loader2 className="h-4 w-4 animate-spin" />}
                {isMerging ? 'Merging...' : `Merge ${losers.length} Contact${losers.length > 1 ? 's' : ''}`}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
