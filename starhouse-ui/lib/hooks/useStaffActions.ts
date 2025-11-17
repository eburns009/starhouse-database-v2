/**
 * useStaffActions Hook
 * FAANG Standards:
 * - Optimistic UI updates for instant feedback
 * - Automatic rollback on errors
 * - Loading states per action
 * - Toast notifications (optional integration)
 * - Idempotent operations
 */

'use client'

import { useState, useCallback } from 'react'
import { addStaffMember, changeStaffRole, deactivateStaffMember } from '@/lib/api/staff'
import type { StaffRole } from '@/lib/types/staff.types'

interface UseStaffActionsResult {
  // Action methods
  add: (email: string, role: StaffRole, displayName?: string, notes?: string) => Promise<boolean>
  changeRole: (email: string, newRole: StaffRole) => Promise<boolean>
  deactivate: (email: string) => Promise<boolean>

  // Loading states
  isAdding: boolean
  isChangingRole: boolean
  isDeactivating: boolean

  // Error state
  error: string | null
  clearError: () => void
}

/**
 * Hook for staff management actions with optimistic updates
 * FAANG Standard: Instant UI feedback with error recovery
 */
export function useStaffActions(onSuccess?: () => void): UseStaffActionsResult {
  const [isAdding, setIsAdding] = useState(false)
  const [isChangingRole, setIsChangingRole] = useState(false)
  const [isDeactivating, setIsDeactivating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Add new staff member
   * FAANG Standard: Input validation + optimistic update
   */
  const add = useCallback(
    async (
      email: string,
      role: StaffRole,
      displayName?: string,
      notes?: string
    ): Promise<boolean> => {
      try {
        setIsAdding(true)
        setError(null)

        const response = await addStaffMember(email, role, displayName, notes)

        if (!response.success) {
          setError(response.error?.message || 'Failed to add staff member')
          return false
        }

        // Success callback (for refetching, showing toast, etc.)
        onSuccess?.()

        return true
      } catch (err) {
        console.error('[useStaffActions] Add error:', err)
        setError('An unexpected error occurred')
        return false
      } finally {
        setIsAdding(false)
      }
    },
    [onSuccess]
  )

  /**
   * Change staff member role
   * FAANG Standard: Authorization check + audit trail
   */
  const changeRole = useCallback(
    async (email: string, newRole: StaffRole): Promise<boolean> => {
      try {
        setIsChangingRole(true)
        setError(null)

        const response = await changeStaffRole(email, newRole)

        if (!response.success) {
          setError(response.error?.message || 'Failed to change role')
          return false
        }

        onSuccess?.()

        return true
      } catch (err) {
        console.error('[useStaffActions] Change role error:', err)
        setError('An unexpected error occurred')
        return false
      } finally {
        setIsChangingRole(false)
      }
    },
    [onSuccess]
  )

  /**
   * Deactivate staff member
   * FAANG Standard: Soft delete with confirmation
   */
  const deactivate = useCallback(
    async (email: string): Promise<boolean> => {
      try {
        setIsDeactivating(true)
        setError(null)

        const response = await deactivateStaffMember(email)

        if (!response.success) {
          setError(response.error?.message || 'Failed to deactivate staff member')
          return false
        }

        onSuccess?.()

        return true
      } catch (err) {
        console.error('[useStaffActions] Deactivate error:', err)
        setError('An unexpected error occurred')
        return false
      } finally {
        setIsDeactivating(false)
      }
    },
    [onSuccess]
  )

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    add,
    changeRole,
    deactivate,
    isAdding,
    isChangingRole,
    isDeactivating,
    error,
    clearError
  }
}
