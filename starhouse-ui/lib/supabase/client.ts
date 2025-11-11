import { createBrowserClient } from '@supabase/ssr'

/**
 * Create Supabase client for Client Components
 * FAANG Standard: Singleton pattern, reuse client instance
 */
let client: ReturnType<typeof createBrowserClient> | undefined

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

  // Try without Database type parameter
  client = createBrowserClient(url, key)

  return client
}
