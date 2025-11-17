/**
 * Staff Management Validation Schemas
 * FAANG Standards:
 * - Zod for runtime type checking
 * - Client-side validation before API calls
 * - Consistent error messages
 * - Reusable validation rules
 */

import { z } from 'zod'

// ============================================================================
// Base Schemas
// ============================================================================

export const emailSchema = z
  .string()
  .min(1, 'Email is required')
  .email('Invalid email format')
  .toLowerCase()
  .trim()

export const staffRoleSchema = z.enum(['admin', 'full_user', 'read_only'], {
  errorMap: () => ({ message: 'Role must be: admin, full_user, or read_only' })
})

export const displayNameSchema = z
  .string()
  .min(1, 'Display name must not be empty')
  .max(100, 'Display name must be less than 100 characters')
  .trim()
  .optional()

export const notesSchema = z
  .string()
  .max(500, 'Notes must be less than 500 characters')
  .trim()
  .optional()

// ============================================================================
// Form Schemas
// ============================================================================

/**
 * Schema for adding a new staff member
 * FAANG Standard: Complete validation before API call
 */
export const addStaffMemberSchema = z.object({
  email: emailSchema,
  role: staffRoleSchema,
  displayName: displayNameSchema,
  notes: notesSchema
})

export type AddStaffMemberInput = z.infer<typeof addStaffMemberSchema>

/**
 * Schema for changing staff role
 * FAANG Standard: Prevent invalid role transitions
 */
export const changeStaffRoleSchema = z.object({
  email: emailSchema,
  newRole: staffRoleSchema
})

export type ChangeStaffRoleInput = z.infer<typeof changeStaffRoleSchema>

/**
 * Schema for deactivating staff member
 */
export const deactivateStaffMemberSchema = z.object({
  email: emailSchema
})

export type DeactivateStaffMemberInput = z.infer<typeof deactivateStaffMemberSchema>

// ============================================================================
// Validation Helper Functions
// ============================================================================

/**
 * Validate email format
 * FAANG Standard: Early validation to prevent API errors
 */
export function validateEmail(email: string): { valid: boolean; error?: string } {
  const result = emailSchema.safeParse(email)
  return {
    valid: result.success,
    error: result.success ? undefined : result.error.errors[0].message
  }
}

/**
 * Validate staff role
 */
export function validateRole(role: string): { valid: boolean; error?: string } {
  const result = staffRoleSchema.safeParse(role)
  return {
    valid: result.success,
    error: result.success ? undefined : result.error.errors[0].message
  }
}

/**
 * Validate add staff member form
 * FAANG Standard: Return all validation errors at once
 */
export function validateAddStaffMember(input: unknown): {
  valid: boolean
  errors?: Record<string, string>
  data?: AddStaffMemberInput
} {
  const result = addStaffMemberSchema.safeParse(input)

  if (result.success) {
    return {
      valid: true,
      data: result.data
    }
  }

  // Convert Zod errors to field-level errors
  const errors: Record<string, string> = {}
  result.error.errors.forEach(err => {
    const field = err.path.join('.')
    errors[field] = err.message
  })

  return {
    valid: false,
    errors
  }
}

/**
 * Validate change role form
 */
export function validateChangeRole(input: unknown): {
  valid: boolean
  errors?: Record<string, string>
  data?: ChangeStaffRoleInput
} {
  const result = changeStaffRoleSchema.safeParse(input)

  if (result.success) {
    return {
      valid: true,
      data: result.data
    }
  }

  const errors: Record<string, string> = {}
  result.error.errors.forEach(err => {
    const field = err.path.join('.')
    errors[field] = err.message
  })

  return {
    valid: false,
    errors
  }
}

// ============================================================================
// Business Logic Validation
// ============================================================================

/**
 * Check if role transition is allowed
 * FAANG Standard: Business rules enforced at multiple layers
 */
export function isRoleTransitionAllowed(
  currentRole: string,
  newRole: string,
  isSelf: boolean
): { allowed: boolean; reason?: string } {
  // Cannot demote yourself from admin
  if (isSelf && currentRole === 'admin' && newRole !== 'admin') {
    return {
      allowed: false,
      reason: 'Cannot demote yourself from admin role'
    }
  }

  // Must be valid role
  if (!['admin', 'full_user', 'read_only'].includes(newRole)) {
    return {
      allowed: false,
      reason: 'Invalid role'
    }
  }

  return { allowed: true }
}

/**
 * Check if email domain is allowed (optional - configure as needed)
 * FAANG Standard: Domain whitelist for security
 */
export function isEmailDomainAllowed(email: string, allowedDomains?: string[]): boolean {
  if (!allowedDomains || allowedDomains.length === 0) {
    return true // No restrictions
  }

  const domain = email.split('@')[1]?.toLowerCase()
  return allowedDomains.some(allowed => domain === allowed.toLowerCase())
}
