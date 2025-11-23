/**
 * Manual Donation Entry Page
 * FAANG Standards:
 * - Comprehensive form validation
 * - Optimistic UI with loading states
 * - Accessible form with proper labels
 * - Error handling with user feedback
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  Search,
  Check,
  UserPlus,
  X,
} from 'lucide-react'

interface DonorOption {
  donor_id: string
  contact_id: string
  email: string | null
  first_name: string | null
  last_name: string | null
  last_gift_date: string | null
}

interface FormData {
  donorId: string
  newDonorFirstName: string
  newDonorLastName: string
  newDonorEmail: string
  amount: string
  date: string
  paymentMethod: string
  checkNumber: string
  category: string
  fund: string
  campaign: string
  memo: string
  queueAcknowledgment: boolean
}

interface FormErrors {
  donor?: string
  amount?: string
  date?: string
  paymentMethod?: string
  newDonorEmail?: string
}

const PAYMENT_METHODS = [
  { value: 'check', label: 'Check' },
  { value: 'cash', label: 'Cash' },
  { value: 'wire', label: 'Wire Transfer' },
  { value: 'other', label: 'Other' },
]

const CATEGORIES = [
  { value: 'General Donations', label: 'General Donations' },
  { value: 'Fundraising', label: 'Fundraising' },
  { value: 'Capital Improvements', label: 'Capital Improvements' },
  { value: 'Membership', label: 'Membership' },
]

function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function NewDonationPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const prefilledDonorId = searchParams.get('donor')

  const [donors, setDonors] = useState<DonorOption[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Form state
  const [formData, setFormData] = useState<FormData>({
    donorId: prefilledDonorId || '',
    newDonorFirstName: '',
    newDonorLastName: '',
    newDonorEmail: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    paymentMethod: '',
    checkNumber: '',
    category: 'General Donations',
    fund: '',
    campaign: '',
    memo: '',
    queueAcknowledgment: true,
  })

  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [searchQuery, setSearchQuery] = useState('')
  const [showDonorSearch, setShowDonorSearch] = useState(!prefilledDonorId)
  const [showNewDonorForm, setShowNewDonorForm] = useState(false)

  // Fetch donors for search
  useEffect(() => {
    async function fetchDonors() {
      setLoading(true)
      const supabase = createClient()

      const { data, error } = await supabase
        .from('v_donor_summary')
        .select('donor_id, contact_id, email, first_name, last_name, last_gift_date')
        .order('last_name', { ascending: true })

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

  // Filter donors based on search
  const filteredDonors = useMemo(() => {
    if (!searchQuery.trim()) return donors.slice(0, 10)

    const query = searchQuery.toLowerCase()
    return donors
      .filter((d) => {
        const fullName = `${d.first_name || ''} ${d.last_name || ''}`.toLowerCase()
        const email = (d.email || '').toLowerCase()
        return fullName.includes(query) || email.includes(query)
      })
      .slice(0, 10)
  }, [donors, searchQuery])

  // Selected donor info
  const selectedDonor = useMemo(() => {
    if (!formData.donorId) return null
    return donors.find((d) => d.donor_id === formData.donorId) || null
  }, [donors, formData.donorId])

  // Validate form
  function validateForm(): boolean {
    const errors: FormErrors = {}

    // Donor validation
    if (!formData.donorId && !showNewDonorForm) {
      errors.donor = 'Please select a donor or create a new one'
    }

    if (showNewDonorForm) {
      if (!formData.newDonorFirstName.trim() && !formData.newDonorLastName.trim()) {
        errors.donor = 'Please enter donor name'
      }
      if (formData.newDonorEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.newDonorEmail)) {
        errors.newDonorEmail = 'Invalid email format'
      }
    }

    // Amount validation
    const amount = parseFloat(formData.amount)
    if (!formData.amount || isNaN(amount) || amount <= 0) {
      errors.amount = 'Amount must be greater than $0'
    }

    // Date validation
    if (!formData.date) {
      errors.date = 'Date is required'
    } else {
      const selectedDate = new Date(formData.date)
      const today = new Date()
      today.setHours(23, 59, 59, 999)
      if (selectedDate > today) {
        errors.date = 'Date cannot be in the future'
      }
    }

    // Payment method validation
    if (!formData.paymentMethod) {
      errors.paymentMethod = 'Payment method is required'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  // Handle form submission
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!validateForm()) return

    setSubmitting(true)
    setError(null)

    try {
      const supabase = createClient()
      let donorId = formData.donorId
      let contactId = selectedDonor?.contact_id

      // Create new donor if needed
      if (showNewDonorForm) {
        // First create contact
        const { data: contactData, error: contactError } = await supabase
          .from('contacts')
          .insert({
            first_name: formData.newDonorFirstName.trim() || null,
            last_name: formData.newDonorLastName.trim() || null,
            email: formData.newDonorEmail.trim() || null,
          })
          .select('id')
          .single()

        if (contactError) {
          throw new Error(`Failed to create contact: ${contactError.message}`)
        }

        contactId = contactData.id

        // Then create donor
        const { data: donorData, error: donorError } = await supabase
          .from('donors')
          .insert({
            contact_id: contactId,
            status: 'first_time',
          })
          .select('id')
          .single()

        if (donorError) {
          throw new Error(`Failed to create donor: ${donorError.message}`)
        }

        donorId = donorData.id
      }

      // Create transaction
      const amount = parseFloat(formData.amount)
      const { data: transactionData, error: transactionError } = await supabase
        .from('transactions')
        .insert({
          contact_id: contactId,
          amount: amount,
          transaction_date: formData.date,
          transaction_type: 'donation',
          payment_method: formData.paymentMethod,
          status: 'completed',
          is_donation: true,
          donation_source: 'manual',
          donation_category: 'DEVELOPMENT',
          donation_subcategory: formData.category || null,
          fund: formData.fund.trim() || null,
          campaign: formData.campaign.trim() || null,
          quickbooks_memo: formData.memo.trim() || null,
          quickbooks_invoice_num: formData.paymentMethod === 'check' ? formData.checkNumber.trim() || null : null,
        })
        .select('id')
        .single()

      if (transactionError) {
        throw new Error(`Failed to create transaction: ${transactionError.message}`)
      }

      // Create acknowledgment if requested
      if (formData.queueAcknowledgment) {
        const donorName = showNewDonorForm
          ? `${formData.newDonorFirstName} ${formData.newDonorLastName}`.trim()
          : `${selectedDonor?.first_name || ''} ${selectedDonor?.last_name || ''}`.trim()

        const { error: ackError } = await supabase
          .from('donation_acknowledgments')
          .insert({
            transaction_id: transactionData.id,
            donor_id: donorId,
            status: 'pending_review',
            donor_name: donorName,
            donation_amount: amount,
            donation_date: formData.date,
            fund_designation: formData.fund.trim() || null,
          })

        if (ackError) {
          console.error('Warning: Failed to create acknowledgment:', ackError)
          // Don't fail the whole transaction for this
        }
      }

      // Update donor metrics
      const { error: metricsError } = await supabase.rpc('update_donor_metrics', {
        p_donor_id: donorId,
      })

      if (metricsError) {
        console.error('Warning: Failed to update donor metrics:', metricsError)
      }

      setSuccess(true)

      // Redirect after short delay to show success
      setTimeout(() => {
        router.push(`/donors/${donorId}`)
      }, 1500)
    } catch (err) {
      console.error('Error saving donation:', err)
      setError(err instanceof Error ? err.message : 'Failed to save donation')
      setSubmitting(false)
    }
  }

  // Handle donor selection
  function selectDonor(donor: DonorOption) {
    setFormData((prev) => ({ ...prev, donorId: donor.donor_id }))
    setShowDonorSearch(false)
    setSearchQuery('')
  }

  // Clear selected donor
  function clearDonor() {
    setFormData((prev) => ({ ...prev, donorId: '' }))
    setShowDonorSearch(true)
    setShowNewDonorForm(false)
  }

  // Toggle new donor form
  function toggleNewDonorForm() {
    setShowNewDonorForm(!showNewDonorForm)
    setFormData((prev) => ({
      ...prev,
      donorId: '',
      newDonorFirstName: '',
      newDonorLastName: '',
      newDonorEmail: '',
    }))
    setShowDonorSearch(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading...</p>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <Check className="h-6 w-6 text-green-600" />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold">Donation Recorded!</p>
            <p className="text-sm text-muted-foreground">
              {formData.queueAcknowledgment
                ? 'Acknowledgment queued for review.'
                : 'Redirecting to donor page...'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8 max-w-2xl">
      {/* Back Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.back()}
        className="mb-6"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Record New Donation</CardTitle>
          <CardDescription>
            Enter donation details manually for check, cash, or wire transfers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Display */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* 1. DONOR SELECTION */}
            <div className="space-y-3">
              <Label className="text-sm font-semibold">Donor *</Label>

              {/* Selected Donor Display */}
              {selectedDonor && !showDonorSearch && !showNewDonorForm && (
                <div className="flex items-center justify-between p-3 bg-slate-50 border rounded-md">
                  <div>
                    <div className="font-medium">
                      {selectedDonor.first_name} {selectedDonor.last_name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {selectedDonor.email || 'No email'} • Last gift:{' '}
                      {formatDate(selectedDonor.last_gift_date)}
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clearDonor}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {/* Donor Search */}
              {showDonorSearch && !showNewDonorForm && (
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Search by name or email..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>

                  {/* Search Results */}
                  {filteredDonors.length > 0 && (
                    <div className="border rounded-md max-h-48 overflow-y-auto">
                      {filteredDonors.map((donor) => (
                        <button
                          key={donor.donor_id}
                          type="button"
                          onClick={() => selectDonor(donor)}
                          className="w-full text-left px-3 py-2 hover:bg-slate-50 border-b last:border-b-0"
                        >
                          <div className="font-medium">
                            {donor.first_name} {donor.last_name}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {donor.email || 'No email'} • Last gift:{' '}
                            {formatDate(donor.last_gift_date)}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={toggleNewDonorForm}
                    className="w-full"
                  >
                    <UserPlus className="mr-2 h-4 w-4" />
                    Create New Donor
                  </Button>
                </div>
              )}

              {/* New Donor Form */}
              {showNewDonorForm && (
                <div className="space-y-3 p-3 bg-slate-50 border rounded-md">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">New Donor</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setShowNewDonorForm(false)
                        setShowDonorSearch(true)
                      }}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="newDonorFirstName" className="text-xs">
                        First Name
                      </Label>
                      <Input
                        id="newDonorFirstName"
                        value={formData.newDonorFirstName}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            newDonorFirstName: e.target.value,
                          }))
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="newDonorLastName" className="text-xs">
                        Last Name
                      </Label>
                      <Input
                        id="newDonorLastName"
                        value={formData.newDonorLastName}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            newDonorLastName: e.target.value,
                          }))
                        }
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="newDonorEmail" className="text-xs">
                      Email (optional)
                    </Label>
                    <Input
                      id="newDonorEmail"
                      type="email"
                      value={formData.newDonorEmail}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          newDonorEmail: e.target.value,
                        }))
                      }
                      placeholder="donor@example.com"
                    />
                    {formErrors.newDonorEmail && (
                      <p className="text-xs text-red-600 mt-1">
                        {formErrors.newDonorEmail}
                      </p>
                    )}
                    {!formData.newDonorEmail && (formData.newDonorFirstName || formData.newDonorLastName) && (
                      <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        No email - acknowledgment cannot be sent electronically
                      </p>
                    )}
                  </div>
                </div>
              )}

              {formErrors.donor && (
                <p className="text-xs text-red-600">{formErrors.donor}</p>
              )}
            </div>

            {/* 2. DONATION DETAILS */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">Donation Details</h3>

              <div className="grid grid-cols-2 gap-4">
                {/* Amount */}
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount *</Label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                      $
                    </span>
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={formData.amount}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, amount: e.target.value }))
                      }
                      className="pl-7"
                    />
                  </div>
                  {formErrors.amount && (
                    <p className="text-xs text-red-600">{formErrors.amount}</p>
                  )}
                </div>

                {/* Date */}
                <div className="space-y-2">
                  <Label htmlFor="date">Date *</Label>
                  <Input
                    id="date"
                    type="date"
                    value={formData.date}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, date: e.target.value }))
                    }
                  />
                  {formErrors.date && (
                    <p className="text-xs text-red-600">{formErrors.date}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Payment Method */}
                <div className="space-y-2">
                  <Label>Payment Method *</Label>
                  <Select
                    value={formData.paymentMethod}
                    onValueChange={(value) =>
                      setFormData((prev) => ({ ...prev, paymentMethod: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select method" />
                    </SelectTrigger>
                    <SelectContent>
                      {PAYMENT_METHODS.map((method) => (
                        <SelectItem key={method.value} value={method.value}>
                          {method.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {formErrors.paymentMethod && (
                    <p className="text-xs text-red-600">{formErrors.paymentMethod}</p>
                  )}
                </div>

                {/* Check Number (conditional) */}
                {formData.paymentMethod === 'check' && (
                  <div className="space-y-2">
                    <Label htmlFor="checkNumber">Check Number</Label>
                    <Input
                      id="checkNumber"
                      value={formData.checkNumber}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, checkNumber: e.target.value }))
                      }
                      placeholder="e.g., 1234"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* 3. CATEGORIZATION */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">Categorization</h3>

              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) =>
                    setFormData((prev) => ({ ...prev, category: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fund">Fund</Label>
                  <Input
                    id="fund"
                    value={formData.fund}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, fund: e.target.value }))
                    }
                    placeholder="e.g., Building Fund"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="campaign">Campaign</Label>
                  <Input
                    id="campaign"
                    value={formData.campaign}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, campaign: e.target.value }))
                    }
                    placeholder="e.g., 2024 Annual Appeal"
                  />
                </div>
              </div>
            </div>

            {/* 4. NOTES */}
            <div className="space-y-2">
              <Label htmlFor="memo">Memo / Description</Label>
              <textarea
                id="memo"
                value={formData.memo}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, memo: e.target.value }))
                }
                placeholder="Optional notes about this donation..."
                rows={3}
                className="flex w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            {/* 5. ACKNOWLEDGMENT */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="queueAcknowledgment"
                  checked={formData.queueAcknowledgment}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      queueAcknowledgment: e.target.checked,
                    }))
                  }
                  className="h-4 w-4 rounded border-slate-300"
                />
                <Label htmlFor="queueAcknowledgment" className="font-normal">
                  Queue acknowledgment for review
                </Label>
              </div>
              <p className="text-xs text-muted-foreground ml-6">
                Donor will receive tax receipt after staff review
              </p>
            </div>

            {/* ACTIONS */}
            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={submitting} className="flex-1">
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save Donation'
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                disabled={submitting}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
