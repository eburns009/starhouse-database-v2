/**
 * Contact-related types
 * FAANG Standard: Domain-specific types for business logic
 */

import type { Database } from './database'

export type Contact = Database['public']['Tables']['contacts']['Row']
export type Transaction = Database['public']['Tables']['transactions']['Row']
export type Subscription = Database['public']['Tables']['subscriptions']['Row']
export type Product = Database['public']['Tables']['products']['Row']

export interface SubscriptionWithProduct extends Subscription {
  products: Pick<Product, 'id' | 'name' | 'product_type'> | null
}

/**
 * Transaction with joined product information
 * FAANG Standard: Explicit type for database joins instead of 'any'
 *
 * Includes multi-source fallback fields for product name display:
 * - products.name (direct product link)
 * - subscriptions.products.name (via subscription)
 * - quickbooks_memo (Kajabi transactions)
 * - raw_source.event_name (Ticket Tailor events)
 */
export interface TransactionWithProduct extends Transaction {
  products?: Pick<Product, 'name' | 'product_type'> | null
  subscriptions?: {
    id: string
    products: Pick<Product, 'name' | 'product_type'> | null
  } | null
  // Multi-source fallback fields
  quickbooks_memo?: string | null
  raw_source?: Record<string, unknown> | null
}

/**
 * Email record from contact_emails table
 * FAANG Standard: Match database schema exactly
 */
export interface ContactEmail {
  id: string
  contact_id: string
  email: string
  email_type: 'personal' | 'work' | 'other'
  is_primary: boolean
  is_outreach: boolean
  source: 'kajabi' | 'paypal' | 'ticket_tailor' | 'zoho' | 'quickbooks' | 'mailchimp' | 'manual' | 'import'
  verified: boolean
  verified_at: string | null
  deliverable: boolean | null
  last_bounce_at: string | null
  bounce_reason: string | null
  created_at: string
  updated_at: string
}

/** @deprecated Use ContactEmail instead */
export interface AlternateEmail {
  id: string
  email: string
  email_type: 'personal' | 'work' | 'other'
  is_primary: boolean
  is_outreach: boolean
  source: string
  verified: boolean
}

/**
 * Tag record from contact_tags junction table with joined tag info
 * FAANG Standard: Match database schema with JOIN result
 */
export interface ContactTag {
  id: string
  contact_id: string
  tag_id: string
  created_at: string
  tags: {
    id: string
    name: string
    name_norm: string
    description: string | null
    category: string | null
  }
}

export interface ContactWithDetails extends Contact {
  alternate_emails: AlternateEmail[]
  transactions: Transaction[]
  subscriptions: Subscription[]
}

export interface ContactStats {
  total_revenue: number
  transaction_count: number
  subscription_count: number
  active_subscriptions: number
}

export interface NameVariant {
  first_name: string | null
  last_name: string | null
  source: string
  label: string
}

export interface PhoneVariant {
  number: string
  source: string
  label: string
  country_code?: string | null
}

export interface AddressVariant {
  line_1: string | null
  line_2: string | null
  city: string | null
  state: string | null
  postal_code: string | null
  country: string | null
  source: string
  label: string
  status?: string | null
}

/**
 * Extended Contact type with validation and enrichment fields
 * FAANG Standard: Explicit type instead of 'any' type assertions
 *
 * Note: These fields exist in the database but may not be in the base Contact type
 * because they're from enrichment processes (USPS validation, Google Contacts, etc.)
 */
export interface ContactWithValidation extends Contact {
  // NCOA (National Change of Address) fields
  ncoa_move_date?: string | null
  ncoa_new_address?: string | null
  address_validated?: boolean | null
  usps_dpv_confirmation?: 'Y' | 'N' | 'S' | 'D' | null
  usps_validation_date?: string | null
  usps_rdi?: string | null
  address_quality_score?: number | null

  // Household management
  household_id?: string | null
  is_primary_household_contact?: boolean | null

  // Duplicate management
  secondary_emails?: string[] | null
  is_alias_of?: string | null
  merge_history?: Array<{
    merged_from_id: string
    merged_at: string
    reason: string
  }> | null

  // USPS validation fields (billing address)
  billing_usps_validated_at?: string | null
  billing_usps_county?: string | null
  billing_usps_rdi?: string | null
  billing_usps_dpv_match_code?: string | null
  billing_usps_latitude?: number | null
  billing_usps_longitude?: number | null
  billing_usps_precision?: string | null
  billing_usps_vacant?: boolean | null
  billing_usps_active?: boolean | null
  billing_address_source?: string | null

  // USPS validation fields (shipping address)
  shipping_usps_validated_at?: string | null
  shipping_usps_county?: string | null
  shipping_usps_rdi?: string | null
  shipping_usps_dpv_match_code?: string | null
  shipping_usps_latitude?: number | null
  shipping_usps_longitude?: number | null
  shipping_usps_precision?: string | null
  shipping_usps_vacant?: boolean | null
  shipping_usps_active?: boolean | null

  // Extended email fields
  paypal_email?: string | null
  additional_email?: string | null
  additional_email_source?: string | null
  zoho_email?: string | null
}
