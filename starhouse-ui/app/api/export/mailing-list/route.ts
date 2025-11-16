/**
 * Mailing List Export API Route
 * FAANG Standard: Streaming response, proper auth, comprehensive error handling
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import {
  fetchMailingListContacts,
  transformToCSVRow,
  rowsToCSV,
  calculateExportStatistics,
  logExport,
} from '@/lib/services/mailingListExport'
import type { MailingListExportFilters } from '@/lib/types/export'
import type { ConfidenceLevel } from '@/lib/constants/scoring'

/**
 * Export mailing list as CSV
 * GET /api/export/mailing-list
 *
 * Query parameters:
 *   - minConfidence: 'very_high' | 'high' | 'medium' | 'low' | 'very_low' (default: 'high')
 *   - recentDays: number (optional, filter by transaction date)
 *   - includeMetadata: 'true' | 'false' (default: 'true')
 *
 * @returns CSV file download
 */
export async function GET(request: NextRequest) {
  const startTime = Date.now()

  try {
    // ========================================================================
    // STEP 1: Authentication Check
    // ========================================================================
    const supabase = createClient()
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser()

    if (authError || !user) {
      console.error('[API /export/mailing-list] Unauthorized access attempt')
      return NextResponse.json(
        {
          error: 'Unauthorized',
          message: 'You must be logged in to export mailing lists',
        },
        { status: 401 }
      )
    }

    console.log(`[API /export/mailing-list] Export requested by user: ${user.email}`)

    // ========================================================================
    // STEP 2: Parse and Validate Query Parameters
    // ========================================================================
    const searchParams = request.nextUrl.searchParams
    const minConfidenceParam = searchParams.get('minConfidence') || 'high'
    const recentDaysParam = searchParams.get('recentDays')
    const includeMetadataParam = searchParams.get('includeMetadata') !== 'false'

    // Validate confidence level
    const validConfidenceLevels: ConfidenceLevel[] = [
      'very_high',
      'high',
      'medium',
      'low',
      'very_low',
    ]

    if (!validConfidenceLevels.includes(minConfidenceParam as ConfidenceLevel)) {
      return NextResponse.json(
        {
          error: 'Invalid Parameter',
          message: `Invalid confidence level: ${minConfidenceParam}. Must be one of: ${validConfidenceLevels.join(', ')}`,
        },
        { status: 400 }
      )
    }

    const minConfidence = minConfidenceParam as ConfidenceLevel

    // Validate recent days
    let recentDays: number | undefined
    if (recentDaysParam) {
      recentDays = parseInt(recentDaysParam, 10)
      if (isNaN(recentDays) || recentDays < 1) {
        return NextResponse.json(
          {
            error: 'Invalid Parameter',
            message: 'recentDays must be a positive integer',
          },
          { status: 400 }
        )
      }
    }

    const filters: MailingListExportFilters = {
      minConfidence,
      recentCustomersDays: recentDays,
      includeMetadata: includeMetadataParam,
    }

    console.log('[API /export/mailing-list] Filters:', filters)

    // ========================================================================
    // STEP 3: Fetch Data from Database
    // ========================================================================
    const { data: contacts, error: fetchError } = await fetchMailingListContacts(
      supabase,
      filters
    )

    if (fetchError || !contacts) {
      console.error('[API /export/mailing-list] Database fetch failed:', fetchError)
      return NextResponse.json(
        {
          error: 'Database Error',
          message: 'Failed to fetch mailing list data',
          details: fetchError?.message,
        },
        { status: 500 }
      )
    }

    // Handle empty result
    if (contacts.length === 0) {
      console.warn('[API /export/mailing-list] No contacts match filters')
      return NextResponse.json(
        {
          error: 'No Data',
          message: 'No contacts match the specified filters',
          filters,
        },
        { status: 404 }
      )
    }

    console.log(`[API /export/mailing-list] Fetched ${contacts.length} contacts`)

    // ========================================================================
    // STEP 4: Transform to CSV
    // ========================================================================
    const csvRows = contacts.map(row => transformToCSVRow(row, includeMetadataParam))
    const csvContent = rowsToCSV(csvRows)

    if (!csvContent) {
      console.error('[API /export/mailing-list] CSV generation failed')
      return NextResponse.json(
        {
          error: 'Export Error',
          message: 'Failed to generate CSV content',
        },
        { status: 500 }
      )
    }

    // ========================================================================
    // STEP 5: Calculate Statistics and Log Export
    // ========================================================================
    const statistics = calculateExportStatistics(contacts)

    // Log export asynchronously (don't block response)
    logExport(supabase, statistics, filters).catch(err => {
      console.error('[API /export/mailing-list] Audit log failed:', err)
    })

    // ========================================================================
    // STEP 6: Return CSV Response
    // ========================================================================
    const duration = Date.now() - startTime
    const timestamp = new Date().toISOString().split('T')[0]
    const filename = `mailing_list_${minConfidence}_${timestamp}.csv`

    console.log(`[API /export/mailing-list] Export successful:`, {
      contacts: contacts.length,
      duration: `${duration}ms`,
      filename,
      user: user.email,
    })

    return new NextResponse(csvContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'X-Export-Count': String(contacts.length),
        'X-Export-Duration': `${duration}ms`,
      },
    })
  } catch (error) {
    // ========================================================================
    // CATCH-ALL ERROR HANDLER
    // ========================================================================
    console.error('[API /export/mailing-list] Unexpected error:', error)

    return NextResponse.json(
      {
        error: 'Internal Server Error',
        message: 'An unexpected error occurred during export',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}

/**
 * OPTIONS handler for CORS preflight
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Allow': 'GET, OPTIONS',
    },
  })
}
