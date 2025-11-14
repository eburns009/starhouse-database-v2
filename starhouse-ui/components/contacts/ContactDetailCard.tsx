'use client'

import { useEffect, useState, useMemo } from 'react'
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
  CheckCircle,
  Tag,
  Package,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  FileText,
} from 'lucide-react'
import { AlmondButton } from './AlmondButton'
import type {
  Contact,
  Transaction,
  SubscriptionWithProduct,
  NameVariant,
  PhoneVariant,
} from '@/lib/types/contact'
import type { MailingListData, RankedAddress, RankedEmail } from '@/lib/types/mailing'
import { EMAIL_SCORE_WEIGHTS, EMAIL_SOURCE_PRIORITY, getConfidenceDisplay } from '@/lib/constants/scoring'

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
 * Get source priority for email ranking
 * FAANG Standard: Pure function with clear business logic
 */
function getEmailSourcePriority(source: string): number {
  const key = source.toLowerCase() as keyof typeof EMAIL_SOURCE_PRIORITY
  return EMAIL_SOURCE_PRIORITY[key] || EMAIL_SOURCE_PRIORITY.MANUAL
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
 * Note: Uses type assertion for extended contact fields not in base type
 */
function buildRankedAddresses(
  contact: Contact,
  mailingListData: MailingListData | null
): RankedAddress[] {
  const addresses: RankedAddress[] = []
  const contactExt = contact as any // Type assertion for extended fields

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
      uspsValidated: !!contactExt.billing_usps_validated_at,
      uspsValidatedDate: contactExt.billing_usps_validated_at || null,
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
      uspsValidated: !!contactExt.shipping_usps_validated_at,
      uspsValidatedDate: contactExt.shipping_usps_validated_at || null,
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

/**
 * Build ranked emails for display with scores and verification
 * FAANG Standard: Pure function, proper types, optimized scoring
 * Note: Uses type assertion for extended contact fields not in base type
 */
function buildRankedEmails(contact: Contact): RankedEmail[] {
  const emails: RankedEmail[] = []
  const processedEmails = new Set<string>()
  const contactExt = contact as any // Type assertion for extended fields

  // Helper to calculate email score using constants
  const calculateEmailScore = (
    isPrimary: boolean,
    isSubscribed: boolean,
    sourcePriority: number,
    isVerified: boolean
  ): number => {
    let score = 0

    // Primary email bonus
    if (isPrimary) score += EMAIL_SCORE_WEIGHTS.PRIMARY

    // Subscription status
    if (isSubscribed) score += EMAIL_SCORE_WEIGHTS.SUBSCRIBED

    // Source priority (inverse of priority number)
    score += Math.max(0, EMAIL_SCORE_WEIGHTS.SOURCE_PRIORITY_MAX - (sourcePriority * 4))

    // Verified email
    if (isVerified) score += EMAIL_SCORE_WEIGHTS.VERIFIED

    return Math.min(100, score)
  }

  // Primary Email (from main contact)
  if (contact.email) {
    const email = contact.email.toLowerCase()
    processedEmails.add(email)

    const sourcePriority = getEmailSourcePriority(contact.source_system || 'manual')
    const score = calculateEmailScore(
      true, // isPrimary
      contact.email_subscribed || false,
      sourcePriority,
      false // isVerified - could add email_verified field later
    )

    emails.push({
      label: 'Primary',
      email: contact.email,
      score,
      isSubscribed: contact.email_subscribed || false,
      isVerified: false,
      isPrimary: true,
      isRecommended: false, // Will be set after sorting
      source: contact.source_system || 'manual',
      sourcePriority,
    })
  }

  // PayPal Email
  if (contactExt.paypal_email && !processedEmails.has(contactExt.paypal_email.toLowerCase())) {
    processedEmails.add(contactExt.paypal_email.toLowerCase())

    const score = calculateEmailScore(
      false,
      false, // PayPal emails not typically in subscription list
      EMAIL_SOURCE_PRIORITY.PAYPAL,
      false
    )

    emails.push({
      label: 'PayPal',
      email: contactExt.paypal_email,
      score,
      isSubscribed: false,
      isVerified: false,
      isPrimary: false,
      isRecommended: false,
      source: 'paypal',
      sourcePriority: EMAIL_SOURCE_PRIORITY.PAYPAL,
    })
  }

  // Additional Email
  if (contactExt.additional_email && !processedEmails.has(contactExt.additional_email.toLowerCase())) {
    processedEmails.add(contactExt.additional_email.toLowerCase())

    const sourcePriority = getEmailSourcePriority(contactExt.additional_email_source || 'manual')
    const score = calculateEmailScore(
      false,
      false,
      sourcePriority,
      false
    )

    emails.push({
      label: 'Additional',
      email: contactExt.additional_email,
      score,
      isSubscribed: false,
      isVerified: false,
      isPrimary: false,
      isRecommended: false,
      source: contactExt.additional_email_source || 'manual',
      sourcePriority,
    })
  }

  // Zoho Email
  if (contactExt.zoho_email && !processedEmails.has(contactExt.zoho_email.toLowerCase())) {
    processedEmails.add(contactExt.zoho_email.toLowerCase())

    const score = calculateEmailScore(
      false,
      false,
      EMAIL_SOURCE_PRIORITY.ZOHO,
      false
    )

    emails.push({
      label: 'Zoho',
      email: contactExt.zoho_email,
      score,
      isSubscribed: false,
      isVerified: false,
      isPrimary: false,
      isRecommended: false,
      source: 'zoho',
      sourcePriority: EMAIL_SOURCE_PRIORITY.ZOHO,
    })
  }

  // Sort by score (highest first)
  emails.sort((a, b) => b.score - a.score)

  // Mark the highest scoring email as recommended
  if (emails.length > 0) {
    emails[0].isRecommended = true
  }

  return emails
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
  const [showAdditionalNames, setShowAdditionalNames] = useState(false)
  const [showOtherEmails, setShowOtherEmails] = useState(false)
  const [showPhones, setShowPhones] = useState(false)
  const [showAddresses, setShowAddresses] = useState(false)
  const [contactTags, setContactTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')
  const [mailingListData, setMailingListData] = useState<MailingListData | null>(null)

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
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contact')
        console.error('Error loading contact:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchContactDetails()
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

  const rankedEmails = useMemo(() => {
    if (!contact) return []
    return buildRankedEmails(contact)
  }, [contact])

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
          <Button onClick={onClose} variant="outline" className="mt-4">
            Back to search
          </Button>
        </div>
      </Card>
    )
  }

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

      {/* Notes Section - Moved to Top with Soft Background */}
      <Card className="bg-gradient-to-br from-rose-50/40 via-lavender-50/30 to-purple-50/40 border-rose-200/30 dark:from-rose-950/10 dark:via-lavender-950/10 dark:to-purple-950/10 dark:border-rose-800/20">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4 text-rose-600" />
            Notes
          </CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowAddNote(!showAddNote)}
            className="border-rose-300 text-rose-700 hover:bg-rose-100 dark:border-rose-800 dark:text-rose-300"
          >
            {showAddNote ? 'Cancel' : '+ Add Note'}
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Add Note Form */}
          {showAddNote && (
            <div className="space-y-3 rounded-lg border border-rose-200/50 bg-white/50 backdrop-blur-sm p-3 sm:p-4 dark:bg-black/20 dark:border-rose-800/30">
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
                className="w-full sm:w-auto h-10 sm:h-9 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600"
              >
                {savingNote ? 'Saving...' : 'Save Note'}
              </Button>
            </div>
          )}

          {/* Notes List */}
          {notes.length === 0 && !showAddNote && (
            <p className="text-sm text-muted-foreground italic text-center py-4">
              No notes yet. Add your first note!
            </p>
          )}

          {notes.map((note) => {
            const isExpanded = expandedNoteIds.has(note.id)
            const summary = note.subject || note.content.split(' ').slice(0, 3).join(' ')

            return (
              <div
                key={note.id}
                className="rounded-lg border border-rose-200/50 bg-white/50 backdrop-blur-sm p-3 transition-all hover:bg-white/70 hover:shadow-sm dark:bg-black/20 dark:border-rose-800/30 dark:hover:bg-black/30"
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
                        <Badge variant="secondary" className="text-xs bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-200 dark:border-rose-800">
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
                  <div className="mt-3 border-t border-rose-200/50 pt-3 dark:border-rose-800/30">
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

      {/* Almond-Shaped Expandable Buttons */}
      <div className="space-y-3">
        {/* Additional Names Button */}
        {nameVariants.length > 1 && (
          <>
            <AlmondButton
              icon={User}
              label="Additional Names"
              count={nameVariants.length - 1}
              isExpanded={showAdditionalNames}
              onClick={() => setShowAdditionalNames(!showAdditionalNames)}
              gradientFrom="from-rose-100"
              gradientTo="to-pink-100"
            />

            {showAdditionalNames && (
              <Card className="border-rose-200/50 bg-gradient-to-br from-rose-50/30 to-transparent dark:border-rose-800/30">
                <CardContent className="pt-4 space-y-2">
                  {nameVariants.slice(1).map((variant, idx) => (
                    <div key={idx} className="rounded-lg bg-white/50 backdrop-blur-sm p-3 dark:bg-black/20">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-sm">
                            {formatName(variant.first_name, variant.last_name)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {variant.label} • {variant.source}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Other Emails Button */}
        {rankedEmails.length > 1 && (
          <>
            <AlmondButton
              icon={Mail}
              label="Other Emails"
              count={rankedEmails.length - 1}
              isExpanded={showOtherEmails}
              onClick={() => setShowOtherEmails(!showOtherEmails)}
              gradientFrom="from-purple-100"
              gradientTo="to-lavender-100"
            />

            {showOtherEmails && (
              <Card className="border-purple-200/50 bg-gradient-to-br from-purple-50/30 to-transparent dark:border-purple-800/30">
                <CardHeader className="pb-3">
                  <p className="text-xs text-muted-foreground">
                    Ranked by deliverability for email campaigns
                  </p>
                </CardHeader>
                <CardContent className="space-y-2">
                  {rankedEmails.slice(1).map((email, idx) => {
                    const confidence = getConfidenceDisplay(email.score)

                    return (
                      <div
                        key={idx}
                        className="relative overflow-hidden rounded-xl border-2 border-purple-200/50 bg-white/50 backdrop-blur-sm p-3 dark:bg-black/20 dark:border-purple-800/30"
                      >
                        <div className="space-y-2">
                          {/* Header Row */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <div className="rounded-lg bg-purple-100 p-1.5 dark:bg-purple-900/30">
                                <Mail className="h-4 w-4 text-purple-600 dark:text-purple-300" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-sm">{email.label}</h4>
                                <p className="text-xs text-muted-foreground capitalize">{getEmailSourceLabel(email.source)}</p>
                              </div>
                            </div>

                            {/* Score Badge */}
                            <div className="flex flex-col items-end gap-1">
                              <div className="flex items-center gap-2">
                                <div className="text-right">
                                  <div className="text-lg font-bold">{email.score}</div>
                                  <div className="text-xs text-muted-foreground leading-none">/ 100</div>
                                </div>
                                <div className={`h-10 w-2 rounded-full ${confidence.bgClass}`} />
                              </div>
                              <Badge className={`${confidence.color} bg-transparent border text-xs font-semibold`}>
                                {confidence.label}
                              </Badge>
                            </div>
                          </div>

                          {/* Email Address */}
                          <div className="space-y-0.5 rounded-lg bg-background/50 p-2">
                            <a
                              href={`mailto:${email.email}`}
                              className="font-medium text-sm hover:text-primary break-all"
                            >
                              {email.email}
                            </a>
                          </div>

                          {/* Status Badges */}
                          <div className="flex flex-wrap gap-1.5">
                            {email.isSubscribed && (
                              <Badge className="bg-emerald-500/10 text-emerald-700 border-emerald-500/20 text-xs py-0">
                                <CheckCircle className="mr-1 h-3 w-3" />
                                Subscribed
                              </Badge>
                            )}
                            {!email.isSubscribed && (
                              <Badge variant="outline" className="text-xs text-muted-foreground py-0">
                                Not Subscribed
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Phone Numbers Button */}
        {phoneVariants.length > 0 && (
          <>
            <AlmondButton
              icon={Phone}
              label="Phone Numbers"
              count={phoneVariants.length}
              isExpanded={showPhones}
              onClick={() => setShowPhones(!showPhones)}
              gradientFrom="from-blue-100"
              gradientTo="to-cyan-100"
            />

            {showPhones && (
              <Card className="border-blue-200/50 bg-gradient-to-br from-blue-50/30 to-transparent dark:border-blue-800/30">
                <CardContent className="pt-4 space-y-2">
                  {phoneVariants.map((variant, idx) => (
                    <div key={idx} className="rounded-lg bg-white/50 backdrop-blur-sm p-3 dark:bg-black/20">
                      <div className="flex items-start justify-between">
                        <div>
                          <a
                            href={`tel:${variant.number}`}
                            className="font-medium text-sm hover:text-primary"
                          >
                            {variant.number}
                          </a>
                          <p className="text-xs text-muted-foreground">
                            {variant.label} • {variant.source}
                            {variant.country_code && ` • ${variant.country_code}`}
                          </p>
                        </div>
                        {idx === 0 && (
                          <Badge variant="secondary" className="text-xs py-0 bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-200 dark:border-blue-800">
                            Primary
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Addresses Button */}
        {rankedAddresses.length > 0 && (
          <>
            <AlmondButton
              icon={MapPin}
              label="Addresses"
              count={rankedAddresses.length}
              isExpanded={showAddresses}
              onClick={() => setShowAddresses(!showAddresses)}
              gradientFrom="from-emerald-100"
              gradientTo="to-teal-100"
            />

            {showAddresses && (
              <Card className="border-emerald-200/50 bg-gradient-to-br from-emerald-50/30 to-transparent dark:border-emerald-800/30">
                <CardHeader className="pb-3">
                  <p className="text-xs text-muted-foreground">
                    Ranked by quality for mailing campaigns
                  </p>
                </CardHeader>
                <CardContent className="space-y-3">
                  {rankedAddresses.map((address, idx) => {
                    const confidence = getConfidenceDisplay(address.score)
                    const hasCompleteAddress = address.line_1 || address.city

                    return (
                      <div
                        key={idx}
                        className={`relative overflow-hidden rounded-xl border-2 p-3 transition-all ${
                          address.isRecommended
                            ? 'border-primary bg-gradient-to-br from-primary/10 via-primary/5 to-background shadow-lg'
                            : 'border-emerald-200/50 bg-white/50 backdrop-blur-sm dark:bg-black/20 dark:border-emerald-800/30'
                        }`}
                      >
                        {/* Recommended Badge Ribbon */}
                        {address.isRecommended && (
                          <div className="absolute -right-1 -top-1">
                            <div className="relative">
                              <div className="absolute inset-0 bg-gradient-to-br from-primary to-primary/80 blur-sm" />
                              <div className="relative flex items-center gap-1 rounded-bl-lg rounded-tr-lg bg-gradient-to-br from-primary to-primary/90 px-2.5 py-1 text-xs font-bold text-primary-foreground shadow-lg">
                                <Mail className="h-3 w-3" />
                                Use for Campaign
                              </div>
                            </div>
                          </div>
                        )}

                        <div className="space-y-2">
                          {/* Header Row */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <div className={`rounded-lg ${address.isRecommended ? 'bg-primary/20' : 'bg-emerald-100 dark:bg-emerald-900/30'} p-1.5`}>
                                <MapPin className={`h-4 w-4 ${address.isRecommended ? 'text-primary' : 'text-emerald-600 dark:text-emerald-300'}`} />
                              </div>
                              <div>
                                <h4 className="font-semibold text-sm">{address.label}</h4>
                                <p className="text-xs text-muted-foreground capitalize">{address.source}</p>
                              </div>
                            </div>

                            {/* Score Badge */}
                            {address.score > 0 && (
                              <div className="flex flex-col items-end gap-1">
                                <div className="flex items-center gap-2">
                                  <div className="text-right">
                                    <div className="text-lg font-bold">{address.score}</div>
                                    <div className="text-xs text-muted-foreground leading-none">/ 100</div>
                                  </div>
                                  <div className={`h-10 w-2 rounded-full ${confidence.bgClass}`} />
                                </div>
                                <Badge className={`${confidence.color} bg-transparent border text-xs font-semibold`}>
                                  {confidence.label}
                                </Badge>
                              </div>
                            )}
                          </div>

                          {/* Address Details */}
                          {hasCompleteAddress ? (
                            <div className="space-y-0.5 rounded-lg bg-background/50 p-2">
                              {address.line_1 && (
                                <p className="font-medium text-sm">{address.line_1}</p>
                              )}
                              {address.line_2 && (
                                <p className="text-sm">{address.line_2}</p>
                              )}
                              {(address.city || address.state || address.postal_code) && (
                                <p className="text-sm text-muted-foreground">
                                  {[
                                    address.city,
                                    address.state,
                                    address.postal_code,
                                  ].filter(Boolean).join(', ')}
                                </p>
                              )}
                              {address.country && address.country !== 'US' && (
                                <p className="text-sm text-muted-foreground">{address.country}</p>
                              )}
                            </div>
                          ) : (
                            <p className="text-sm italic text-muted-foreground">
                              No address on file
                            </p>
                          )}

                          {/* Status Badges */}
                          <div className="flex flex-wrap gap-1.5">
                            {address.uspsValidated && (
                              <Badge className="bg-emerald-500/10 text-emerald-700 border-emerald-500/20 text-xs py-0">
                                <CheckCircle className="mr-1 h-3 w-3" />
                                USPS Validated
                              </Badge>
                            )}
                            {!address.uspsValidated && address.score > 0 && (
                              <Badge variant="outline" className="text-xs text-muted-foreground py-0">
                                Not Validated
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Tags Button */}
        <AlmondButton
          icon={Tag}
          label="Tags"
          count={contactTags.length}
          isExpanded={showTags}
          onClick={() => setShowTags(!showTags)}
          gradientFrom="from-violet-100"
          gradientTo="to-purple-100"
        />

        {showTags && (
          <Card className="border-violet-200/50 bg-gradient-to-br from-violet-50/30 to-transparent dark:border-violet-800/30">
            <CardContent className="pt-4 space-y-4">
              {/* Add Tag Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="Add a tag..."
                  className="flex-1 rounded-full border border-input bg-background/50 backdrop-blur-sm px-4 py-2.5 sm:py-2 text-sm focus:border-violet-300 focus:outline-none focus:ring-2 focus:ring-violet-200 dark:focus:border-violet-700 dark:focus:ring-violet-900"
                />
                <Button
                  size="sm"
                  onClick={handleAddTag}
                  disabled={!newTag.trim()}
                  className="rounded-full px-4 h-10 sm:h-9 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 flex-shrink-0"
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
                      className="rounded-full px-3 py-1 text-xs font-medium bg-gradient-to-r from-violet-100 to-purple-100 text-violet-900 border-violet-200 dark:from-violet-900/30 dark:to-purple-900/30 dark:text-violet-200 dark:border-violet-800 hover:shadow-md transition-all"
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

        {/* Products & Subscriptions Button */}
        <AlmondButton
          icon={Package}
          label="Products & Subscriptions"
          count={subscriptions.length}
          isExpanded={showProducts}
          onClick={() => setShowProducts(!showProducts)}
          gradientFrom="from-fuchsia-100"
          gradientTo="to-pink-100"
        />

        {showProducts && (
          <Card className="border-fuchsia-200/50 bg-gradient-to-br from-fuchsia-50/30 to-transparent dark:border-fuchsia-800/30">
            <CardContent className="pt-4 space-y-3">
              {subscriptions.length === 0 ? (
                <p className="text-sm text-muted-foreground italic text-center py-4">No products or subscriptions yet</p>
              ) : (
                <div className="grid gap-3">
                  {subscriptions.map((subscription) => (
                    <div
                      key={subscription.id}
                      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-fuchsia-200/50 bg-white/50 backdrop-blur-sm p-3 sm:p-4 transition-all hover:shadow-md hover:border-fuchsia-300/50 dark:bg-black/20 dark:border-fuchsia-800/30"
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
