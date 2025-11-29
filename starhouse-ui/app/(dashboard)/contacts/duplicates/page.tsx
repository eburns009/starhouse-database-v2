'use client'

import { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, RefreshCw, AlertCircle, ArrowLeft, Users } from 'lucide-react'
import Link from 'next/link'
import { DuplicateSetList } from '@/components/duplicates/DuplicateSetList'
import { DuplicateSetDetail } from '@/components/duplicates/DuplicateSetDetail'

export interface DuplicateSet {
  normalized_name: string
  contact_count: number
  contact_ids: string[]
  emails: string[]
  oldest_created: string
}

export default function DuplicatesPage() {
  const [duplicateSets, setDuplicateSets] = useState<DuplicateSet[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSet, setSelectedSet] = useState<DuplicateSet | null>(null)

  const fetchDuplicates = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { data, error: fetchError } = await supabase
        .from('v_name_based_duplicates')
        .select('*')
        .order('contact_count', { ascending: false })

      if (fetchError) throw fetchError

      setDuplicateSets(data || [])
    } catch (err) {
      console.error('Error fetching duplicates:', err)
      setError(err instanceof Error ? err.message : 'Failed to load duplicates')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDuplicates()
  }, [fetchDuplicates])

  const handleMergeComplete = useCallback(() => {
    setSelectedSet(null)
    fetchDuplicates()
  }, [fetchDuplicates])

  // Loading state
  if (loading && duplicateSets.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading duplicate contacts...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto p-8">
        <Card className="max-w-lg mx-auto">
          <CardHeader>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <CardTitle>Failed to Load Duplicates</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-4">{error}</p>
            <Button onClick={fetchDuplicates} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Link href="/contacts">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Users className="h-8 w-8 text-primary" />
              Duplicate Contacts
            </h1>
            <p className="text-slate-500 mt-1">
              Review and merge duplicate contact records
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-500">
            {duplicateSets.length} duplicate {duplicateSets.length === 1 ? 'set' : 'sets'} found
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchDuplicates}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      {selectedSet ? (
        <DuplicateSetDetail
          duplicateSet={selectedSet}
          onBack={() => setSelectedSet(null)}
          onMergeComplete={handleMergeComplete}
        />
      ) : duplicateSets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Users className="h-12 w-12 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              No Duplicates Found
            </h3>
            <p className="text-slate-500 max-w-md mx-auto">
              All contacts have been deduplicated. New duplicates will appear here
              as data is imported from external systems.
            </p>
          </CardContent>
        </Card>
      ) : (
        <DuplicateSetList
          duplicateSets={duplicateSets}
          onSelectSet={setSelectedSet}
        />
      )}
    </div>
  )
}
