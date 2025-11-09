// Health Check Endpoint - Monitor System Performance
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = performance.now()
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    checks: {
      database: { status: 'unknown' },
      tables: { status: 'unknown' }
    },
    metrics: {}
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Check database connection with actual query
    const dbStart = performance.now()
    const { count: contactCount, error: contactError } = await supabase
      .from('contacts')
      .select('*', { count: 'exact', head: true })

    health.checks.database = {
      status: contactError ? 'unhealthy' : 'healthy',
      latencyMs: parseFloat((performance.now() - dbStart).toFixed(2)),
      error: contactError?.message
    }

    if (contactError) {
      health.status = 'degraded'
    }

    // Get table counts for monitoring
    const tableStart = performance.now()

    const [txnResult, subResult] = await Promise.all([
      supabase.from('transactions').select('*', { count: 'exact', head: true }),
      supabase.from('subscriptions').select('*', { count: 'exact', head: true })
    ])

    health.checks.tables = {
      status: 'healthy',
      contacts: contactCount || 0,
      transactions: txnResult.count || 0,
      subscriptions: subResult.count || 0,
      latencyMs: parseFloat((performance.now() - tableStart).toFixed(2))
    }

    // Overall metrics
    health.metrics = {
      totalLatencyMs: parseFloat((performance.now() - startTime).toFixed(2)),
      databaseLatencyMs: health.checks.database.latencyMs,
      version: '1.0.0',
      environment: Deno.env.get('ENVIRONMENT') || 'production'
    }

  } catch (error) {
    health.status = 'unhealthy'
    health.checks.database = {
      status: 'unhealthy',
      error: error.message,
      latencyMs: parseFloat((performance.now() - startTime).toFixed(2))
    }
  }

  return new Response(
    JSON.stringify(health, null, 2),
    {
      status: health.status === 'healthy' ? 200 : 503,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    }
  )
})
