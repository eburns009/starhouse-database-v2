/**
 * Reset Staff Password - Supabase Edge Function
 *
 * FAANG Standards:
 * - Admin-triggered password reset for staff members
 * - Sends password reset email to staff member
 * - Audit logging for security compliance
 * - Authorization checks
 *
 * Security:
 * - Requires authenticated admin user
 * - Can only reset passwords for active staff members
 * - Uses Supabase's built-in secure password reset flow
 * - Audit trail of who triggered the reset
 *
 * Flow:
 * 1. Verify caller is authenticated admin
 * 2. Validate target email exists and is active staff
 * 3. Trigger password reset email via Supabase Auth
 * 4. Log audit trail
 * 5. Return success
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

interface ResetPasswordRequest {
  email: string
}

interface ResetPasswordResponse {
  success: boolean
  data?: {
    email: string
    resetEmailSent: boolean
  }
  error?: {
    code: string
    message: string
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

    const authHeader = req.headers.get('Authorization')!
    const supabaseClient = createClient(supabaseUrl, supabaseServiceRoleKey, {
      global: { headers: { Authorization: authHeader } }
    })

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
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'FORBIDDEN',
            message: 'Only administrators can reset staff passwords'
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 403
        }
      )
    }

    // ========================================================================
    // Step 2: Parse and validate request
    // ========================================================================
    const body: ResetPasswordRequest = await req.json()
    const { email } = body

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

    const normalizedEmail = email.toLowerCase().trim()

    // ========================================================================
    // Step 3: Verify target is active staff member
    // ========================================================================
    const { data: staffMember, error: staffError } = await supabaseAdmin
      .from('staff_members')
      .select('email, active, role')
      .eq('email', normalizedEmail)
      .maybeSingle()

    if (staffError) {
      console.error('[reset-password] Database error:', staffError)
      return new Response(
        JSON.stringify({
          success: false,
          error: { code: 'DATABASE_ERROR', message: 'Failed to verify staff member' }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    if (!staffMember) {
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'STAFF_NOT_FOUND',
            message: 'No staff member found with this email address'
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 404
        }
      )
    }

    if (!staffMember.active) {
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'STAFF_INACTIVE',
            message: 'Cannot reset password for inactive staff member'
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400
        }
      )
    }

    // ========================================================================
    // Step 4: Trigger password reset email
    // ========================================================================
    console.log(`[reset-password] Sending password reset email to: ${normalizedEmail}`)

    const { error: resetError } = await supabaseAdmin.auth.resetPasswordForEmail(
      normalizedEmail,
      {
        redirectTo: `${Deno.env.get('PUBLIC_APP_URL') || 'http://localhost:3000'}/auth/reset-password`
      }
    )

    if (resetError) {
      console.error('[reset-password] Failed to send reset email:', resetError)
      return new Response(
        JSON.stringify({
          success: false,
          error: {
            code: 'RESET_FAILED',
            message: 'Failed to send password reset email',
            details: resetError.message
          }
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    // ========================================================================
    // Step 5: Log audit trail
    // ========================================================================
    console.log(`[reset-password] SUCCESS: Password reset triggered for ${normalizedEmail} by ${user.email}`)

    // ========================================================================
    // Step 6: Return success
    // ========================================================================
    const response: ResetPasswordResponse = {
      success: true,
      data: {
        email: normalizedEmail,
        resetEmailSent: true
      }
    }

    return new Response(
      JSON.stringify(response),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )

  } catch (error) {
    console.error('[reset-password] Unexpected error:', error)

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
