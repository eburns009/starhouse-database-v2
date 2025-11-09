// ============================================================================
// SHARED WEBHOOK SECURITY UTILITIES
// ============================================================================
// Purpose: Common security functions used by all webhooks
// Created: 2025-10-31
// ============================================================================

import { crypto } from "https://deno.land/std@0.168.0/crypto/mod.ts"

// ============================================================================
// CONSTANTS
// ============================================================================

export const MAX_REQUESTS_PER_WINDOW = 100
export const RATE_LIMIT_WINDOW_MS = 60000 // 1 minute
export const MAX_PAYLOAD_SIZE_BYTES = 1048576 // 1MB
export const REPLAY_ATTACK_WINDOW_MS = 300000 // 5 minutes
export const CLOCK_SKEW_TOLERANCE_MS = 60000 // 1 minute

// ============================================================================
// TYPES
// ============================================================================

export interface WebhookConfig {
  source: 'kajabi' | 'paypal' | 'ticket-tailor'
  secret?: string
  environment: 'production' | 'staging' | 'development'
  testMode: boolean
}

export interface WebhookValidationResult {
  valid: boolean
  error?: string
  errorCode?: string
  requestId: string
}

export interface WebhookEvent {
  requestId: string
  webhookId: string
  source: string
  eventType: string
  ipAddress?: string
  userAgent?: string
  signatureValid: boolean
  webhookTimestamp?: string
  payloadHash: string
  payloadSize: number
}

// ============================================================================
// ENVIRONMENT & CONFIGURATION
// ============================================================================

export function getWebhookConfig(source: 'kajabi' | 'paypal' | 'ticket-tailor', secretEnvVar: string): WebhookConfig & { secrets: string[] } {
  const environment = (Deno.env.get('WEBHOOK_ENVIRONMENT') || 'development') as 'production' | 'staging' | 'development'
  const testMode = Deno.env.get('WEBHOOK_TEST_MODE') === 'true'
  const secret = Deno.env.get(secretEnvVar)

  // Support multiple keys for rotation: WEBHOOK_SECRET=key1,key2,key3
  // Try all keys; log which one matched for rotation tracking
  const secrets = secret ? secret.split(',').map(s => s.trim()).filter(Boolean) : []

  return {
    source,
    secret: secrets[0], // Primary key (backwards compat)
    secrets, // All keys for dual-key verification
    environment,
    testMode
  }
}

export function validateConfig(config: WebhookConfig): WebhookValidationResult {
  const requestId = crypto.randomUUID()

  // In production, webhook secret is REQUIRED
  if (config.environment === 'production' && !config.secret) {
    return {
      valid: false,
      error: 'Webhook not configured - missing secret in production',
      errorCode: 'WEBHOOK_CONFIG_ERROR',
      requestId
    }
  }

  // Test mode should only be enabled in non-production
  if (config.testMode && config.environment === 'production') {
    return {
      valid: false,
      error: 'Test mode cannot be enabled in production',
      errorCode: 'INVALID_TEST_MODE',
      requestId
    }
  }

  return { valid: true, requestId }
}

// ============================================================================
// REQUEST VALIDATION
// ============================================================================

export function generateRequestId(): string {
  return crypto.randomUUID()
}

export function hashPayload(payload: string): string {
  const encoder = new TextEncoder()
  const data = encoder.encode(payload)
  const hashBuffer = crypto.subtle.digestSync("SHA-256", data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

export function validatePayloadSize(payload: string): boolean {
  return payload.length <= MAX_PAYLOAD_SIZE_BYTES
}

// ============================================================================
// SIGNATURE VERIFICATION
// ============================================================================

// Timing-safe string comparison to prevent timing attacks
export function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false
  }

  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }

  return result === 0
}

// HMAC-SHA256 signature verification (for Kajabi, Ticket Tailor)
export async function verifyHmacSignature(
  payload: string,
  signature: string,
  secret: string
): Promise<boolean> {
  try {
    const encoder = new TextEncoder()
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )

    const expectedBuffer = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(payload)
    )

    // Convert signature hex string to Uint8Array for constant-time comparison
    const providedBuffer = new Uint8Array(
      signature.toLowerCase().match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []
    )

    const expected = new Uint8Array(expectedBuffer)

    // CRITICAL: Use constant-time comparison on raw bytes, not hex strings
    // This prevents timing attacks that could leak signature information
    if (expected.length !== providedBuffer.length) {
      return false
    }

    // Constant-time byte-by-byte comparison
    let result = 0
    for (let i = 0; i < expected.length; i++) {
      result |= expected[i] ^ providedBuffer[i]
    }

    return result === 0
  } catch (error) {
    console.error('[Security] HMAC verification error:', error)
    return false
  }
}

