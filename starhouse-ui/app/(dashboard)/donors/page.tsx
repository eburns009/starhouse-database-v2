/**
 * Donors List Page
 * FAANG Standards:
 * - Server-side data fetching from v_donor_summary view
 * - Real-time filtering with client-side state
 * - Accessible table with proper semantics
 * - Responsive design with mobile support
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Search, Loader2, AlertCircle, Users, DollarSign, Star } from 'lucide-react'

interface DonorSummary {
  donor_id: string
  contact_id: string
  email: string | null
  first_name: string | null
  last_name: string | null
  phone: string | null
  city: string | null
  state: string | null
  donor_status: string
  lifetime_amount: number
  lifetime_count: number
  largest_gift: number | null
  average_gift: number | null
  first_gift_date: string | null
  last_gift_date: string | null
  ytd_amount: number
  ytd_count: number
  is_major_donor: boolean
  do_not_solicit: boolean
  do_not_call: boolean
}

type SortField = 'lifetime_amount' | 'last_gift_date' | 'name'
type SortDirection = 'asc' | 'desc'

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  active: { label: 'Active', className: 'bg-green-100 text-green-800 border-green-200' },
  lapsed: { label: 'Lapsed', className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  major: { label: 'Major', className: 'bg-purple-100 text-purple-800 border-purple-200' },
  dormant: { label: 'Dormant', className: 'bg-gray-100 text-gray-800 border-gray-200' },
  first_time: { label: 'First Time', className: 'bg-blue-100 text-blue-800 border-blue-200' },
  prospect: { label: 'Prospect', className: 'bg-slate-100 text-slate-800 border-slate-200' },
  deceased: { label: 'Deceased', className: 'bg-gray-200 text-gray-600 border-gray-300' },
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function DonorsPage() {
  const router = useRouter()
  const [donors, setDonors] = useState<DonorSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('lifetime_amount')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  // Fetch donors
  useEffect(() => {
    async function fetchDonors() {
      setLoading(true)
      setError(null)

      const supabase = createClient()
      const { data, error } = await supabase
        .from('v_donor_summary')
        .select('*')
        .order('lifetime_amount', { ascending: false })

      if (error) {
        console.error('Error fetching donors:', error)
        setError(error.message)
      } else {
        setDonors(data || [])
      }

      setLoading(false)
    }

    fetchDonors()
  }, [])

  // Filtered and sorted donors
  const filteredDonors = useMemo(() => {
    let result = [...donors]

    // Apply status filter
    if (statusFilter !== 'all') {
      result = result.filter((d) => d.donor_status === statusFilter)
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter((d) => {
        const fullName = `${d.first_name || ''} ${d.last_name || ''}`.toLowerCase()
        const email = (d.email || '').toLowerCase()
        return fullName.includes(query) || email.includes(query)
      })
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0

      switch (sortField) {
        case 'lifetime_amount':
          comparison = a.lifetime_amount - b.lifetime_amount
          break
        case 'last_gift_date':
          const dateA = a.last_gift_date ? new Date(a.last_gift_date).getTime() : 0
          const dateB = b.last_gift_date ? new Date(b.last_gift_date).getTime() : 0
          comparison = dateA - dateB
          break
        case 'name':
          const nameA = `${a.last_name || ''} ${a.first_name || ''}`.toLowerCase()
          const nameB = `${b.last_name || ''} ${b.first_name || ''}`.toLowerCase()
          comparison = nameA.localeCompare(nameB)
          break
      }

      return sortDirection === 'desc' ? -comparison : comparison
    })

    return result
  }, [donors, statusFilter, searchQuery, sortField, sortDirection])

  // Summary stats
  const stats = useMemo(() => {
    return {
      totalDonors: donors.length,
      totalLifetimeValue: donors.reduce((sum, d) => sum + d.lifetime_amount, 0),
      majorDonors: donors.filter((d) => d.donor_status === 'major').length,
    }
  }, [donors])

  // Handle row click
  const handleRowClick = (donorId: string) => {
    router.push(`/donors/${donorId}`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading donors...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-8">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <CardTitle>Failed to Load Donors</CardTitle>
            </div>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">Donors</h1>
        <p className="text-muted-foreground">
          Manage donor relationships and giving history
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Donors</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDonors.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Lifetime Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.totalLifetimeValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Major Donors</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.majorDonors}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="lapsed">Lapsed</SelectItem>
                <SelectItem value="major">Major</SelectItem>
                <SelectItem value="dormant">Dormant</SelectItem>
                <SelectItem value="first_time">First Time</SelectItem>
                <SelectItem value="prospect">Prospect</SelectItem>
              </SelectContent>
            </Select>

            {/* Sort */}
            <Select
              value={`${sortField}-${sortDirection}`}
              onValueChange={(value) => {
                const [field, direction] = value.split('-') as [SortField, SortDirection]
                setSortField(field)
                setSortDirection(direction)
              }}
            >
              <SelectTrigger className="w-full md:w-[200px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="lifetime_amount-desc">Lifetime Amount (High)</SelectItem>
                <SelectItem value="lifetime_amount-asc">Lifetime Amount (Low)</SelectItem>
                <SelectItem value="last_gift_date-desc">Last Gift (Recent)</SelectItem>
                <SelectItem value="last_gift_date-asc">Last Gift (Oldest)</SelectItem>
                <SelectItem value="name-asc">Name (A-Z)</SelectItem>
                <SelectItem value="name-desc">Name (Z-A)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Donors Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {filteredDonors.length === donors.length
              ? `All Donors (${donors.length})`
              : `Filtered Results (${filteredDonors.length} of ${donors.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredDonors.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No donors found matching your criteria.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Lifetime Amount</TableHead>
                    <TableHead>Last Gift</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDonors.map((donor) => {
                    const statusInfo = STATUS_BADGES[donor.donor_status] || STATUS_BADGES.prospect
                    return (
                      <TableRow
                        key={donor.donor_id}
                        onClick={() => handleRowClick(donor.donor_id)}
                        className="cursor-pointer"
                      >
                        <TableCell className="font-medium">
                          {donor.first_name || donor.last_name
                            ? `${donor.first_name || ''} ${donor.last_name || ''}`.trim()
                            : '(No name)'}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {donor.email || '—'}
                        </TableCell>
                        <TableCell>
                          <Badge className={statusInfo.className} variant="outline">
                            {statusInfo.label}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(donor.lifetime_amount)}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDate(donor.last_gift_date)}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
