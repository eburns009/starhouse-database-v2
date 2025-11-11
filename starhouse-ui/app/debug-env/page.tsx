'use client'

/**
 * Debug page to verify environment variables are properly set
 * This helps diagnose "Invalid value" fetch errors
 */
export default function DebugEnvPage() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  const appUrl = process.env.NEXT_PUBLIC_APP_URL

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Environment Variables Debug</h1>

        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <h2 className="font-semibold text-lg mb-2">NEXT_PUBLIC_SUPABASE_URL</h2>
            <code className="block bg-gray-100 p-3 rounded">
              {supabaseUrl || '❌ UNDEFINED'}
            </code>
            <p className="mt-2 text-sm text-gray-600">
              {supabaseUrl ? '✅ Set correctly' : '❌ Not set - this is causing the fetch error!'}
            </p>
          </div>

          <div>
            <h2 className="font-semibold text-lg mb-2">NEXT_PUBLIC_SUPABASE_ANON_KEY</h2>
            <code className="block bg-gray-100 p-3 rounded break-all">
              {supabaseKey ? `${supabaseKey.substring(0, 50)}...` : '❌ UNDEFINED'}
            </code>
            <p className="mt-2 text-sm text-gray-600">
              {supabaseKey ? '✅ Set correctly' : '❌ Not set'}
            </p>
          </div>

          <div>
            <h2 className="font-semibold text-lg mb-2">NEXT_PUBLIC_APP_URL</h2>
            <code className="block bg-gray-100 p-3 rounded">
              {appUrl || '❌ UNDEFINED'}
            </code>
            <p className="mt-2 text-sm text-gray-600">
              {appUrl ? '✅ Set correctly' : '⚠️ Not set (optional)'}
            </p>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded">
            <h3 className="font-semibold mb-2">What to do if variables are undefined:</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Check Vercel dashboard → Settings → Environment Variables</li>
              <li>Make sure variables are set for Production, Preview, and Development</li>
              <li>Trigger a new deployment (without cache!)</li>
              <li>Hard refresh this page (Ctrl+Shift+R or Cmd+Shift+R)</li>
            </ol>
          </div>

          <div className="mt-4 p-4 bg-green-50 rounded">
            <h3 className="font-semibold mb-2">Expected values:</h3>
            <ul className="text-sm space-y-1">
              <li>NEXT_PUBLIC_SUPABASE_URL: https://lnagadkqejnopgfxwlkb.supabase.co</li>
              <li>NEXT_PUBLIC_SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIs...</li>
              <li>NEXT_PUBLIC_APP_URL: https://starhouse-database-v2.vercel.app</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
