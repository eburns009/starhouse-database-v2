'use client'

/**
 * Mailing List Export Button
 * FAANG Standard: Proper loading states, error handling, user feedback
 */

import { useState } from 'react'
import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { ConfidenceLevel } from '@/lib/constants/scoring'

interface ExportOptions {
  minConfidence: ConfidenceLevel
  recentDays?: number
  includeMetadata: boolean
}

interface ExportState {
  status: 'idle' | 'loading' | 'success' | 'error'
  message?: string
  count?: number
}

interface Props {
  /** Optional custom export options */
  defaultOptions?: Partial<ExportOptions>
  /** Button variant */
  variant?: 'default' | 'outline' | 'ghost'
  /** Button size */
  size?: 'default' | 'sm' | 'lg'
  /** Show detailed status messages */
  showStatusMessage?: boolean
}

export function ExportMailingListButton({
  defaultOptions = {},
  variant = 'default',
  size = 'default',
  showStatusMessage = true,
}: Props) {
  const [exportState, setExportState] = useState<ExportState>({ status: 'idle' })

  const options: ExportOptions = {
    minConfidence: defaultOptions.minConfidence || 'high',
    recentDays: defaultOptions.recentDays,
    includeMetadata: defaultOptions.includeMetadata ?? true,
  }

  /**
   * Trigger mailing list export
   * Downloads CSV file directly to user's browser
   */
  const handleExport = async () => {
    setExportState({ status: 'loading' })

    try {
      // Build query parameters
      const params = new URLSearchParams({
        minConfidence: options.minConfidence,
        includeMetadata: String(options.includeMetadata),
      })

      if (options.recentDays) {
        params.append('recentDays', String(options.recentDays))
      }

      console.log('[ExportMailingListButton] Starting export with params:', Object.fromEntries(params))

      // Fetch CSV from API
      const response = await fetch(`/api/export/mailing-list?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Accept': 'text/csv',
        },
      })

      // Handle error responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        const errorMessage = errorData?.message || `Export failed with status ${response.status}`
        console.error('[ExportMailingListButton] Export failed:', errorMessage)
        throw new Error(errorMessage)
      }

      // Get export metadata from headers
      const count = parseInt(response.headers.get('X-Export-Count') || '0', 10)
      const duration = response.headers.get('X-Export-Duration')

      console.log('[ExportMailingListButton] Export successful:', { count, duration })

      // Get CSV content
      const csvBlob = await response.blob()

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition')
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/)
      const filename = filenameMatch?.[1] || `mailing_list_${new Date().toISOString().split('T')[0]}.csv`

      // Trigger download
      const url = window.URL.createObjectURL(csvBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      console.log('[ExportMailingListButton] Download triggered:', filename)

      // Show success state
      setExportState({
        status: 'success',
        message: `Successfully exported ${count.toLocaleString()} contacts`,
        count,
      })

      // Reset to idle after 3 seconds
      setTimeout(() => {
        setExportState({ status: 'idle' })
      }, 3000)
    } catch (error) {
      console.error('[ExportMailingListButton] Export failed:', error)

      setExportState({
        status: 'error',
        message: error instanceof Error ? error.message : 'Export failed. Please try again.',
      })

      // Reset to idle after 5 seconds
      setTimeout(() => {
        setExportState({ status: 'idle' })
      }, 5000)
    }
  }

  // Render different states
  const isLoading = exportState.status === 'loading'
  const isSuccess = exportState.status === 'success'
  const isError = exportState.status === 'error'

  // Determine button appearance based on state
  const getButtonVariant = () => {
    if (isError) return 'destructive'
    return variant
  }

  const getButtonContent = () => {
    if (isLoading) {
      return (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Exporting...
        </>
      )
    }

    if (isSuccess) {
      return (
        <>
          <CheckCircle className="h-4 w-4" />
          Exported {exportState.count?.toLocaleString()}
        </>
      )
    }

    if (isError) {
      return (
        <>
          <AlertCircle className="h-4 w-4" />
          Export Failed
        </>
      )
    }

    return (
      <>
        <Download className="h-4 w-4" />
        Export Mailing List
      </>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <Button
        onClick={handleExport}
        disabled={isLoading}
        variant={getButtonVariant()}
        size={size}
        className="gap-2"
      >
        {getButtonContent()}
      </Button>

      {/* Status Message */}
      {showStatusMessage && exportState.message && (
        <p
          className={`text-xs transition-all ${
            isSuccess ? 'text-emerald-600' : isError ? 'text-destructive' : 'text-muted-foreground'
          }`}
        >
          {exportState.message}
        </p>
      )}
    </div>
  )
}

/**
 * Pre-configured export button variants for common use cases
 */
export function ExportHighConfidenceButton() {
  return (
    <ExportMailingListButton
      defaultOptions={{
        minConfidence: 'high',
        includeMetadata: true,
      }}
    />
  )
}

export function ExportVeryHighConfidenceButton() {
  return (
    <ExportMailingListButton
      defaultOptions={{
        minConfidence: 'very_high',
        includeMetadata: true,
      }}
    />
  )
}

export function ExportRecentCustomersButton() {
  return (
    <ExportMailingListButton
      defaultOptions={{
        minConfidence: 'high',
        recentDays: 365,
        includeMetadata: true,
      }}
    />
  )
}

export function ExportCleanListButton() {
  return (
    <ExportMailingListButton
      defaultOptions={{
        minConfidence: 'high',
        includeMetadata: false,
      }}
    />
  )
}