// DUAL-KEY VERIFICATION - Try multiple keys for safe rotation
export async function verifyHmacSignatureMultiKey(
  payload: string,
  signature: string,
  secrets: string[],
  context: LogContext
): Promise<{ valid: boolean; keyIndex?: number }> {
  if (!secrets || secrets.length === 0) {
    logError('No secrets provided for verification', new Error('Missing secrets'), context)
    return { valid: false }
  }

  // Try each key in order
  for (let i = 0; i < secrets.length; i++) {
    const isValid = await verifyHmacSignature(payload, signature, secrets[i])
    if (isValid) {
      // Log which key matched for rotation tracking
      if (i > 0) {
        logWarning(`Signature verified with key ${i} (not primary)`, {
          ...context,
          keyIndex: i,
          totalKeys: secrets.length
        })
      } else {
        logInfo(`Signature verified with primary key`, {
          ...context,
          keyIndex: 0
        })
      }
      return { valid: true, keyIndex: i }
    }
  }

  // None of the keys matched
  logError('Signature verification failed with all keys', new Error('Invalid signature'), {
    ...context,
    keysAttempted: secrets.length
  })

  return { valid: false }
}

// ============================================================================
// REPLAY ATTACK PREVENTION
// ============================================================================

export function checkReplayAttack(webhookTimestamp?: string): { isReplay: boolean; reason?: string } {
  if (!webhookTimestamp) {
    // If no timestamp provided, allow but log
    return { isReplay: false }
  }

  try {
    const timestamp = new Date(webhookTimestamp).getTime()
    const now = Date.now()

    // Check if timestamp is too old (replay attack)
    if (now - timestamp > REPLAY_ATTACK_WINDOW_MS) {
      return {
        isReplay: true,
        reason: `Timestamp too old (>${REPLAY_ATTACK_WINDOW_MS / 1000}s)`
      }
    }

    // Check if timestamp is in future (clock skew or manipulation)
    if (timestamp - now > CLOCK_SKEW_TOLERANCE_MS) {
      return {
        isReplay: true,
        reason: `Timestamp in future (clock skew > ${CLOCK_SKEW_TOLERANCE_MS / 1000}s)`
      }
    }

    return { isReplay: false }
  } catch (error) {
    console.error('[Security] Invalid timestamp format:', webhookTimestamp, error)
    return {
      isReplay: true,
      reason: 'Invalid timestamp format'
    }
  }
}

// ============================================================================
// IDEMPOTENCY CHECKING
// ============================================================================

export async function checkIdempotency(
  supabase: any,
  webhookId: string,
  payloadHash: string,
  source: string
): Promise<{ isDuplicate: boolean; reason?: string }> {
  try {
    // Check 1: Exact webhook ID match
    const { data: existingById } = await supabase
      .from('webhook_events')
      .select('id, status, created_at')
      .eq('webhook_id', webhookId)
      .eq('source', source)
      .maybeSingle()

    if (existingById && existingById.status === 'success') {
      return {
        isDuplicate: true,
        reason: `Webhook ID already processed at ${existingById.created_at}`
      }
    }

    // Check 2: Same payload hash within 1 hour (duplicate detection)
    const { data: existingByHash } = await supabase
      .from('webhook_events')
      .select('id, webhook_id, created_at')
      .eq('payload_hash', payloadHash)
      .eq('source', source)
      .eq('status', 'success')
      .gte('received_at', new Date(Date.now() - 3600000).toISOString()) // Last 1 hour
      .maybeSingle()

    if (existingByHash) {
      return {
        isDuplicate: true,
        reason: `Duplicate payload detected (original: ${existingByHash.webhook_id})`
      }
    }

    return { isDuplicate: false }
  } catch (error) {
    console.error('[Security] Idempotency check error:', error)
    // On error, allow processing (fail open for idempotency, not security)
    return { isDuplicate: false }
  }
}

