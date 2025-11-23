/**
 * Donor Detail Page
 * FAANG Standards:
 * - Comprehensive donor profile with giving history
 * - Accessible table with proper semantics
 * - Responsive design with mobile support
 * - Error handling with user feedback
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableFooter,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  Phone,
  Mail,
  MapPin,
  Calendar,
  DollarSign,
  Hash,
  PhoneCall,
  Plus,
  Send,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { formatDonationCategory } from '@/lib/utils'

interface Donor {
  id: string
  contact_id: string
  status: string
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
  recognition_name: string | null
  notes: string | null
}

interface Contact {
  id: string
  email: string | null
  first_name: string | null
  last_name: string | null
  phone: string | null
  address_line_1: string | null
  address_line_2: string | null
  city: string | null
  state: string | null
  postal_code: string | null
}

interface Transaction {
  id: string
  transaction_date: string
  amount: number
  transaction_type: string
  payment_method: string | null
  donation_category: string | null
  donation_subcategory: string | null
  quickbooks_invoice_num: string | null
  quickbooks_memo: string | null
  status: string
}

interface Outreach {
  id: string
  campaign_name: string
  campaign_year: number
  outreach_type: string
  outreach_date: string
  outcome: string | null
  pledge_amount: number | null
  notes: string | null
}

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  active: { label: 'Active', className: 'bg-green-100 text-green-800 border-green-200' },
  lapsed: { label: 'Lapsed', className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  major: { label: 'Major', className: 'bg-purple-100 text-purple-800 border-purple-200' },
  dormant: { label: 'Dormant', className: 'bg-gray-100 text-gray-800 border-gray-200' },
  first_time: { label: 'First Time', className: 'bg-blue-100 text-blue-800 border-blue-200' },
  prospect: { label: 'Prospect', className: 'bg-slate-100 text-slate-800 border-slate-200' },
  deceased: { label: 'Deceased', className: 'bg-gray-200 text-gray-600 border-gray-300' },
}

const OUTCOME_LABELS: Record<string, string> = {
  pledged: 'Pledged',
  declined: 'Declined',
  callback: 'Callback Requested',
  no_answer: 'No Answer',
  wrong_number: 'Wrong Number',
  do_not_call: 'Do Not Call',
  voicemail: 'Voicemail',
  not_reached: 'Not Reached',
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

function formatAddress(contact: Contact): string | null {
  const parts = []
  if (contact.address_line_1) parts.push(contact.address_line_1)
  if (contact.address_line_2) parts.push(contact.address_line_2)

  const cityStateZip = []
  if (contact.city) cityStateZip.push(contact.city)
  if (contact.state) cityStateZip.push(contact.state)
  if (contact.postal_code) cityStateZip.push(contact.postal_code)

  if (cityStateZip.length > 0) {
    parts.push(cityStateZip.join(', '))
  }

  return parts.length > 0 ? parts.join('\n') : null
}

const ITEMS_PER_PAGE = 20

export default function DonorDetailPage() {
  const params = useParams()
  const router = useRouter()
  const donorId = params.id as string

  const [donor, setDonor] = useState<Donor | null>(null)
  const [contact, setContact] = useState<Contact | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [outreach, setOutreach] = useState<Outreach[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)

  // Fetch donor data
  useEffect(() => {
    async function fetchDonorData() {
      setLoading(true)
      setError(null)

      const supabase = createClient()

      // Fetch donor
      const { data: donorData, error: donorError } = await supabase
        .from('donors')
        .select('*')
        .eq('id', donorId)
        .single()

      if (donorError) {
        console.error('Error fetching donor:', donorError)
        setError(donorError.message)
        setLoading(false)
        return
      }

      setDonor(donorData)

      // Fetch contact
      const { data: contactData, error: contactError } = await supabase
        .from('contacts')
        .select('*')
        .eq('id', donorData.contact_id)
        .single()

      if (contactError) {
        console.error('Error fetching contact:', contactError)
        setError(contactError.message)
        setLoading(false)
        return
      }

      setContact(contactData)

      // Fetch transactions (donations)
      const { data: transactionsData, error: transactionsError } = await supabase
        .from('transactions')
        .select('*')
        .eq('contact_id', donorData.contact_id)
        .eq('is_donation', true)
        .order('transaction_date', { ascending: false })

      if (transactionsError) {
        console.error('Error fetching transactions:', transactionsError)
      } else {
        setTransactions(transactionsData || [])
      }

      // Fetch outreach history
      const { data: outreachData, error: outreachError } = await supabase
        .from('donor_outreach')
        .select('*')
        .eq('donor_id', donorId)
        .order('outreach_date', { ascending: false })

      if (outreachError) {
        console.error('Error fetching outreach:', outreachError)
      } else {
        setOutreach(outreachData || [])
      }

      setLoading(false)
    }

    if (donorId) {
      fetchDonorData()
    }
  }, [donorId])

  // Paginated transactions
  const paginatedTransactions = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    return transactions.slice(startIndex, startIndex + ITEMS_PER_PAGE)
  }, [transactions, currentPage])

  const totalPages = Math.ceil(transactions.length / ITEMS_PER_PAGE)

  // Calculate running total
  const runningTotal = useMemo(() => {
    return transactions.reduce((sum, t) => {
      const amount = t.transaction_type === 'refund' ? -t.amount : t.amount
      return sum + amount
    }, 0)
  }, [transactions])

  // Donor display name
  const donorName = useMemo(() => {
    if (!contact) return 'Unknown Donor'
    if (donor?.recognition_name) return donor.recognition_name
    if (contact.first_name || contact.last_name) {
      return `${contact.first_name || ''} ${contact.last_name || ''}`.trim()
    }
    return contact.email || 'Unknown Donor'
  }, [contact, donor])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading donor details...</p>
        </div>
      </div>
    )
  }

  if (error || !donor || !contact) {
    return (
      <div className="container mx-auto p-8">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <CardTitle>Failed to Load Donor</CardTitle>
            </div>
            <CardDescription>{error || 'Donor not found'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => router.push('/donors')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Donors
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const statusInfo = STATUS_BADGES[donor.status] || STATUS_BADGES.prospect
  const address = formatAddress(contact)

  return (
    <div className="container mx-auto p-8">
      {/* Back Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push('/donors')}
        className="mb-6"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Donors
      </Button>

      {/* 1. HEADER CARD */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <CardTitle className="text-2xl">{donorName}</CardTitle>
              <div className="mt-2">
                <Badge className={statusInfo.className} variant="outline">
                  {statusInfo.label}
                </Badge>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">Lifetime Total</div>
              <div className="text-3xl font-bold text-primary">
                {formatCurrency(donor.lifetime_amount)}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            {/* Key Metrics */}
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Giving History
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-xs text-muted-foreground">First Gift</div>
                    <div className="text-sm font-medium">
                      {formatDate(donor.first_gift_date)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-xs text-muted-foreground">Last Gift</div>
                    <div className="text-sm font-medium">
                      {formatDate(donor.last_gift_date)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-xs text-muted-foreground">Total Gifts</div>
                    <div className="text-sm font-medium">{donor.lifetime_count}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-xs text-muted-foreground">Average Gift</div>
                    <div className="text-sm font-medium">
                      {donor.average_gift ? formatCurrency(donor.average_gift) : '—'}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Contact Info */}
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Contact Information
              </h3>
              <div className="space-y-3">
                {contact.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={`mailto:${contact.email}`}
                      className="text-sm text-primary hover:underline"
                    >
                      {contact.email}
                    </a>
                  </div>
                )}
                {contact.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{contact.phone}</span>
                  </div>
                )}
                {address && (
                  <div className="flex items-start gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <span className="text-sm whitespace-pre-line">{address}</span>
                  </div>
                )}
                {!contact.email && !contact.phone && !address && (
                  <p className="text-sm text-muted-foreground">
                    No contact information available
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3. QUICK ACTIONS */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" disabled>
              <PhoneCall className="mr-2 h-4 w-4" />
              Log Phone Call
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/donors/new-donation?donor=${donorId}`)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Donation
            </Button>
            <Button variant="outline" disabled>
              <Send className="mr-2 h-4 w-4" />
              Send Acknowledgment
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 2. DONATION HISTORY TABLE */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Donation History</CardTitle>
          <CardDescription>
            {transactions.length === 0
              ? 'No donations recorded'
              : `${transactions.length} donation${transactions.length === 1 ? '' : 's'} on record`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No donation history yet.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Payment Method</TableHead>
                      <TableHead>Invoice #</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedTransactions.map((transaction) => {
                      const isRefund = transaction.transaction_type === 'refund'
                      const displayAmount = isRefund ? -transaction.amount : transaction.amount
                      return (
                        <TableRow key={transaction.id}>
                          <TableCell>{formatDate(transaction.transaction_date)}</TableCell>
                          <TableCell
                            className={`text-right font-medium ${
                              isRefund ? 'text-red-600' : ''
                            }`}
                          >
                            {formatCurrency(displayAmount)}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {transaction.donation_subcategory || formatDonationCategory(transaction.donation_category)}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {transaction.payment_method || '—'}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {transaction.quickbooks_invoice_num || '—'}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                  <TableFooter>
                    <TableRow>
                      <TableCell>Running Total</TableCell>
                      <TableCell className="text-right font-bold">
                        {formatCurrency(runningTotal)}
                      </TableCell>
                      <TableCell colSpan={3} />
                    </TableRow>
                  </TableFooter>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* 4. OUTREACH HISTORY */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Outreach History</CardTitle>
          <CardDescription>
            {outreach.length === 0
              ? 'No outreach history yet'
              : `${outreach.length} outreach attempt${outreach.length === 1 ? '' : 's'}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {outreach.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No outreach history yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Campaign</TableHead>
                    <TableHead>Outcome</TableHead>
                    <TableHead>Notes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {outreach.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>{formatDate(record.outreach_date)}</TableCell>
                      <TableCell>
                        {record.campaign_name} ({record.campaign_year})
                      </TableCell>
                      <TableCell>
                        {record.outcome ? (
                          <Badge variant="outline">
                            {OUTCOME_LABELS[record.outcome] || record.outcome}
                          </Badge>
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground max-w-xs truncate">
                        {record.notes || '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
