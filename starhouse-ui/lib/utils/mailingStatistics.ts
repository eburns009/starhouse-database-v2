/**
 * Mailing statistics calculation utilities
 * FAANG Standard: Pure functions, single responsibility, optimized performance
 */

import type { MailingListEntry, MailingStatistics } from '../types/mailing'
import type { ConfidenceLevel } from '../constants/scoring'

/**
 * Calculate mailing list statistics from raw data
 * Optimized: Single reduce operation instead of multiple array iterations
 * Complexity: O(n) instead of O(7n)
 *
 * @param stats - Raw mailing list entries from database
 * @returns Aggregated statistics
 */
export function calculateMailingStatistics(stats: MailingListEntry[]): MailingStatistics {
  const initialCounts: Record<ConfidenceLevel, number> = {
    very_high: 0,
    high: 0,
    medium: 0,
    low: 0,
    very_low: 0,
  }

  const aggregated = stats.reduce(
    (acc, stat) => {
      // Count confidence levels
      acc.confidenceCounts[stat.confidence]++

      // Count recommendations
      if (stat.recommended_address === 'billing') {
        acc.recommendBilling++
      } else if (stat.recommended_address === 'shipping') {
        acc.recommendShipping++
      }

      // Sum scores for average calculation
      const maxScore = Math.max(stat.billing_score || 0, stat.shipping_score || 0)
      acc.scoreSum += maxScore

      return acc
    },
    {
      confidenceCounts: { ...initialCounts },
      recommendBilling: 0,
      recommendShipping: 0,
      scoreSum: 0,
    }
  )

  const total = stats.length
  const readyToMail = aggregated.confidenceCounts.very_high + aggregated.confidenceCounts.high
  const avgScore = Math.round(aggregated.scoreSum / total)
  const readyPercentage = Math.round((readyToMail / total) * 100)

  return {
    total,
    ...aggregated,
    avgScore,
    readyToMail,
    readyPercentage,
  }
}

/**
 * Calculate percentage safely (handles division by zero)
 *
 * @param value - Numerator
 * @param total - Denominator
 * @returns Percentage rounded to nearest integer (0 if total is 0)
 */
export function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}
