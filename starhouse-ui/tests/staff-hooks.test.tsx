/**
 * Staff Management Hooks Tests
 * FAANG Standards:
 * - Test React hooks with proper mocking
 * - Test real-time subscriptions
 * - Test loading and error states
 * - Test optimistic updates
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useStaffMembers } from '@/lib/hooks/useStaffMembers'
import { useCurrentStaff } from '@/lib/hooks/useCurrentStaff'

// Mock Supabase client
const mockChannel = {
  on: vi.fn().mockReturnThis(),
  subscribe: vi.fn().mockReturnThis(),
  unsubscribe: vi.fn(),
}

vi.mock('@/lib/supabase/client', () => ({
  createClient: vi.fn(() => ({
    channel: vi.fn(() => mockChannel),
    from: vi.fn(),
    auth: {
      getSession: vi.fn(),
    },
    rpc: vi.fn(),
  })),
}))

vi.mock('@/lib/api/staff', () => ({
  getStaffMembers: vi.fn(),
  getCurrentStaff: vi.fn(),
}))

describe('useStaffMembers Hook - FAANG Standards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch staff members on mount', async () => {
    const mockStaff = [
      { email: 'admin@test.com', role: 'admin', active: true },
      { email: 'user@test.com', role: 'full_user', active: true },
    ]

    const { getStaffMembers } = await import('@/lib/api/staff')
    vi.mocked(getStaffMembers).mockResolvedValue({
      success: true,
      data: mockStaff,
    })

    const { result } = renderHook(() => useStaffMembers())

    expect(result.current.loading).toBe(true)
    expect(result.current.staff).toEqual([])

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.staff).toEqual(mockStaff)
    expect(result.current.error).toBeNull()
  })

  it('should handle fetch errors', async () => {
    const { getStaffMembers } = await import('@/lib/api/staff')
    vi.mocked(getStaffMembers).mockResolvedValue({
      success: false,
      error: {
        message: 'Database error',
        code: 'FETCH_ERROR',
      },
    })

    const { result } = renderHook(() => useStaffMembers())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.staff).toEqual([])
    expect(result.current.error).toBe('Database error')
  })

  it('should set up real-time subscription', async () => {
    const { getStaffMembers } = await import('@/lib/api/staff')
    vi.mocked(getStaffMembers).mockResolvedValue({
      success: true,
      data: [],
    })

    const { createClient } = await import('@/lib/supabase/client')
    const mockSupabase = createClient()

    renderHook(() => useStaffMembers())

    await waitFor(() => {
      expect(mockSupabase.channel).toHaveBeenCalledWith('staff_members_changes')
      expect(mockChannel.on).toHaveBeenCalledWith(
        'postgres_changes',
        expect.objectContaining({
          event: '*',
          schema: 'public',
          table: 'staff_members',
        }),
        expect.any(Function)
      )
      expect(mockChannel.subscribe).toHaveBeenCalled()
    })
  })

  it('should cleanup subscription on unmount', async () => {
    const { getStaffMembers } = await import('@/lib/api/staff')
    vi.mocked(getStaffMembers).mockResolvedValue({
      success: true,
      data: [],
    })

    const { unmount } = renderHook(() => useStaffMembers())

    await waitFor(() => {
      expect(mockChannel.subscribe).toHaveBeenCalled()
    })

    unmount()

    expect(mockChannel.unsubscribe).toHaveBeenCalled()
  })

  it('should provide refetch function', async () => {
    const mockStaff = [{ email: 'admin@test.com', role: 'admin', active: true }]

    const { getStaffMembers } = await import('@/lib/api/staff')
    vi.mocked(getStaffMembers).mockResolvedValue({
      success: true,
      data: mockStaff,
    })

    const { result } = renderHook(() => useStaffMembers())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Clear mock to verify refetch call
    vi.clearAllMocks()

    await result.current.refetch()

    expect(getStaffMembers).toHaveBeenCalled()
  })
})

describe('useCurrentStaff Hook - FAANG Standards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch current staff with permissions', async () => {
    const mockCurrentStaff = {
      email: 'admin@test.com',
      role: 'admin' as const,
      active: true,
      isAdmin: true,
      canEdit: true,
    }

    const { getCurrentStaff } = await import('@/lib/api/staff')
    vi.mocked(getCurrentStaff).mockResolvedValue({
      success: true,
      data: mockCurrentStaff,
    })

    const { result } = renderHook(() => useCurrentStaff())

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.staff).toEqual(mockCurrentStaff)
    expect(result.current.isAdmin).toBe(true)
    expect(result.current.canEdit).toBe(true)
  })

  it('should handle unauthenticated users', async () => {
    const { getCurrentStaff } = await import('@/lib/api/staff')
    vi.mocked(getCurrentStaff).mockResolvedValue({
      success: false,
      error: {
        message: 'No active session',
        code: 'UNAUTHORIZED',
      },
    })

    const { result } = renderHook(() => useCurrentStaff())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.staff).toBeNull()
    expect(result.current.isAdmin).toBe(false)
    expect(result.current.canEdit).toBe(false)
    expect(result.current.error).toBe('No active session')
  })

  it('should correctly identify read-only users', async () => {
    const mockCurrentStaff = {
      email: 'readonly@test.com',
      role: 'read_only' as const,
      active: true,
      isAdmin: false,
      canEdit: false,
    }

    const { getCurrentStaff } = await import('@/lib/api/staff')
    vi.mocked(getCurrentStaff).mockResolvedValue({
      success: true,
      data: mockCurrentStaff,
    })

    const { result } = renderHook(() => useCurrentStaff())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.isAdmin).toBe(false)
    expect(result.current.canEdit).toBe(false)
  })

  it('should correctly identify full users', async () => {
    const mockCurrentStaff = {
      email: 'fulluser@test.com',
      role: 'full_user' as const,
      active: true,
      isAdmin: false,
      canEdit: true,
    }

    const { getCurrentStaff } = await import('@/lib/api/staff')
    vi.mocked(getCurrentStaff).mockResolvedValue({
      success: true,
      data: mockCurrentStaff,
    })

    const { result } = renderHook(() => useCurrentStaff())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.isAdmin).toBe(false)
    expect(result.current.canEdit).toBe(true)
  })
})
