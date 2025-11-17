/**
 * Staff Management API
 * FAANG Standards:
 * - Type-safe operations with generated types
 * - Comprehensive error handling with specific error types
 * - Idempotent operations where applicable
 * - Detailed logging for debugging
 * - Input validation before API calls
 * - Consistent response format
 */

import { createClient } from '@/lib/supabase/client'
import type { StaffMember, StaffRole, Database } from '@/lib/types/staff.types'

// ============================================================================
// Error Types (FAANG Standard: Specific error handling)
// ============================================================================

export class StaffAPIError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'StaffAPIError'
  }
}

export class UnauthorizedError extends StaffAPIError {
  constructor(message = 'Not authorized to perform this action') {
    super(message, 'UNAUTHORIZED')
    this.name = 'UnauthorizedError'
  }
}

export class ValidationError extends StaffAPIError {
  constructor(message: string, details?: unknown) {
    super(message, 'VALIDATION_ERROR', details)
    this.name = 'ValidationError'
  }
}

// ============================================================================
// Response Types (FAANG Standard: Consistent API responses)
// ============================================================================

export interface APIResponse<T> {
  success: boolean
  data?: T
  error?: {
    message: string
    code: string
    details?: unknown
  }
}

// ============================================================================
// Staff API Methods
// ============================================================================

/**
 * Get all staff members
 * FAANG Standard: Efficient query with proper error handling
 */
