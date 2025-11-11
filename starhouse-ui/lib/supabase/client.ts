import { createClient as createSupabaseClient } from '@supabase/supabase-js'

/**
 * Create Supabase client for Client Components
 * Using basic @supabase/supabase-js instead of @supabase/ssr to avoid fetch issues
 * FAANG Standard: Singleton pattern, reuse client instance
 */
let client: ReturnType<typeof createSupabaseClient> | undefined

export function createClient() {
  if (client) return client

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

  // Debug logging
  console.log('[Supabase Client] Creating client with:', {
    url,
    keyLength: key?.length,
    urlType: typeof url,
    keyType: typeof key,
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
