/**
 * Mailing List Export Service
 * FAANG Standard: Separation of concerns, testable business logic
 */

import type { SupabaseClient } from '@supabase/supabase-js'
import type { Database } from '../types/database'
import type {
  MailingListExportFilters,
  MailingListExportRow,
  MailingListCSVRow,
  ExportStatistics,
} from '../types/export'
import type { ConfidenceLevel } from '../constants/scoring'

/**
 * Confidence level ranking (for filtering)
 * Lower number = higher confidence
 */
const CONFIDENCE_RANK: Record<ConfidenceLevel, number> = {
  very_high: 1,
  high: 2,
  medium: 3,
  low: 4,
  very_low: 5,
}

/**
 * Fetch mailing list contacts with filters
 * Returns data optimized for CSV export
 */
export async function fetchMailingListContacts(
  supabase: SupabaseClient<Database>,
  filters: MailingListExportFilters = {}
): Promise<{ data: MailingListExportRow[] | null; error: Error | null }> {
  try {
    // Start with base query
    let query = supabase
      .from('mailing_list_export')
      .select('*')
      .order('confidence', { ascending: true })
      .order('billing_score', { ascending: false })

    // Apply confidence filter
    if (filters.minConfidence) {
      const minRank = CONFIDENCE_RANK[filters.minConfidence]
      const allowedLevels = Object.entries(CONFIDENCE_RANK)
        .filter(([_, rank]) => rank <= minRank)
        .map(([level]) => level)

      query = query.in('confidence', allowedLevels)
    }

    // Apply recent customers filter
    if (filters.recentCustomersDays) {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - filters.recentCustomersDays)
      query = query.gte('last_transaction_date', cutoffDate.toISOString())
    }

    const { data, error } = await query.returns<MailingListExportRow[]>()

    if (error) {
      console.error('[fetchMailingListContacts] Database query failed:', error)
      return { data: null, error: new Error(`Database query failed: ${error.message}`) }
    }

    return { data, error: null }
  } catch (err) {
    console.error('[fetchMailingListContacts] Unexpected error:', err)
    return {
      data: null,
      error: err instanceof Error ? err : new Error('Unknown error occurred'),
    }
  }
}

/**
 * Transform database row to CSV row
 * Handles null values and optional metadata
 */
export function transformToCSVRow(
  row: MailingListExportRow,
  includeMetadata: boolean = true
): MailingListCSVRow {
  const baseRow: MailingListCSVRow = {
    first_name: row.first_name || '',
    last_name: row.last_name || '',
    email: row.email || '',
    address_line_1: row.address_line_1 || '',
    address_line_2: row.address_line_2 || '',
    city: row.city || '',
    state: row.state || '',
    postal_code: row.postal_code || '',
    country: row.country || 'US',
  }

  if (includeMetadata) {
    const maxScore = Math.max(row.billing_score || 0, row.shipping_score || 0)
    return {
      ...baseRow,
      address_source: row.address_source,
      confidence: row.confidence,
      score: String(maxScore),
      billing_score: String(row.billing_score || 0),
      shipping_score: String(row.shipping_score || 0),
      manual_override: row.is_manual_override ? 'yes' : 'no',
      last_transaction_date: row.last_transaction_date || '',
    }
  }

  return baseRow
}

/**
 * Calculate export statistics
 */
export function calculateExportStatistics(rows: MailingListExportRow[]): ExportStatistics {
  const confidenceBreakdown: Record<ConfidenceLevel, number> = {
    very_high: 0,
    high: 0,
    medium: 0,
    low: 0,
    very_low: 0,
  }

  const sourceBreakdown = {
    billing: 0,
    shipping: 0,
  }

  for (const row of rows) {
    confidenceBreakdown[row.confidence]++
    if (row.address_source === 'billing') {
      sourceBreakdown.billing++
    } else {
      sourceBreakdown.shipping++
    }
  }

  return {
    totalContacts: rows.length,
    confidenceBreakdown,
    sourceBreakdown,
  }
}

/**
 * Convert rows to CSV string
 * Uses RFC 4180 compliant CSV formatting
 */
export function rowsToCSV(rows: MailingListCSVRow[]): string {
  if (rows.length === 0) {
    return ''
  }

  // Get headers from first row
  const headers = Object.keys(rows[0])

  // Escape CSV value (handle quotes and commas)
  const escapeValue = (value: string | undefined): string => {
    if (value === undefined) return ''
    const str = String(value)
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`
    }
    return str
  }

  // Build CSV
  const lines: string[] = []

  // Header row
  lines.push(headers.map(escapeValue).join(','))

  // Data rows
  for (const row of rows) {
    const values = headers.map(header => escapeValue(row[header as keyof MailingListCSVRow]))
    lines.push(values.join(','))
  }

  return lines.join('\n')
}

/**
 * Log export to audit table
 * Note: This function logs to the audit table if the RPC function exists
 */
export async function logExport(
  supabase: SupabaseClient<Database>,
  statistics: ExportStatistics,
  filters: MailingListExportFilters
): Promise<void> {
  try {
    const { data: userData } = await supabase.auth.getUser()

    if (!userData.user) {
      console.warn('[logExport] No authenticated user for audit log')
      return
    }

    // Log export to audit table
    // @ts-expect-error - RPC function may not be in generated types yet
    await supabase.rpc('log_mailing_list_export', {
      p_total_records: statistics.totalContacts,
      p_min_confidence: filters.minConfidence || 'high',
      p_recent_days: filters.recentCustomersDays || null,
      p_include_metadata: filters.includeMetadata ?? true,
    })

    console.log('[logExport] Audit log created successfully')
  } catch (err) {
    // Don't fail the export if logging fails, just log the error
    console.error('[logExport] Failed to log export:', err)
  }
}
