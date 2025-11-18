// Kajabi Webhook Receiver - Supabase Edge Function (SECURED)
// Handles real-time events from Kajabi
// Supported events: order.created, payment.succeeded
// Security: Signature verification, rate limiting, input validation

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts"
import { logToDLQ, categorizeError } from '../_shared/error-handling.ts'

// Restricted CORS - only allow Kajabi's webhook IPs
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://app.kajabi.com',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-kajabi-signature',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

// Rate limiting: Track requests by IP
const rateLimitMap = new Map<string, { count: number; resetTime: number }>()
const RATE_LIMIT_REQUESTS = 100 // Max requests per window
const RATE_LIMIT_WINDOW = 60000 // 1 minute in milliseconds

// Request size limit
const MAX_PAYLOAD_SIZE = 1048576 // 1MB

serve(async (req) => {
  let webhookEventId: string | undefined

  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Only accept POST requests
  if (req.method !== 'POST') {
    return new Response(
      JSON.stringify({ error: 'Method not allowed' }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 405
      }
    )
  }

  try {
    // Rate limiting check
    const clientIP = req.headers.get('x-forwarded-for') || 'unknown'
    const now = Date.now()
    const rateLimit = rateLimitMap.get(clientIP)

    if (rateLimit) {
      if (now < rateLimit.resetTime) {
        if (rateLimit.count >= RATE_LIMIT_REQUESTS) {
          return new Response(
            JSON.stringify({ error: 'Rate limit exceeded' }),
            {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' },
              status: 429
            }
          )
        }
        rateLimit.count++
      } else {
        // Reset window
        rateLimitMap.set(clientIP, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
      }
    } else {
      rateLimitMap.set(clientIP, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
    }

    // Clean up old rate limit entries (keep map from growing infinitely)
    for (const [ip, limit] of rateLimitMap.entries()) {
      if (now > limit.resetTime + RATE_LIMIT_WINDOW) {
        rateLimitMap.delete(ip)
      }
    }

    // Get raw body for signature verification
    const rawBody = await req.text()

    // Check payload size
    if (rawBody.length > MAX_PAYLOAD_SIZE) {
      return new Response(
        JSON.stringify({ error: 'Payload too large' }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 413
        }
      )
    }

    // SECURITY: Dual-mode authentication (Zapier OR Direct webhooks)
    let isAuthenticated = false
    let authMethod = ''

    // METHOD 1: Check for Zapier authentication via custom header
    const zapierSecret = req.headers.get('x-zapier-secret')
    const expectedZapierSecret = Deno.env.get('ZAPIER_SECRET')

    if (zapierSecret && expectedZapierSecret && zapierSecret === expectedZapierSecret) {
      isAuthenticated = true
      authMethod = 'Zapier custom header'
      console.log('✅ Authenticated via Zapier (custom header)')
    }

    // METHOD 2: Check for direct webhook signature (if not already authenticated)
    if (!isAuthenticated) {
      const signature = req.headers.get('x-kajabi-signature')
      const webhookSecret = Deno.env.get('KAJABI_WEBHOOK_SECRET')

      if (webhookSecret && signature) {
        const isValidSignature = await verifyKajabiSignature(rawBody, signature, webhookSecret)
        if (isValidSignature) {
          isAuthenticated = true
          authMethod = 'Kajabi signature'
          console.log('✅ Authenticated via Kajabi signature')
        }
      }
    }

    // REJECT if neither authentication method succeeded
    if (!isAuthenticated) {
      console.error('❌ Authentication FAILED - no valid Zapier secret or Kajabi signature')
      console.error('Headers present:', {
        hasZapierSecret: !!zapierSecret,
        hasKajabiSignature: !!req.headers.get('x-kajabi-signature'),
        userAgent: req.headers.get('user-agent')?.substring(0, 50) || 'none'
      })

      return new Response(
        JSON.stringify({
          error: 'Unauthorized - authentication required',
          code: 'AUTHENTICATION_FAILED',
          hint: 'Provide either X-Zapier-Secret header (for Zapier) or X-Kajabi-Signature (for direct webhooks)'
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 401
        }
      )
    }

    // ✅ Authentication successful
    console.log(`✅ Request authenticated via: ${authMethod}`)

    // Parse payload after verification
    const payload = JSON.parse(rawBody)
    console.log('Verified Kajabi webhook:', payload.event || payload.event_type || payload.type)

    // Input validation
    if (!payload || typeof payload !== 'object') {
      return new Response(
        JSON.stringify({ error: 'Invalid payload' }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 400
        }
      )
    }

    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Extract event type and data
    // Kajabi uses 'event' field (not 'event_type' or 'type')
    const eventType = sanitizeString(payload.event || payload.event_type || payload.type)
    const data = payload.data || payload

    // Calculate payload hash for duplicate detection
    const encoder = new TextEncoder()
    const payloadData = encoder.encode(rawBody)
    const hashBuffer = await crypto.subtle.digest('SHA-256', payloadData)
    const payloadHash = Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')

    // Generate webhook ID (use Zapier's request ID if available, otherwise generate UUID)
    const webhookId = req.headers.get('x-request-id') || req.headers.get('x-zapier-request-id') || crypto.randomUUID()

    // Log incoming webhook event to webhook_events table
    try {
      const { data: eventLog, error: eventLogError } = await supabaseClient
        .from('webhook_events')
        .insert({
          webhook_id: webhookId,
          source: 'kajabi',
          event_type: eventType,
          status: 'processing',
          payload_hash: payloadHash,
          payload_size: rawBody.length,
          ip_address: req.headers.get('x-forwarded-for') || 'unknown',
          user_agent: req.headers.get('user-agent')?.substring(0, 255),
          signature_valid: isAuthenticated,
          received_at: new Date().toISOString()
        })
        .select('id')
        .single()

      if (eventLogError) {
        console.error('[webhook_events] Failed to log event:', eventLogError)
      } else {
        webhookEventId = eventLog?.id
        console.log(`[webhook_events] Event logged: ${webhookEventId}`)
      }
    } catch (eventLogError) {
      console.error('[webhook_events] Exception logging event:', eventLogError)
    }

    // Route to appropriate handler
    let result
    switch (eventType) {
      // Kajabi's actual webhook events
      case 'order.created':
      case 'payment.succeeded':
        result = await handleOrder(supabaseClient, data)
        break

      // Legacy event names (keep for backwards compatibility)
      case 'purchase.created':
      case 'purchase.succeed':
        result = await handleOrder(supabaseClient, data)
        break

      case 'member.created':
      case 'member.updated':
        result = await handleMember(supabaseClient, data)
        break

      case 'contact.created':
      case 'contact.updated':
        result = await handleContact(supabaseClient, data)
        break

      case 'subscription.updated':
      case 'subscription.created':
        result = await handleSubscription(supabaseClient, data)
        break

      case 'tag.added':
        result = await handleTagAdded(supabaseClient, data)
        break

      case 'tag.removed':
        result = await handleTagRemoved(supabaseClient, data)
        break

      case 'email.unsubscribe':
        result = await handleEmailUnsubscribe(supabaseClient, data)
        break

      default:
        console.log(`Unhandled event type: ${eventType}`)
        result = { message: 'Event type not handled', eventType }
    }

    // Update webhook_events with success status
    if (webhookEventId) {
      try {
        await supabaseClient
          .from('webhook_events')
          .update({
            status: 'success',
            processed_at: new Date().toISOString()
          })
          .eq('id', webhookEventId)
      } catch (updateError) {
        console.error('[webhook_events] Failed to update success status:', updateError)
      }
    }

    return new Response(
      JSON.stringify({ success: true, result }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 }
    )

  } catch (error) {
    console.error('Error processing webhook:', error)

    // Log to DLQ with error categorization
    let errorInfo

    // Create supabase client for DLQ logging
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    try {
      // Try to parse payload for DLQ logging
      let payload
      let eventType = 'unknown'

      try {
        payload = JSON.parse(rawBody)
        eventType = payload.event || payload.event_type || payload.type || 'unknown'
      } catch (parseError) {
        // If JSON parse fails, store raw body (truncated)
        console.log('Failed to parse rawBody for DLQ, storing raw data')
        payload = {
          _raw: rawBody.slice(0, 1000),
          _parseError: String(parseError).slice(0, 200)
        }
        eventType = 'parse_error'
      }

      errorInfo = await logToDLQ(
        supabaseClient,
        'kajabi',
        eventType,
        payload,
        error as Error,
        webhookEventId
      )
    } catch (dlqError) {
      console.error('[CRITICAL] DLQ logging failed:', dlqError)
      errorInfo = categorizeError(error as Error)
    }

    // Update webhook_events with failure status if we have an event ID
    if (webhookEventId && errorInfo) {
      try {
        await supabaseClient
          .from('webhook_events')
          .update({
            status: 'failed',
            error_message: errorInfo.message.slice(0, 2000),
            error_code: errorInfo.code,
            processed_at: new Date().toISOString()
          })
          .eq('id', webhookEventId)
      } catch (updateError) {
        console.error('[webhook_events] Failed to update failure status:', updateError)
      }
    }

    // Return appropriate status code based on retryability
    const statusCode = errorInfo?.retryable ? 500 : 400

    return new Response(
      JSON.stringify({
        error: errorInfo?.code || 'UNKNOWN_ERROR',
        message: errorInfo?.message || 'Internal server error',
        retryable: errorInfo?.retryable ?? true
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: statusCode
      }
    )
  }
})

// SECURITY: Verify Kajabi webhook signature
async function verifyKajabiSignature(
  rawBody: string,
  signature: string,
  secret: string
): Promise<boolean> {
  try {
    // Kajabi uses HMAC-SHA256 for webhook signatures
    const encoder = new TextEncoder()
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )

    const signatureBuffer = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(rawBody)
    )

    const expectedSignature = Array.from(new Uint8Array(signatureBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    return timingSafeEqual(expectedSignature, signature.toLowerCase())
  } catch (error) {
    console.error('Signature verification error:', error)
    return false
  }
}

// SECURITY: Timing-safe string comparison
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false
  }

  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }

  return result === 0
}

// SECURITY: Sanitize string input
function sanitizeString(input: any): string {
  if (typeof input !== 'string') {
    return String(input)
  }
  // Remove any control characters and limit length
  return input.replace(/[\x00-\x1F\x7F]/g, '').substring(0, 255)
}

// SECURITY: Validate and sanitize email
function validateEmail(email: any): string | null {
  if (typeof email !== 'string') {
    return null
  }

  const sanitized = email.trim().toLowerCase().substring(0, 255)

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(sanitized)) {
    return null
  }

  return sanitized
}

