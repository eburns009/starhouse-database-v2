import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { Database } from '@/lib/types/database'

/**
 * Create Supabase client for Server Components
 * FAANG Standard: Always use SSR-compatible client on server
 */
export function createClient() {
  const cookieStore = cookies()

  // CRITICAL FIX: Strip newlines from environment variables
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!.trim().replace(/\n/g, '')
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.trim().replace(/\n/g, '')

  return createServerClient<Database>(
    url,
    key,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value, ...options })
          } catch (error) {
            // Handle cookies() being called from Server Component
            // (cookies can only be set in Server Actions or Route Handlers)
          }
        },
        remove(name: string, options: CookieOptions) {
          try {
            cookieStore.set({ name, value: '', ...options })
          } catch (error) {
            // Handle cookies() being called from Server Component
          }
        },
      },
    }
  )
}

/**
 * Create Supabase client with service role (full access, bypasses RLS)
 * CRITICAL: Only use in Node runtime Route Handlers or Server Actions
 * NEVER expose service role key to client or edge runtime
 */
export function createServiceClient() {
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error('SUPABASE_SERVICE_ROLE_KEY is required for service client')
  }

  // CRITICAL FIX: Strip newlines from environment variables
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!.trim().replace(/\n/g, '')
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY.trim().replace(/\n/g, '')

  return createServerClient<Database>(
    url,
    serviceKey,
    {
      cookies: {
        get() { return undefined },
        set() {},
        remove() {},
      },
    }
  )
}
