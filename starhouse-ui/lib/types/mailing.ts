/**
 * Mailing list and contact ranking types
 * FAANG Standard: Proper type definitions for type safety
 */

import type { ConfidenceLevel } from '../constants/scoring'

/**
 * Mailing list entry from database
 */
export interface MailingListEntry {
  confidence: ConfidenceLevel
  billing_score: number
  shipping_score: number
  recommended_address: 'billing' | 'shipping'
}

/**
 * Mailing list data for a contact
 * FAANG Standard: Complete type definition with NCOA fields
 */
export interface MailingListData {
  recommended_address: 'billing' | 'shipping'
  billing_score: number
  shipping_score: number
  confidence: ConfidenceLevel
  // NCOA (National Change of Address) fields
  ncoa_detected?: boolean
  ncoa_move_date?: string | null
  ncoa_new_address?: string | null
  // Address validation fields
  address_quality_score?: number | null
  address_validated?: boolean | null
  last_validation_date?: string | null
}

/**
 * Ranked address for mailing campaigns
 */
export interface RankedAddress {
  label: 'Mailing' | 'Shipping' | 'Other'
  line_1: string | null
  line_2: string | null
  city: string | null
  state: string | null
  postal_code: string | null
  country: string | null
  score: number
  uspsValidated: boolean
  uspsValidatedDate: string | null
  isRecommended: boolean
  source: string
}

/**
 * Ranked email for campaigns
 */
export interface RankedEmail {
  label: 'Primary' | 'PayPal' | 'Additional' | 'Zoho'
  email: string
  score: number
  isSubscribed: boolean
  isVerified: boolean
  isPrimary: boolean
  isRecommended: boolean
  source: string
  sourcePriority: number
}

/**
 * Mailing statistics aggregated data
 * FAANG Standard: Complete statistics including NCOA tracking
 */
export interface MailingStatistics {
  total: number
  confidenceCounts: Record<ConfidenceLevel, number>
  recommendBilling: number
  recommendShipping: number
  scoreSum: number
  avgScore: number
  readyToMail: number
  readyPercentage: number
  // NCOA statistics
  ncoaMoveCount?: number
  ncoaPercentage?: number
  validatedCount?: number
  validatedPercentage?: number
}
