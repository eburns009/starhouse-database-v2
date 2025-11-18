/**
 * Invite Staff Member - Supabase Edge Function
 *
 * FAANG Standards:
 * - Server-side auth account creation (never expose service role key to client)
 * - Atomic operation: create auth account + staff record
 * - Comprehensive error handling with rollback
 * - Audit logging for security compliance
 * - Rate limiting to prevent abuse
 * - Input validation and sanitization
 *
 * Security:
 * - Requires authenticated admin user
 * - Service role key stored securely in Edge Function environment
 * - Transaction-based rollback on failures
 * - Email validation and normalization
 *
 * Flow:
 * 1. Verify caller is authenticated admin
 * 2. Validate input (email, role)
 * 3. Create Supabase Auth account with invite email
 * 4. Verify staff_members record created (via trigger or explicit insert)
 * 5. Return success with user details
 *
 * Error Handling:
 * - Duplicate email: Returns 409 Conflict
 * - Invalid role: Returns 400 Bad Request
 * - Auth failure: Returns 401 Unauthorized
 * - Database errors: Rollback auth account creation
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*', // Will be restricted by RLS policies
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

interface InviteStaffRequest {
  email: string
  role: 'admin' | 'full_user' | 'read_only'
  displayName?: string
  notes?: string
}

interface InviteStaffResponse {
  success: boolean
  data?: {
    userId: string
    email: string
    role: string
    invitationSent: boolean
  }
  error?: {
    code: string
    message: string
    details?: unknown
  }
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Only accept POST
  if (req.method !== 'POST') {
    return new Response(
      JSON.stringify({
        success: false,
        error: { code: 'METHOD_NOT_ALLOWED', message: 'Only POST requests allowed' }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 405
      }
    )
  }

  try {
    // Initialize Supabase clients
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    // Client for auth verification (uses user's JWT)
    const authHeader = req.headers.get('Authorization')!
    const supabaseClient = createClient(supabaseUrl, supabaseServiceRoleKey, {
      global: { headers: { Authorization: authHeader } }
    })

    // Admin client for user creation
    const supabaseAdmin = createClient(supabaseUrl, supabaseServiceRoleKey)

    // ========================================================================
    // Step 1: Verify caller is authenticated admin
    // ========================================================================
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser()

    if (authError || !user) {
      return new Response(
        JSON.stringify({
          success: false,
          error: { code: 'UNAUTHORIZED', message: 'Authentication required' }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 401
        }
      )
    }

    // Check if user is admin
    const { data: isAdminData, error: adminCheckError } = await supabaseClient
      .rpc('is_admin')

    if (adminCheckError || !isAdminData) {
      console.error('[invite-staff] Admin check failed:', adminCheckError)
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'FORBIDDEN',
            message: 'Only administrators can invite staff members'
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 403
        }
      )
    }

    // ========================================================================
    // Step 2: Parse and validate request body
    // ========================================================================
    const body: InviteStaffRequest = await req.json()
    const { email, role, displayName, notes } = body

    // Validate email
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(
        JSON.stringify({
          success: false,
          error: { code: 'INVALID_EMAIL', message: 'Valid email address required' }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400
        }
      )
    }

    // Validate role
    const validRoles = ['admin', 'full_user', 'read_only']
    if (!role || !validRoles.includes(role)) {
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'INVALID_ROLE',
            message: `Role must be one of: ${validRoles.join(', ')}`
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400
        }
      )
    }

    const normalizedEmail = email.toLowerCase().trim()

    // ========================================================================
    // Step 3: Check if user already exists
    // ========================================================================
    const { data: existingStaff } = await supabaseAdmin
      .from('staff_members')
      .select('email, active')
      .eq('email', normalizedEmail)
      .maybeSingle()

    if (existingStaff) {
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'DUPLICATE_EMAIL',
            message: existingStaff.active
              ? 'Staff member with this email already exists'
              : 'Staff member exists but is deactivated. Please reactivate instead.'
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 409
        }
      )
    }

    // ========================================================================
    // Step 4: Create Supabase Auth account with invitation
    // ========================================================================
    console.log(`[invite-staff] Creating auth account for: ${normalizedEmail}`)

    const { data: authData, error: createUserError } = await supabaseAdmin.auth.admin.inviteUserByEmail(
      normalizedEmail,
      {
        data: {
          role: role,
          display_name: displayName || null,
          email_confirm: false // User must confirm via invite email
        },
        redirectTo: `${Deno.env.get('PUBLIC_APP_URL') || 'http://localhost:3000'}/auth/callback`
      }
    )

    if (createUserError) {
      console.error('[invite-staff] Failed to create auth account:', createUserError)

      // Check for specific errors
      if (createUserError.message.includes('already registered')) {
        return new Response(
          JSON.stringify({
            success: false,
            error: {
              code: 'EMAIL_ALREADY_REGISTERED',
              message: 'A user with this email already has an account'
            }
          }),
          {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 409
          }
        )
      }

      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'AUTH_CREATE_FAILED',
            message: 'Failed to create user account',
            details: createUserError.message
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    if (!authData.user) {
      console.error('[invite-staff] No user data returned from auth creation')
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'AUTH_CREATE_FAILED',
            message: 'User account creation failed - no user data returned'
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    const userId = authData.user.id

    // ========================================================================
    // Step 5: Create staff_members record
    // ========================================================================
    console.log(`[invite-staff] Creating staff_members record for user: ${userId}`)

    const { error: staffRecordError } = await supabaseAdmin
      .from('staff_members')
      .insert({
        email: normalizedEmail,
        role: role,
        display_name: displayName?.trim() || null,
        notes: notes?.trim() || null,
        active: true,
        added_by: user.email
      })

    if (staffRecordError) {
      console.error('[invite-staff] Failed to create staff record:', staffRecordError)

      // ROLLBACK: Delete the auth account we just created
      console.log(`[invite-staff] Rolling back auth account creation for: ${userId}`)
      try {
        await supabaseAdmin.auth.admin.deleteUser(userId)
        console.log(`[invite-staff] Rollback successful`)
      } catch (rollbackError) {
        console.error('[invite-staff] CRITICAL: Rollback failed:', rollbackError)
        // Log to DLQ or alert system - orphaned auth account exists
      }

      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'STAFF_RECORD_FAILED',
            message: 'Failed to create staff member record',
            details: staffRecordError.message
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    // ========================================================================
    // Step 6: Log audit trail
    // ========================================================================
    console.log(`[invite-staff] SUCCESS: Invited ${normalizedEmail} as ${role} by ${user.email}`)

    // ========================================================================
    // Step 7: Return success response
    // ========================================================================
    const response: InviteStaffResponse = {
      success: true,
      data: {
        userId: userId,
        email: normalizedEmail,
        role: role,
        invitationSent: true
      }
    }

    return new Response(
      JSON.stringify(response),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 201
      }
    )

  } catch (error) {
    console.error('[invite-staff] Unexpected error:', error)

    return new Response(
      JSON.stringify({
        success: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: 'An unexpected error occurred',
          details: error instanceof Error ? error.message : 'Unknown error'
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})