// ============================================================================
// WEBHOOK EVENT LOGGING
// ============================================================================

export async function logWebhookEvent(
  supabase: any,
  event: WebhookEvent
): Promise<void> {
  try {
    await supabase
      .from('webhook_events')
      .insert({
        request_id: event.requestId,
        webhook_id: event.webhookId,
        source: event.source,
        event_type: event.eventType,
        ip_address: event.ipAddress,
        user_agent: event.userAgent,
        signature_valid: event.signatureValid,
        webhook_timestamp: event.webhookTimestamp,
        payload_hash: event.payloadHash,
        payload_size: event.payloadSize,
        status: 'processing',
        received_at: new Date().toISOString()
      })
  } catch (error) {
    console.error('[Security] Failed to log webhook event:', error)
    // Don't throw - logging failure shouldn't block processing
  }
}

export async function updateWebhookEventStatus(
  supabase: any,
  webhookId: string,
  status: 'success' | 'failed' | 'duplicate',
  processingTimeMs?: number,
  errorMessage?: string,
  errorCode?: string,
  relatedIds?: {
    contactId?: string
    transactionId?: string
    subscriptionId?: string
  }
): Promise<void> {
  try {
    await supabase
      .from('webhook_events')
      .update({
        status,
        processed_at: new Date().toISOString(),
        processing_duration_ms: processingTimeMs,
        error_message: errorMessage,
        error_code: errorCode,
        contact_id: relatedIds?.contactId,
        transaction_id: relatedIds?.transactionId,
        subscription_id: relatedIds?.subscriptionId
      })
      .eq('webhook_id', webhookId)
  } catch (error) {
    console.error('[Security] Failed to update webhook event status:', error)
    // Don't throw - logging failure shouldn't block processing
  }
}

// ============================================================================
// PII REDACTION
// ============================================================================

export function redactPII(data: any): any {
  if (!data || typeof data !== 'object') {
    return data
  }

  const redacted = { ...data }
  const piiFields = [
    'email', 'phone', 'ssn', 'credit_card', 'password',
    'address', 'ip_address', 'first_name', 'last_name',
    'name', 'payer_email', 'subscriber_email'
  ]

  for (const field of piiFields) {
    if (field in redacted) {
      const value = redacted[field]
      if (typeof value === 'string') {
        // Redact but keep format for debugging
        if (field === 'email' && value.includes('@')) {
          const [local, domain] = value.split('@')
          redacted[field] = `${local[0]}***@${domain}`
        } else if (field === 'phone') {
          redacted[field] = '***-***-' + value.slice(-4)
        } else {
          redacted[field] = '***REDACTED***'
        }
      }
    }
  }

  return redacted
}

// ============================================================================
// STRUCTURED LOGGING
// ============================================================================

export interface LogContext {
  requestId: string
  source: string
  eventType?: string
  webhookId?: string
  [key: string]: any
}

export function logInfo(message: string, context: LogContext): void {
  console.log(JSON.stringify({
    level: 'INFO',
    message,
    timestamp: new Date().toISOString(),
    ...context
  }))
}

export function logWarning(message: string, context: LogContext): void {
  console.warn(JSON.stringify({
    level: 'WARN',
    message,
    timestamp: new Date().toISOString(),
    ...context
  }))
}

export function logError(message: string, error: any, context: LogContext): void {
  console.error(JSON.stringify({
    level: 'ERROR',
    message,
    error: error?.message || String(error),
    stack: error?.stack,
    timestamp: new Date().toISOString(),
    ...context
  }))
}

// ============================================================================
// INPUT VALIDATION (from duplicated code)
// ============================================================================

export function sanitizeString(input: any): string {
  if (typeof input !== 'string') {
    return String(input)
  }
  // Remove control characters and limit length
  return input.replace(/[\x00-\x1F\x7F]/g, '').substring(0, 255)
}

export function validateEmail(email: any): string | null {
  if (typeof email !== 'string') {
    return null
  }

  const sanitized = email.trim().toLowerCase().substring(0, 255)

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(sanitized)) {
    return null
  }

  return sanitized
}

export function validateAmount(amount: any): number | null {
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
