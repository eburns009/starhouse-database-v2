'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Avatar } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatName, getInitials, formatCurrency, formatDate } from '@/lib/utils'
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Loader2,
  User,
  Copy,
  Check,
  Tag,
  Package,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import type {
  Contact,
  Transaction,
  SubscriptionWithProduct,
  NameVariant,
  PhoneVariant,
  AddressVariant,
} from '@/lib/types/contact'

// Note type for contact notes
interface ContactNote {
  id: string
  contact_id: string
  note_type: string
  subject: string | null
  content: string
  author_name: string
  is_pinned: boolean
  created_at: string
  updated_at: string
}

interface ContactDetailCardProps {
  contactId: string
  onClose: () => void
}

// Extended Contact type with additional email fields
interface ContactWithEmails extends Contact {
  paypal_email?: string | null
  additional_email?: string | null
  additional_email_source?: string | null
  zoho_email?: string | null
}

interface AdditionalEmail {
  email: string
  source: string
  priority: number
}

/**
 * Get source priority for email ranking
 * FAANG Standard: Pure function with clear business logic
 */
function getEmailSourcePriority(source: string): number {
  const priorities: Record<string, number> = {
    'kajabi': 1,
    'ticket_tailor': 2,
    'paypal': 3,
    'manual': 4,
    'zoho': 4,
  }
  return priorities[source.toLowerCase()] || 4
}

/**
 * Get display label for email source
 */
function getEmailSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    'kajabi': 'Kajabi',
    'ticket_tailor': 'Ticket Tailor',
    'paypal': 'PayPal',
    'manual': 'Manual Entry',
    'zoho': 'Zoho CRM',
  }
  return labels[source.toLowerCase()] || source
}

/**
 * Extract additional emails from contact fields
 * FAANG Standard: Pure function, no side effects
 */
function extractAdditionalEmails(contact: ContactWithEmails): AdditionalEmail[] {
  const additionalEmails: AdditionalEmail[] = []
  const primaryEmail = contact.email.toLowerCase()

  // PayPal email
  if (contact.paypal_email && contact.paypal_email.toLowerCase() !== primaryEmail) {
    additionalEmails.push({
      email: contact.paypal_email,
      source: 'paypal',
      priority: 3,
    })
  }

  // Additional email (from various sources)
  if (contact.additional_email && contact.additional_email.toLowerCase() !== primaryEmail) {
    additionalEmails.push({
      email: contact.additional_email,
      source: contact.additional_email_source || 'manual',
      priority: getEmailSourcePriority(contact.additional_email_source || 'manual'),
    })
  }

  // Zoho email
  if (contact.zoho_email && contact.zoho_email.toLowerCase() !== primaryEmail) {
    additionalEmails.push({
      email: contact.zoho_email,
      source: 'zoho',
      priority: 4,
    })
  }

  // Sort by priority (ascending)
  return additionalEmails.sort((a, b) => a.priority - b.priority)
}

/**
 * Extract all name variants from contact data
 * FAANG Standard: Pure function, no side effects
 */
function extractNameVariants(contact: Contact): NameVariant[] {
  const variants: NameVariant[] = []

  // Primary name
  if (contact.first_name || contact.last_name) {
    variants.push({
      first_name: contact.first_name,
      last_name: contact.last_name,
      source: contact.source_system,
      label: 'Primary Name',
    })
  }

  // PayPal name
  if (contact.paypal_first_name || contact.paypal_last_name) {
    variants.push({
      first_name: contact.paypal_first_name,
      last_name: contact.paypal_last_name,
      source: 'paypal',
      label: 'PayPal Name',
    })
  }

  // Business name
  if (contact.paypal_business_name) {
    variants.push({
      first_name: contact.paypal_business_name,
      last_name: null,
      source: 'paypal',
      label: 'Business Name',
    })
  }

  // Additional name
  if (contact.additional_name) {
    variants.push({
      first_name: contact.additional_name,
      last_name: null,
      source: contact.additional_name_source || 'unknown',
      label: 'Additional Name',
    })
  }

  return variants
}

