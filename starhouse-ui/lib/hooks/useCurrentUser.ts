/**
 * useCurrentUser Hook
 * FAANG Standards:
 * - Single source of truth for user permissions
 * - Automatic permission checking
 * - Session management
 * - Type-safe role checking
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import { getCurrentStaff, updateLastLogin } from '@/lib/api/staff'
import type { StaffMember } from '@/lib/types/staff.types'

interface CurrentUser extends StaffMember {
  isAdmin: boolean
  canEdit: boolean
}

interface UseCurrentUserResult {
  user: CurrentUser | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  // Convenience permission checkers
  isAdmin: boolean
  canEdit: boolean
  isReadOnly: boolean
}

/**
 * Hook to manage current user's staff information and permissions
 * FAANG Standard: Centralized permission management
 */
export function useCurrentUser(): UseCurrentUserResult {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCurrentUser = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await getCurrentStaff()

      if (!response.success) {
        setError(response.error?.message || 'Not authorized')
        setUser(null)
        return
      }

      setUser(response.data || null)

      // Update last login timestamp (fire and forget)
      updateLastLogin().catch(err => {
        console.warn('[useCurrentUser] Failed to update last login:', err)
      })
    } catch (err) {
      console.error('[useCurrentUser] Fetch error:', err)
      setError('An unexpected error occurred')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCurrentUser()
  }, [fetchCurrentUser])

  // Convenience computed properties
  const isAdmin = user?.isAdmin ?? false
  const canEdit = user?.canEdit ?? false
  const isReadOnly = user?.role === 'read_only'

  return {
    user,
    loading,
    error,
    refetch: fetchCurrentUser,
    isAdmin,
    canEdit,
    isReadOnly
  }
}
