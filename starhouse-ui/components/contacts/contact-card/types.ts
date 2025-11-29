/**
 * Types for Contact 360 Card components
 * FAANG Standard: Centralized types for the contact card module
 */

import type { Contact, ContactEmail, ContactTag, TransactionWithProduct, SubscriptionWithProduct } from '@/lib/types/contact'

export interface ContactNote {
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

export interface ContactRole {
  id: string
  contact_id: string
  role: string
  status: string
  started_at: string | null
  ended_at: string | null
  source: string | null
  notes: string | null
}

export interface DonorSummary {
  donor_id: string
  contact_id: string
  donor_status: string
  lifetime_amount: number
  lifetime_count: number
  largest_gift: number
  average_gift: number
  first_gift_date: string | null
  last_gift_date: string | null
  ytd_amount: number
  ytd_count: number
  is_major_donor: boolean
  do_not_solicit: boolean
  recognition_name: string | null
}

export interface MembershipStatus {
  contact_id: string
  subscription_id: string
  subscription_status: string
  membership_fee: number
  billing_cycle: string
  start_date: string | null
  next_billing_date: string | null
  cancellation_date: string | null
  membership_status: string
  member_since: string | null
  lifetime_value: number
  last_payment_date: string | null
}

export interface Contact360Data {
  contact: Contact
  contactEmails: ContactEmail[]
  contactTags: ContactTag[]
  contactRoles: ContactRole[]
  contactNotes: ContactNote[]
  transactions: TransactionWithProduct[]
  subscriptions: SubscriptionWithProduct[]
  donorSummary: DonorSummary | null
  membershipStatus: MembershipStatus | null
  totalRevenue: number
  totalTransactionCount: number
}

export interface CollapsibleSectionProps {
  title: string
  count?: number
  icon: React.ReactNode
  defaultOpen?: boolean
  children: React.ReactNode
  emptyMessage?: string
  isEmpty?: boolean
}
