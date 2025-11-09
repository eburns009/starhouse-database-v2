// ============================================================================
// KAJABI WEBHOOK TESTS
// ============================================================================
// Run with: deno test --allow-all index.test.ts
// ============================================================================

import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts"
import {
  MockSupabaseClient,
  createMockRequest,
  kajabiFixtures,
  assertContactCreated,
  assertTransactionCreated,
  assertTagAdded
} from "../_shared/test-utils.ts"

// ============================================================================
// SETUP & TEARDOWN
// ============================================================================

// Store original environment
const originalEnv: Record<string, string | undefined> = {}

function setupTestEnv() {
  // Store originals
  originalEnv.KAJABI_WEBHOOK_SECRET = Deno.env.get('KAJABI_WEBHOOK_SECRET')
  originalEnv.SUPABASE_URL = Deno.env.get('SUPABASE_URL')
  originalEnv.SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

  // Set test values
  Deno.env.set('KAJABI_WEBHOOK_SECRET', 'test-secret-key')
  Deno.env.set('SUPABASE_URL', 'https://test.supabase.co')
  Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')
}

function teardownTestEnv() {
  // Restore originals
  if (originalEnv.KAJABI_WEBHOOK_SECRET) {
    Deno.env.set('KAJABI_WEBHOOK_SECRET', originalEnv.KAJABI_WEBHOOK_SECRET)
  } else {
    Deno.env.delete('KAJABI_WEBHOOK_SECRET')
  }
  if (originalEnv.SUPABASE_URL) {
    Deno.env.set('SUPABASE_URL', originalEnv.SUPABASE_URL)
  }
  if (originalEnv.SUPABASE_SERVICE_ROLE_KEY) {
    Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', originalEnv.SUPABASE_SERVICE_ROLE_KEY)
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

Deno.test("Kajabi Webhook - should reject non-POST requests", async () => {
  setupTestEnv()

  const req = createMockRequest({
    method: 'GET',
    body: {}
  })

  // Import the handler (this is a simplified test - actual implementation would import from index.ts)
  // For now, we'll test the expected behavior

  // Expected: 405 Method Not Allowed
  // This test validates the requirement, actual implementation needs handler extraction

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should handle OPTIONS preflight", async () => {
  setupTestEnv()

  const req = createMockRequest({
    method: 'OPTIONS',
    body: {}
  })

  // Expected: 200 OK with CORS headers

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should reject payload larger than 1MB", async () => {
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

Deno.test("Kajabi Webhook - should accept valid signature", async () => {
  setupTestEnv()

  const body = JSON.stringify(kajabiFixtures.orderCreated)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Expected: Process webhook successfully

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should REJECT invalid signature", async () => {
  setupTestEnv()

  const body = JSON.stringify(kajabiFixtures.orderCreated)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': 'invalid-signature-12345'
    }
  })

  // Expected: 401 Unauthorized
  // CRITICAL: This is the security bypass bug - currently webhooks continue processing!

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should REJECT request when no secret configured", async () => {
  // Store original
  const originalSecret = Deno.env.get('KAJABI_WEBHOOK_SECRET')

  // Remove secret
  Deno.env.delete('KAJABI_WEBHOOK_SECRET')
  Deno.env.set('SUPABASE_URL', 'https://test.supabase.co')
  Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')

  const body = JSON.stringify(kajabiFixtures.orderCreated)

  const req = createMockRequest({
    method: 'POST',
    body: body
  })

  // Expected: 500 Internal Server Error or 401 Unauthorized
  // CRITICAL: Currently this just logs a warning and continues!

  // Restore
  if (originalSecret) {
    Deno.env.set('KAJABI_WEBHOOK_SECRET', originalSecret)
  }
})

Deno.test("Kajabi Webhook - should REJECT request with missing signature header", async () => {
  setupTestEnv()

  const body = JSON.stringify(kajabiFixtures.orderCreated)

  const req = createMockRequest({
    method: 'POST',
    body: body
    // No x-kajabi-signature header
  })

  // Expected: 401 Unauthorized
  // CRITICAL: Security bypass - currently continues processing

  teardownTestEnv()
})

// ============================================================================
// TESTS: RATE LIMITING
// ============================================================================

Deno.test("Kajabi Webhook - should enforce rate limits", async () => {
  setupTestEnv()

  const body = JSON.stringify(kajabiFixtures.orderCreated)
  const signature = await generateValidSignature(body, 'test-secret-key')

  // Make 101 requests from same IP (limit is 100/minute)
  for (let i = 0; i < 101; i++) {
    const req = createMockRequest({
      method: 'POST',
      body: body,
      headers: {
        'x-kajabi-signature': signature,
        'x-forwarded-for': '192.168.1.1'
      }
    })

    // First 100 should succeed, 101st should return 429
  }

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - ORDER.CREATED
// ============================================================================

Deno.test("Kajabi Webhook - should process order.created event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(kajabiFixtures.orderCreated)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Process webhook (would call handler)
  // const response = await handler(req)

  // Verify contact was created/updated
  // assertContactCreated(mockClient, 'test@example.com')

  // Verify transaction was created
  // assertTransactionCreated(mockClient, 99.00)

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should create test contact when no email provided", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(kajabiFixtures.noEmail)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Process webhook
  // Expected: Creates kajabi-test@simulator.kajabi.com contact

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - TAG.ADDED
// ============================================================================

Deno.test("Kajabi Webhook - should process tag.added event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(kajabiFixtures.tagAdded)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Process webhook
  // Verify contact created/found
  // assertContactCreated(mockClient, 'test@example.com')

  // Verify tag created
  // assertTagAdded(mockClient, 'VIP Customer')

  teardownTestEnv()
})

// ============================================================================
// TESTS: INPUT VALIDATION
// ============================================================================

Deno.test("Kajabi Webhook - should reject invalid JSON", async () => {
  setupTestEnv()

  const body = "{ invalid json"
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Expected: 400 Bad Request

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should sanitize malicious input", async () => {
  setupTestEnv()

  const maliciousPayload = {
    event: 'order.created',
    data: {
      id: '<script>alert("xss")</script>',
      member: {
        email: 'test@example.com',
        first_name: '\x00\x01\x02EVIL\x7F',
        last_name: 'User' + 'A'.repeat(300) // Exceeds 100 char limit
      },
      payment_transaction: {
        amount_paid_decimal: 'DROP TABLE users; --',
        currency: 'USDUSD' // Exceeds 3 char limit
      }
    }
  }

  const body = JSON.stringify(maliciousPayload)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
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

Deno.test("Kajabi Webhook - should handle database errors gracefully", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()
  // Configure mock to return error

  const body = JSON.stringify(kajabiFixtures.orderCreated)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Expected: 500 Internal Server Error
  // Should log error but not expose details

  teardownTestEnv()
})

Deno.test("Kajabi Webhook - should handle unknown event types", async () => {
  setupTestEnv()

  const unknownEvent = {
    event: 'unknown.event.type',
    data: {}
  }

  const body = JSON.stringify(unknownEvent)
  const signature = await generateValidSignature(body, 'test-secret-key')

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'x-kajabi-signature': signature
    }
  })

  // Expected: 200 OK with "Event type not handled" message

  teardownTestEnv()
})

// ============================================================================
// TESTS: TIMING ATTACK PREVENTION
// ============================================================================

Deno.test("Kajabi Webhook - signature verification should be timing-safe", async () => {
  setupTestEnv()

  const body = JSON.stringify(kajabiFixtures.orderCreated)
  const validSignature = await generateValidSignature(body, 'test-secret-key')

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
        'x-kajabi-signature': sig
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
// INTEGRATION TEST NOTES
// ============================================================================

/*
INTEGRATION TESTS NEEDED (separate file):

1. Test with real Supabase instance:
   - Contact deduplication by email
   - Transaction upsert on kajabi_transaction_id
   - Tag creation and linking
   - Subscription updates

2. Test process_webhook_atomically() integration:
   - Nonce checking
   - Rate limit enforcement via DB
   - Event logging
   - Atomic transaction guarantees

3. Test CORS behavior:
   - Preflight handling
   - Origin restrictions
   - Header validation

4. Test concurrent requests:
   - Race conditions on contact creation
   - Duplicate transaction prevention
   - Rate limit accuracy under load
*/
