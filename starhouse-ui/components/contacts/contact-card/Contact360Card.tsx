'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Card } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'
import { ContactHeader } from './ContactHeader'
import { IdentityColumn } from './IdentityColumn'
import { RelationshipsColumn } from './RelationshipsColumn'
import { ContactEditModal } from '../ContactEditModal'
import type { Contact, ContactEmail, ContactTag, TransactionWithProduct, SubscriptionWithProduct } from '@/lib/types/contact'
import type { ContactNote, ContactRole, DonorSummary, MembershipStatus } from './types'

interface Contact360CardProps {
  contactId: string
  onClose: () => void
}

/**
 * 360° Contact Card - Unified view of all contact relationships
 * FAANG Standard: Modular component following CRM best practices from UI research
 *
 * Layout:
 * - Header: Name, badges, key contact methods
 * - Left Column (40%): Identity (emails, phones, addresses, tags, roles, notes)
 * - Right Column (60%): Relationships (donations, membership, transactions, purchases)
 */
export function Contact360Card({ contactId, onClose }: Contact360CardProps) {
  // Data state
  const [contact, setContact] = useState<Contact | null>(null)
  const [contactEmails, setContactEmails] = useState<ContactEmail[]>([])
  const [contactTags, setContactTags] = useState<ContactTag[]>([])
  const [contactRoles, setContactRoles] = useState<ContactRole[]>([])
  const [contactNotes, setContactNotes] = useState<ContactNote[]>([])
  const [transactions, setTransactions] = useState<TransactionWithProduct[]>([])
  const [subscriptions, setSubscriptions] = useState<SubscriptionWithProduct[]>([])
  const [donorSummary, setDonorSummary] = useState<DonorSummary | null>(null)
  const [membershipStatus, setMembershipStatus] = useState<MembershipStatus | null>(null)
  const [totalRevenue, setTotalRevenue] = useState(0)
  const [totalTransactionCount, setTotalTransactionCount] = useState(0)

  // UI state
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)

  /**
   * Fetch all contact data
   */
  const fetchContactData = useCallback(async () => {
    try {
      const supabase = createClient()

      // Fetch contact
      const { data: contactData, error: contactError } = await supabase
        .from('contacts')
        .select('*')
        .eq('id', contactId)
        .single()

      if (contactError) throw contactError
      setContact(contactData)

      // Fetch contact emails
      const { data: emailsData } = await supabase
        .from('contact_emails')
        .select('*')
        .eq('contact_id', contactId)
        .order('is_primary', { ascending: false })
        .order('created_at', { ascending: true })

      setContactEmails(emailsData || [])

      // Fetch contact tags with tag info
      const { data: tagsData } = await supabase
        .from('contact_tags')
        .select(`
          id,
          contact_id,
          tag_id,
          created_at,
          tags (
            id,
            name,
            name_norm,
            description,
            category
          )
        `)
        .eq('contact_id', contactId)
        .order('created_at', { ascending: true })

      setContactTags((tagsData as ContactTag[]) || [])

      // Fetch contact roles
      const { data: rolesData } = await supabase
        .from('contact_roles')
        .select('*')
        .eq('contact_id', contactId)
        .order('status', { ascending: true })
        .order('started_at', { ascending: false })

      setContactRoles(rolesData || [])

      // Fetch contact notes
      const { data: notesData } = await supabase
        .from('contact_notes')
        .select('*')
        .eq('contact_id', contactId)
        .order('is_pinned', { ascending: false })
        .order('created_at', { ascending: false })

      setContactNotes(notesData || [])

      // Fetch transactions with product info
      const { data: transactionsData } = await supabase
        .from('transactions')
        .select(`
          *,
          quickbooks_memo,
          raw_source,
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
        .limit(10)

      setTransactions(transactionsData || [])

      // Fetch total revenue
      const { data: revenueData } = await supabase
        .from('transactions')
        .select('amount')
        .eq('contact_id', contactId)
        .in('status', ['completed', 'succeeded'])

      const revenue = revenueData?.reduce((sum: number, t: { amount: number }) => sum + Number(t.amount), 0) || 0
      setTotalRevenue(revenue)

      // Fetch transaction count
      const { count: transactionCount } = await supabase
        .from('transactions')
        .select('*', { count: 'exact', head: true })
        .eq('contact_id', contactId)

      setTotalTransactionCount(transactionCount || 0)

      // Fetch subscriptions with product info
      const { data: subscriptionsData } = await supabase
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
        .not('product_id', 'is', null)
        .order('created_at', { ascending: false })

      setSubscriptions(subscriptionsData || [])

      // Fetch donor summary (if exists)
      const { data: donorData } = await supabase
        .from('v_donor_summary')
        .select('*')
        .eq('contact_id', contactId)
        .single()

      setDonorSummary(donorData || null)

      // Fetch membership status (if exists)
      const { data: membershipData } = await supabase
        .from('v_membership_status')
        .select('*')
        .eq('contact_id', contactId)
        .single()

      setMembershipStatus(membershipData || null)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contact')
      console.error('Error loading contact:', err)
    } finally {
      setLoading(false)
    }
  }, [contactId])

  // Fetch data on mount and when contactId changes
  useEffect(() => {
    fetchContactData()
  }, [fetchContactData])

  // Callback for refreshing tags
  const handleTagsUpdated = useCallback(async () => {
    const supabase = createClient()
    const { data: tagsData } = await supabase
      .from('contact_tags')
      .select(`
        id,
        contact_id,
        tag_id,
        created_at,
        tags (
          id,
          name,
          name_norm,
          description,
          category
        )
      `)
      .eq('contact_id', contactId)
      .order('created_at', { ascending: true })

    setContactTags((tagsData as ContactTag[]) || [])
  }, [contactId])

  // Callback for refreshing notes
  const handleNotesUpdated = useCallback(async () => {
    const supabase = createClient()
    const { data: notesData } = await supabase
      .from('contact_notes')
      .select('*')
      .eq('contact_id', contactId)
      .order('is_pinned', { ascending: false })
      .order('created_at', { ascending: false })

    setContactNotes(notesData || [])
  }, [contactId])

  // Loading state
  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </Card>
    )
  }

  // Error state
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
        onSaved={fetchContactData}
      />

      {/* Header */}
      <ContactHeader
        contact={contact}
        donorSummary={donorSummary}
        membershipStatus={membershipStatus}
        onEdit={() => setShowEditModal(true)}
        onClose={onClose}
      />

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Left Column - Identity (40%) */}
        <div className="lg:col-span-2">
          <IdentityColumn
            contact={contact}
            contactEmails={contactEmails}
            contactTags={contactTags}
            contactRoles={contactRoles}
            contactNotes={contactNotes}
            onTagsUpdated={handleTagsUpdated}
            onNotesUpdated={handleNotesUpdated}
          />
        </div>

        {/* Right Column - Relationships (60%) */}
        <div className="lg:col-span-3">
          <RelationshipsColumn
            transactions={transactions}
            subscriptions={subscriptions}
            donorSummary={donorSummary}
            membershipStatus={membershipStatus}
            totalRevenue={totalRevenue}
            totalTransactionCount={totalTransactionCount}
          />
        </div>
      </div>
    </div>
  )
}