/**
 * Extract all phone variants from contact data
 */
function extractPhoneVariants(contact: Contact): PhoneVariant[] {
  const variants: PhoneVariant[] = []

  if (contact.phone) {
    variants.push({
      number: contact.phone,
      source: contact.source_system,
      label: 'Primary Phone',
      country_code: contact.phone_country_code,
    })
  }

  if (contact.paypal_phone && contact.paypal_phone !== contact.phone) {
    variants.push({
      number: contact.paypal_phone,
      source: 'paypal',
      label: 'PayPal Phone',
    })
  }

  return variants
}

/**
 * Check if a string looks like a complete address (not just line 2)
 * FAANG Standard: Data quality heuristics
 */
function looksLikeCompleteAddress(line: string): boolean {
  if (!line) return false

  // Contains street number + street name pattern
  const hasStreetNumber = /^\d+\s+/.test(line.trim())

  // Contains common address indicators
  const hasAddressKeywords = /\b(street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct|circle|blvd|boulevard|box|po box)\b/i.test(line)

  return hasStreetNumber || hasAddressKeywords
}

/**
 * Extract all address variants from contact data
 * Handles cases where address_line_2 contains a separate address
 */
function extractAddressVariants(contact: Contact): AddressVariant[] {
  const variants: AddressVariant[] = []

  // Check if address_line_2 looks like a separate address
  const line2IsSeparateAddress =
    contact.address_line_2 &&
    looksLikeCompleteAddress(contact.address_line_2) &&
    contact.address_line_1 &&
    contact.address_line_2 !== contact.address_line_1

  // Primary address (address_line_1 only if line_2 is separate)
  if (contact.address_line_1) {
    variants.push({
      line_1: contact.address_line_1,
      line_2: line2IsSeparateAddress ? null : contact.address_line_2,
      city: contact.city,
      state: contact.state,
      postal_code: contact.postal_code,
      country: contact.country,
      source: contact.source_system,
      label: 'Primary Address',
    })
  }

  // If address_line_2 is a separate address, add it as alternate
  if (line2IsSeparateAddress) {
    variants.push({
      line_1: contact.address_line_2,
      line_2: null,
      city: contact.city,
      state: contact.state,
      postal_code: contact.postal_code,
      country: contact.country,
      source: contact.source_system,
      label: 'Alternate Address (from line 2)',
    })
  }

  // Additional alternate address fields (if different from above)
  if (contact.address && contact.address !== contact.address_line_1 && contact.address !== contact.address_line_2) {
    variants.push({
      line_1: contact.address,
      line_2: contact.address_2 || null,
      city: null,
      state: null,
      postal_code: null,
      country: null,
      source: contact.source_system,
      label: 'Additional Address',
    })
  }

  // Shipping address
  if (contact.shipping_address_line_1) {
    // Check if shipping line 2 is different from other addresses
    const shippingLine2 =
      contact.shipping_address_line_2 !== contact.address_line_1 &&
      contact.shipping_address_line_2 !== contact.address_line_2 &&
      contact.shipping_address_line_2 !== contact.address
        ? contact.shipping_address_line_2
        : null

    variants.push({
      line_1: contact.shipping_address_line_1,
      line_2: shippingLine2,
      city: null,
      state: null,
      postal_code: null,
      country: null,
      source: 'paypal',
      label: 'Shipping Address',
      status: contact.shipping_address_status,
    })
  }

  return variants
}

/**
 * Format address for display
 */
function formatAddress(address: AddressVariant): string {
  const parts = [
    address.line_1,
    address.line_2,
    [address.city, address.state].filter(Boolean).join(', '),
    address.postal_code,
    address.country,
  ].filter(Boolean)

  return parts.join('\n')
}

