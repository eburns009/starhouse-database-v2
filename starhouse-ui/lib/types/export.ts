/**
 * Export types and interfaces
 * FAANG Standard: Comprehensive type safety for export operations
 */

import type { ConfidenceLevel } from '../constants/scoring'

/**
 * Mailing list export filters
 */
export interface MailingListExportFilters {
  minConfidence?: ConfidenceLevel
  recentCustomersDays?: number
  includeMetadata?: boolean
}

/**
 * Mailing list export row (from database view)
 */
export interface MailingListExportRow {
  first_name: string | null
  last_name: string | null
  email: string | null
  address_line_1: string | null
  address_line_2: string | null
  city: string | null
  state: string | null
  postal_code: string | null
  country: string | null
  address_source: 'billing' | 'shipping'
  confidence: ConfidenceLevel
  billing_score: number
  shipping_score: number
  billing_complete: boolean
  shipping_complete: boolean
  is_manual_override: boolean
  last_transaction_date: string | null
}

/**
 * CSV row for export (clean format for mail merge)
 */
export interface MailingListCSVRow {
  first_name: string
  last_name: string
  email: string
  address_line_1: string
  address_line_2: string
  city: string
  state: string
  postal_code: string
  country: string
  // Optional metadata fields
  address_source?: string
  confidence?: string
  score?: string
  billing_score?: string
  shipping_score?: string
  manual_override?: string
  last_transaction_date?: string
}

/**
 * Export result statistics
 */
export interface ExportStatistics {
  totalContacts: number
  confidenceBreakdown: Record<ConfidenceLevel, number>
  sourceBreakdown: {
    billing: number
    shipping: number
  }
}

/**
 * Export audit log entry
 */
export interface ExportAuditLog {
  exportedBy: string
  exportedAt: string
  totalRecords: number
  minConfidence: ConfidenceLevel
  filters: MailingListExportFilters
}
