import { createClient as createSupabaseClient } from '@supabase/supabase-js'

/**
 * Create Supabase client for Client Components
 * Using basic @supabase/supabase-js instead of @supabase/ssr to avoid fetch issues
 * FAANG Standard: Singleton pattern, reuse client instance
 */
let client: ReturnType<typeof createSupabaseClient> | undefined

export function createClient() {
  if (client) return client

  // CRITICAL FIX: Strip newlines and whitespace from environment variables
  // The Vercel environment variable input can wrap long JWTs with newlines,
  // which causes "Invalid value" errors in fetch() headers
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!.trim().replace(/\n/g, '')
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.trim().replace(/\n/g, '')

  // Debug logging
  console.log('[Supabase Client] Creating client with:', {
    url,
    keyLength: key?.length,
    urlType: typeof url,
    keyType: typeof key,
    hasNewlines: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.includes('\n')
  })

  // Use basic createClient from @supabase/supabase-js
  // This avoids the SSR package's fetch wrapper that causes "Invalid value" errors
  client = createSupabaseClient(url, key, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true
    }
  })

  return client
}