// SECURITY: Validate and parse amount
function validateAmount(amount: any): number | null {
  if (typeof amount === 'number' && !isNaN(amount) && isFinite(amount)) {
    return amount
  }

  if (typeof amount === 'string') {
    const parsed = parseFloat(amount)
    if (!isNaN(parsed) && isFinite(parsed)) {
      return parsed
    }
  }

  return null
}

// SECURITY: Standardize country code to ISO 3166-1 alpha-2
function standardizeCountryCode(country: string): string {
  if (!country) return ''

  const countryUpper = country.toUpperCase().trim()

  // Map common country names to ISO codes
  const countryMap: Record<string, string> = {
    'UNITED STATES': 'US',
    'UNITED STATES OF AMERICA': 'US',
    'USA': 'US',
    'CANADA': 'CA',
    'UNITED KINGDOM': 'GB',
    'UK': 'GB',
    'GREAT BRITAIN': 'GB',
    'AUSTRALIA': 'AU',
    'NEW ZEALAND': 'NZ',
    'FRANCE': 'FR',
    'GERMANY': 'DE',
    'SPAIN': 'ES',
    'ITALY': 'IT',
    'NETHERLANDS': 'NL',
    'MEXICO': 'MX',
    'BRAZIL': 'BR',
    'CHINA': 'CN',
    'JAPAN': 'JP',
    'INDIA': 'IN',
    'SOUTH KOREA': 'KR',
    'ISRAEL': 'IL',
    'SOUTH AFRICA': 'ZA',
    'TAIWAN': 'TW',
    'HONG KONG': 'HK',
    'SINGAPORE': 'SG',
    'THAILAND': 'TH',
    'PHILIPPINES': 'PH',
    'INDONESIA': 'ID',
    'MALAYSIA': 'MY',
    'VIETNAM': 'VN',
    'DENMARK': 'DK',
    'SWEDEN': 'SE',
    'NORWAY': 'NO',
    'FINLAND': 'FI',
    'IRELAND': 'IE',
    'POLAND': 'PL',
    'ROMANIA': 'RO',
    'COSTA RICA': 'CR'
  }

  // Return mapped code if found
  if (countryMap[countryUpper]) {
    return countryMap[countryUpper]
  }

  // If already 2 characters, assume it's ISO code
  if (countryUpper.length === 2) {
    return countryUpper
  }

  // Otherwise take first 2 characters (may need manual cleanup)
  return countryUpper.substring(0, 2)
}

