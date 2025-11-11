import { createBrowserClient } from '@supabase/ssr'
import { Database } from '@/lib/types/database'

/**
 * Create Supabase client for Client Components
 * FAANG Standard: Singleton pattern, reuse client instance
 */
let client: ReturnType<typeof createBrowserClient<Database>> | undefined

export function createClient() {
  if (client) return client

  client = createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )

  return client
}
