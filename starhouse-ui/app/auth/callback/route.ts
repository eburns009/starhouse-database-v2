import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Auth callback handler for Supabase
 *
 * Handles THREE authentication flows:
 * 1. OAuth/Magic Links (code parameter) - exchangeCodeForSession
 * 2. User Invitations (token + type=invite) - verifyOtp
 * 3. Password Reset (token + type=recovery) - verifyOtp
 *
 * FAANG Standards:
 * - Clear session before new auth to prevent session contamination
 * - Comprehensive logging for debugging
 * - Type-safe parameter handling
 */
export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)

  // Extract all possible auth parameters
  const code = requestUrl.searchParams.get('code')
  const token = requestUrl.searchParams.get('token')
  const type = requestUrl.searchParams.get('type')
  const next = requestUrl.searchParams.get('next') || '/'

  // Initialize Supabase client
  const cookieStore = cookies()
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!.trim().replace(/\n/g, '')
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.trim().replace(/\n/g, '')

  const supabase = createServerClient(url, key, {
    cookies: {
      get(name: string) {
        return cookieStore.get(name)?.value
      },
      set(name: string, value: string, options: CookieOptions) {
        cookieStore.set({ name, value, ...options })
      },
      remove(name: string, options: CookieOptions) {
        cookieStore.set({ name, value: '', ...options })
      },
    },
  })

  // ============================================================================
  // FLOW 1: OAuth/Magic Link (code parameter)
  // ============================================================================
  if (code) {
    console.log('[auth/callback] Processing OAuth/Magic Link flow')

    // SECURITY: Clear existing session to prevent session contamination
    await supabase.auth.signOut()

    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error) {
      console.log('[auth/callback] OAuth/Magic Link SUCCESS - redirecting to:', next)
      return NextResponse.redirect(new URL(next, requestUrl.origin))
    }

    console.error('[auth/callback] OAuth/Magic Link FAILED:', error.message)
  }

  // ============================================================================
  // FLOW 2: User Invitation (token + type=invite)
  // ============================================================================
  if (token && type === 'invite') {
    console.log('[auth/callback] Processing invitation flow')

    // SECURITY: Clear existing session to prevent session contamination
    await supabase.auth.signOut()

    const { error } = await supabase.auth.verifyOtp({
      token_hash: token,
      type: 'invite'
    })

    if (!error) {
      console.log('[auth/callback] Invitation verification SUCCESS - redirecting to password setup')
      // Redirect to password setup page for new users
      return NextResponse.redirect(new URL('/auth/setup-password', requestUrl.origin))
    }

    console.error('[auth/callback] Invitation verification FAILED:', error.message)
  }

  // ============================================================================
  // FLOW 3: Password Reset (token + type=recovery)
  // ============================================================================
  if (token && type === 'recovery') {
    console.log('[auth/callback] Processing password recovery flow')

    // SECURITY: Clear existing session to prevent session contamination
    await supabase.auth.signOut()

    const { error } = await supabase.auth.verifyOtp({
      token_hash: token,
      type: 'recovery'
    })

    if (!error) {
      console.log('[auth/callback] Recovery verification SUCCESS - redirecting to password reset')
      // Redirect to password reset page
      return NextResponse.redirect(new URL('/auth/reset-password', requestUrl.origin))
    }

    console.error('[auth/callback] Recovery verification FAILED:', error.message)
  }

  // ============================================================================
  // FLOW 4: Magic Link (token + type=magiclink)
  // ============================================================================
  if (token && type === 'magiclink') {
    console.log('[auth/callback] Processing magic link flow')

    const { error } = await supabase.auth.verifyOtp({
      token_hash: token,
      type: 'magiclink'
    })

    if (!error) {
      console.log('[auth/callback] Magic link SUCCESS - redirecting to:', next)
      return NextResponse.redirect(new URL(next, requestUrl.origin))
    }

    console.error('[auth/callback] Magic link FAILED:', error.message)
  }

  // ============================================================================
  // Fallback: No valid parameters or all flows failed
  // ============================================================================
  console.log('[auth/callback] No valid auth parameters or verification failed - redirecting to login')
  return NextResponse.redirect(new URL('/login', requestUrl.origin))
}
