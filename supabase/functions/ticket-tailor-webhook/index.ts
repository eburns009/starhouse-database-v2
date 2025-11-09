// Ticket Tailor Webhook Receiver - Supabase Edge Function (SECURED)
// Handles real-time events from Ticket Tailor
// Supported events: order.completed, order.refunded, order.cancelled
// Security: Signature verification, rate limiting, input validation

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts"
import { logToDLQ, categorizeError } from '../_shared/error-handling.ts'

// Restricted CORS - only allow Ticket Tailor
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://www.tickettailor.com',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, tickettailor-webhook-signature',
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

    // SECURITY: Verify webhook signature from Ticket Tailor
    const signature = req.headers.get('tickettailor-webhook-signature')
    const webhookSecret = Deno.env.get('TICKET_TAILOR_WEBHOOK_SECRET')

    // CRITICAL: Webhook secret MUST be configured
    if (!webhookSecret) {
      console.error('❌ TICKET_TAILOR_WEBHOOK_SECRET not configured')
      return new Response(
        JSON.stringify({
          error: 'Webhook not configured',
          code: 'WEBHOOK_CONFIG_ERROR'
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 500
        }
      )
    }

    // CRITICAL: Signature verification is REQUIRED
    if (!signature) {
      console.error('❌ Missing Tickettailor-Webhook-Signature header')
      return new Response(
        JSON.stringify({
          error: 'Unauthorized - missing signature',
          code: 'MISSING_SIGNATURE'
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 401
        }
      )
    }

    // CRITICAL: Verify signature - REJECT if invalid
    const isValidSignature = await verifyTicketTailorSignature(rawBody, signature, webhookSecret)
    if (!isValidSignature) {
      console.error('❌ Ticket Tailor webhook signature verification FAILED')
      console.error('Signature:', signature.substring(0, 16) + '...')
      console.error('Body length:', rawBody.length)
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
    console.log('✅ Ticket Tailor webhook signature verified successfully')

    // Parse payload after verification
    const payload = JSON.parse(rawBody)
    console.log('Verified Ticket Tailor webhook:', payload.type || payload.event_type)

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
    const eventType = sanitizeString(payload.type || payload.event_type)
    const data = payload.data || payload

    // Calculate payload hash for duplicate detection
    const encoder = new TextEncoder()
    const payloadData = encoder.encode(rawBody)
    const hashBuffer = await crypto.subtle.digest('SHA-256', payloadData)
    const payloadHash = Array.from(new Uint8Array(hashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')

    // Generate webhook ID (use event ID if available, otherwise generate UUID)
    const webhookId = payload.id || crypto.randomUUID()

    // Log incoming webhook event to webhook_events table
    try {
      const { data: eventLog, error: eventLogError } = await supabaseClient
        .from('webhook_events')
        .insert({
          webhook_id: webhookId,
          source: 'ticket-tailor',
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
      case 'order.completed':
      case 'order.created':
        result = await handleOrderCompleted(supabaseClient, data)
        break

      case 'order.refunded':
        result = await handleOrderRefunded(supabaseClient, data)
        break

      case 'order.cancelled':
        result = await handleOrderCancelled(supabaseClient, data)
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
        eventType = payload.object || payload.event_type || 'unknown'
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
        'ticket-tailor',
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

// SECURITY: Verify Ticket Tailor webhook signature
async function verifyTicketTailorSignature(
  rawBody: string,
  signatureHeader: string,
  secret: string
): Promise<boolean> {
  try {
    // Parse the signature header format: "t=<timestamp>,s=<signature>"
    const parts = signatureHeader.split(',')
    let timestamp = ''
    let signature = ''

    for (const part of parts) {
      const [key, value] = part.split('=')
      if (key === 't') {
        timestamp = value
      } else if (key === 's') {
        signature = value
      }
    }

    if (!timestamp || !signature) {
      console.error('Invalid signature format - missing timestamp or signature')
      return false
    }

    // Validate timestamp is within 5 minutes (300 seconds) to prevent replay attacks
    const webhookTime = parseInt(timestamp, 10)
    const currentTime = Math.floor(Date.now() / 1000)
    const timeDifference = Math.abs(currentTime - webhookTime)

    if (timeDifference > 300) {
      console.error(`Webhook timestamp too old: ${timeDifference} seconds`)
      return false
    }

    // Ticket Tailor uses HMAC-SHA256 with timestamp + body
    const encoder = new TextEncoder()
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )

    // The message is: timestamp + rawBody
    const message = timestamp + rawBody
    const signatureBuffer = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(message)
    )

    const expectedSignature = Array.from(new Uint8Array(signatureBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    const isValid = timingSafeEqual(expectedSignature, signature.toLowerCase())

    if (!isValid) {
      console.error('Signature mismatch')
      console.error('Expected:', expectedSignature.substring(0, 20) + '...')
      console.error('Received:', signature.substring(0, 20) + '...')
    }

    return isValid
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

// SECURITY: Validate and sanitize phone number
function validatePhone(phone: any): string | null {
  if (typeof phone !== 'string') {
    return null
  }

  // Remove all non-numeric characters except + (for international)
  const sanitized = phone.trim().replace(/[^\d+\-\(\)\s]/g, '').substring(0, 20)

  // Basic validation - must have at least 10 digits
  const digitsOnly = sanitized.replace(/\D/g, '')
  if (digitsOnly.length >= 10) {
    return sanitized
  }

  return null
}

// Extract email subscription preference from custom questions
function getEmailSubscriptionPreference(data: any): boolean {
  // Check custom questions for email consent
  const customQuestions = data.custom_questions || data.questions || []

  for (const question of customQuestions) {
    const questionText = (question.question || question.title || '').toLowerCase()
    const answer = (question.answer || question.response || '').toLowerCase()

    // Look for email consent question
    if (questionText.includes('email') || questionText.includes('starhouse')) {
      console.log(`📧 Found email consent question: "${question.question}" = "${question.answer}"`)

      // Check if answer indicates consent
      if (answer === 'yes' || answer === 'true' || answer === '1') {
        return true
      } else if (answer === 'no' || answer === 'false' || answer === '0') {
        return false
      }
    }
  }

  // Default: no consent if question not found or answered
  console.log('⚠️ No email consent question found or answered - defaulting to false')
  return false
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

// Extract billing address from Ticket Tailor payload
function extractBillingAddress(data: any): any | null {
  const billing = data.billing_address || data.address || data.customer?.address || null

  if (!billing) return null

  // Must have at least street address and city
  if (!billing.address_line_1 && !billing.line1 && !billing.street) return null

  return {
    line1: sanitizeString(billing.address_line_1 || billing.line1 || billing.street || '').substring(0, 255),
    line2: sanitizeString(billing.address_line_2 || billing.line2 || '').substring(0, 255),
    city: sanitizeString(billing.city || '').substring(0, 100),
    state: sanitizeString(billing.state || billing.region || '').substring(0, 100),
    postal_code: sanitizeString(billing.postal_code || billing.postcode || billing.zip || '').substring(0, 20),
    country: billing.country || ''
  }
}

// Find or create contact (with smart duplicate prevention)
async function findOrCreateContact(supabase: any, data: any): Promise<any> {
  const email = validateEmail(data.email || data.customer?.email || data.buyer_email)

  if (!email) {
    throw new Error('No valid email found in order data')
  }

  const first_name = sanitizeString(data.first_name || data.customer?.first_name || '').substring(0, 100)
  const last_name = sanitizeString(data.last_name || data.customer?.last_name || '').substring(0, 100)
  const ticket_tailor_id = sanitizeString(data.customer_id || '')

  // Get phone number
  const phone = validatePhone(data.phone || data.customer?.phone || data.phone_number)

  // Get email subscription preference from custom question
  const email_subscribed = getEmailSubscriptionPreference(data)

  // Extract billing address if available
  const billingAddress = extractBillingAddress(data)

  // STEP 1: Try to find by Ticket Tailor ID
  if (ticket_tailor_id) {
    const { data: contactById } = await supabase
      .from('contacts')
      .select('id')
      .eq('ticket_tailor_id', ticket_tailor_id)
      .single()

    if (contactById) {
      console.log(`✅ Found contact by Ticket Tailor ID: ${contactById.id}`)

      // Update email subscription preference, phone, and billing address
      const updates: any = {
        email_subscribed: email_subscribed,
        updated_at: new Date().toISOString()
      }

      if (phone) {
        updates.phone = phone
        updates.phone_source = 'ticket_tailor'
        updates.phone_verified = false
        console.log(`📱 Updating phone: ${phone}`)
      }

      if (billingAddress) {
        updates.address_line_1 = billingAddress.line1
        updates.address_line_2 = billingAddress.line2
        updates.city = billingAddress.city
        updates.state = billingAddress.state
        updates.postal_code = billingAddress.postal_code
        updates.country = standardizeCountryCode(billingAddress.country)
        updates.billing_address_source = 'ticket_tailor'
        updates.billing_address_verified = false
        updates.billing_address_updated_at = new Date().toISOString()
        console.log(`📍 Updating billing address from Ticket Tailor`)
      }

      await supabase
        .from('contacts')
        .update(updates)
        .eq('id', contactById.id)

      console.log(`✅ Updated contact ${contactById.id} email_subscribed: ${email_subscribed}`)
      return contactById
    }
  }

  // STEP 2: Try to find by email
  let { data: contact } = await supabase
    .from('contacts')
    .select('id')
    .eq('email', email)
    .single()

  if (contact) {
    console.log(`✅ Found contact by email: ${contact.id}`)

    // Update Ticket Tailor ID, email subscription preference, phone, and billing address
    const updates: any = {
      ticket_tailor_id: ticket_tailor_id,
      email_subscribed: email_subscribed,
      updated_at: new Date().toISOString()
    }

    if (phone) {
      updates.phone = phone
      updates.phone_source = 'ticket_tailor'
      updates.phone_verified = false
      console.log(`📱 Updating phone: ${phone}`)
    }

    if (billingAddress) {
      updates.address_line_1 = billingAddress.line1
      updates.address_line_2 = billingAddress.line2
      updates.city = billingAddress.city
      updates.state = billingAddress.state
      updates.postal_code = billingAddress.postal_code
      updates.country = standardizeCountryCode(billingAddress.country)
      updates.billing_address_source = 'ticket_tailor'
      updates.billing_address_verified = false
      updates.billing_address_updated_at = new Date().toISOString()
      console.log(`📍 Updating billing address from Ticket Tailor`)
    }

    await supabase
      .from('contacts')
      .update(updates)
      .eq('id', contact.id)

    console.log(`✅ Updated contact ${contact.id} with Ticket Tailor ID and email_subscribed: ${email_subscribed}`)

    return contact
  }

  // STEP 3: Try to find by name match (if names provided)
  if (first_name && last_name) {
    const { data: contactByName } = await supabase
      .from('contacts')
      .select('id, email')
      .ilike('first_name', first_name)
      .ilike('last_name', last_name)
      .single()

    if (contactByName) {
      console.log(`✅ Found contact by name match: ${contactByName.id}`)
      console.log(`   Existing email: ${contactByName.email}, Ticket Tailor email: ${email}`)

      // Update with Ticket Tailor info, email preference, phone, and billing address
      const updates: any = {
        ticket_tailor_id: ticket_tailor_id,
        email_subscribed: email_subscribed,
        updated_at: new Date().toISOString()
      }

      if (phone) {
        updates.phone = phone
        updates.phone_source = 'ticket_tailor'
        updates.phone_verified = false
        console.log(`📱 Updating phone: ${phone}`)
      }

      if (billingAddress) {
        updates.address_line_1 = billingAddress.line1
        updates.address_line_2 = billingAddress.line2
        updates.city = billingAddress.city
        updates.state = billingAddress.state
        updates.postal_code = billingAddress.postal_code
        updates.country = standardizeCountryCode(billingAddress.country)
        updates.billing_address_source = 'ticket_tailor'
        updates.billing_address_verified = false
        updates.billing_address_updated_at = new Date().toISOString()
        console.log(`📍 Updating billing address from Ticket Tailor`)
      }

      await supabase
        .from('contacts')
        .update(updates)
        .eq('id', contactByName.id)

      console.log(`✅ Updated contact ${contactByName.id} with Ticket Tailor details and email_subscribed: ${email_subscribed}`)

      return contactByName
    }
  }

  // STEP 4: Create new contact
  console.log(`📝 Creating new contact for email: ${email} with email_subscribed: ${email_subscribed}${phone ? `, phone: ${phone}` : ''}`)

  const newContact: any = {
    email: email,
    first_name: first_name,
    last_name: last_name,
    ticket_tailor_id: ticket_tailor_id,
    source_system: 'ticket_tailor',
    email_subscribed: email_subscribed,
    updated_at: new Date().toISOString()
  }

  if (phone) {
    newContact.phone = phone
    newContact.phone_source = 'ticket_tailor'
    newContact.phone_verified = false
    console.log(`📱 Adding phone: ${phone}`)
  }

  if (billingAddress) {
    newContact.address_line_1 = billingAddress.line1
    newContact.address_line_2 = billingAddress.line2
    newContact.city = billingAddress.city
    newContact.state = billingAddress.state
    newContact.postal_code = billingAddress.postal_code
    newContact.country = standardizeCountryCode(billingAddress.country)
    newContact.billing_address_source = 'ticket_tailor'
    newContact.billing_address_verified = false
    newContact.billing_address_updated_at = new Date().toISOString()
    console.log(`📍 Adding billing address from Ticket Tailor`)
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

// Handle completed orders (ticket purchases)
async function handleOrderCompleted(supabase: any, data: any) {
  console.log('Processing completed order:', data.id || data.order_id)

  // Log custom questions to see format
  if (data.custom_questions || data.questions) {
    console.log('📋 Custom questions received:', JSON.stringify(data.custom_questions || data.questions, null, 2))
  } else {
    console.log('⚠️ No custom questions found in payload')
  }

  // Find or create contact
  const contact = await findOrCreateContact(supabase, data)

  // Create transaction record for financial tracking
  const totalPaid = validateAmount(data.total || data.amount || data.price)

  if (totalPaid && totalPaid > 0) {
    const bookingId = sanitizeString(data.id || data.order_id || data.booking_id)
    const transaction = {
      contact_id: contact.id,
      source_system: 'ticket_tailor', // Required, no default
      external_transaction_id: bookingId, // Ticket Tailor's booking ID
      external_order_id: sanitizeString(data.order_number || data.reference || ''), // Optional order reference
      kajabi_transaction_id: bookingId, // DEPRECATED: Legacy field, keep for backward compat
      order_number: sanitizeString(data.order_number || data.reference || ''),
      transaction_type: 'purchase' as const,
      status: 'completed',
      amount: totalPaid,
      currency: sanitizeString(data.currency || 'USD').substring(0, 3).toUpperCase(),
      quantity: validateAmount(data.quantity) || 1,
      payment_method: 'ticket_tailor',
      payment_processor: 'Ticket Tailor',
      transaction_date: data.created_at || data.order_date || new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    const { data: transactionResult, error: transactionError} = await supabase
      .from('transactions')
      .upsert(transaction, {
        onConflict: 'source_system,external_transaction_id',
        ignoreDuplicates: false
      })
      .select()

    if (transactionError) {
      console.error('Failed to create transaction:', transactionError)
      throw transactionError
    } else {
      console.log(`✅ Created transaction record for $${totalPaid} ${transaction.currency}`)
    }
  }

  return {
    message: 'Order processed successfully',
    contact_id: contact.id
  }
}

// Handle refunded orders
async function handleOrderRefunded(supabase: any, data: any) {
  console.log('Processing refunded order:', data.id || data.order_id)

  const bookingId = sanitizeString(data.id || data.order_id || data.booking_id)

  // Update event registration status
  const { data: result, error } = await supabase
    .from('event_registrations')
    .update({
      status: 'refunded',
      updated_at: new Date().toISOString()
    })
    .eq('ticket_tailor_booking_id', bookingId)
    .select()

  if (error) throw error

  // Also update transaction status
  const { error: transactionError } = await supabase
    .from('transactions')
    .update({
      status: 'refunded',
      updated_at: new Date().toISOString()
    })
    .eq('kajabi_transaction_id', bookingId)

  if (transactionError) {
    console.error('Failed to update transaction status:', transactionError)
    // Don't throw - registration update is more important
  } else {
    console.log(`✅ Updated transaction status to refunded`)
  }

  return { message: 'Order refunded', data: result }
}

// Handle cancelled orders
async function handleOrderCancelled(supabase: any, data: any) {
  console.log('Processing cancelled order:', data.id || data.order_id)

  const bookingId = sanitizeString(data.id || data.order_id || data.booking_id)

  // Update event registration status
  const { data: result, error } = await supabase
    .from('event_registrations')
    .update({
      status: 'cancelled',
      updated_at: new Date().toISOString()
    })
    .eq('ticket_tailor_booking_id', bookingId)
    .select()

  if (error) throw error

  // Also update transaction status
  const { error: transactionError } = await supabase
    .from('transactions')
    .update({
      status: 'cancelled',
      updated_at: new Date().toISOString()
    })
    .eq('kajabi_transaction_id', bookingId)

  if (transactionError) {
    console.error('Failed to update transaction status:', transactionError)
    // Don't throw - registration update is more important
  } else {
    console.log(`✅ Updated transaction status to cancelled`)
  }

  return { message: 'Order cancelled', data: result }
}
