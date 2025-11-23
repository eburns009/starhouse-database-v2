import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind classes without conflicts
 * FAANG Standard: Type-safe className utility
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format currency
 */
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount)
}

/**
 * Format date
 */
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(date))
}

/**
 * Format full name
 */
export function formatName(firstName: string | null, lastName: string | null): string {
  if (!firstName && !lastName) return 'Unknown'
  return [firstName, lastName].filter(Boolean).join(' ')
}

/**
 * Get initials from name
 */
export function getInitials(firstName: string | null, lastName: string | null): string {
  if (!firstName && !lastName) return '?'
  const first = firstName?.[0] || ''
  const last = lastName?.[0] || ''
  return (first + last).toUpperCase() || '?'
}

/**
 * Truncate text
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

/**
 * Sleep utility for demos/testing
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Format donation category to show only subcategory
 * Removes parent category prefix (e.g., "DEVELOPMENT:", "STARHOUSE REVENUE:")
 *
 * Examples:
 * - "DEVELOPMENT:General Donations" → "General Donations"
 * - "DEVELOPMENT:Fundraising" → "Fundraising"
 * - "STARHOUSE REVENUE:ASC Offerings" → "ASC Offerings"
 */
export function formatDonationCategory(fullCategory: string | null): string {
  if (!fullCategory) return 'Uncategorized'

  // Split on colon and take last part
  const parts = fullCategory.split(':')
  const subcategory = parts[parts.length - 1].trim()

  return subcategory || fullCategory
}
