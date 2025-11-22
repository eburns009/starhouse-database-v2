import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Auth callback handler for Supabase
 * Handles OAuth and email confirmation flows
 */
export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const next = requestUrl.searchParams.get('next') || '/'

  if (code) {
    const cookieStore = cookies()

    // CRITICAL FIX: Strip newlines from environment variables
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL!.trim().replace(/\n/g, '')
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.trim().replace(/\n/g, '')

    const supabase = createServerClient(
      url,
      key,
      {
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
      }
    )

    // SECURITY FIX (P0): Clear any existing session before exchanging invite code
    // This prevents session contamination when invitation links are clicked
    // Without this, a new user clicking an invite link while another user is logged in
    // would see the existing user's dashboard instead of their own account setup
    await supabase.auth.signOut()

    // Now exchange the invitation code for a new session
    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error) {
      return NextResponse.redirect(new URL(next, requestUrl.origin))
    }
  }

  // If no code or error, redirect to login
  return NextResponse.redirect(new URL('/login', requestUrl.origin))
}
