// PayPal Webhook Receiver - Supabase Edge Function (SECURED)
// Handles real-time events from PayPal
// Supported: payments, subscriptions, refunds
// Security: PayPal signature verification, rate limiting, input validation

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts"
import { logToDLQ, categorizeError } from '../_shared/error-handling.ts'

// Restricted CORS - only allow PayPal's webhook IPs
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://www.paypal.com',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, paypal-transmission-id, paypal-transmission-time, paypal-transmission-sig, paypal-cert-url, paypal-auth-algo',
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

    // Clean up old rate limit entries
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

    // CRITICAL: Verify webhook signature from PayPal
    const webhookId = Deno.env.get('PAYPAL_WEBHOOK_ID')

    if (!webhookId) {
      console.error('PAYPAL_WEBHOOK_ID not configured')
      return new Response(
        JSON.stringify({ error: 'Webhook not configured' }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    // Extract PayPal signature headers
    const transmissionId = req.headers.get('paypal-transmission-id')
    const transmissionTime = req.headers.get('paypal-transmission-time')
    const transmissionSig = req.headers.get('paypal-transmission-sig')
    const certUrl = req.headers.get('paypal-cert-url')
    const authAlgo = req.headers.get('paypal-auth-algo')

    // Verify all required headers are present
    if (!transmissionId || !transmissionTime || !transmissionSig || !certUrl || !authAlgo) {
      console.error('Missing PayPal signature headers')
      return new Response(
        JSON.stringify({ error: 'Unauthorized - missing signature headers' }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 401
        }
      )
    }

    // CRITICAL: Verify signature using PayPal API - REJECT if invalid
    console.log('Verifying PayPal webhook signature...')
    const isValid = await verifyPayPalSignature(
      rawBody,
      transmissionId,
      transmissionTime,
      transmissionSig,
      certUrl,
      authAlgo,
      webhookId
    )

    if (!isValid) {
      console.error('❌ PayPal webhook signature verification FAILED')
      console.error('Transmission ID:', transmissionId)
      console.error('Transmission Time:', transmissionTime)
      return new Response(
        JSON.stringify({
          error: 'Unauthorized - invalid signature',
          code: 'INVALID_SIGNATURE'
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 401
        }
      )
    }

    // ✅ Signature verified successfully
    console.log('✅ PayPal webhook signature verified successfully')

    // Parse payload after verification
    const payload = JSON.parse(rawBody)
    console.log('Verified PayPal webhook:', payload.event_type)

    // Input validation
    if (!payload || typeof payload !== 'object' || !payload.event_type) {
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

    // Extract event type
    const eventType = sanitizeString(payload.event_type)

    // Calculate payload hash for duplicate detection
    const encoder = new TextEncoder()
    const payloadData = encoder.encode(rawBody)
    const hashBuffer = await crypto.subtle.digest('SHA-256', payloadData)
    const payloadHash = Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')

    // Use PayPal's transmission ID as webhook ID (guaranteed unique)
    const webhookId = transmissionId

    // Log incoming webhook event to webhook_events table
    try {
      const { data: eventLog, error: eventLogError } = await supabaseClient
        .from('webhook_events')
        .insert({
          webhook_id: webhookId,
          source: 'paypal',
          event_type: eventType,
          status: 'processing',
          payload_hash: payloadHash,
          payload_size: rawBody.length,
          ip_address: req.headers.get('x-forwarded-for') || 'unknown',
          user_agent: req.headers.get('user-agent')?.substring(0, 255),
          signature_valid: true, // Already verified at this point
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
      // Payment completed events
      case 'PAYMENT.SALE.COMPLETED':
      case 'PAYMENT.CAPTURE.COMPLETED':
        result = await handlePaymentCompleted(supabaseClient, payload)
        break

      // Subscription events
      case 'BILLING.SUBSCRIPTION.CREATED':
        result = await handleSubscriptionCreated(supabaseClient, payload)
        break

      case 'BILLING.SUBSCRIPTION.UPDATED':
      case 'BILLING.SUBSCRIPTION.ACTIVATED':
        result = await handleSubscriptionUpdated(supabaseClient, payload)
        break

      case 'BILLING.SUBSCRIPTION.CANCELLED':
      case 'BILLING.SUBSCRIPTION.SUSPENDED':
      case 'BILLING.SUBSCRIPTION.EXPIRED':
        result = await handleSubscriptionCancelled(supabaseClient, payload)
        break

      // Refund events
      case 'PAYMENT.SALE.REFUNDED':
      case 'PAYMENT.CAPTURE.REFUNDED':
        result = await handleRefund(supabaseClient, payload)
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

    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    try {
      let payload
      let eventType = 'unknown'

      try {
        payload = JSON.parse(rawBody)
        eventType = payload.event_type || 'unknown'
      } catch (parseError) {
        console.log('Failed to parse rawBody for DLQ, storing raw data')
        payload = {
          _raw: rawBody.slice(0, 1000),
          _parseError: String(parseError).slice(0, 200)
        }
        eventType = 'parse_error'
      }

      errorInfo = await logToDLQ(
        supabaseClient,
        'paypal',
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

// SECURITY: Verify PayPal webhook signature using PayPal API
async function verifyPayPalSignature(
  rawBody: string,
  transmissionId: string,
  transmissionTime: string,
  transmissionSig: string,
  certUrl: string,
  authAlgo: string,
  webhookId: string
): Promise<boolean> {
  try {
    // Get PayPal access token
    const clientId = Deno.env.get('PAYPAL_CLIENT_ID')
    const clientSecret = Deno.env.get('PAYPAL_CLIENT_SECRET')
    const paypalEnv = Deno.env.get('PAYPAL_ENV') || 'sandbox' // 'sandbox' or 'live'

    if (!clientId || !clientSecret) {
      console.error('PayPal credentials not configured')
      return false
    }

    const baseUrl = paypalEnv === 'live'
      ? 'https://api-m.paypal.com'
      : 'https://api-m.sandbox.paypal.com'

    // Get access token
    const authResponse = await fetch(`${baseUrl}/v1/oauth2/token`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${btoa(`${clientId}:${clientSecret}`)}`
      },
      body: 'grant_type=client_credentials'
    })

    if (!authResponse.ok) {
      console.error('Failed to get PayPal access token')
      return false
    }

    const authData = await authResponse.json()
    const accessToken = authData.access_token

    // Verify webhook signature
    const verifyResponse = await fetch(`${baseUrl}/v1/notifications/verify-webhook-signature`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        transmission_id: transmissionId,
        transmission_time: transmissionTime,
        cert_url: certUrl,
        auth_algo: authAlgo,
        transmission_sig: transmissionSig,
        webhook_id: webhookId,
        webhook_event: JSON.parse(rawBody)
      })
    })

    if (!verifyResponse.ok) {
      console.error('PayPal signature verification failed')
      return false
    }

    const verifyData = await verifyResponse.json()
    return verifyData.verification_status === 'SUCCESS'

  } catch (error) {
    console.error('PayPal signature verification error:', error)
    return false
  }
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

// Extract payer email from various payload structures
function getPayerEmail(payload: any): string | null {
  const rawEmail = payload.resource?.payer?.email_address ||
                   payload.resource?.subscriber?.email_address ||
                   payload.resource?.payer_email ||
                   null

  return validateEmail(rawEmail)
}

// Extract payer name from payload
function getPayerName(payload: any): { first_name: string; last_name: string } {
  const payer = payload.resource?.payer || payload.resource?.subscriber || {}
  const name = payer.name || {}

  return {
    first_name: sanitizeString(name.given_name || payer.first_name || '').substring(0, 100),
    last_name: sanitizeString(name.surname || payer.last_name || '').substring(0, 100)
  }
}

// Extract Kajabi identifiers from PayPal custom fields (if available)
function extractKajabiIds(resource: any): {
  kajabi_transaction_id?: string;
  kajabi_member_id?: string;
  kajabi_offer_id?: string;
} {
  const result: any = {}

  // Check various custom field locations where Kajabi might pass IDs
  const customFields = [
    resource.custom,
    resource.custom_id,
    resource.invoice_id,
    resource.purchase_units?.[0]?.custom_id,
    resource.purchase_units?.[0]?.reference_id,
    resource.purchase_units?.[0]?.invoice_id
  ]

  for (const field of customFields) {
    if (field && typeof field === 'string') {
      // Check if field contains Kajabi transaction ID pattern (UUID)
      const uuidMatch = field.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i)
      if (uuidMatch && !result.kajabi_transaction_id) {
        result.kajabi_transaction_id = uuidMatch[0]
        console.log(`✅ Found Kajabi transaction ID in PayPal custom fields: ${result.kajabi_transaction_id}`)
      }

      // Check for member ID pattern (usually numeric)
      const memberMatch = field.match(/member[_-]?id[:\s=]+(\d+)/i) || field.match(/kajabi[_-]?member[:\s=]+(\d+)/i)
      if (memberMatch && !result.kajabi_member_id) {
        result.kajabi_member_id = memberMatch[1]
        console.log(`✅ Found Kajabi member ID in PayPal custom fields: ${result.kajabi_member_id}`)
      }

      // Check for offer ID
      const offerMatch = field.match(/offer[_-]?id[:\s=]+(\d+)/i)
      if (offerMatch && !result.kajabi_offer_id) {
        result.kajabi_offer_id = offerMatch[1]
        console.log(`✅ Found Kajabi offer ID in PayPal custom fields: ${result.kajabi_offer_id}`)
      }
    }
  }

  return result
}

// Standardize country code to ISO 3166-1 alpha-2
function standardizeCountryCode(country: string): string {
  if (!country) return ''

  const countryUpper = country.toUpperCase().trim()

  const countryMap: Record<string, string> = {
    'UNITED STATES': 'US', 'UNITED STATES OF AMERICA': 'US', 'USA': 'US',
    'CANADA': 'CA', 'UNITED KINGDOM': 'GB', 'UK': 'GB', 'GREAT BRITAIN': 'GB',
    'AUSTRALIA': 'AU', 'NEW ZEALAND': 'NZ', 'FRANCE': 'FR', 'GERMANY': 'DE',
    'SPAIN': 'ES', 'ITALY': 'IT', 'NETHERLANDS': 'NL', 'MEXICO': 'MX',
    'BRAZIL': 'BR', 'CHINA': 'CN', 'JAPAN': 'JP', 'INDIA': 'IN',
    'SOUTH KOREA': 'KR', 'ISRAEL': 'IL', 'SOUTH AFRICA': 'ZA',
    'TAIWAN': 'TW', 'HONG KONG': 'HK', 'SINGAPORE': 'SG',
    'THAILAND': 'TH', 'PHILIPPINES': 'PH', 'INDONESIA': 'ID',
    'MALAYSIA': 'MY', 'VIETNAM': 'VN', 'DENMARK': 'DK',
    'SWEDEN': 'SE', 'NORWAY': 'NO', 'FINLAND': 'FI',
    'IRELAND': 'IE', 'POLAND': 'PL', 'ROMANIA': 'RO', 'COSTA RICA': 'CR'
  }

  if (countryMap[countryUpper]) return countryMap[countryUpper]
  if (countryUpper.length === 2) return countryUpper
  return countryUpper.substring(0, 2)
}

// Extract phone from PayPal payload
function extractPayPalPhone(payload: any): string | null {
  const resource = payload.resource || {}
  const payer = resource.payer || resource.subscriber || {}

  const phone = payer.phone?.phone_number?.national_number ||
                payer.phone_number ||
                resource.purchase_units?.[0]?.shipping?.phone_number ||
                null

  if (!phone) return null

  const sanitized = String(phone).trim().replace(/[^\d+\-\(\)\s]/g, '').substring(0, 20)
  const digitsOnly = sanitized.replace(/\D/g, '')

  return digitsOnly.length >= 10 ? sanitized : null
}

// Extract shipping address from PayPal payload
function extractShippingAddress(payload: any): any | null {
  const resource = payload.resource || {}
  const shipping = resource.purchase_units?.[0]?.shipping ||
                   resource.shipping_info ||
                   resource.shipping_address ||
                   null

  if (!shipping || !shipping.address) return null

  const addr = shipping.address

  if (!addr.address_line_1 && !addr.line1) return null

  return {
    line1: sanitizeString(addr.address_line_1 || addr.line1 || '').substring(0, 255),
    line2: sanitizeString(addr.address_line_2 || addr.line2 || '').substring(0, 255),
    city: sanitizeString(addr.admin_area_2 || addr.city || '').substring(0, 100),
    state: sanitizeString(addr.admin_area_1 || addr.state || '').substring(0, 100),
    postal_code: sanitizeString(addr.postal_code || '').substring(0, 20),
    country: addr.country_code || addr.country || ''
  }
}

// Find or create contact (with smart duplicate prevention)
async function findOrCreateContact(supabase: any, payload: any): Promise<any> {
  const paypalEmail = getPayerEmail(payload)
  const { first_name, last_name } = getPayerName(payload)

  // Extract phone and shipping address
  const paypalPhone = extractPayPalPhone(payload)
  const shippingAddress = extractShippingAddress(payload)

  // Check if PayPal custom fields contain Kajabi IDs
  const kajabiIds = extractKajabiIds(payload.resource)

  // PRIORITY 1: If Kajabi member ID found in PayPal, use it to find contact
  if (kajabiIds.kajabi_member_id) {
    const { data: contactByMemberId } = await supabase
      .from('contacts')
      .select('id, email, paypal_email')
      .eq('kajabi_member_id', kajabiIds.kajabi_member_id)
      .single()

    if (contactByMemberId) {
      console.log(`✅ Found contact by Kajabi member ID from PayPal: ${contactByMemberId.id}`)

      // Build updates object
      const updates: any = { updated_at: new Date().toISOString() }

      // Update PayPal email if not already set
      if (!contactByMemberId.paypal_email && paypalEmail) {
        updates.paypal_email = paypalEmail
        updates.paypal_first_name = first_name
        updates.paypal_last_name = last_name
      }

      // Add phone if available
      if (paypalPhone) {
        updates.paypal_phone = paypalPhone
        updates.phone_source = 'paypal'
        updates.phone_verified = false
        console.log(`📱 Adding PayPal phone: ${paypalPhone}`)
      }

      // Add shipping address if available (PayPal verified!)
      if (shippingAddress) {
        updates.shipping_address_line_1 = shippingAddress.line1
        updates.shipping_address_line_2 = shippingAddress.line2
        updates.shipping_city = shippingAddress.city
        updates.shipping_state = shippingAddress.state
        updates.shipping_postal_code = shippingAddress.postal_code
        updates.shipping_country = standardizeCountryCode(shippingAddress.country)
        updates.shipping_address_source = 'paypal'
        updates.shipping_address_verified = true  // PayPal verified!
        updates.shipping_address_updated_at = new Date().toISOString()
        console.log(`📦 Adding verified shipping address from PayPal`)
      }

      await supabase
        .from('contacts')
        .update(updates)
        .eq('id', contactByMemberId.id)

      console.log(`✅ Updated contact ${contactByMemberId.id} with PayPal data`)
      return contactByMemberId
    }
  }

  if (!paypalEmail) {
    console.warn('⚠️ No email found in PayPal payload - using test contact')

    // For simulator events without email, use/create a test contact
    const testEmail = 'paypal-test@simulator.paypal.com'

    let { data: testContact, error: selectError } = await supabase
      .from('contacts')
      .select('id')
      .eq('email', testEmail)
      .single()

    if (selectError && selectError.code !== 'PGRST116') {
      console.error('Error finding test contact:', selectError)
    }

    if (!testContact) {
      console.log('Creating test contact...')
      const { data: createdContact, error: insertError } = await supabase
        .from('contacts')
        .insert({
          email: testEmail,
          first_name: 'PayPal',
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
      console.log('✅ Test contact created:', testContact.id)
    } else {
      console.log('✅ Using existing test contact:', testContact.id)
    }

    return testContact
  }

  // STEP 1: Try to find by PayPal email (in paypal_email field)
  let { data: contact } = await supabase
    .from('contacts')
    .select('id, email, paypal_email')
    .eq('paypal_email', paypalEmail)
    .single()

  if (contact) {
    console.log(`✅ Found existing contact by PayPal email: ${contact.id}`)
    return contact
  }

  // STEP 2: Try to find by primary email
  const { data: contactByEmail } = await supabase
    .from('contacts')
    .select('id, email, paypal_email')
    .eq('email', paypalEmail)
    .single()

  if (contactByEmail) {
    console.log(`✅ Found existing contact by primary email: ${contactByEmail.id}`)

    // Build updates object
    const updates: any = { updated_at: new Date().toISOString() }

    // Update PayPal fields if not already set
    if (!contactByEmail.paypal_email) {
      updates.paypal_email = paypalEmail
      updates.paypal_first_name = first_name
      updates.paypal_last_name = last_name
    }

    // Add phone if available
    if (paypalPhone) {
      updates.paypal_phone = paypalPhone
      updates.phone_source = 'paypal'
      updates.phone_verified = false
    }

    // Add shipping address if available (PayPal verified!)
    if (shippingAddress) {
      updates.shipping_address_line_1 = shippingAddress.line1
      updates.shipping_address_line_2 = shippingAddress.line2
      updates.shipping_city = shippingAddress.city
      updates.shipping_state = shippingAddress.state
      updates.shipping_postal_code = shippingAddress.postal_code
      updates.shipping_country = standardizeCountryCode(shippingAddress.country)
      updates.shipping_address_source = 'paypal'
      updates.shipping_address_verified = true
      updates.shipping_address_updated_at = new Date().toISOString()
    }

    await supabase
      .from('contacts')
      .update(updates)
      .eq('id', contactByEmail.id)

    console.log(`✅ Updated contact ${contactByEmail.id} with PayPal data`)
    return contactByEmail
  }

  // STEP 3: Try to find by name match (prevents Kajabi/PayPal duplicates)
  if (first_name && last_name) {
    const { data: contactByName } = await supabase
      .from('contacts')
      .select('id, email, paypal_email, first_name, last_name')
      .ilike('first_name', first_name)
      .ilike('last_name', last_name)
      .single()

    if (contactByName) {
      console.log(`✅ Found existing contact by name match: ${contactByName.id}`)
      console.log(`   Primary email: ${contactByName.email}, PayPal email: ${paypalEmail}`)

      // Build updates object
      const updates: any = {
        paypal_email: paypalEmail,
        paypal_first_name: first_name,
        paypal_last_name: last_name,
        updated_at: new Date().toISOString()
      }

      // Add phone if available
      if (paypalPhone) {
        updates.paypal_phone = paypalPhone
        updates.phone_source = 'paypal'
        updates.phone_verified = false
      }

      // Add shipping address if available (PayPal verified!)
      if (shippingAddress) {
        updates.shipping_address_line_1 = shippingAddress.line1
        updates.shipping_address_line_2 = shippingAddress.line2
        updates.shipping_city = shippingAddress.city
        updates.shipping_state = shippingAddress.state
        updates.shipping_postal_code = shippingAddress.postal_code
        updates.shipping_country = standardizeCountryCode(shippingAddress.country)
        updates.shipping_address_source = 'paypal'
        updates.shipping_address_verified = true
        updates.shipping_address_updated_at = new Date().toISOString()
      }

      await supabase
        .from('contacts')
        .update(updates)
        .eq('id', contactByName.id)

      console.log(`✅ Updated contact ${contactByName.id} with PayPal data`)
      return contactByName
    }
  }

  // STEP 4: No match found - create new contact
  console.log(`📝 Creating new contact for PayPal email: ${paypalEmail}`)

  const newContact: any = {
    email: paypalEmail,
    first_name: first_name,
    last_name: last_name,
    paypal_email: paypalEmail,
    paypal_first_name: first_name,
    paypal_last_name: last_name,
    source_system: 'manual',
    email_subscribed: true,
    updated_at: new Date().toISOString()
  }

  // Add phone if available
  if (paypalPhone) {
    newContact.paypal_phone = paypalPhone
    newContact.phone_source = 'paypal'
    newContact.phone_verified = false
    console.log(`📱 Adding PayPal phone: ${paypalPhone}`)
  }

  // Add shipping address if available (PayPal verified!)
  if (shippingAddress) {
    newContact.shipping_address_line_1 = shippingAddress.line1
    newContact.shipping_address_line_2 = shippingAddress.line2
    newContact.shipping_city = shippingAddress.city
    newContact.shipping_state = shippingAddress.state
    newContact.shipping_postal_code = shippingAddress.postal_code
    newContact.shipping_country = standardizeCountryCode(shippingAddress.country)
    newContact.shipping_address_source = 'paypal'
    newContact.shipping_address_verified = true  // PayPal verified!
    newContact.shipping_address_updated_at = new Date().toISOString()
    console.log(`📦 Adding verified shipping address from PayPal`)
  }

  const { data: createdContact } = await supabase
    .from('contacts')
    .upsert(newContact, {
      onConflict: 'email',
      ignoreDuplicates: false
    })
    .select()
    .single()

  if (!createdContact) {
    throw new Error('Failed to create contact')
  }

  console.log(`✅ New contact created: ${createdContact.id}`)
  return createdContact
}

// Determine transaction type based on item description or amount
function determineTransactionType(resource: any): 'purchase' | 'subscription' {
  // Check if it's a subscription payment
  if (resource.billing_agreement_id || resource.plan_id) {
    return 'subscription'
  }

  // Default to purchase
  return 'purchase'
}

// Handle payment completed
async function handlePaymentCompleted(supabase: any, payload: any) {
  console.log('Processing payment completed:', payload.resource?.id)

  const resource = payload.resource

  // Log custom fields that might contain Kajabi IDs
  console.log('🔍 PayPal Custom Fields Check:', JSON.stringify({
    invoice_id: resource.invoice_id,
    custom: resource.custom,
    custom_id: resource.custom_id,
    reference_id: resource.reference_id,
    purchase_units: resource.purchase_units?.map((unit: any) => ({
      reference_id: unit.reference_id,
      custom_id: unit.custom_id,
      invoice_id: unit.invoice_id,
      description: unit.description
    })),
    supplementary_data: resource.supplementary_data
  }, null, 2))

  const contact = await findOrCreateContact(supabase, payload)

  // Extract Kajabi IDs from PayPal custom fields
  const kajabiIds = extractKajabiIds(resource)

  // Validate and extract amount
  const amount = validateAmount(resource.amount?.total || resource.amount?.value)
  if (amount === null) {
    throw new Error('Invalid payment amount')
  }

  const paypalId = sanitizeString(resource.id)
  const transactionDate = resource.create_time || resource.update_time || new Date().toISOString()

  // Strategy: Try to merge with existing Kajabi transaction if possible
  let existingTransaction = null
  let mergeStrategy = 'new_paypal_transaction'

  // 1. Check if Kajabi passed its transaction ID in custom fields
  if (kajabiIds.kajabi_transaction_id) {
    console.log(`🔗 Found Kajabi transaction ID in PayPal custom fields: ${kajabiIds.kajabi_transaction_id}`)

    // Look for existing Kajabi transaction with this ID
    const { data: kajabiTxn } = await supabase
      .from('transactions')
      .select('*')
      .eq('source_system', 'kajabi')
      .eq('external_transaction_id', kajabiIds.kajabi_transaction_id)
      .single()

    if (kajabiTxn) {
      console.log(`✅ Found existing Kajabi transaction - will merge PayPal data into it`)
      existingTransaction = kajabiTxn
      mergeStrategy = 'merge_with_kajabi'
    }
  }

  // 2. If no Kajabi ID or no match, check for probable duplicate (same contact, amount, time window)
  if (!existingTransaction) {
    const { data: probableDupe } = await supabase.rpc('find_probable_duplicate_transaction', {
      p_contact_id: contact.id,
      p_amount: amount,
      p_transaction_date: transactionDate,
      p_source_system: 'paypal',
      p_window_minutes: 10
    })

    if (probableDupe) {
      console.log(`⚠️ Found probable duplicate transaction from ${probableDupe.source_system} - will merge`)
      existingTransaction = probableDupe
      mergeStrategy = 'probable_merge'
    }
  }

  // 3. Build transaction data
  const transaction: any = {
    source_system: existingTransaction ? existingTransaction.source_system : 'paypal', // Preserve original source if merging
    external_transaction_id: existingTransaction ? existingTransaction.external_transaction_id : paypalId, // Keep original external ID if merging
    external_order_id: paypalId, // Always store PayPal ID as reference
    kajabi_transaction_id: kajabiIds.kajabi_transaction_id || paypalId, // DEPRECATED: Legacy field
    order_number: paypalId, // PayPal transaction ID
    contact_id: contact.id,
    transaction_type: determineTransactionType(resource),
    status: 'completed',
    amount: amount,
    currency: sanitizeString(resource.amount?.currency || 'USD').substring(0, 3).toUpperCase(),
    payment_method: 'paypal',
    payment_processor: 'PayPal',
    transaction_date: transactionDate,
    created_at: existingTransaction ? existingTransaction.created_at : new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  // 4. If merging, update existing transaction; otherwise insert new
  let result
  let error

  if (existingTransaction) {
    // Update existing transaction with PayPal data
    console.log(`🔄 Updating existing ${existingTransaction.source_system} transaction ${existingTransaction.id}`)
    const update = await supabase
      .from('transactions')
      .update({
        external_order_id: transaction.external_order_id,
        payment_method: 'paypal', // PayPal processed the payment
        payment_processor: 'PayPal',
        updated_at: transaction.updated_at
      })
      .eq('id', existingTransaction.id)
      .select()

    result = update.data
    error = update.error
  } else {
    // Insert new PayPal transaction
    console.log(`➕ Creating new PayPal transaction: ${paypalId}`)
    const insert = await supabase
      .from('transactions')
      .upsert(transaction, {
        onConflict: 'source_system,external_transaction_id',
        ignoreDuplicates: false
      })
      .select()

    result = insert.data
    error = insert.error
  }

  if (error) throw error

  return {
    message: mergeStrategy === 'merge_with_kajabi'
      ? 'Merged with existing Kajabi transaction'
      : mergeStrategy === 'probable_merge'
      ? 'Merged with probable duplicate'
      : 'New PayPal transaction created',
    merge_strategy: mergeStrategy,
    contact_id: contact.id,
    transaction: result
  }
}

// Handle subscription created
async function handleSubscriptionCreated(supabase: any, payload: any) {
  console.log('Processing subscription created:', payload.resource?.id)

  const resource = payload.resource
  const contact = await findOrCreateContact(supabase, payload)

  // Validate amount
  const amount = validateAmount(resource.billing_info?.last_payment?.amount?.value)

  // Create subscription record
  const subscription: any = {
    contact_id: contact.id,
    kajabi_subscription_id: sanitizeString(resource.id),
    status: sanitizeString(resource.status?.toLowerCase() || 'active'),
    amount: amount,
    currency: sanitizeString(resource.billing_info?.last_payment?.amount?.currency_code || 'USD').substring(0, 3).toUpperCase(),
    billing_cycle: sanitizeString(resource.plan?.billing_cycles?.[0]?.frequency?.interval_unit?.toLowerCase() || 'Month').substring(0, 50),
    start_date: resource.start_time || resource.create_time || new Date().toISOString(),
    next_billing_date: resource.billing_info?.next_billing_time,
    payment_processor: 'PayPal',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  const { data: result, error } = await supabase
    .from('subscriptions')
    .upsert(subscription, {
      onConflict: 'kajabi_subscription_id',
      ignoreDuplicates: false
    })
    .select()

  if (error) throw error

  return {
    message: 'Subscription created',
    contact_id: contact.id,
    subscription: result
  }
}

// Handle subscription updated
async function handleSubscriptionUpdated(supabase: any, payload: any) {
  console.log('Processing subscription updated:', payload.resource?.id)

  const resource = payload.resource

  const { data: result, error } = await supabase
    .from('subscriptions')
    .update({
      status: sanitizeString(resource.status?.toLowerCase() || 'active'),
      next_billing_date: resource.billing_info?.next_billing_time,
      updated_at: new Date().toISOString()
    })
    .eq('kajabi_subscription_id', sanitizeString(resource.id))
    .select()

  if (error) throw error

  return {
    message: 'Subscription updated',
    subscription: result
  }
}

// Handle subscription cancelled
async function handleSubscriptionCancelled(supabase: any, payload: any) {
  console.log('Processing subscription cancelled:', payload.resource?.id)

  const resource = payload.resource

  const { data: result, error } = await supabase
    .from('subscriptions')
    .update({
      status: 'canceled',
      cancellation_date: new Date().toISOString(),
      updated_at: new Date().toISOString()
    })
    .eq('kajabi_subscription_id', sanitizeString(resource.id))
    .select()

  if (error) throw error

  return {
    message: 'Subscription cancelled',
    subscription: result
  }
}

// Handle refund
async function handleRefund(supabase: any, payload: any) {
  console.log('Processing refund:', payload.resource?.id)

  const resource = payload.resource
  const saleId = sanitizeString(resource.sale_id || resource.parent_payment || '')

  if (!saleId) {
    console.error('No sale ID found in refund payload')
    return { message: 'Refund processed but original transaction not found' }
  }

  // Update original transaction
  const { data: result, error } = await supabase
    .from('transactions')
    .update({
      status: 'refunded',
      updated_at: new Date().toISOString()
    })
    .eq('kajabi_transaction_id', saleId)
    .select()

  if (error) {
    console.error('Transaction not found for refund:', saleId, error)
    // Don't throw - just log it
  }

  return {
    message: 'Refund processed',
    transaction: result
  }
}
