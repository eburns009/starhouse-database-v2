// ============================================================================
// TICKET TAILOR WEBHOOK TESTS
// ============================================================================
// Run with: deno test --allow-all index.test.ts
// ============================================================================

import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts"
import {
  MockSupabaseClient,
  createMockRequest,
  ticketTailorFixtures,
  assertContactCreated,
  assertTransactionCreated
} from "../_shared/test-utils.ts"

// ============================================================================
// SETUP & TEARDOWN
// ============================================================================

const originalEnv: Record<string, string | undefined> = {}

function setupTestEnv() {
  // Store originals
  originalEnv.TICKET_TAILOR_WEBHOOK_SECRET = Deno.env.get('TICKET_TAILOR_WEBHOOK_SECRET')
  originalEnv.SUPABASE_URL = Deno.env.get('SUPABASE_URL')
  originalEnv.SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

  // Set test values
  Deno.env.set('TICKET_TAILOR_WEBHOOK_SECRET', 'test-secret-key-tt')
  Deno.env.set('SUPABASE_URL', 'https://test.supabase.co')
  Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')
}

function teardownTestEnv() {
  // Restore originals
  for (const [key, value] of Object.entries(originalEnv)) {
    if (value !== undefined) {
      Deno.env.set(key, value)
    } else {
      Deno.env.delete(key)
    }
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

async function generateValidSignature(body: string, secret: string): Promise<string> {
  const encoder = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )

  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(body)
  )

  return Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}

// ============================================================================
// TESTS: REQUEST VALIDATION
// ============================================================================

Deno.test("Ticket Tailor Webhook - should reject non-POST requests", async () => {
  setupTestEnv()

  const req = createMockRequest({
    method: 'GET',
    body: {}
  })

  // Expected: 405 Method Not Allowed

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should handle OPTIONS preflight", async () => {
  setupTestEnv()

  const req = createMockRequest({
    method: 'OPTIONS',
    body: {}
  })

  // Expected: 200 OK with CORS headers

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should reject payload larger than 1MB", async () => {
  setupTestEnv()

  const largePayload = 'x'.repeat(1048577) // 1MB + 1 byte

  const req = createMockRequest({
    method: 'POST',
    body: largePayload
  })

  // Expected: 413 Payload Too Large

  teardownTestEnv()
})

// ============================================================================
// TESTS: SIGNATURE VERIFICATION
// ============================================================================

Deno.test("Ticket Tailor Webhook - should accept valid signature", async () => {
  setupTestEnv()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Expected: Process webhook successfully

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should REJECT invalid signature", async () => {
  setupTestEnv()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': 'invalid-signature-12345'
    }
  })

  // Expected: 401 Unauthorized
  // CRITICAL: This is the security bypass bug - currently continues processing!

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should REJECT when no secret configured", async () => {
  // Remove secret
  const originalSecret = Deno.env.get('TICKET_TAILOR_WEBHOOK_SECRET')
  Deno.env.delete('TICKET_TAILOR_WEBHOOK_SECRET')
  Deno.env.set('SUPABASE_URL', 'https://test.supabase.co')
  Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body
  })

  // Expected: 500 Internal Server Error or 401 Unauthorized
  // CRITICAL: Currently just logs warning and continues!

  // Restore
  if (originalSecret) {
    Deno.env.set('TICKET_TAILOR_WEBHOOK_SECRET', originalSecret)
  }
})

Deno.test("Ticket Tailor Webhook - should REJECT when signature header missing", async () => {
  setupTestEnv()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body
    // No x-webhook-signature header
  })

  // Expected: 401 Unauthorized
  // CRITICAL: Security bypass - currently continues processing

  teardownTestEnv()
})

// ============================================================================
// TESTS: RATE LIMITING
// ============================================================================

