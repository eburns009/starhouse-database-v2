'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Badge } from '@/components/ui/badge'
import { Loader2, TrendingUp, MapPin, AlertTriangle, CheckCircle2 } from 'lucide-react'

interface MailingListQualityProps {
  contactId: string
}

interface MailingListInfo {
  recommended_address: 'billing' | 'shipping'
  billing_score: number
  shipping_score: number
  confidence: string
  is_manual_override: boolean
  billing_line1: string | null
  shipping_line1: string | null
  billing_complete: boolean
  shipping_complete: boolean
  // NCOA fields
  ncoa_detected?: boolean
  ncoa_move_date?: string | null
  ncoa_new_address?: string | null
  address_quality_score?: number | null
  address_validated?: boolean | null
}

// Export for use by parent components
export interface MailingRecommendation {
  recommended: 'billing' | 'shipping'
  confidence: string
  score: number
}

export function MailingListQuality({ contactId }: MailingListQualityProps) {
  const [info, setInfo] = useState<MailingListInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchMailingListInfo() {
      const supabase = createClient()

      const { data, error } = await supabase
        .from('mailing_list_priority')
        .select('*')
        .eq('id', contactId)
        .single()

      if (error) {
        console.error('Error fetching mailing list info:', error)
      } else if (data) {
        setInfo(data)
      }
      setLoading(false)
    }

    fetchMailingListInfo()
  }, [contactId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!info) {
    return (
      <div className="text-sm text-muted-foreground">
        No mailing list data available
      </div>
    )
  }

  const bestScore = Math.max(info.billing_score || 0, info.shipping_score || 0)

  const confidenceColor = {
    very_high: 'bg-green-500',
    high: 'bg-blue-500',
    medium: 'bg-yellow-500',
    low: 'bg-orange-500',
    very_low: 'bg-red-500',
  }[info.confidence] || 'bg-gray-500'

  const confidenceLabel = {
    very_high: 'Very High',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    very_low: 'Very Low',
  }[info.confidence] || info.confidence

  return (
    <div className="space-y-3">
      {/* NCOA Move Alert - CRITICAL */}
      {(info.ncoa_detected || info.ncoa_move_date) && (
        <div className="rounded-lg border-2 border-destructive/50 bg-destructive/10 p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
            <div className="flex-1 space-y-1">
              <div className="font-semibold text-sm text-destructive">
                Contact Has Moved (NCOA)
              </div>
              {info.ncoa_move_date && (
                <div className="text-xs">
                  Move Date: <span className="font-medium">{new Date(info.ncoa_move_date).toLocaleDateString()}</span>
                </div>
              )}
              {info.ncoa_new_address && (
                <div className="text-xs mt-2 pt-2 border-t border-destructive/20">
                  <div className="font-medium mb-1">New Address:</div>
                  <div className="whitespace-pre-line">{info.ncoa_new_address}</div>
                </div>
              )}
              <div className="text-xs font-medium text-destructive/80 mt-2 pt-2 border-t border-destructive/20">
                ⚠️ Update address before mailing
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Address Validation Status */}
      {info.address_validated && !info.ncoa_detected && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-2">
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span className="font-medium text-emerald-700 dark:text-emerald-300">
              USPS Validated Address
            </span>
          </div>
        </div>
      )}

      {/* Recommended Address */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          <div>
            <div className="text-sm font-medium">
              Recommended: {info.recommended_address === 'billing' ? 'Billing' : 'Shipping'}
            </div>
            <div className="text-xs text-muted-foreground">
              {info.recommended_address === 'billing' ? info.billing_line1 : info.shipping_line1}
            </div>
          </div>
        </div>
        {info.is_manual_override && (
          <Badge variant="outline" className="text-xs">
            Manual
          </Badge>
        )}
      </div>

      {/* Score & Confidence */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm font-medium">
            Score: {bestScore} / 100
          </div>
        </div>
        <Badge className={confidenceColor}>
          {confidenceLabel}
        </Badge>
      </div>

      {/* Individual Scores */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded bg-muted/30 p-2">
          <div className="font-medium">Billing</div>
          <div className="text-muted-foreground">{info.billing_score || 0} pts</div>
        </div>
        <div className="rounded bg-muted/30 p-2">
          <div className="font-medium">Shipping</div>
          <div className="text-muted-foreground">{info.shipping_score || 0} pts</div>
        </div>
      </div>

      {/* Address Quality Score */}
      {info.address_quality_score !== null && info.address_quality_score !== undefined && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Address Quality</span>
            <span className="font-semibold">{info.address_quality_score}/100</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full transition-all ${
                info.address_quality_score >= 80
                  ? 'bg-emerald-500'
                  : info.address_quality_score >= 60
                  ? 'bg-blue-500'
                  : info.address_quality_score >= 40
                  ? 'bg-amber-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${info.address_quality_score}%` }}
            />
          </div>
        </div>
      )}

      {/* Help text */}
      {info.confidence === 'medium' && !info.ncoa_detected && (
        <div className="rounded-lg bg-blue-500/10 p-2 text-xs text-blue-700 dark:text-blue-300">
          <strong>Partial USPS validation.</strong> Address likely deliverable but missing full confirmation. Run USPS validation to boost to High.
        </div>
      )}
      {info.confidence === 'low' && !info.ncoa_detected && (
        <div className="rounded-lg bg-yellow-500/10 p-2 text-xs text-yellow-700 dark:text-yellow-300">
          <strong>Not USPS validated.</strong> Run address validation to confirm deliverability before mailing.
        </div>
      )}

      {/* Address completeness warnings */}
      {!info.billing_complete && !info.shipping_complete && (
        <div className="rounded-lg bg-red-500/10 p-2 text-xs text-red-700 dark:text-red-300">
          ⚠️ Both addresses incomplete. Cannot mail to this contact.
        </div>
      )}
      {info.recommended_address === 'billing' && !info.billing_complete && info.shipping_complete && (
        <div className="rounded-lg bg-yellow-500/10 p-2 text-xs text-yellow-700 dark:text-yellow-300">
          ⚠️ Recommended billing address is incomplete. Using shipping instead.
        </div>
      )}
      {info.recommended_address === 'shipping' && !info.shipping_complete && info.billing_complete && (
        <div className="rounded-lg bg-yellow-500/10 p-2 text-xs text-yellow-700 dark:text-yellow-300">
          ⚠️ Recommended shipping address is incomplete. Using billing instead.
        </div>
      )}
    </div>
  )
}
