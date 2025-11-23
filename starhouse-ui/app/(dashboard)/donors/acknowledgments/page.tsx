/**
 * Pending Acknowledgments Page
 * FAANG Standards:
 * - Comprehensive data fetching with pagination
 * - Bulk actions with optimistic updates
 * - Accessible table with proper ARIA labels
 * - Error handling with user feedback
 */

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  MoreHorizontal,
  Send,
  CheckCircle,
  SkipForward,
  User,
  ChevronLeft,
  ChevronRight,
  Clock,
  DollarSign,
  Mail,
} from 'lucide-react'

interface Acknowledgment {
  acknowledgment_id: string
  status: 'pending_review' | 'auto_queued'
  donor_name: string
  donation_amount: number
  donation_date: string
  fund_designation: string | null
  queued_at: string
  email: string | null
  first_name: string | null
  last_name: string | null
  transaction_id: string
  donation_source: string
  donor_id?: string
}

interface SummaryStats {
  totalPending: number
  totalAmount: number
  oldestDate: string | null
}

type StatusFilter = 'all' | 'pending_review' | 'auto_queued'
type SortOption = 'oldest' | 'newest' | 'amount_high'

const PAGE_SIZE = 50

export default function PendingAcknowledgmentsPage() {
  const [acknowledgments, setAcknowledgments] = useState<Acknowledgment[]>([])
  const [stats, setStats] = useState<SummaryStats>({ totalPending: 0, totalAmount: 0, oldestDate: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortOption, setSortOption] = useState<SortOption>('oldest')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [actionLoading, setActionLoading] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  const supabase = createClient()

  // Fetch acknowledgments
  async function fetchAcknowledgments() {
    setLoading(true)
    setError(null)

    try {
      // Build query
      let query = supabase
        .from('v_pending_acknowledgments')
        .select('*', { count: 'exact' })

      // Apply status filter
      if (statusFilter === 'pending_review') {
        query = query.eq('status', 'pending_review')
      } else if (statusFilter === 'auto_queued') {
        query = query.eq('status', 'auto_queued')
      }

      // Apply sorting
      if (sortOption === 'oldest') {
        query = query.order('queued_at', { ascending: true })
      } else if (sortOption === 'newest') {
        query = query.order('queued_at', { ascending: false })
      } else if (sortOption === 'amount_high') {
        query = query.order('donation_amount', { ascending: false })
      }

      // Apply pagination
      const from = (currentPage - 1) * PAGE_SIZE
      const to = from + PAGE_SIZE - 1
      query = query.range(from, to)

      const { data, error: fetchError, count } = await query

      if (fetchError) {
        console.error('Error fetching acknowledgments:', fetchError)
        setError(fetchError.message)
        return
      }

      setAcknowledgments(data || [])
      setTotalCount(count || 0)
    } catch (err) {
      console.error('Unexpected error:', err)
      setError('Failed to load acknowledgments')
    } finally {
      setLoading(false)
    }
  }

  // Fetch summary stats
  async function fetchStats() {
    try {
      const { data, error: statsError } = await supabase
        .from('v_pending_acknowledgments')
        .select('donation_amount, queued_at')

      if (statsError) {
        console.error('Error fetching stats:', statsError)
        return
      }

      if (data && data.length > 0) {
        const totalAmount = data.reduce((sum: number, row: { donation_amount: number | null }) => sum + (row.donation_amount || 0), 0)
        const dates = data.map((row: { queued_at: string }) => new Date(row.queued_at).getTime())
        const oldestDate = new Date(Math.min(...dates)).toISOString()

        setStats({
          totalPending: data.length,
          totalAmount,
          oldestDate,
        })
      } else {
        setStats({ totalPending: 0, totalAmount: 0, oldestDate: null })
      }
    } catch (err) {
      console.error('Error fetching stats:', err)
    }
  }

  useEffect(() => {
    fetchAcknowledgments()
    fetchStats()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, sortOption, currentPage])

  // Show toast with auto-dismiss
  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  // Handle select all on current page
  function handleSelectAll(checked: boolean) {
    if (checked) {
      const allIds = new Set(acknowledgments.map(a => a.acknowledgment_id))
      setSelectedIds(allIds)
    } else {
      setSelectedIds(new Set())
    }
  }

  // Handle individual selection
  function handleSelectOne(id: string, checked: boolean) {
    const newSelected = new Set(selectedIds)
    if (checked) {
      newSelected.add(id)
    } else {
      newSelected.delete(id)
    }
    setSelectedIds(newSelected)
  }

  // Bulk action: Send selected (placeholder)
  async function handleSendSelected() {
    if (selectedIds.size === 0) return
    showToast(`Would send ${selectedIds.size} acknowledgments (email sending not implemented yet)`, 'success')
  }

  // Bulk action: Mark as sent
  async function handleMarkAsSent() {
    if (selectedIds.size === 0) return
    setActionLoading(true)

    try {
      const { error: updateError } = await supabase
        .from('donation_acknowledgments')
        .update({
          status: 'sent',
          sent_at: new Date().toISOString()
        })
        .in('id', Array.from(selectedIds))

      if (updateError) {
        showToast(`Error: ${updateError.message}`, 'error')
        return
      }

      showToast(`Marked ${selectedIds.size} acknowledgments as sent`, 'success')
      setSelectedIds(new Set())
      fetchAcknowledgments()
      fetchStats()
    } catch (err) {
      showToast('Failed to update acknowledgments', 'error')
    } finally {
      setActionLoading(false)
    }
  }

  // Bulk action: Skip selected
  async function handleSkipSelected() {
    if (selectedIds.size === 0) return
    setActionLoading(true)

    try {
      const { error: updateError } = await supabase
        .from('donation_acknowledgments')
        .update({ status: 'skipped_old' })
        .in('id', Array.from(selectedIds))

      if (updateError) {
        showToast(`Error: ${updateError.message}`, 'error')
        return
      }

      showToast(`Skipped ${selectedIds.size} acknowledgments`, 'success')
      setSelectedIds(new Set())
      fetchAcknowledgments()
      fetchStats()
    } catch (err) {
      showToast('Failed to update acknowledgments', 'error')
    } finally {
      setActionLoading(false)
    }
  }

  // Single action: Send now (placeholder)
  function handleSendOne(_id: string) {
    showToast('Would send 1 acknowledgment (email sending not implemented yet)', 'success')
  }

  // Single action: Skip
  async function handleSkipOne(id: string) {
    setActionLoading(true)
    try {
      const { error: updateError } = await supabase
        .from('donation_acknowledgments')
        .update({ status: 'skipped_old' })
        .eq('id', id)

      if (updateError) {
        showToast(`Error: ${updateError.message}`, 'error')
        return
      }

      showToast('Acknowledgment skipped', 'success')
      fetchAcknowledgments()
      fetchStats()
    } catch (err) {
      showToast('Failed to skip acknowledgment', 'error')
    } finally {
      setActionLoading(false)
    }
  }

  // Format currency
  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  // Format date
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  // Check if row is old (>30 days)
  function isOldRow(queuedAt: string): boolean {
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
    return new Date(queuedAt) < thirtyDaysAgo
  }

  // Calculate pagination
  const totalPages = Math.ceil(totalCount / PAGE_SIZE)
  const allSelected = acknowledgments.length > 0 && selectedIds.size === acknowledgments.length

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/donors">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Pending Acknowledgments</h1>
            <p className="text-muted-foreground">
              Review and send donation acknowledgment emails
            </p>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg ${
            toast.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pending</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalPending}</div>
            <p className="text-xs text-muted-foreground">
              Awaiting review or sending
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Amount</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.totalAmount)}</div>
            <p className="text-xs text-muted-foreground">
              Sum of pending donations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Oldest Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.oldestDate ? formatDate(stats.oldestDate) : 'None'}
            </div>
            <p className="text-xs text-muted-foreground">
              Earliest queued acknowledgment
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v as StatusFilter); setCurrentPage(1); }}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Pending</SelectItem>
                  <SelectItem value="pending_review">Manual Entry</SelectItem>
                  <SelectItem value="auto_queued">Auto-Queued</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Sort:</span>
              <Select value={sortOption} onValueChange={(v) => { setSortOption(v as SortOption); setCurrentPage(1); }}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="oldest">Oldest First</SelectItem>
                  <SelectItem value="newest">Newest First</SelectItem>
                  <SelectItem value="amount_high">Amount (High to Low)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading acknowledgments...</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && acknowledgments.length === 0 && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
              <p className="text-lg font-medium">No pending acknowledgments</p>
              <p>All caught up! Check back after new donations come in.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      {!loading && !error && acknowledgments.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={handleSelectAll}
                      aria-label="Select all"
                    />
                  </TableHead>
                  <TableHead>Donor</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {acknowledgments.map((ack) => (
                  <TableRow
                    key={ack.acknowledgment_id}
                    className={isOldRow(ack.queued_at) ? 'bg-yellow-50' : ''}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(ack.acknowledgment_id)}
                        onCheckedChange={(checked: boolean | 'indeterminate') =>
                          handleSelectOne(ack.acknowledgment_id, checked === true)
                        }
                        aria-label={`Select ${ack.donor_name}`}
                      />
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/donors/${ack.transaction_id}`}
                        className="font-medium hover:underline"
                      >
                        {ack.donor_name || `${ack.first_name || ''} ${ack.last_name || ''}`.trim() || 'Unknown'}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {ack.email || 'No email'}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(ack.donation_amount)}
                    </TableCell>
                    <TableCell>{formatDate(ack.donation_date)}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                          ack.status === 'pending_review'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {ack.status === 'pending_review' ? 'Pending Review' : 'Auto-Queued'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleSendOne(ack.acknowledgment_id)}>
                            <Send className="h-4 w-4 mr-2" />
                            Send Now
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleSkipOne(ack.acknowledgment_id)}>
                            <SkipForward className="h-4 w-4 mr-2" />
                            Skip
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link href={`/donors/${ack.transaction_id}`}>
                              <User className="h-4 w-4 mr-2" />
                              View Donor
                            </Link>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Bulk Actions & Pagination */}
      {!loading && acknowledgments.length > 0 && (
        <div className="flex items-center justify-between">
          {/* Bulk Actions */}
          <div className="flex items-center gap-2">
            <Button
              onClick={handleSendSelected}
              disabled={selectedIds.size === 0 || actionLoading}
            >
              {actionLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Send className="h-4 w-4 mr-2" />
              )}
              Send Selected
            </Button>
            <Button
              variant="secondary"
              onClick={handleMarkAsSent}
              disabled={selectedIds.size === 0 || actionLoading}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Mark as Sent
            </Button>
            <Button
              variant="secondary"
              onClick={handleSkipSelected}
              disabled={selectedIds.size === 0 || actionLoading}
            >
              <SkipForward className="h-4 w-4 mr-2" />
              Skip Selected
            </Button>
            {selectedIds.size > 0 && (
              <span className="text-sm text-muted-foreground ml-2">
                {selectedIds.size} selected
              </span>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
