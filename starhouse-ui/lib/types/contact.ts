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

export interface AlternateEmail {
  id: string
  email: string
  email_type: 'personal' | 'work' | 'other'
  is_primary: boolean
  is_outreach: boolean
  source: string
  verified: boolean
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
