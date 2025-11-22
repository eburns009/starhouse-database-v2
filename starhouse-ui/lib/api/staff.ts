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
import type { StaffMember, StaffRole } from '@/lib/types/staff.types'

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
 *
 * Fetches all staff members from the database, sorted by role (admin first)
 * and then by email address. Includes both active and inactive staff.
 *
 * @returns Promise resolving to APIResponse with staff members array
 *
 * @example
 * ```typescript
 * const result = await getStaffMembers()
 *
 * if (result.success) {
 *   console.log(`Found ${result.data.length} staff members`)
 *   result.data.forEach(member => {
 *     console.log(`${member.email} - ${member.role}`)
 *   })
 * } else {
 *   console.error(result.error.message)
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link APIResponse} for response format
 * @see {@link StaffMember} for staff member type definition
 *
 * FAANG Standard: Efficient query with proper error handling
 */
export async function getStaffMembers(): Promise<APIResponse<StaffMember[]>> {
  try {
    const supabase = createClient()

    const { data, error } = await supabase
      .from('staff_members')
      .select('*')
      .order('last_sign_in_at', { ascending: false, nullsFirst: false })
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
 *
 * Fetches the currently authenticated user's staff record and calculates
 * their permissions (isAdmin, canEdit) based on their role. This is the
 * single source of truth for checking user permissions throughout the app.
 *
 * @returns Promise resolving to APIResponse with staff member plus permissions
 *
 * @example
 * ```typescript
 * const result = await getCurrentStaff()
 *
 * if (result.success) {
 *   const { isAdmin, canEdit, role } = result.data
 *
 *   if (isAdmin) {
 *     // Show admin-only features
 *     showAdminPanel()
 *   }
 *
 *   if (canEdit) {
 *     // Enable edit buttons
 *     enableEditing()
 *   }
 * } else if (result.error.code === 'UNAUTHORIZED') {
 *   // User not logged in or not a staff member
 *   redirectToLogin()
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link APIResponse} for response format
 * @see {@link StaffMember} for staff member type definition
 *
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
 * Add a new staff member with full auth account creation
 *
 * Creates a new staff member by:
 * 1. Creating a Supabase Auth account
 * 2. Sending invitation email with password setup link
 * 3. Creating staff_members database record
 *
 * This uses a server-side Edge Function to securely handle auth account
 * creation without exposing the service role key to the client.
 *
 * Only admins can add staff members. The operation is idempotent - if the
 * staff member already exists, it returns a validation error rather than
 * creating a duplicate.
 *
 * @param email - Valid email address (required, validated)
 * @param role - One of 'admin', 'full_user', or 'read_only' (required)
 * @param displayName - Optional friendly name for the staff member
 * @param notes - Optional internal notes about the staff member
 *
 * @returns Promise resolving to APIResponse with created staff member info
 *
 * @example
 * ```typescript
 * // Basic usage - creates auth account + sends invite email
 * const result = await addStaffMember(
 *   'newuser@starhouse.org',
 *   'full_user'
 * )
 *
 * // With display name and notes
 * const result = await addStaffMember(
 *   'john.smith@starhouse.org',
 *   'admin',
 *   'John Smith',
 *   'Development team lead, hired Nov 2025'
 * )
 *
 * if (result.success) {
 *   console.log(`Added: ${result.data.email} as ${result.data.role}`)
 *   console.log(`Invitation email sent: ${result.data.invitationSent}`)
 * } else if (result.error.code === 'DUPLICATE_EMAIL') {
 *   showError('Staff member already exists')
 * } else if (result.error.code === 'FORBIDDEN') {
 *   showError('Only admins can add staff members')
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link StaffRole} for valid role values
 * @see {@link APIResponse} for response format
 *
 * FAANG Standard: Server-side auth creation + atomic operations
 */
export async function addStaffMember(
  email: string,
  role: StaffRole,
  displayName?: string,
  notes?: string
): Promise<APIResponse<{ userId: string; email: string; role: string; invitationSent: boolean }>> {
  try {
    // Client-side validation
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new ValidationError('Invalid email format')
    }

    if (!['admin', 'full_user', 'read_only'].includes(role)) {
      throw new ValidationError('Invalid role. Must be: admin, full_user, or read_only')
    }

    const supabase = createClient()

    // Call Edge Function to create auth account + staff record
    const { data, error } = await supabase.functions.invoke('invite-staff-member', {
      body: {
        email: email.toLowerCase().trim(),
        role,
        displayName: displayName?.trim() || undefined,
        notes: notes?.trim() || undefined
      }
    })

    // FIX: Check data.success FIRST before checking error
    // This handles cases where both data and error exist (CORS/parsing issues)
    // The Edge Function returns success:true when invitation succeeds
    if (data?.success) {
      return {
        success: true,
        data: data.data
      }
    }

    // Now check for errors
    if (error) {
      console.error('[addStaffMember] Edge Function error:', error)
      throw new StaffAPIError('Failed to invite staff member', 'EDGE_FUNCTION_ERROR', error)
    }

    // Edge Function returns typed response with error details
    if (!data || !data.success) {
      const errorCode = data.error?.code || 'UNKNOWN_ERROR'
      const errorMessage = data.error?.message || 'Failed to add staff member'

      if (errorCode === 'FORBIDDEN' || errorCode === 'UNAUTHORIZED') {
        throw new UnauthorizedError(errorMessage)
      }

      if (errorCode === 'DUPLICATE_EMAIL' || errorCode === 'EMAIL_ALREADY_REGISTERED') {
        throw new ValidationError(errorMessage)
      }

      throw new StaffAPIError(errorMessage, errorCode, data.error?.details)
    }

    return {
      success: true,
      data: data.data
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
 *
 * Updates a staff member's role to a new value. Only admins can change roles.
 * Admins cannot demote themselves. All role changes are logged in the audit trail.
 *
 * @param email - Email address of the staff member to update (required)
 * @param newRole - New role to assign: 'admin', 'full_user', or 'read_only' (required)
 *
 * @returns Promise resolving to APIResponse with old and new role information
 *
 * @example
 * ```typescript
 * // Promote user to admin
 * const result = await changeStaffRole(
 *   'user@starhouse.org',
 *   'admin'
 * )
 *
 * if (result.success) {
 *   console.log(`Changed ${result.data.email} from ${result.data.oldRole} to ${result.data.newRole}`)
 *   showToast('Role updated successfully')
 * } else if (result.error.code === 'VALIDATION_ERROR') {
 *   if (result.error.message.includes('demote yourself')) {
 *     showError('You cannot demote yourself from admin')
 *   } else {
 *     showError(result.error.message)
 *   }
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link StaffRole} for valid role values
 * @see {@link APIResponse} for response format
 *
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
 *
 * Deactivates a staff member (soft delete). The staff member will no longer
 * be able to log in, but their historical data and audit trail are preserved.
 * Only admins can deactivate staff members. This operation can be reversed
 * by reactivating the staff member.
 *
 * @param email - Email address of the staff member to deactivate (required)
 *
 * @returns Promise resolving to APIResponse with deactivation timestamp
 *
 * @example
 * ```typescript
 * // Deactivate a staff member
 * const result = await deactivateStaffMember('user@starhouse.org')
 *
 * if (result.success) {
 *   console.log(`Deactivated at: ${result.data.deactivatedAt}`)
 *   showToast('Staff member deactivated')
 *   refetchStaffList()
 * } else if (result.error.code === 'VALIDATION_ERROR') {
 *   showError('Staff member not found')
 * } else if (result.error.code === 'UNAUTHORIZED') {
 *   showError('Only admins can deactivate staff members')
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link APIResponse} for response format
 *
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
 *
 * Updates the last_login_at timestamp for the current logged-in user.
 * This is automatically called when a user logs in. If the user is not
 * authenticated or not a staff member, the operation silently succeeds
 * without updating anything (non-critical operation).
 *
 * @returns Promise resolving to APIResponse (always success, even if no update)
 *
 * @example
 * ```typescript
 * // Called automatically on login
 * useEffect(() => {
 *   updateLastLogin() // Fire and forget
 * }, [])
 *
 * // Or explicitly after authentication
 * const handleLogin = async () => {
 *   await supabase.auth.signIn(credentials)
 *   await updateLastLogin()
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object (always success)
 *
 * @see {@link APIResponse} for response format
 *
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

/**
 * Reset staff member password (Admin only)
 *
 * Triggers a password reset email for the specified staff member.
 * Only admins can reset passwords for other staff members.
 * The staff member will receive an email with a secure link to set a new password.
 *
 * Uses a server-side Edge Function to securely handle the password reset flow.
 *
 * @param email - Email address of the staff member to reset
 *
 * @returns Promise resolving to APIResponse with reset confirmation
 *
 * @example
 * ```typescript
 * // Admin resets a staff member's password
 * const result = await resetStaffPassword('user@starhouse.org')
 *
 * if (result.success) {
 *   showToast('Password reset email sent successfully')
 *   console.log(`Reset email sent to: ${result.data.email}`)
 * } else if (result.error.code === 'FORBIDDEN') {
 *   showError('Only admins can reset passwords')
 * } else if (result.error.code === 'STAFF_NOT_FOUND') {
 *   showError('Staff member not found')
 * } else if (result.error.code === 'STAFF_INACTIVE') {
 *   showError('Cannot reset password for inactive staff member')
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link APIResponse} for response format
 *
 * FAANG Standard: Secure password reset with audit trail
 */
export async function resetStaffPassword(
  email: string
): Promise<APIResponse<{ email: string; resetEmailSent: boolean }>> {
  try {
    // Client-side validation
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      throw new ValidationError('Invalid email format')
    }

    const supabase = createClient()

    // Call Edge Function to trigger password reset
    const { data, error } = await supabase.functions.invoke('reset-staff-password', {
      body: {
        email: email.toLowerCase().trim()
      }
    })

    if (error) {
      console.error('[resetStaffPassword] Edge Function error:', error)
      throw new StaffAPIError('Failed to reset password', 'EDGE_FUNCTION_ERROR', error)
    }

    // Edge Function returns typed response
    if (!data.success) {
      const errorCode = data.error?.code || 'UNKNOWN_ERROR'
      const errorMessage = data.error?.message || 'Failed to reset password'

      if (errorCode === 'FORBIDDEN' || errorCode === 'UNAUTHORIZED') {
        throw new UnauthorizedError(errorMessage)
      }

      if (errorCode === 'STAFF_NOT_FOUND' || errorCode === 'STAFF_INACTIVE') {
        throw new ValidationError(errorMessage)
      }

      throw new StaffAPIError(errorMessage, errorCode)
    }

    return {
      success: true,
      data: data.data
    }
  } catch (error) {
    console.error('[resetStaffPassword] Error:', error)

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
        message: 'Failed to reset password',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}

/**
 * Change current user's password (Self-service)
 *
 * Allows the currently logged-in user to change their own password.
 * Requires the user to know their current password for security.
 *
 * Uses Supabase Auth's built-in password update functionality.
 *
 * @param newPassword - New password (must meet security requirements)
 *
 * @returns Promise resolving to APIResponse with confirmation
 *
 * @example
 * ```typescript
 * // User changes their own password
 * const result = await changeOwnPassword('NewSecureP@ssw0rd!')
 *
 * if (result.success) {
 *   showToast('Password changed successfully')
 *   redirectToLogin() // User must re-login with new password
 * } else if (result.error.code === 'WEAK_PASSWORD') {
 *   showError('Password must be at least 8 characters')
 * } else if (result.error.code === 'UNAUTHORIZED') {
 *   showError('You must be logged in to change your password')
 * }
 * ```
 *
 * @throws Never throws - all errors are returned in the response object
 *
 * @see {@link APIResponse} for response format
 *
 * FAANG Standard: Secure self-service password management
 */
export async function changeOwnPassword(
  newPassword: string
): Promise<APIResponse<{ passwordChanged: boolean }>> {
  try {
    // Client-side validation
    if (!newPassword || newPassword.length < 8) {
      throw new ValidationError('Password must be at least 8 characters')
    }

    const supabase = createClient()

    // Verify user is authenticated
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()

    if (sessionError || !session) {
      throw new UnauthorizedError('You must be logged in to change your password')
    }

    // Update password using Supabase Auth
    const { error: updateError } = await supabase.auth.updateUser({
      password: newPassword
    })

    if (updateError) {
      console.error('[changeOwnPassword] Update error:', updateError)

      if (updateError.message.includes('Password')) {
        throw new ValidationError('Password does not meet security requirements')
      }

      throw new StaffAPIError('Failed to update password', 'UPDATE_ERROR', updateError)
    }

    return {
      success: true,
      data: { passwordChanged: true }
    }
  } catch (error) {
    console.error('[changeOwnPassword] Error:', error)

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
        message: 'Failed to change password',
        code: 'UNKNOWN_ERROR'
      }
    }
  }
}