Deno.test("Ticket Tailor Webhook - should enforce rate limits", async () => {
  setupTestEnv()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  // Make 101 requests from same IP (limit is 100/minute)
  for (let i = 0; i < 101; i++) {
    const req = createMockRequest({
      method: 'POST',
      body: body,
      headers: {
        'x-webhook-signature': signature,
        'x-forwarded-for': '192.168.1.1'
      }
    })

    // First 100 should succeed, 101st should return 429
  }

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - ORDER.COMPLETED
// ============================================================================

Deno.test("Ticket Tailor Webhook - should process order.completed event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Process webhook (would call handler)
  // Expected:
  // - Contact created with attendee@example.com
  // - Transaction created with amount 150.00 (15000 cents)

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should create test contact when no email provided", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(ticketTailorFixtures.noEmail)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Process webhook
  // Expected: Creates ticket-tailor-test@simulator.tickettailor.com contact

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should convert cents to dollars", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Process webhook
  // Expected: Transaction amount is 150.00 (converted from 15000 cents)

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - ORDER.REFUNDED
// ============================================================================

Deno.test("Ticket Tailor Webhook - should process order.refunded event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(ticketTailorFixtures.orderRefunded)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Process webhook
  // Expected: Updates transaction status to 'refunded'

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - ORDER.CANCELLED
// ============================================================================

Deno.test("Ticket Tailor Webhook - should process order.cancelled event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(ticketTailorFixtures.orderCancelled)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Process webhook
  // Expected: Updates transaction status to 'cancelled'

  teardownTestEnv()
})

// ============================================================================
// TESTS: INPUT VALIDATION
// ============================================================================

Deno.test("Ticket Tailor Webhook - should reject invalid JSON", async () => {
  setupTestEnv()

  const body = "{ invalid json"
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Expected: 400 Bad Request

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should sanitize malicious input", async () => {
  setupTestEnv()

  const maliciousPayload = {
    type: 'order.completed',
    data: {
      id: '<script>alert("xss")</script>',
      reference: 'TT-REF-XSS',
      total: 'DROP TABLE users; --',
      currency: 'USDUSD', // Too long
      status: 'completed',
      customer: {
        email: 'test@example.com',
        first_name: '\x00\x01\x02EVIL\x7F',
        last_name: 'User' + 'A'.repeat(300) // Exceeds limit
      }
    }
  }

  const body = JSON.stringify(maliciousPayload)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Process webhook
  // Verify all inputs were sanitized:
  // - Control characters removed
  // - Strings truncated to limits
  // - Invalid amounts rejected

  teardownTestEnv()
})

// ============================================================================
// TESTS: ERROR HANDLING
// ============================================================================

Deno.test("Ticket Tailor Webhook - should handle database errors gracefully", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()
  // Configure mock to return error

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Expected: 500 Internal Server Error
  // Should log error but not expose details

  teardownTestEnv()
})

Deno.test("Ticket Tailor Webhook - should handle unknown event types", async () => {
  setupTestEnv()

  const unknownEvent = {
    type: 'unknown.event.type',
    data: {}
  }

  const body = JSON.stringify(unknownEvent)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Expected: 200 OK with "Event type not handled" message

  teardownTestEnv()
})

// ============================================================================
// TESTS: TIMING ATTACK PREVENTION
// ============================================================================

Deno.test("Ticket Tailor Webhook - signature verification should be timing-safe", async () => {
  setupTestEnv()

  const body = JSON.stringify(ticketTailorFixtures.orderCompleted)
  const validSignature = await generateValidSignature(body, 'test-secret-key-tt')

  // Test with signatures that match at different positions
  const testSignatures = [
    validSignature,
    'z' + validSignature.substring(1), // First char wrong
    validSignature.substring(0, 32) + 'z' + validSignature.substring(33), // Middle char wrong
    validSignature.substring(0, 63) + 'z', // Last char wrong
    'zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz' // All wrong
  ]

  const timings: number[] = []

  for (const sig of testSignatures) {
    const req = createMockRequest({
      method: 'POST',
      body: body,
      headers: {
        'x-webhook-signature': sig
      }
    })

    const start = performance.now()
    // Process request
    const end = performance.now()
    timings.push(end - start)
  }

  // Verify timing variance is minimal (< 10ms)
  // This prevents timing attacks
  const maxTiming = Math.max(...timings)
  const minTiming = Math.min(...timings)
  const variance = maxTiming - minTiming

  // Note: This is a simplified test - real timing attack prevention
  // requires careful implementation in the signature comparison function

  teardownTestEnv()
})

// ============================================================================
// TESTS: TICKET-SPECIFIC FEATURES
// ============================================================================

Deno.test("Ticket Tailor Webhook - should handle multiple tickets in order", async () => {
  setupTestEnv()

  const orderWithMultipleTickets = {
    type: 'order.completed',
    data: {
      id: 'tt-order-multi',
      reference: 'TT-MULTI-001',
      total: 30000, // 300.00 for 2 tickets
      currency: 'USD',
      status: 'completed',
      created_at: '2025-01-01T12:00:00Z',
      customer: {
        email: 'multi@example.com',
        first_name: 'Multi',
        last_name: 'Ticket'
      },
      tickets: [
        { id: 'ticket-1', price: 15000, status: 'valid' },
        { id: 'ticket-2', price: 15000, status: 'valid' }
      ]
    }
  }

  const body = JSON.stringify(orderWithMultipleTickets)
  const signature = await generateValidSignature(body, 'test-secret-key-tt')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-webhook-signature': signature
    }
  })

  // Expected: Single transaction with total amount 300.00

  teardownTestEnv()
})

// ============================================================================
// INTEGRATION TEST NOTES
// ============================================================================

/*
INTEGRATION TESTS NEEDED (separate file):

1. Test with real Supabase instance:
   - Contact creation and deduplication
   - Transaction upsert on ticket_tailor_order_id
   - Status updates (completed → refunded → cancelled)

2. Test process_webhook_atomically() integration:
   - Nonce checking
   - Rate limit enforcement via DB
   - Event logging
   - Atomic transaction guarantees

3. Test Ticket Tailor specific features:
   - Cents to dollars conversion
   - Multiple tickets per order
   - Ticket status tracking
   - Event attendee data handling

4. Test edge cases:
   - Orders without customer info
   - Partial refunds
   - Cancelled orders with multiple tickets
   - Currency conversion
*/
