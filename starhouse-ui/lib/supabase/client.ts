import { createBrowserClient } from '@supabase/ssr'

/**
 * Create Supabase client for Client Components
 * Uses @supabase/ssr for proper cookie management between client/server
 * FAANG Standard: Singleton pattern, reuse client instance
 */
let client: ReturnType<typeof createBrowserClient> | undefined

export function createClient() {
  if (client) return client

  // CRITICAL FIX: Strip newlines and whitespace from environment variables
  // The Vercel environment variable input can wrap long JWTs with newlines,
  // which causes "Invalid value" errors in fetch() headers
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!.trim().replace(/\n/g, '').replace(/\s/g, '')
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.trim().replace(/\n/g, '').replace(/\s/g, '')

  // Use SSR package for proper cookie management
  // With newline stripping, this now works correctly
  client = createBrowserClient(url, key)

  return client
}
