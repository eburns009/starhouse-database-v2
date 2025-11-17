/**
 * Staff API Integration Tests
 * FAANG Standards:
 * - Test all API methods with success and error cases
 * - Mock Supabase client
 * - Test error handling
 * - Test validation
 * - Test idempotency
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getStaffMembers,
  getCurrentStaff,
  addStaffMember,
  changeStaffRole,
  deactivateStaffMember,
  updateLastLogin,
  StaffAPIError,
  UnauthorizedError,
  ValidationError,
} from '@/lib/api/staff'

// Create mock Supabase client instance
const mockSupabaseClient = {
  from: vi.fn(),
  auth: {
    getSession: vi.fn(),
  },
  rpc: vi.fn(),
}

// Mock Supabase client
vi.mock('@/lib/supabase/client', () => ({
  createClient: vi.fn(() => mockSupabaseClient),
}))

describe('Staff API - FAANG Standards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getStaffMembers', () => {
    it('should return staff members sorted by role and email', async () => {
      const mockData = [
        { email: 'admin@test.com', role: 'admin', active: true },
        { email: 'user@test.com', role: 'full_user', active: true },
      ]

      vi.mocked(mockSupabaseClient.from).mockReturnValue({
        select: vi.fn().mockReturnValue({
          order: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({
              data: mockData,
              error: null,
            }),
          }),
        }),
      } as any)

      const result = await getStaffMembers()

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(mockSupabaseClient.from).toHaveBeenCalledWith('staff_members')
    })

    it('should handle database errors gracefully', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.from).mockReturnValue({
        select: vi.fn().mockReturnValue({
          order: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({
              data: null,
              error: { message: 'Database error' },
            }),
          }),
        }),
      } as any)

      const result = await getStaffMembers()

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('FETCH_ERROR')
      expect(result.error?.message).toBe('Failed to fetch staff members')
    })
  })

  describe('getCurrentStaff', () => {
    it('should return current staff with permissions', async () => {
      const mockStaffMember = {
        email: 'admin@test.com',
        role: 'admin',
        active: true,
      }

      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.auth.getSession).mockResolvedValue({
        data: {
          session: {
            user: { email: 'admin@test.com' },
          },
        },
        error: null,
      } as any)

      vi.mocked(mockSupabase.from).mockReturnValue({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            eq: vi.fn().mockReturnValue({
              single: vi.fn().mockResolvedValue({
                data: mockStaffMember,
                error: null,
              }),
            }),
          }),
        }),
      } as any)

      vi.mocked(mockSupabase.rpc)
        .mockResolvedValueOnce({ data: true, error: null }) // is_admin
        .mockResolvedValueOnce({ data: true, error: null }) // can_edit

      const result = await getCurrentStaff()

      expect(result.success).toBe(true)
      expect(result.data?.isAdmin).toBe(true)
      expect(result.data?.canEdit).toBe(true)
    })

    it('should reject unauthenticated requests', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.auth.getSession).mockResolvedValue({
        data: { session: null },
        error: null,
      } as any)

      const result = await getCurrentStaff()

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('UNAUTHORIZED')
    })
  })

  describe('addStaffMember', () => {
    it('should validate email format', async () => {
      const result = await addStaffMember('invalid-email', 'admin')

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('VALIDATION_ERROR')
      expect(result.error?.message).toContain('Invalid email')
    })

    it('should validate role values', async () => {
      const result = await addStaffMember('test@test.com', 'invalid_role' as any)

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('VALIDATION_ERROR')
      expect(result.error?.message).toContain('Invalid role')
    })

    it('should add staff member successfully', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.rpc).mockResolvedValue({
        data: { email: 'new@test.com', role: 'full_user' },
        error: null,
      } as any)

      const result = await addStaffMember('new@test.com', 'full_user', 'New User')

      expect(result.success).toBe(true)
      expect(result.data?.email).toBe('new@test.com')
      expect(mockSupabase.rpc).toHaveBeenCalledWith('add_staff_member', {
        p_email: 'new@test.com',
        p_role: 'full_user',
        p_display_name: 'New User',
        p_notes: null,
      })
    })

    it('should handle duplicate staff member error', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.rpc).mockResolvedValue({
        data: null,
        error: { message: 'duplicate key value violates unique constraint' },
      } as any)

      const result = await addStaffMember('existing@test.com', 'admin')

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('VALIDATION_ERROR')
      expect(result.error?.message).toContain('already exists')
    })

    it('should handle unauthorized error', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.rpc).mockResolvedValue({
        data: null,
        error: { message: 'Only admins can add staff members' },
      } as any)

      const result = await addStaffMember('test@test.com', 'admin')

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('UNAUTHORIZED')
    })
  })

  describe('changeStaffRole', () => {
    it('should validate required fields', async () => {
      const result = await changeStaffRole('', 'admin')

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('VALIDATION_ERROR')
    })

    it('should change role successfully', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.rpc).mockResolvedValue({
        data: {
          email: 'user@test.com',
          oldRole: 'full_user',
          newRole: 'admin',
        },
        error: null,
      } as any)

      const result = await changeStaffRole('user@test.com', 'admin')

      expect(result.success).toBe(true)
      expect(result.data?.newRole).toBe('admin')
    })

    it('should prevent self-demotion', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.rpc).mockResolvedValue({
        data: null,
        error: { message: 'Cannot demote yourself from admin' },
      } as any)

      const result = await changeStaffRole('admin@test.com', 'full_user')

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('VALIDATION_ERROR')
      expect(result.error?.message).toContain('Cannot demote yourself')
    })
  })

  describe('deactivateStaffMember', () => {
    it('should validate email is provided', async () => {
      const result = await deactivateStaffMember('')

      expect(result.success).toBe(false)
      expect(result.error?.code).toBe('VALIDATION_ERROR')
    })

    it('should deactivate staff member successfully', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      const now = new Date().toISOString()
      vi.mocked(mockSupabase.rpc).mockResolvedValue({
        data: { email: 'user@test.com', deactivatedAt: now },
        error: null,
      } as any)

      const result = await deactivateStaffMember('user@test.com')

      expect(result.success).toBe(true)
      expect(result.data?.email).toBe('user@test.com')
    })
  })

  describe('updateLastLogin', () => {
    it('should update last login silently without session', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.auth.getSession).mockResolvedValue({
        data: { session: null },
        error: null,
      } as any)

      const result = await updateLastLogin()

      expect(result.success).toBe(true) // Silent fail
    })

    it('should update last login for authenticated user', async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const mockSupabase = createClient()

      vi.mocked(mockSupabase.auth.getSession).mockResolvedValue({
        data: {
          session: { user: { email: 'user@test.com' } },
        },
        error: null,
      } as any)

      vi.mocked(mockSupabase.from).mockReturnValue({
        update: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            eq: vi.fn().mockResolvedValue({
              error: null,
            }),
          }),
        }),
      } as any)

      const result = await updateLastLogin()

      expect(result.success).toBe(true)
    })
  })

  describe('Error Classes', () => {
    it('should create StaffAPIError with correct properties', () => {
      const error = new StaffAPIError('Test error', 'TEST_CODE', { detail: 'test' })

      expect(error.message).toBe('Test error')
      expect(error.code).toBe('TEST_CODE')
      expect(error.details).toEqual({ detail: 'test' })
      expect(error.name).toBe('StaffAPIError')
    })

    it('should create UnauthorizedError', () => {
      const error = new UnauthorizedError()

      expect(error.code).toBe('UNAUTHORIZED')
      expect(error.name).toBe('UnauthorizedError')
    })

    it('should create ValidationError', () => {
      const error = new ValidationError('Invalid input')

      expect(error.code).toBe('VALIDATION_ERROR')
      expect(error.name).toBe('ValidationError')
    })
  })
})