export async function getStaffMembers(): Promise<APIResponse<StaffMember[]>> {
  try {
    const supabase = createClient()

    const { data, error } = await supabase
      .from('staff_members')
      .select('*')
      .order('role', { ascending: true })
      .order('email', { ascending: true })

    if (error) {
      throw new StaffAPIError('Failed to fetch staff members', 'FETCH_ERROR', error)
    }

    return {
      success: true,
      data: data as StaffMember[]
    }
  } catch (error) {
    console.error('[getStaffMembers] Error:', error)

    if (error instanceof StaffAPIError) {
      return {
        success: false,
        error: {
          message: error.message,
          code: error.code,
          details: error.details
        }
      }
    }

    return {
      success: false,
      error: {
        message: 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}

/**
 * Get current user's staff information and permissions
 * FAANG Standard: Single source of truth for user permissions
 */
export async function getCurrentStaff(): Promise<APIResponse<StaffMember & { isAdmin: boolean; canEdit: boolean }>> {
  try {
    const supabase = createClient()

    // Get current session
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()

    if (sessionError || !session?.user?.email) {
      throw new UnauthorizedError('No active session')
    }

    // Get staff member record
    const { data, error } = await supabase
      .from('staff_members')
      .select('*')
      .eq('email', session.user.email)
      .eq('active', true)
      .single()

    if (error) {
      throw new UnauthorizedError('User is not a staff member')
    }

    const staffMember = data as StaffMember

    // Call helper functions for permissions
    const [isAdminResult, canEditResult] = await Promise.all([
      supabase.rpc('is_admin'),
      supabase.rpc('can_edit')
    ])

    return {
      success: true,
      data: {
        ...staffMember,
        isAdmin: isAdminResult.data ?? false,
        canEdit: canEditResult.data ?? false
      }
    }
  } catch (error) {
    console.error('[getCurrentStaff] Error:', error)

    if (error instanceof StaffAPIError) {
      return {
        success: false,
        error: {
          message: error.message,
          code: error.code
        }
      }
    }

    return {
      success: false,
      error: {
        message: 'Failed to fetch current staff information',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}

/**
 * Add a new staff member
 * FAANG Standard: Input validation + idempotent operation
 */
export async function addStaffMember(
  email: string,
  role: StaffRole,
  displayName?: string,
  notes?: string
): Promise<APIResponse<{ email: string; role: string }>> {
  try {
    // Validation
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new ValidationError('Invalid email format')
    }

    if (!['admin', 'full_user', 'read_only'].includes(role)) {
      throw new ValidationError('Invalid role. Must be: admin, full_user, or read_only')
    }

    const supabase = createClient()

    // Call database function (handles authorization check)
    const { data, error } = await supabase.rpc('add_staff_member', {
      p_email: email.toLowerCase().trim(),
      p_role: role,
      p_display_name: displayName?.trim() || null,
      p_notes: notes?.trim() || null
    })

    if (error) {
      // Check for specific error types
      if (error.message.includes('Only admins')) {
        throw new UnauthorizedError(error.message)
      }
      if (error.message.includes('duplicate key')) {
        throw new ValidationError('Staff member already exists')
      }
      throw new StaffAPIError('Failed to add staff member', 'ADD_ERROR', error)
    }

    return {
      success: true,
      data: data as { email: string; role: string }
    }
  } catch (error) {
    console.error('[addStaffMember] Error:', error)

    if (error instanceof StaffAPIError) {
      return {
        success: false,
        error: {
          message: error.message,
          code: error.code,
          details: error.details
        }
      }
    }

    return {
      success: false,
      error: {
        message: 'Failed to add staff member',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}

/**
 * Change staff member role
 * FAANG Standard: Authorization check + audit trail
 */
export async function changeStaffRole(
  email: string,
  newRole: StaffRole
): Promise<APIResponse<{ email: string; oldRole: string; newRole: string }>> {
  try {
    // Validation
    if (!email) {
      throw new ValidationError('Email is required')
    }

    if (!['admin', 'full_user', 'read_only'].includes(newRole)) {
      throw new ValidationError('Invalid role')
    }

    const supabase = createClient()

    // Call database function
    const { data, error } = await supabase.rpc('change_staff_role', {
      p_email: email.toLowerCase().trim(),
      p_new_role: newRole
    })

    if (error) {
      if (error.message.includes('Only admins')) {
        throw new UnauthorizedError(error.message)
      }
      if (error.message.includes('Cannot demote yourself')) {
        throw new ValidationError('Cannot demote yourself from admin')
      }
      if (error.message.includes('not found')) {
        throw new ValidationError('Staff member not found')
      }
      throw new StaffAPIError('Failed to change role', 'CHANGE_ROLE_ERROR', error)
    }

    return {
      success: true,
      data: data as { email: string; oldRole: string; newRole: string }
    }
  } catch (error) {
    console.error('[changeStaffRole] Error:', error)

    if (error instanceof StaffAPIError) {
      return {
        success: false,
        error: {
          message: error.message,
          code: error.code,
          details: error.details
        }
      }
    }

    return {
      success: false,
      error: {
        message: 'Failed to change staff role',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}

/**
 * Deactivate staff member
 * FAANG Standard: Soft delete with audit trail
 */
export async function deactivateStaffMember(
  email: string
): Promise<APIResponse<{ email: string; deactivatedAt: string }>> {
  try {
    if (!email) {
      throw new ValidationError('Email is required')
    }

    const supabase = createClient()

    const { data, error } = await supabase.rpc('deactivate_staff_member', {
      p_email: email.toLowerCase().trim()
    })

    if (error) {
      if (error.message.includes('Only admins')) {
        throw new UnauthorizedError(error.message)
      }
      if (error.message.includes('not found')) {
        throw new ValidationError('Staff member not found')
      }
      throw new StaffAPIError('Failed to deactivate staff member', 'DEACTIVATE_ERROR', error)
    }

    return {
      success: true,
      data: data as { email: string; deactivatedAt: string }
    }
  } catch (error) {
    console.error('[deactivateStaffMember] Error:', error)

    if (error instanceof StaffAPIError) {
      return {
        success: false,
        error: {
          message: error.message,
          code: error.code,
          details: error.details
        }
      }
    }

    return {
      success: false,
      error: {
        message: 'Failed to deactivate staff member',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}

/**
 * Update staff member last login timestamp
 * FAANG Standard: Automatic audit trail
 */
export async function updateLastLogin(): Promise<APIResponse<void>> {
  try {
    const supabase = createClient()

    const { data: { session } } = await supabase.auth.getSession()

    if (!session?.user?.email) {
      return { success: true } // Silent fail if not logged in
    }

    const { error } = await supabase
      .from('staff_members')
      .update({ last_login_at: new Date().toISOString() })
      .eq('email', session.user.email)
      .eq('active', true)

    if (error) {
      // Log but don't throw - this is non-critical
      console.warn('[updateLastLogin] Failed to update last login:', error)
    }

    return { success: true }
  } catch (error) {
    console.error('[updateLastLogin] Error:', error)
    return { success: true } // Silent fail
  }
}