// Handle order/payment events from Kajabi
async function handleOrder(supabase: any, data: any) {
  console.log('Processing order/payment:', data.id || data.order_id)

  // Kajabi nests transaction data in 'payment_transaction' field
  const txn = data.payment_transaction || data

  // Extract and validate transaction data
  const transaction: any = {
    source_system: 'kajabi', // Required, no default
    external_transaction_id: sanitizeString(data.id || txn.id || data.transaction_id || data.order_id), // Kajabi's actual txn ID
    external_order_id: sanitizeString(data.order_number || data.number), // Optional order reference
    kajabi_transaction_id: sanitizeString(data.id || txn.id || data.transaction_id || data.order_id), // DEPRECATED: Legacy field, keep for backward compat
    order_number: sanitizeString(data.order_number || data.number),
    amount: validateAmount(txn.amount_paid_decimal || txn.amount_paid || txn.amount || data.amount),
    currency: sanitizeString(txn.currency || data.currency || 'USD').substring(0, 3).toUpperCase(),
    status: sanitizeString(data.status || 'completed'),
    transaction_type: 'purchase',
    payment_method: sanitizeString(txn.payment_method || 'kajabi'),
    payment_processor: sanitizeString(txn.payment_processor || 'Kajabi'),
    tax_amount: validateAmount(txn.sales_tax_decimal || txn.sales_tax),
    quantity: validateAmount(txn.quantity || 1),
    coupon_code: sanitizeString(txn.coupon_code || ''),
    transaction_date: txn.created_at || data.created_at || new Date().toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  // Validate required fields
  if (!transaction.external_transaction_id) {
    throw new Error('Missing external_transaction_id from Kajabi')
  }

  // Find or create contact by email
  // Kajabi nests member data in 'member' field
  const email = validateEmail(data.member?.email || data.email || data.customer?.email)

  if (email) {
    // Try to find existing contact
    let { data: contact } = await supabase
      .from('contacts')
      .select('id')
      .eq('email', email)
      .single()

    // If contact doesn't exist, create it
    if (!contact) {
      const newContact = {
        email: email,
        first_name: sanitizeString(data.member?.first_name || data.first_name || data.customer?.first_name || '').substring(0, 100),
        last_name: sanitizeString(data.member?.last_name || data.last_name || data.customer?.last_name || '').substring(0, 100),
        kajabi_id: sanitizeString(data.member?.id || data.customer?.id || ''),
        source_system: 'kajabi',
        email_subscribed: true,
        updated_at: new Date().toISOString()
      }

      const { data: createdContact } = await supabase
        .from('contacts')
        .upsert(newContact, {
          onConflict: 'email',
          ignoreDuplicates: false
        })
        .select()
        .single()

      contact = createdContact
    }

    if (contact) {
      transaction.contact_id = contact.id
    }
  } else {
    // No email found - create/use test contact for simulator events
    console.warn('⚠️ No email found in Kajabi payload - using test contact')

    const testEmail = 'kajabi-test@simulator.kajabi.com'

    let { data: testContact, error: selectError } = await supabase
      .from('contacts')
      .select('id')
      .eq('email', testEmail)
      .single()

    if (selectError && selectError.code !== 'PGRST116') {
      console.error('Error finding test contact:', selectError)
    }

    if (!testContact) {
      console.log('Creating Kajabi test contact...')
      const { data: createdContact, error: insertError } = await supabase
        .from('contacts')
        .insert({
          email: testEmail,
          first_name: 'Kajabi',
          last_name: 'Test',
          source_system: 'manual',
          email_subscribed: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .select()
        .single()

      if (insertError) {
        console.error('Failed to create test contact:', insertError)
        throw new Error(`Failed to create test contact: ${insertError.message}`)
      }

      testContact = createdContact
      console.log('✅ Kajabi test contact created:', testContact.id)
    } else {
      console.log('✅ Using existing Kajabi test contact:', testContact.id)
    }

    transaction.contact_id = testContact.id
  }

  // Upsert transaction (proper provenance-based idempotency)
  const { data: result, error } = await supabase
    .from('transactions')
    .upsert(transaction, {
      onConflict: 'source_system,external_transaction_id',
      ignoreDuplicates: false
    })
    .select()

  if (error) throw error
  return { message: 'Transaction processed', data: result }
}

// Handle member events (course enrollments, membership)
async function handleMember(supabase: any, data: any) {
  console.log('Processing member:', data.id)

  const email = validateEmail(data.email)
  if (!email) {
    throw new Error('Invalid email in member data')
  }

  // Extract contact info
  const contactData = {
    email: email,
    first_name: sanitizeString(data.first_name || data.name?.split(' ')[0]).substring(0, 100),
    last_name: sanitizeString(data.last_name || data.name?.split(' ').slice(1).join(' ')).substring(0, 100),
    kajabi_id: sanitizeString(data.kajabi_id || data.id),
    kajabi_member_id: sanitizeString(data.member_id),
    source_system: 'kajabi',
    email_subscribed: data.email_subscribed ?? true,
    updated_at: new Date().toISOString()
  }

  // Upsert contact
  const { data: result, error } = await supabase
    .from('contacts')
    .upsert(contactData, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()

  if (error) throw error
  return { message: 'Member processed', data: result }
}

// Handle contact events
async function handleContact(supabase: any, data: any) {
  console.log('Processing contact:', data.id)

  const email = validateEmail(data.email)
  if (!email) {
    throw new Error('Invalid email in contact data')
  }

  const contactData: any = {
    email: email,
    first_name: sanitizeString(data.first_name).substring(0, 100),
    last_name: sanitizeString(data.last_name).substring(0, 100),
    kajabi_id: sanitizeString(data.id),
    source_system: 'kajabi',
    email_subscribed: data.email_subscribed ?? true,
    updated_at: new Date().toISOString()
  }

  // Capture phone with metadata
  if (data.phone) {
    contactData.phone = sanitizeString(data.phone).substring(0, 20)
    contactData.phone_source = 'kajabi'
    contactData.phone_verified = false
  }

  // Capture billing address if provided (from checkout or profile)
  const addr = data.billing_address || data.address || {}
  if (addr.line1 || addr.address_line_1 || addr.street) {
    contactData.address_line_1 = sanitizeString(addr.line1 || addr.address_line_1 || addr.street || '').substring(0, 255)

    if (addr.line2 || addr.address_line_2) {
      contactData.address_line_2 = sanitizeString(addr.line2 || addr.address_line_2 || '').substring(0, 255)
    }
    if (addr.city) {
      contactData.city = sanitizeString(addr.city).substring(0, 100)
    }
    if (addr.state || addr.state_province) {
      contactData.state = sanitizeString(addr.state || addr.state_province).substring(0, 100)
    }
    if (addr.postal_code || addr.zip) {
      contactData.postal_code = sanitizeString(addr.postal_code || addr.zip).substring(0, 20)
    }
    if (addr.country) {
      contactData.country = standardizeCountryCode(addr.country)
    }

    // Address metadata
    contactData.billing_address_source = 'kajabi'
    contactData.billing_address_verified = false
    contactData.billing_address_updated_at = new Date().toISOString()

    console.log(`📍 Captured billing address from Kajabi for ${email}`)
  }

  // AUDIT LOGGING: Set context for name change tracking
  // This will be captured by the log_contact_name_change() trigger
  try {
    await supabase.rpc('execute_sql', {
      sql: `SELECT set_config('app.change_source', 'kajabi_webhook', false), set_config('app.change_context', 'kajabi_id:${data.id}', false)`
    })
    console.log(`🔍 Audit context set for contact ${email}`)
  } catch (auditError) {
    // Non-fatal: continue even if audit context fails
    console.warn('⚠️ Failed to set audit context:', auditError)
  }

  // Upsert contact
  const { data: result, error } = await supabase
    .from('contacts')
    .upsert(contactData, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()

  if (error) throw error
  return { message: 'Contact processed', data: result }
}

// Handle subscription events
async function handleSubscription(supabase: any, data: any) {
  console.log('Processing subscription:', data.id)

  // Find contact by email
  const email = validateEmail(data.email || data.member?.email)
  if (!email) {
    throw new Error('Invalid email in subscription data')
  }

  const { data: contact } = await supabase
    .from('contacts')
    .select('id')
    .eq('email', email)
    .single()

  if (!contact) {
    throw new Error(`Contact not found for email: ${email}`)
  }

  // Create or update subscription
  const subscriptionData: any = {
    contact_id: contact.id,
    kajabi_subscription_id: sanitizeString(data.id || data.subscription_id),
    status: sanitizeString(data.status || 'active'),
    amount: validateAmount(data.amount),
    currency: sanitizeString(data.currency || 'USD').substring(0, 3).toUpperCase(),
    billing_cycle: sanitizeString(data.billing_cycle).substring(0, 50),
    start_date: data.start_date,
    next_billing_date: data.next_billing_date || data.end_date,
    updated_at: new Date().toISOString()
  }

  // Handle cancellation
  if (data.status === 'canceled' || data.status === 'cancelled') {
    subscriptionData.cancellation_date = new Date().toISOString()
  }

  const { data: result, error } = await supabase
    .from('subscriptions')
    .upsert(subscriptionData, {
      onConflict: 'kajabi_subscription_id',
      ignoreDuplicates: false
    })
    .select()

  if (error) throw error
  return { message: 'Subscription processed', data: result }
}

// Handle tag added events
async function handleTagAdded(supabase: any, data: any) {
  console.log('Processing tag added')

  // Find contact by email
  const email = validateEmail(data.email || data.contact_email)
  if (!email) {
    throw new Error('Invalid email in tag data')
  }

  // Find or create contact - always upsert to update timestamp
  const contactData = {
    email: email,
    first_name: sanitizeString(data.first_name).substring(0, 100),
    last_name: sanitizeString(data.last_name).substring(0, 100),
    kajabi_id: sanitizeString(data.contact_id),
    source_system: 'kajabi',
    email_subscribed: true,
    updated_at: new Date().toISOString()
  }

  const { data: contact } = await supabase
    .from('contacts')
    .upsert(contactData, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()
    .single()

  if (!contact) {
    throw new Error('Failed to create/find contact')
  }

  // Find or create tag
  const tagName = sanitizeString(data.tag_name || data.name).substring(0, 100)
  if (!tagName) {
    throw new Error('No tag name provided')
  }

  let { data: tag } = await supabase
    .from('tags')
    .select('id')
    .eq('name', tagName)
    .single()

  if (!tag) {
    const { data: createdTag } = await supabase
      .from('tags')
      .insert({
        name: tagName,
        category: 'general',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
      .select()
      .single()

    tag = createdTag
  }

  if (!tag) {
    throw new Error('Failed to create/find tag')
  }

  // Create contact-tag relationship
  const contactTagData = {
    contact_id: contact.id,
    tag_id: tag.id,
    created_at: new Date().toISOString()
  }

  const { data: result, error } = await supabase
    .from('contact_tags')
    .upsert(contactTagData, {
      onConflict: 'contact_id,tag_id',
      ignoreDuplicates: true
    })
    .select()

  if (error && !error.message.includes('duplicate')) {
    throw error
  }

  return { message: 'Tag added to contact', data: result }
}

// Handle tag removed events
async function handleTagRemoved(supabase: any, data: any) {
  console.log('Processing tag removed')

  const tagName = sanitizeString(data.tag_name || data.name).substring(0, 100)

  if (!tagName) {
    throw new Error('Tag name missing/invalid')
  }

  // Find contact by email OR kajabi_id (supports both Zapier formats)
  const email = validateEmail(data.email || data.contact_email)
  const kajabiId = sanitizeString(data.contact_id || '')

  let contact = null

  // Try to find contact by kajabi_id first (from Zapier Tag Removed trigger)
  if (kajabiId) {
    console.log(`Looking up contact by kajabi_id: ${kajabiId}`)
    const { data: foundContact } = await supabase
      .from('contacts')
      .select('id')
      .eq('kajabi_id', kajabiId)
      .single()

    contact = foundContact
  }

  // Fallback to email if kajabi_id lookup failed
  if (!contact && email) {
    console.log(`Looking up contact by email: ${email}`)
    const { data: foundContact } = await supabase
      .from('contacts')
      .select('id')
      .eq('email', email)
      .single()

    contact = foundContact
  }

  if (!contact) {
    return { message: 'Contact not found, nothing to remove', kajabi_id: kajabiId, email: email }
  }

  // Find tag
  const { data: tag } = await supabase
    .from('tags')
    .select('id')
    .eq('name', tagName)
    .single()

  if (!tag) {
    return { message: 'Tag not found, nothing to remove', tag_name: tagName }
  }

  // Delete contact-tag relationship
  const { data: result, error } = await supabase
    .from('contact_tags')
    .delete()
    .eq('contact_id', contact.id)
    .eq('tag_id', tag.id)
    .select()

  if (error) throw error

  return { message: 'Tag removed from contact', data: result }
}

// Handle email unsubscribe events
async function handleEmailUnsubscribe(supabase: any, data: any) {
  console.log('Processing email unsubscribe')

  const email = validateEmail(data.email || data.contact_email)

  if (!email) {
    throw new Error('Invalid email in unsubscribe data')
  }

  // Update contact email_subscribed status
  const { data: result, error } = await supabase
    .from('contacts')
    .update({
      email_subscribed: false,
      updated_at: new Date().toISOString()
    })
    .eq('email', email)
    .select()

  if (error) throw error

  return { message: 'Contact unsubscribed from email', data: result }
}
