'use client'

import { useEffect, useState, useMemo, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Avatar } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatName, getInitials, formatCurrency, formatDate } from '@/lib/utils'
import {
  Mail,
  Phone,
  MapPin,
  Loader2,
  Copy,
  Check,
  CheckCircle,
  X,
  Plus,
  FileText,
  ChevronRight,
  User,
  AtSign,
  Tag,
  DollarSign,
  Building2,
  AlertTriangle,
  Truck,
  Pencil,
} from 'lucide-react'
import { ContactEditModal } from './ContactEditModal'
import type {
  Contact,
  ContactWithValidation,
  TransactionWithProduct,
  SubscriptionWithProduct,
  NameVariant,
  PhoneVariant,
  ContactEmail,
} from '@/lib/types/contact'
import type { MailingListData, RankedAddress } from '@/lib/types/mailing'
import { getConfidenceDisplay } from '@/lib/constants/scoring'

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
    'quickbooks': 'QuickBooks',
    'mailchimp': 'Mailchimp',
    'import': 'Imported',
  }
  return labels[source.toLowerCase()] || source
}

/**
 * Get product name from transaction
 * FAANG Standard: Pure function with clear priority logic
 * Priority: Direct product > Subscription product > Transaction type fallback
 */
function getTransactionDisplayName(transaction: TransactionWithProduct): string {
  return (
    transaction.products?.name ||
    transaction.subscriptions?.products?.name ||
    transaction.transaction_type.replace('_', ' ')
  )
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
 * Build ranked addresses for display with scores and USPS validation
 * FAANG Standard: Pure function, proper types, clear business logic
 */
function buildRankedAddresses(
  contact: ContactWithValidation,
  mailingListData: MailingListData | null
): RankedAddress[] {
  const addresses: RankedAddress[] = []

  // Mailing Address (Billing)
  if (contact.address_line_1 || contact.city) {
    addresses.push({
      label: 'Mailing',
      line_1: contact.address_line_1,
      line_2: contact.address_line_2,
      city: contact.city,
      state: contact.state,
      postal_code: contact.postal_code,
      country: contact.country,
      score: mailingListData?.billing_score || 0,
      uspsValidated: !!contact.billing_usps_validated_at,
      uspsValidatedDate: contact.billing_usps_validated_at || null,
      isRecommended: mailingListData?.recommended_address === 'billing',
      source: contact.source_system || 'unknown',
    })
  }

  // Shipping Address
  if (contact.shipping_address_line_1 || contact.shipping_city) {
    addresses.push({
      label: 'Shipping',
      line_1: contact.shipping_address_line_1,
      line_2: contact.shipping_address_line_2,
      city: contact.shipping_city,
      state: contact.shipping_state,
      postal_code: contact.shipping_postal_code,
      country: contact.shipping_country,
      score: mailingListData?.shipping_score || 0,
      uspsValidated: !!contact.shipping_usps_validated_at,
      uspsValidatedDate: contact.shipping_usps_validated_at || null,
      isRecommended: mailingListData?.recommended_address === 'shipping',
      source: 'paypal',
    })
  }

  // Other Address (from alternate fields if different)
  if (contact.address && contact.address !== contact.address_line_1 && contact.address !== contact.shipping_address_line_1) {
    addresses.push({
      label: 'Other',
      line_1: contact.address,
      line_2: contact.address_2,
      city: null,
      state: null,
      postal_code: null,
      country: null,
      score: 0, // No scoring for other addresses
      uspsValidated: false,
      uspsValidatedDate: null,
      isRecommended: false,
      source: 'legacy',
    })
  }

  // Sort by: recommended first, then by score
  return addresses.sort((a, b) => {
    if (a.isRecommended && !b.isRecommended) return -1
    if (!a.isRecommended && b.isRecommended) return 1
    return b.score - a.score
  })
}

export function ContactDetailCard({
  contactId,
  onClose,
}: ContactDetailCardProps) {
  const [contact, setContact] = useState<Contact | null>(null)
  const [transactions, setTransactions] = useState<TransactionWithProduct[]>([])
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
  const [showTags, setShowTags] = useState(false)
  const [showAdditionalNames, setShowAdditionalNames] = useState(false)
  const [showOtherEmails, setShowOtherEmails] = useState(false)
  const [showPhones, setShowPhones] = useState(false)
  const [showAddresses, setShowAddresses] = useState(false)
  const [showTransactionsSection, setShowTransactionsSection] = useState(false)
  const [contactTags, setContactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [mailingListData, setMailingListData] = useState<MailingListData | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [contactEmails, setContactEmails] = useState<ContactEmail[]>([])

  // Refs for scrolling to expanded sections
  const additionalNamesRef = useRef<HTMLDivElement>(null)
  const otherEmailsRef = useRef<HTMLDivElement>(null)
  const phonesRef = useRef<HTMLDivElement>(null)
  const addressesRef = useRef<HTMLDivElement>(null)
  const tagsRef = useRef<HTMLDivElement>(null)
  const transactionsRef = useRef<HTMLDivElement>(null)

  // Helper to scroll to a section when expanded
  const scrollToSection = (ref: React.RefObject<HTMLDivElement>) => {
    setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }

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

  /**
   * Validate and normalize tag input
   * FAANG Standard: Client-side validation before database call
   */
  const validateTag = (tag: string): { valid: boolean; normalized: string; error?: string } => {
    const normalized = tag.trim().toLowerCase()

    if (normalized.length === 0) {
      return { valid: false, normalized: '', error: 'Tag cannot be empty' }
    }

    if (normalized.length > 50) {
      return { valid: false, normalized: '', error: 'Tag cannot exceed 50 characters' }
    }

    // Check for duplicate (case-insensitive)
    if (contactTags.some(existingTag => existingTag.toLowerCase() === normalized)) {
      return { valid: false, normalized: '', error: 'Tag already exists' }
    }

    return { valid: true, normalized }
  }

  /**
   * Add tag using atomic database operation
   * FAANG Standard: Use PostgreSQL RPC to prevent race conditions
   */
  const handleAddTag = async () => {
    const validation = validateTag(newTag)

    if (!validation.valid) {
      if (validation.error) {
        alert(validation.error)
      }
      return
    }

    // Optimistic UI update
    const optimisticTags = [...contactTags, validation.normalized]
    setContactTags(optimisticTags)
    setNewTag('')

    try {
      const supabase = createClient()

      // Use atomic RPC function to prevent race conditions
      const { data, error } = await supabase.rpc('add_contact_tag', {
        p_contact_id: contactId,
        p_new_tag: validation.normalized,
      })

      if (error) {
        console.error('Error adding tag:', error)
        // Revert optimistic update
        setContactTags(contactTags)
        setNewTag(newTag) // Restore input
        alert(`Failed to add tag: ${error.message}`)
        return
      }

      // Sync with actual database state to handle any normalization
      if (data && data.tags) {
        setContactTags(data.tags)
      }
    } catch (err) {
      console.error('Error adding tag:', err)
      // Revert optimistic update
      setContactTags(contactTags)
      setNewTag(newTag) // Restore input
      alert('Failed to add tag. Please try again.')
    }
  }

  /**
   * Remove tag using atomic database operation
   * FAANG Standard: Use PostgreSQL RPC to prevent race conditions
   */
  const handleRemoveTag = async (tagToRemove: string) => {
    // Optimistic UI update
    const previousTags = [...contactTags]
    const optimisticTags = contactTags.filter((tag) => tag !== tagToRemove)
    setContactTags(optimisticTags)

    try {
      const supabase = createClient()

      // Use atomic RPC function to prevent race conditions
      const { data, error } = await supabase.rpc('remove_contact_tag', {
        p_contact_id: contactId,
        p_tag_to_remove: tagToRemove,
      })

      if (error) {
        console.error('Error removing tag:', error)
        // Revert optimistic update
        setContactTags(previousTags)
        alert(`Failed to remove tag: ${error.message}`)
        return
      }

      // Sync with actual database state
      if (data && data.tags) {
        setContactTags(data.tags)
      }
    } catch (err) {
      console.error('Error removing tag:', err)
      // Revert optimistic update
      setContactTags(previousTags)
      alert('Failed to remove tag. Please try again.')
    }
  }

  // Fetch contact details - extracted for reuse (initial load and after edit)
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

      // Fetch transactions with product information (both direct and via subscription)
      // FAANG Standard: Explicit select with proper joins for type safety
      const { data: transactionsData, error: transactionsError } = await supabase
        .from('transactions')
        .select(`
          *,
          products (
            name,
            product_type
          ),
          subscriptions (
            id,
            products (
              name,
              product_type
            )
          )
        `)
        .eq('contact_id', contactId)
        .order('transaction_date', { ascending: false })
        .limit(5)

      if (transactionsError) {
        console.error('Error fetching transactions:', transactionsError)
      }

      // Fetch total revenue (all transactions, not just the recent 5)
      // FAANG Standard: Include refunds - they are stored as negative amounts
      const { data: revenueData, error: revenueError } = await supabase
        .from('transactions')
        .select('amount, status')
        .eq('contact_id', contactId)
        .in('status', ['completed', 'succeeded'])

      if (revenueError) {
        console.error('Error fetching revenue:', revenueError)
      } else {
        // Sum all amounts (refunds are negative, so they subtract automatically)
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

      // Load tags from contact data
      if (contactData.tags && Array.isArray(contactData.tags)) {
        setContactTags(contactData.tags)
      }

      // Fetch mailing list recommendation with scores
      const { data: mailingData } = await supabase
        .from('mailing_list_priority')
        .select('recommended_address, billing_score, shipping_score, confidence')
        .eq('id', contactId)
        .single()

      if (mailingData) {
        setMailingListData(mailingData)
      }

      // Fetch contact emails from contact_emails table
      // FAANG Standard: Use normalized table for multi-value fields
      const { data: emailsData, error: emailsError } = await supabase
        .from('contact_emails')
        .select('*')
        .eq('contact_id', contactId)
        .order('is_primary', { ascending: false })
        .order('is_outreach', { ascending: false })
        .order('created_at', { ascending: true })

      if (emailsError) {
        console.error('Error fetching contact emails:', emailsError)
      } else {
        setContactEmails(emailsData || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contact')
      console.error('Error loading contact:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchContactDetails()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contactId])

  // Extract all variants with memoization for performance
  // FAANG Standard: Memoize expensive calculations to prevent unnecessary re-renders
  // CRITICAL: ALL hooks MUST be called BEFORE any conditional returns (Rules of Hooks)
  const nameVariants = useMemo(() => {
    if (!contact) return []
    return extractNameVariants(contact)
  }, [contact])

  const phoneVariants = useMemo(() => {
    if (!contact) return []
    return extractPhoneVariants(contact)
  }, [contact])

  const rankedAddresses = useMemo(() => {
    if (!contact) return []
    return buildRankedAddresses(contact, mailingListData)
  }, [contact, mailingListData])

  // Note: rankedEmails removed - now using contactEmails from contact_emails table

  // Calculate stats
  const activeSubscriptions = useMemo(() => {
    if (!subscriptions) return []
    return subscriptions.filter((s) => s.status === 'active')
  }, [subscriptions])

  // Early return for LOADING state - AFTER all hooks
  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </Card>
    )
  }

  // Early return for ERROR state - AFTER all hooks
  if (error || !contact) {
    return (
      <Card className="p-8">
        <div className="text-center">
          <p className="text-destructive">{error || 'Contact not found'}</p>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Edit Modal */}
      <ContactEditModal
        contact={contact}
        open={showEditModal}
        onOpenChange={setShowEditModal}
        onSaved={fetchContactDetails}
      />

      {/* Header Card */}
      <Card className="relative">
        <div className="absolute top-4 right-4 flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowEditModal(true)}
            className="h-8 w-8 p-0 rounded-full hover:bg-muted"
            title="Edit contact"
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0 rounded-full hover:bg-muted"
            title="Close"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4 sm:gap-6">
            <Avatar
              initials={getInitials(contact.first_name, contact.last_name)}
              className="h-16 w-16 sm:h-20 sm:w-20 text-base sm:text-lg flex-shrink-0"
            />

            <div className="flex-1 space-y-3 min-w-0 pr-8">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold">
                  {formatName(contact.first_name, contact.last_name)}
                </h2>

                {/* Contact Info - Email & Phone */}
                <div className="mt-3 space-y-3">
                  {/* Email */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <span className="font-mono text-foreground select-all text-xs sm:text-sm">
                        {contact.email}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 px-2 flex-shrink-0"
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

                    {/* Email Status Badge */}
                    <div className="flex items-center gap-2 ml-6">
                      {contact.email_subscribed ? (
                        <Badge variant="secondary" className="text-xs bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Email Subscribed
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs text-muted-foreground">
                          No Email Record
                        </Badge>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs"
                        onClick={() => window.open(`mailto:${contact.email}`, '_blank')}
                      >
                        <Mail className="h-3 w-3 mr-1" />
                        Send Email
                      </Button>
                    </div>
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

                  {/* Organization/Business */}
                  {contact.paypal_business_name && (
                    <div className="flex items-center gap-3 text-sm">
                      <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{contact.paypal_business_name}</span>
                        {(contact as ContactWithValidation).billing_address_source === 'google_contacts' && (
                          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300">
                            from Google
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant="outline" className="capitalize text-xs">
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

      {/* Notes Section - Clean, Minimal Design */}
      <Card className="border-border/50 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            <FileText className="h-4 w-4 text-muted-foreground" />
            Notes
          </CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowAddNote(!showAddNote)}
            className="h-8"
          >
            {showAddNote ? 'Cancel' : '+ Add Note'}
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Add Note Form */}
          {showAddNote && (
            <div className="space-y-3 rounded-lg border border-border bg-muted/30 p-4">
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Subject
                </label>
                <input
                  type="text"
                  value={newNoteSubject}
                  onChange={(e) => setNewNoteSubject(e.target.value)}
                  placeholder="e.g., Follow up needed"
                  className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
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
                  className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y min-h-[100px] focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  rows={4}
                />
              </div>
              <Button
                size="sm"
                onClick={handleSaveNote}
                disabled={savingNote || !newNoteSubject.trim() || !newNoteContent.trim()}
                className="h-9"
              >
                {savingNote ? 'Saving...' : 'Save Note'}
              </Button>
            </div>
          )}

          {/* Notes List */}
          {notes.length === 0 && !showAddNote && (
            <p className="text-sm text-muted-foreground italic text-center py-6">
              No notes yet. Add your first note!
            </p>
          )}

          {notes.map((note) => {
            const isExpanded = expandedNoteIds.has(note.id)
            const summary = note.subject || note.content.split(' ').slice(0, 3).join(' ')

            return (
              <div
                key={note.id}
                className="rounded-lg border border-border bg-card p-3 transition-colors hover:bg-muted/30"
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
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatDate(note.created_at)} • {note.author_name}
                    </p>
                  </div>
                  <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </div>

                {isExpanded && (
                  <div className="mt-3 border-t border-border pt-3">
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

      {/* Clean Expandable Section Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Names Card */}
        <button
          onClick={() => {
            setShowAdditionalNames(!showAdditionalNames)
            if (!showAdditionalNames) scrollToSection(additionalNamesRef)
          }}
          className={`group rounded-lg border p-4 text-left transition-all ${
            showAdditionalNames
              ? 'border-primary bg-muted/50 shadow-sm'
              : 'border-border bg-card hover:border-border/80 hover:shadow-sm'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-muted p-2">
                <User className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm">Names</div>
                <div className="text-xs text-muted-foreground">{nameVariants.length} variant{nameVariants.length !== 1 ? 's' : ''}</div>
              </div>
            </div>
            <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${showAdditionalNames ? 'rotate-90' : ''}`} />
          </div>
        </button>

        {/* Other Emails Card */}
        <button
          onClick={() => {
            setShowOtherEmails(!showOtherEmails)
            if (!showOtherEmails) scrollToSection(otherEmailsRef)
          }}
          className={`group rounded-lg border p-4 text-left transition-all ${
            showOtherEmails
              ? 'border-primary bg-muted/50 shadow-sm'
              : 'border-border bg-card hover:border-border/80 hover:shadow-sm'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-muted p-2">
                <AtSign className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm">All Emails</div>
                <div className="text-xs text-muted-foreground">
                  {contactEmails.length} email{contactEmails.length !== 1 ? 's' : ''} on file
                </div>
              </div>
            </div>
            <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${showOtherEmails ? 'rotate-90' : ''}`} />
          </div>
        </button>

        {/* Phone Numbers Card */}
        <button
          onClick={() => {
            setShowPhones(!showPhones)
            if (!showPhones) scrollToSection(phonesRef)
          }}
          className={`group rounded-lg border p-4 text-left transition-all ${
            showPhones
              ? 'border-primary bg-muted/50 shadow-sm'
              : 'border-border bg-card hover:border-border/80 hover:shadow-sm'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-muted p-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm">Phone Numbers</div>
                <div className="text-xs text-muted-foreground">{phoneVariants.length} number{phoneVariants.length !== 1 ? 's' : ''}</div>
              </div>
            </div>
            <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${showPhones ? 'rotate-90' : ''}`} />
          </div>
        </button>

        {/* Addresses Card */}
        <button
          onClick={() => {
            setShowAddresses(!showAddresses)
            if (!showAddresses) scrollToSection(addressesRef)
          }}
          className={`group rounded-lg border p-4 text-left transition-all ${
            showAddresses
              ? 'border-primary bg-muted/50 shadow-sm'
              : 'border-border bg-card hover:border-border/80 hover:shadow-sm'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-muted p-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm">Addresses</div>
                <div className="text-xs text-muted-foreground">{rankedAddresses.length} address{rankedAddresses.length !== 1 ? 'es' : ''}</div>
              </div>
            </div>
            <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${showAddresses ? 'rotate-90' : ''}`} />
          </div>
        </button>

        {/* Tags Card */}
        <button
          onClick={() => {
            setShowTags(!showTags)
            if (!showTags) scrollToSection(tagsRef)
          }}
          className={`group rounded-lg border p-4 text-left transition-all ${
            showTags
              ? 'border-primary bg-muted/50 shadow-sm'
              : 'border-border bg-card hover:border-border/80 hover:shadow-sm'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-muted p-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm">Tags</div>
                <div className="text-xs text-muted-foreground">{contactTags.length} tag{contactTags.length !== 1 ? 's' : ''}</div>
              </div>
            </div>
            <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${showTags ? 'rotate-90' : ''}`} />
          </div>
        </button>

        {/* Transactions Card */}
        <button
          onClick={() => {
            setShowTransactionsSection(!showTransactionsSection)
            if (!showTransactionsSection) scrollToSection(transactionsRef)
          }}
          className={`group rounded-lg border p-4 text-left transition-all ${
            showTransactionsSection
              ? 'border-primary bg-muted/50 shadow-sm'
              : 'border-border bg-card hover:border-border/80 hover:shadow-sm'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-md bg-muted p-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm">Transactions</div>
                <div className="text-xs text-muted-foreground">{transactions.length} recent</div>
              </div>
            </div>
            <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${showTransactionsSection ? 'rotate-90' : ''}`} />
          </div>
        </button>
      </div>

      {/* Expanded Content Sections */}
      <div className="space-y-4">

        {/* Expanded Sections */}

        {/* All Names Expanded */}
        {showAdditionalNames && (
          <div ref={additionalNamesRef}>
            <Card className="shadow-sm">
            <CardContent className="pt-6 space-y-2">
              {nameVariants.length > 0 ? (
                nameVariants.map((variant, idx) => (
                  <div key={idx} className="rounded-md border border-border bg-card p-3">
                    <p className="font-medium text-sm">
                      {formatName(variant.first_name, variant.last_name)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {variant.label} • {variant.source}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground italic text-center py-6">
                  No Names
                </p>
              )}
            </CardContent>
            </Card>
          </div>
        )}

        {/* All Emails Expanded - Using contact_emails table */}
        {showOtherEmails && (
          <div ref={otherEmailsRef}>
            <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <p className="text-sm text-muted-foreground">
                All email addresses from contact_emails table
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              {contactEmails.length === 0 ? (
                <p className="text-sm text-muted-foreground italic text-center py-6">
                  No emails in contact_emails table. Primary email: {contact.email}
                </p>
              ) : (
                contactEmails.map((email) => (
                  <div
                    key={email.id}
                    className={`rounded-lg border p-4 ${
                      email.is_primary
                        ? 'border-primary bg-primary/5'
                        : 'border-border bg-card'
                    }`}
                  >
                    <div className="space-y-3">
                      {/* Header Row with Badges */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          {email.is_primary && (
                            <Badge variant="default" className="text-xs">
                              Primary
                            </Badge>
                          )}
                          {email.is_outreach && (
                            <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300">
                              <Mail className="mr-1 h-3 w-3" />
                              Outreach
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs capitalize">
                            {email.email_type}
                          </Badge>
                        </div>

                        {/* Verification/Deliverability Status */}
                        <div className="flex flex-col items-end gap-1">
                          {email.verified && (
                            <Badge variant="secondary" className="text-xs bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              Verified
                            </Badge>
                          )}
                          {email.deliverable === true && (
                            <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 border-green-200">
                              Deliverable
                            </Badge>
                          )}
                          {email.deliverable === false && (
                            <Badge variant="destructive" className="text-xs">
                              Undeliverable
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Email Address */}
                      <div className="flex items-center gap-2">
                        <a
                          href={`mailto:${email.email}`}
                          className="font-mono text-sm hover:text-primary break-all"
                        >
                          {email.email}
                        </a>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 flex-shrink-0"
                          onClick={() => handleCopyEmail(email.email)}
                          title="Copy email"
                        >
                          {copiedEmail ? (
                            <Check className="h-3 w-3 text-green-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>

                      {/* Source and Metadata */}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="capitalize">{getEmailSourceLabel(email.source)}</span>
                        <span>•</span>
                        <span>Added {formatDate(email.created_at)}</span>
                      </div>

                      {/* Bounce Info if present */}
                      {email.last_bounce_at && (
                        <div className="mt-2 rounded-md bg-destructive/10 p-2 text-xs">
                          <span className="font-medium text-destructive">Last bounce:</span>{' '}
                          {formatDate(email.last_bounce_at)}
                          {email.bounce_reason && (
                            <span className="text-muted-foreground"> — {email.bounce_reason}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
            </Card>
          </div>
        )}

        {/* Phone Numbers Expanded */}
        {showPhones && phoneVariants.length > 0 && (
          <div ref={phonesRef}>
            <Card className="shadow-sm">
            <CardContent className="pt-6 space-y-2">
              {phoneVariants.map((variant, idx) => (
                <div key={idx} className="rounded-md border border-border bg-card p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <a
                        href={`tel:${variant.number}`}
                        className="font-medium text-sm hover:text-primary"
                      >
                        {variant.number}
                      </a>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        <p className="text-xs text-muted-foreground">
                          {variant.label} • {variant.source}
                          {variant.country_code && ` • ${variant.country_code}`}
                        </p>
                        {variant.source === 'google_contacts' && (
                          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                            Google
                          </Badge>
                        )}
                      </div>
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
          </div>
        )}

        {/* Addresses Expanded */}
        {showAddresses && rankedAddresses.length > 0 && (
          <div ref={addressesRef}>
            <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <p className="text-sm text-muted-foreground">
                Ranked by quality for mailing campaigns
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              {rankedAddresses.map((address, idx) => {
                const contactWithValidation = contact as ContactWithValidation
                const isGoogleSource = (
                  address.label === 'Mailing' &&
                  contactWithValidation.billing_address_source === 'google_contacts'
                )

                // USPS validation data
                const uspsData = address.label === 'Mailing' ? {
                  county: contactWithValidation.billing_usps_county,
                  rdi: contactWithValidation.billing_usps_rdi,
                  dpv: contactWithValidation.billing_usps_dpv_match_code,
                  latitude: contactWithValidation.billing_usps_latitude,
                  longitude: contactWithValidation.billing_usps_longitude,
                  precision: contactWithValidation.billing_usps_precision,
                  vacant: contactWithValidation.billing_usps_vacant,
                  active: contactWithValidation.billing_usps_active,
                } : address.label === 'Shipping' ? {
                  county: contactWithValidation.shipping_usps_county,
                  rdi: contactWithValidation.shipping_usps_rdi,
                  dpv: contactWithValidation.shipping_usps_dpv_match_code,
                  latitude: contactWithValidation.shipping_usps_latitude,
                  longitude: contactWithValidation.shipping_usps_longitude,
                  precision: contactWithValidation.shipping_usps_precision,
                  vacant: contactWithValidation.shipping_usps_vacant,
                  active: contactWithValidation.shipping_usps_active,
                } : null

                const confidence = getConfidenceDisplay(address.score)
                const hasCompleteAddress = address.line_1 || address.city

                return (
                  <div
                    key={idx}
                    className={`rounded-lg border p-4 ${
                      address.isRecommended
                        ? 'border-primary bg-primary/5'
                        : 'border-border bg-card'
                    }`}
                  >
                    <div className="space-y-3">
                      {/* Header Row */}
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="font-medium text-sm">{address.label}</h4>
                            {address.isRecommended && (
                              <Badge variant="default" className="text-xs">
                                Recommended
                              </Badge>
                            )}
                            {isGoogleSource && (
                              <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                                Google Contacts
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground capitalize mt-0.5">
                            {address.source}
                          </p>
                        </div>

                        {/* Tiered Score Badge */}
                        {address.score > 0 && (
                          <div className="text-right">
                            <Badge
                              variant="secondary"
                              className={`text-xs font-semibold ${
                                confidence.label === 'Very High' ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300' :
                                confidence.label === 'High' ? 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300' :
                                confidence.label === 'Medium' ? 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300' :
                                confidence.label === 'Low' ? 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300' :
                                'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300'
                              }`}
                            >
                              {confidence.label}
                            </Badge>
                            <div className="text-xs text-muted-foreground mt-1">Score: {address.score}</div>
                          </div>
                        )}
                      </div>

                      {/* Address Details */}
                      {hasCompleteAddress ? (
                        <div className="space-y-0.5 text-sm">
                          {address.line_1 && (
                            <p className="font-medium">{address.line_1}</p>
                          )}
                          {address.line_2 && (
                            <p>{address.line_2}</p>
                          )}
                          {(address.city || address.state || address.postal_code) && (
                            <p className="text-muted-foreground">
                              {[
                                address.city,
                                address.state,
                                address.postal_code,
                              ].filter(Boolean).join(', ')}
                            </p>
                          )}
                          {address.country && address.country !== 'US' && (
                            <p className="text-muted-foreground">{address.country}</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm italic text-muted-foreground">
                          No address on file
                        </p>
                      )}

                      {/* USPS Validation Details - ENHANCED */}
                      {address.uspsValidated && uspsData && (
                        <div className="mt-4 pt-3 border-t border-border/50 space-y-2">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <Badge variant="secondary" className="text-xs bg-emerald-100 text-emerald-700 border-emerald-200">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              USPS Validated
                            </Badge>
                            {uspsData.dpv === 'Y' && (
                              <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 border-green-200">
                                ✓ Deliverable
                              </Badge>
                            )}
                            {uspsData.vacant && (
                              <Badge variant="destructive" className="text-xs">
                                Vacant
                              </Badge>
                            )}
                          </div>

                          <div className="grid grid-cols-2 gap-3 text-xs">
                            {/* County */}
                            {uspsData.county && (
                              <div>
                                <span className="text-muted-foreground">County:</span>
                                <span className="ml-1.5 font-medium">{uspsData.county}</span>
                              </div>
                            )}

                            {/* Property Type */}
                            {uspsData.rdi && (
                              <div>
                                <span className="text-muted-foreground">Type:</span>
                                <span className="ml-1.5 font-medium capitalize">{uspsData.rdi}</span>
                              </div>
                            )}

                            {/* Precision */}
                            {uspsData.precision && (
                              <div>
                                <span className="text-muted-foreground">Precision:</span>
                                <span className="ml-1.5 font-medium">{uspsData.precision}</span>
                              </div>
                            )}

                            {/* DPV Match */}
                            {uspsData.dpv && (
                              <div>
                                <span className="text-muted-foreground">DPV:</span>
                                <span className="ml-1.5 font-medium">{uspsData.dpv}</span>
                              </div>
                            )}
                          </div>

                          {/* Geocoding */}
                          {uspsData.latitude && uspsData.longitude && (
                            <div className="mt-2 pt-2 border-t border-border/50">
                              <div className="text-xs">
                                <span className="text-muted-foreground">Location:</span>
                                <span className="ml-1.5 font-mono">
                                  {Number(uspsData.latitude).toFixed(4)}, {Number(uspsData.longitude).toFixed(4)}
                                </span>
                                <a
                                  href={`https://www.google.com/maps?q=${uspsData.latitude},${uspsData.longitude}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="ml-2 text-primary hover:underline"
                                >
                                  View on Map →
                                </a>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* NCOA Move Detection - CRITICAL ALERT */}
                      {(contactWithValidation.ncoa_move_date || contactWithValidation.ncoa_new_address) && (
                        <div className="mt-4 pt-3 border-t-2 border-destructive/30 space-y-3">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <Badge variant="destructive" className="text-xs font-semibold">
                              <AlertTriangle className="mr-1 h-3 w-3" />
                              NCOA: Contact Moved
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              <Truck className="mr-1 h-3 w-3" />
                              Address Update Required
                            </Badge>
                          </div>

                          <div className="rounded-lg bg-destructive/10 p-3 space-y-2">
                            {contactWithValidation.ncoa_move_date && (
                              <div className="text-xs">
                                <span className="font-semibold text-destructive">Move Date:</span>
                                <span className="ml-1.5 font-medium">
                                  {formatDate(contactWithValidation.ncoa_move_date)}
                                </span>
                              </div>
                            )}

                            {contactWithValidation.ncoa_new_address && (
                              <div className="text-xs">
                                <span className="font-semibold text-destructive">New Address:</span>
                                <div className="ml-1.5 mt-1 font-medium whitespace-pre-line">
                                  {contactWithValidation.ncoa_new_address}
                                </div>
                              </div>
                            )}

                            <div className="pt-2 mt-2 border-t border-destructive/20">
                              <p className="text-xs text-destructive/80 font-medium">
                                ⚠️ Do not mail to current address. Update contact information before next campaign.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Address Quality Score */}
                      {contactWithValidation.address_quality_score !== null &&
                       contactWithValidation.address_quality_score !== undefined && (
                        <div className="mt-3 pt-3 border-t border-border/50">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-muted-foreground">Address Quality</span>
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                                <div
                                  className={`h-full rounded-full transition-all ${
                                    contactWithValidation.address_quality_score >= 80
                                      ? 'bg-emerald-500'
                                      : contactWithValidation.address_quality_score >= 60
                                      ? 'bg-blue-500'
                                      : contactWithValidation.address_quality_score >= 40
                                      ? 'bg-amber-500'
                                      : 'bg-red-500'
                                  }`}
                                  style={{ width: `${contactWithValidation.address_quality_score}%` }}
                                />
                              </div>
                              <span className="text-xs font-semibold">
                                {contactWithValidation.address_quality_score}/100
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </CardContent>
            </Card>
          </div>
        )}

        {/* Tags Expanded */}
        {showTags && (
          <div ref={tagsRef}>
            <Card className="shadow-sm">
            <CardContent className="pt-6 space-y-4">
              {/* Add Tag Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="Add a tag..."
                  className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <Button
                  size="sm"
                  onClick={handleAddTag}
                  disabled={!newTag.trim()}
                  className="h-9"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>

              {/* Tags Display */}
              {contactTags.length === 0 ? (
                <p className="text-sm text-muted-foreground italic text-center py-6">
                  No tags yet. Add your first tag above!
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {contactTags.map((tag, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="text-sm"
                    >
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1.5 hover:text-destructive transition-colors"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
            </Card>
          </div>
        )}

        {/* Transactions Expanded */}
        {showTransactionsSection && transactions.length > 0 && (
          <div ref={transactionsRef}>
            <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-base font-semibold">Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {transactions.map((transaction) => (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between rounded-lg border border-border bg-card p-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm capitalize">
                          {getTransactionDisplayName(transaction)}
                        </span>
                        <Badge
                          variant={
                            transaction.status === 'completed'
                              ? 'secondary'
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
                    <div className="text-right font-semibold text-sm">
                      {formatCurrency(
                        Number(transaction.amount),
                        transaction.currency
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
            </Card>
          </div>
        )}
      </div>

    </div>
  )
}
