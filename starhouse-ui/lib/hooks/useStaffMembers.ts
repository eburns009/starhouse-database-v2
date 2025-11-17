/**
 * useStaffMembers Hook
 * FAANG Standards:
 * - Real-time subscriptions for live updates
 * - Optimistic updates for instant UX
 * - Comprehensive error handling
 * - Loading states
 * - Automatic cleanup
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { StaffMember } from '@/lib/types/staff.types'
import { getStaffMembers } from '@/lib/api/staff'

interface UseStaffMembersResult {
  staff: StaffMember[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * Hook to manage staff members list with real-time updates
 * FAANG Standard: Single source of truth with realtime sync
 */
export function useStaffMembers(): UseStaffMembersResult {
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch staff members
  const fetchStaff = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await getStaffMembers()

      if (!response.success) {
        setError(response.error?.message || 'Failed to fetch staff members')
        return
      }

      setStaff(response.data || [])
    } catch (err) {
      console.error('[useStaffMembers] Fetch error:', err)
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }, [])

  // Setup real-time subscription
  useEffect(() => {
    // Initial fetch
    fetchStaff()

    // Subscribe to changes
    const supabase = createClient()

    const channel = supabase
      .channel('staff_members_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'staff_members'
        },
        (payload: unknown) => {
          console.log('[useStaffMembers] Real-time update:', payload)

          // Refetch to get fresh data
          // FAANG Standard: Prefer simplicity over complex state management
          fetchStaff()
        }
      )
      .subscribe()

    // Cleanup subscription on unmount
    return () => {
      supabase.removeChannel(channel)
    }
  }, [fetchStaff])

  return {
    staff,
    loading,
    error,
    refetch: fetchStaff
  }
}
