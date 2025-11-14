/**
 * Scoring and confidence thresholds
 * FAANG Standard: Extract magic numbers to constants for maintainability
 */

/**
 * Confidence score thresholds (0-100 scale)
 */
export const CONFIDENCE_THRESHOLDS = {
  VERY_HIGH: 75,
  HIGH: 60,
  MEDIUM: 45,
  LOW: 30,
  VERY_LOW: 0,
} as const

/**
 * Email scoring weights (total = 100 points)
 */
export const EMAIL_SCORE_WEIGHTS = {
  PRIMARY: 40,           // Primary email bonus
  SUBSCRIBED: 30,        // Email subscription status
  SOURCE_PRIORITY_MAX: 20, // Source priority (inverse of priority number)
  VERIFIED: 10,          // Email verification status
} as const

/**
 * Source priority for email ranking
 * Lower number = higher priority
 */
export const EMAIL_SOURCE_PRIORITY = {
  KAJABI: 1,
  TICKET_TAILOR: 2,
  PAYPAL: 3,
  MANUAL: 4,
  ZOHO: 4,
} as const

/**
 * Confidence level display configuration
 */
export const CONFIDENCE_LEVELS = [
  {
    label: 'Very High',
    threshold: CONFIDENCE_THRESHOLDS.VERY_HIGH,
    color: 'bg-emerald-500',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/20',
    textColor: 'text-emerald-600',
    description: 'Premium quality',
  },
  {
    label: 'High',
    threshold: CONFIDENCE_THRESHOLDS.HIGH,
    color: 'bg-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20',
    textColor: 'text-blue-600',
    description: 'Good to mail',
  },
  {
    label: 'Medium',
    threshold: CONFIDENCE_THRESHOLDS.MEDIUM,
    color: 'bg-amber-500',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    textColor: 'text-amber-600',
    description: 'Verify first',
  },
  {
    label: 'Low',
    threshold: CONFIDENCE_THRESHOLDS.LOW,
    color: 'bg-orange-500',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
    textColor: 'text-orange-600',
    description: 'Needs update',
  },
  {
    label: 'Very Low',
    threshold: CONFIDENCE_THRESHOLDS.VERY_LOW,
    color: 'bg-red-500',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    textColor: 'text-red-600',
    description: 'Do not mail',
  },
] as const

/**
 * Type-safe confidence level type
 */
export type ConfidenceLevel = 'very_high' | 'high' | 'medium' | 'low' | 'very_low'

/**
 * Type-safe confidence display
 */
export interface ConfidenceDisplay {
  color: string
  label: string
  bgClass: string
}

/**
 * Get confidence display configuration based on score
 * @param score - Confidence score (0-100)
 * @returns Display configuration for the confidence level
 */
export function getConfidenceDisplay(score: number): ConfidenceDisplay {
  if (score >= CONFIDENCE_THRESHOLDS.VERY_HIGH) {
    return { color: 'text-emerald-600', label: 'Very High', bgClass: 'bg-emerald-500' }
  }
  if (score >= CONFIDENCE_THRESHOLDS.HIGH) {
    return { color: 'text-blue-600', label: 'High', bgClass: 'bg-blue-500' }
  }
  if (score >= CONFIDENCE_THRESHOLDS.MEDIUM) {
    return { color: 'text-amber-600', label: 'Medium', bgClass: 'bg-amber-500' }
  }
  if (score >= CONFIDENCE_THRESHOLDS.LOW) {
    return { color: 'text-orange-600', label: 'Low', bgClass: 'bg-orange-500' }
  }
  return { color: 'text-red-600', label: 'Very Low', bgClass: 'bg-red-500' }
}