export function ContactDetailCard({
  contactId,
  onClose,
}: ContactDetailCardProps) {
  const [contact, setContact] = useState<Contact | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [subscriptions, setSubscriptions] = useState<SubscriptionWithProduct[]>([])
  const [notes, setNotes] = useState<ContactNote[]>([])
  const [totalRevenue, setTotalRevenue] = useState(0)
  const [totalTransactionCount, setTotalTransactionCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedEmail, setCopiedEmail] = useState(false)
  const [expandedNoteIds, setExpandedNoteIds] = useState<Set<string>>(new Set())
  const [showAddNote, setShowAddNote] = useState(false)
  const [newNoteSubject, setNewNoteSubject] = useState('')
  const [newNoteContent, setNewNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [showProducts, setShowProducts] = useState(false)
  const [showTags, setShowTags] = useState(false)
  const [showTransactions, setShowTransactions] = useState(false)
  const [showSubscriptions, setShowSubscriptions] = useState(false)
  const [contactTags, setContactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')

  const handleCopyEmail = async (email: string) => {
    try {
      await navigator.clipboard.writeText(email)
      setCopiedEmail(true)
      setTimeout(() => setCopiedEmail(false), 2000)
    } catch (err) {
      console.error('Failed to copy email:', err)
    }
  }

  const toggleNoteExpand = (noteId: string) => {
    setExpandedNoteIds((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(noteId)) {
        newSet.delete(noteId)
      } else {
        newSet.add(noteId)
      }
      return newSet
    })
  }

  const handleSaveNote = async () => {
    if (!newNoteSubject.trim() || !newNoteContent.trim()) {
      return
    }

    setSavingNote(true)
    try {
      const supabase = createClient()
      const { data, error } = await supabase
        .from('contact_notes')
        .insert({
          contact_id: contactId,
          subject: newNoteSubject.trim(),
          content: newNoteContent.trim(),
          note_type: 'general',
          author_name: 'User', // TODO: Get from auth when available
        })
        .select()
        .single()

      if (error) throw error

      // Add new note to the list
      setNotes((prev) => [data, ...prev])

      // Reset form
      setNewNoteSubject('')
      setNewNoteContent('')
      setShowAddNote(false)
    } catch (err) {
      console.error('Error saving note:', err)
      alert('Failed to save note. Please try again.')
    } finally {
      setSavingNote(false)
    }
  }

  const handleAddTag = () => {
    if (newTag.trim() && !contactTags.includes(newTag.trim())) {
      setContactTags([...contactTags, newTag.trim()])
      setNewTag('')
      // TODO: Save to database when tags field is added to contacts table
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setContactTags(contactTags.filter((tag) => tag !== tagToRemove))
    // TODO: Save to database when tags field is added to contacts table
  }

  useEffect(() => {
    const fetchContactDetails = async () => {
      try {
        const supabase = createClient()

        // Fetch contact
        const { data: contactData, error: contactError } = await supabase
          .from('contacts')
          .select('*')
          .eq('id', contactId)
          .single()

        if (contactError) throw contactError

        // Fetch transactions
        const { data: transactionsData, error: transactionsError } = await supabase
          .from('transactions')
          .select('*')
          .eq('contact_id', contactId)
          .order('transaction_date', { ascending: false })
          .limit(5)

        if (transactionsError) {
          console.error('Error fetching transactions:', transactionsError)
        }

        // Fetch total revenue (all transactions, not just the recent 5)
        const { data: revenueData, error: revenueError } = await supabase
          .from('transactions')
          .select('amount, transaction_type')
          .eq('contact_id', contactId)
          .neq('transaction_type', 'refund')

        if (revenueError) {
          console.error('Error fetching revenue:', revenueError)
        } else {
          const revenue = revenueData?.reduce((sum: number, t: any) => sum + Number(t.amount), 0) || 0
          setTotalRevenue(revenue)
        }

        // Get total transaction count
        const { count: transactionCount } = await supabase
          .from('transactions')
          .select('*', { count: 'exact', head: true })
          .eq('contact_id', contactId)

        setTotalTransactionCount(transactionCount || 0)

        // Fetch subscriptions with product information (JOIN)
        const { data: subscriptionsData, error: subscriptionsError } = await supabase
          .from('subscriptions')
          .select(`
            *,
            products (
              id,
              name,
              product_type
            )
          `)
          .eq('contact_id', contactId)
          .not('product_id', 'is', null)  // Only show subscriptions with products
          .order('created_at', { ascending: false })

        if (subscriptionsError) {
          console.error('Error fetching subscriptions:', subscriptionsError)
        }

        // Fetch notes
        const { data: notesData, error: notesError } = await supabase
          .from('contact_notes')
          .select('*')
          .eq('contact_id', contactId)
          .order('is_pinned', { ascending: false })  // Pinned notes first
          .order('created_at', { ascending: false })  // Then by date

        if (notesError) {
          console.error('Error fetching notes:', notesError)
        }

        setContact(contactData)
        setTransactions(transactionsData || [])
        setSubscriptions(subscriptionsData || [])
        setNotes(notesData || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contact')
        console.error('Error loading contact:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchContactDetails()
  }, [contactId])

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </Card>
    )
  }

  if (error || !contact) {
    return (
      <Card className="p-8">
        <div className="text-center">
          <p className="text-destructive">{error || 'Contact not found'}</p>
          <Button onClick={onClose} variant="outline" className="mt-4">
            Back to search
          </Button>
        </div>
      </Card>
    )
  }

  // Extract all variants
  const nameVariants = extractNameVariants(contact)
  const phoneVariants = extractPhoneVariants(contact)
  const addressVariants = extractAddressVariants(contact)
  const additionalEmails = extractAdditionalEmails(contact)

  // Calculate stats
  const activeSubscriptions = subscriptions.filter((s) => s.status === 'active')

  return (
    <div className="space-y-4">
      {/* Back Button */}
      <Button variant="ghost" onClick={onClose} className="gap-2">
        <ArrowLeft className="h-4 w-4" />
        Back to search
      </Button>

      {/* Header Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4 sm:gap-6">
            <Avatar
              initials={getInitials(contact.first_name, contact.last_name)}
              className="h-16 w-16 sm:h-20 sm:w-20 text-base sm:text-lg flex-shrink-0"
            />

            <div className="flex-1 space-y-3 min-w-0">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold">
                  {formatName(contact.first_name, contact.last_name)}
                </h2>

                {/* Contact Info - Email & Phone */}
                <div className="mt-3 space-y-3">
                  {/* Email */}
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 text-sm">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="font-mono text-foreground select-all text-xs sm:text-sm truncate">
                        {contact.email}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 px-2 flex-shrink-0"
                        onClick={() => handleCopyEmail(contact.email)}
                        title="Copy email"
                      >
                        {copiedEmail ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                    <Button
                      size="sm"
                      className="h-8 w-full sm:w-auto sm:ml-auto"
                      onClick={() => window.open(`mailto:${contact.email}`, '_blank')}
                    >
                      <Mail className="h-3 w-3 mr-1" />
                      Send Email
                    </Button>
                  </div>

                  {/* Phone */}
                  {contact.phone && (
                    <div className="flex items-center gap-3 text-sm">
                      <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <a
                        href={`tel:${contact.phone}`}
                        className="font-mono text-primary hover:underline select-all"
                        title="Click to call or select to copy"
                      >
                        {contact.phone}
                      </a>
                    </div>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {contact.email_subscribed && <Badge>Email Subscribed</Badge>}
                  <Badge variant="outline" className="capitalize">
                    {contact.source_system.replace('_', ' ')}
                  </Badge>
                </div>

                {/* Inline Stats */}
                <div className="mt-4 grid grid-cols-3 gap-3 sm:gap-4 pt-3 border-t border-border/50">
                  <div className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">Total Revenue</div>
                    <div className="font-bold text-sm sm:text-base">{formatCurrency(totalRevenue)}</div>
                    <div className="text-xs text-muted-foreground">{totalTransactionCount} txns</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">
                      {activeSubscriptions.length > 0
                        ? activeSubscriptions.map(s => s.products?.name).filter(Boolean).join(', ').substring(0, 20) + (activeSubscriptions.length > 1 ? '...' : '')
                        : 'No Active Memberships'
                      }
                    </div>
                    <div className="font-bold text-sm sm:text-base">{activeSubscriptions.length}</div>
                    <div className="text-xs text-muted-foreground">active</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">Friend Since</div>
                    <div className="font-bold text-sm sm:text-base">{formatDate(contact.created_at)}</div>
                    <div className="text-xs text-muted-foreground">{contact.source_system}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Action Buttons - Products & Tags */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        <Button
          variant={showProducts ? "default" : "outline"}
          size="sm"
          onClick={() => {
            setShowProducts(!showProducts)
            if (showTags) setShowTags(false)
          }}
          className={`flex-1 transition-all h-10 sm:h-9 ${showProducts ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 border-0' : 'border-purple-200 text-purple-700 hover:bg-purple-50 dark:border-purple-800 dark:text-purple-300 dark:hover:bg-purple-950/30'}`}
        >
          <Package className="h-4 w-4 mr-2" />
          Products ({subscriptions.length})
          {showProducts ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
        </Button>
        <Button
          variant={showTags ? "default" : "outline"}
          size="sm"
          onClick={() => {
            setShowTags(!showTags)
            if (showProducts) setShowProducts(false)
          }}
          className={`flex-1 transition-all h-10 sm:h-9 ${showTags ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 border-0' : 'border-purple-200 text-purple-700 hover:bg-purple-50 dark:border-purple-800 dark:text-purple-300 dark:hover:bg-purple-950/30'}`}
        >
          <Tag className="h-4 w-4 mr-2" />
          Tags ({contactTags.length})
          {showTags ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
        </Button>
      </div>

      {/* Products Expandable Section */}
      {showProducts && (
        <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-4 w-4" />
              Products & Subscriptions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {subscriptions.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No products or subscriptions yet</p>
            ) : (
              <div className="grid gap-3">
                {subscriptions.map((subscription) => (
                  <div
                    key={subscription.id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-border/50 bg-background/50 backdrop-blur-sm p-3 sm:p-4 transition-all hover:shadow-md hover:border-primary/30"
                  >
                    <div className="space-y-1 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-sm">
                          {subscription.products?.name || 'Unknown Product'}
                        </span>
                        <Badge
                          variant={subscription.status === 'active' ? 'default' : 'outline'}
                          className="text-xs"
                        >
                          {subscription.status}
                        </Badge>
                      </div>
                      {subscription.products?.product_type && (
                        <p className="text-xs text-muted-foreground capitalize">
                          {subscription.products.product_type}
                        </p>
                      )}
                    </div>
                    {subscription.amount && (
                      <div className="text-left sm:text-right flex-shrink-0">
                        <div className="font-semibold text-sm">
                          {formatCurrency(Number(subscription.amount))}
                          <span className="text-xs text-muted-foreground font-normal ml-1">
                            / {subscription.billing_cycle}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tags Expandable Section */}
      {showTags && (
        <Card className="border-purple-200/50 bg-gradient-to-br from-purple-50/50 to-transparent dark:from-purple-950/20 dark:border-purple-800/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Contact Tags
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Add Tag Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                placeholder="Add a tag..."
                className="flex-1 rounded-full border border-input bg-background/50 backdrop-blur-sm px-4 py-2.5 sm:py-2 text-sm focus:border-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-200 dark:focus:border-purple-700 dark:focus:ring-purple-900"
              />
              <Button
                size="sm"
                onClick={handleAddTag}
                disabled={!newTag.trim()}
                className="rounded-full px-4 sm:px-4 h-10 sm:h-9 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 flex-shrink-0"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {/* Tags Display */}
            {contactTags.length === 0 ? (
              <p className="text-sm text-muted-foreground italic text-center py-4">
                No tags yet. Add your first tag above!
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {contactTags.map((tag, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="rounded-full px-3 py-1 text-xs font-medium bg-gradient-to-r from-purple-100 to-pink-100 text-purple-900 border-purple-200 dark:from-purple-900/30 dark:to-pink-900/30 dark:text-purple-200 dark:border-purple-800 hover:shadow-md transition-all"
                  >
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-2 hover:text-destructive transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Notes</CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowAddNote(!showAddNote)}
          >
            {showAddNote ? 'Cancel' : '+ Add Note'}
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Add Note Form */}
          {showAddNote && (
            <div className="space-y-3 rounded-lg border border-border/50 bg-muted/30 p-3 sm:p-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Subject (3-5 words)
                </label>
                <input
                  type="text"
                  value={newNoteSubject}
                  onChange={(e) => setNewNoteSubject(e.target.value)}
                  placeholder="e.g., Follow up needed"
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2.5 sm:py-2 text-sm"
                  maxLength={50}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Note Content
                </label>
                <textarea
                  value={newNoteContent}
                  onChange={(e) => setNewNoteContent(e.target.value)}
                  placeholder="Enter your note here..."
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2.5 sm:py-2 text-sm resize-y min-h-[100px]"
                  rows={4}
                />
              </div>
              <Button
                size="sm"
                onClick={handleSaveNote}
                disabled={savingNote || !newNoteSubject.trim() || !newNoteContent.trim()}
                className="w-full sm:w-auto h-10 sm:h-9"
              >
                {savingNote ? 'Saving...' : 'Save Note'}
              </Button>
            </div>
          )}

          {/* Notes List */}
          {notes.length === 0 && !showAddNote && (
            <p className="text-sm text-muted-foreground">No notes yet. Add your first note!</p>
          )}

          {notes.map((note) => {
            const isExpanded = expandedNoteIds.has(note.id)
            const summary = note.subject || note.content.split(' ').slice(0, 3).join(' ')

            return (
              <div
                key={note.id}
                className="rounded-lg border border-border/50 bg-muted/30 p-3 transition-colors hover:bg-muted/50"
              >
                <div
                  className="flex cursor-pointer items-start justify-between"
                  onClick={() => toggleNoteExpand(note.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {summary}
                      </span>
                      {note.is_pinned && (
                        <Badge variant="secondary" className="text-xs">
                          Pinned
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(note.created_at)} • {note.author_name}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>

                {isExpanded && (
                  <div className="mt-3 border-t border-border/50 pt-3">
                    <p className="whitespace-pre-wrap text-sm text-foreground">
                      {note.content}
                    </p>
                    {note.note_type !== 'general' && (
                      <Badge variant="outline" className="mt-2 text-xs">
                        {note.note_type}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* Contact Information Sections */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Names */}
        {nameVariants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-4 w-4" />
                Names
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {nameVariants.map((variant, idx) => (
                <div key={idx} className="rounded-lg bg-muted/30 p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">
                        {formatName(variant.first_name, variant.last_name)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {variant.label} • {variant.source}
                      </p>
                    </div>
                    {idx === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Emails */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="h-4 w-4" />
              Email Addresses
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Primary email with subscription status */}
            <div className="rounded-lg bg-muted/30 p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <a
                    href={`mailto:${contact.email}`}
                    className="font-medium hover:text-primary"
                  >
                    {contact.email}
                  </a>
                  <p className="text-xs text-muted-foreground">
                    Primary • {contact.source_system}
                  </p>
                </div>
                <div className="flex gap-1 flex-wrap">
                  <Badge variant="secondary" className="text-xs">
                    Primary
                  </Badge>
                  {contact.email_subscribed ? (
                    <Badge variant="default" className="text-xs bg-green-600">
                      Subscribed
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">
                      Not Subscribed
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Additional emails with source priority */}
            {additionalEmails.map((additionalEmail, idx) => (
              <div key={idx} className="rounded-lg bg-muted/30 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 overflow-hidden">
                    <a
                      href={`mailto:${additionalEmail.email}`}
                      className="block truncate font-medium hover:text-primary"
                    >
                      {additionalEmail.email}
                    </a>
                    <p className="text-xs text-muted-foreground">
                      {getEmailSourceLabel(additionalEmail.source)}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {getEmailSourceLabel(additionalEmail.source)}
                  </Badge>
                </div>
              </div>
            ))}

            {additionalEmails.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No additional emails found
              </p>
            )}
          </CardContent>
        </Card>

        {/* Phones */}
        {phoneVariants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Phone className="h-4 w-4" />
                Phone Numbers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {phoneVariants.map((variant, idx) => (
                <div key={idx} className="rounded-lg bg-muted/30 p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <a
                        href={`tel:${variant.number}`}
                        className="font-medium hover:text-primary"
                      >
                        {variant.number}
                      </a>
                      <p className="text-xs text-muted-foreground">
                        {variant.label} • {variant.source}
                        {variant.country_code && ` • ${variant.country_code}`}
                      </p>
                    </div>
                    {idx === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Addresses */}
        {addressVariants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <MapPin className="h-4 w-4" />
                Addresses
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {addressVariants.map((variant, idx) => (
                <div key={idx} className="rounded-lg bg-muted/30 p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="whitespace-pre-line text-sm font-medium">
                        {formatAddress(variant)}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {variant.label} • {variant.source}
                        {variant.status && ` • ${variant.status}`}
                      </p>
                    </div>
                    {idx === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent Transactions Button */}
      {transactions.length > 0 && (
        <Button
          variant={showTransactions ? "default" : "outline"}
          size="sm"
          onClick={() => setShowTransactions(!showTransactions)}
          className="w-full h-10 sm:h-9"
        >
          Recent Transactions ({transactions.length})
          {showTransactions ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
        </Button>
      )}

      {/* Recent Transactions */}
      {transactions.length > 0 && showTransactions && (
        <Card id="transactions">
          <CardHeader>
            <CardTitle className="text-base">Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between rounded-xl border border-border/50 p-3 transition-colors hover:bg-accent/50"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">
                        {transaction.transaction_type.replace('_', ' ')}
                      </span>
                      <Badge
                        variant={
                          transaction.status === 'completed'
                            ? 'default'
                            : transaction.status === 'failed'
                            ? 'destructive'
                            : 'outline'
                        }
                        className="text-xs"
                      >
                        {transaction.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(transaction.transaction_date)}
                      {transaction.payment_method && ` • ${transaction.payment_method}`}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {formatCurrency(
                        Number(transaction.amount),
                        transaction.currency
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Subscriptions Button */}
      {activeSubscriptions.length > 0 && (
        <Button
          variant={showSubscriptions ? "default" : "outline"}
          size="sm"
          onClick={() => setShowSubscriptions(!showSubscriptions)}
          className="w-full h-10 sm:h-9"
        >
          Active Subscriptions ({activeSubscriptions.length})
          {showSubscriptions ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
        </Button>
      )}

      {/* Active Subscriptions */}
      {activeSubscriptions.length > 0 && showSubscriptions && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Subscriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeSubscriptions.map((subscription) => (
                <div
                  key={subscription.id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-border/50 p-3"
                >
                  <div className="space-y-1 flex-1">
                    <div className="font-medium text-sm sm:text-base">
                      {subscription.products?.name || subscription.billing_cycle || 'Subscription'}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {subscription.next_billing_date &&
                        `Next billing: ${formatDate(subscription.next_billing_date)}`}
                    </p>
                  </div>
                  <div className="flex items-center justify-between sm:flex-col sm:text-right gap-2 sm:gap-1">
                    {subscription.amount && (
                      <div className="font-semibold text-sm">
                        {formatCurrency(
                          Number(subscription.amount),
                          subscription.currency
                        )}
                        <span className="ml-1 text-xs font-normal text-muted-foreground">
                          / {subscription.billing_cycle}
                        </span>
                      </div>
                    )}
                    <Badge variant="default" className="text-xs">
                      {subscription.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}


    </div>
  )
}
