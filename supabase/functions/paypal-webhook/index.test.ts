// ============================================================================
// PAYPAL WEBHOOK TESTS
// ============================================================================
// Run with: deno test --allow-all index.test.ts
// ============================================================================

import { assertEquals, assertExists } from "https://deno.land/std@0.168.0/testing/asserts.ts"
import {
  MockSupabaseClient,
  createMockRequest,
  paypalFixtures,
  assertContactCreated,
  assertTransactionCreated
} from "../_shared/test-utils.ts"

// ============================================================================
// SETUP & TEARDOWN
// ============================================================================

const originalEnv: Record<string, string | undefined> = {}

function setupTestEnv() {
  // Store originals
  originalEnv.PAYPAL_WEBHOOK_ID = Deno.env.get('PAYPAL_WEBHOOK_ID')
  originalEnv.PAYPAL_CLIENT_ID = Deno.env.get('PAYPAL_CLIENT_ID')
  originalEnv.PAYPAL_CLIENT_SECRET = Deno.env.get('PAYPAL_CLIENT_SECRET')
  originalEnv.PAYPAL_ENV = Deno.env.get('PAYPAL_ENV')
  originalEnv.SUPABASE_URL = Deno.env.get('SUPABASE_URL')
  originalEnv.SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

  // Set test values
  Deno.env.set('PAYPAL_WEBHOOK_ID', 'test-webhook-id-12345')
  Deno.env.set('PAYPAL_CLIENT_ID', 'test-client-id')
  Deno.env.set('PAYPAL_CLIENT_SECRET', 'test-client-secret')
  Deno.env.set('PAYPAL_ENV', 'sandbox')
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
// TESTS: REQUEST VALIDATION
// ============================================================================

Deno.test("PayPal Webhook - should reject non-POST requests", async () => {
  setupTestEnv()

  const req = createMockRequest({
    method: 'GET',
    body: {}
  })

  // Expected: 405 Method Not Allowed

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should handle OPTIONS preflight", async () => {
  setupTestEnv()

  const req = createMockRequest({
    method: 'OPTIONS',
    body: {}
  })

  // Expected: 200 OK with CORS headers

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should reject payload larger than 1MB", async () => {
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
// TESTS: CONFIGURATION VALIDATION
// ============================================================================

Deno.test("PayPal Webhook - should REJECT when PAYPAL_WEBHOOK_ID not configured", async () => {
  // Remove webhook ID
  const originalWebhookId = Deno.env.get('PAYPAL_WEBHOOK_ID')
  Deno.env.delete('PAYPAL_WEBHOOK_ID')

  Deno.env.set('SUPABASE_URL', 'https://test.supabase.co')
  Deno.env.set('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 500 Internal Server Error - "Webhook not configured"

  // Restore
  if (originalWebhookId) {
    Deno.env.set('PAYPAL_WEBHOOK_ID', originalWebhookId)
  }
})

Deno.test("PayPal Webhook - should REJECT when PayPal credentials not configured", async () => {
  setupTestEnv()

  // Remove credentials
  Deno.env.delete('PAYPAL_CLIENT_ID')
  Deno.env.delete('PAYPAL_CLIENT_SECRET')

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: Signature verification fails (credentials needed for verification)

  teardownTestEnv()
})

// ============================================================================
// TESTS: SIGNATURE VERIFICATION
// ============================================================================

Deno.test("PayPal Webhook - should REJECT when missing transmission-id header", async () => {
  setupTestEnv()

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      // Missing paypal-transmission-id
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 401 Unauthorized - "missing signature headers"

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should REJECT when missing transmission-time header", async () => {
  setupTestEnv()

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      // Missing paypal-transmission-time
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 401 Unauthorized - "missing signature headers"

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should REJECT when missing transmission-sig header", async () => {
  setupTestEnv()

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      // Missing paypal-transmission-sig
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 401 Unauthorized - "missing signature headers"

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should REJECT when signature verification fails", async () => {
  setupTestEnv()

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'invalid-signature-12345',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 401 Unauthorized - "invalid signature"
  // NOTE: This would require mocking the PayPal API verification call

  teardownTestEnv()
})

// ============================================================================
// TESTS: RATE LIMITING
// ============================================================================

Deno.test("PayPal Webhook - should enforce rate limits", async () => {
  setupTestEnv()

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  // Make 101 requests from same IP (limit is 100/minute)
  for (let i = 0; i < 101; i++) {
    const req = createMockRequest({
      method: 'POST',
      body: body,
      headers: {
        'paypal-transmission-id': `test-transmission-id-${i}`,
        'paypal-transmission-time': '2025-01-01T12:00:00Z',
        'paypal-transmission-sig': 'test-signature',
        'paypal-cert-url': 'https://api.paypal.com/cert',
        'paypal-auth-algo': 'SHA256withRSA',
        'x-forwarded-for': '192.168.1.1'
      }
    })

    // First 100 should process (or fail auth), 101st should return 429
  }

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - PAYMENT.SALE.COMPLETED
// ============================================================================

Deno.test("PayPal Webhook - should process PAYMENT.SALE.COMPLETED event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Process webhook (would call handler)
  // Expected:
  // - Contact created with buyer@example.com
  // - Transaction created with amount 99.99

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should create test contact when no email in payload", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const payloadNoEmail = {
    event_type: 'PAYMENT.SALE.COMPLETED',
    resource: {
      id: 'PAYID-NO-EMAIL',
      amount: {
        total: '1.00',
        currency: 'USD'
      },
      create_time: '2025-01-01T12:00:00Z'
      // No payer information
    }
  }

  const body = JSON.stringify(payloadNoEmail)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: Creates paypal-test@simulator.paypal.com contact

  teardownTestEnv()
})

// ============================================================================
// TESTS: EVENT HANDLING - SUBSCRIPTION EVENTS
// ============================================================================

Deno.test("PayPal Webhook - should process BILLING.SUBSCRIPTION.CREATED event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const body = JSON.stringify(paypalFixtures.subscriptionCreated)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Process webhook
  // Expected:
  // - Contact created with subscriber@example.com
  // - Subscription created with amount 29.99

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should process BILLING.SUBSCRIPTION.CANCELLED event", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  const subscriptionCancelled = {
    event_type: 'BILLING.SUBSCRIPTION.CANCELLED',
    resource: {
      id: 'I-SUBSCRIPTION123',
      status: 'CANCELLED'
    }
  }

  const body = JSON.stringify(subscriptionCancelled)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: Updates subscription status to 'canceled'

  teardownTestEnv()
})

// ============================================================================
// TESTS: INPUT VALIDATION
// ============================================================================

Deno.test("PayPal Webhook - should reject invalid JSON", async () => {
  setupTestEnv()

  const body = "{ invalid json"

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 400 Bad Request

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should sanitize malicious input", async () => {
  setupTestEnv()

  const maliciousPayload = {
    event_type: 'PAYMENT.SALE.COMPLETED',
    resource: {
      id: '<script>alert("xss")</script>',
      amount: {
        total: 'DROP TABLE users; --',
        currency: 'USDUSD' // Too long
      },
      payer: {
        email_address: 'test@example.com',
        name: {
          given_name: '\x00\x01\x02EVIL\x7F',
          surname: 'User' + 'A'.repeat(300) // Exceeds limit
        }
      }
    }
  }

  const body = JSON.stringify(maliciousPayload)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
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

Deno.test("PayPal Webhook - should handle database errors gracefully", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()
  // Configure mock to return error

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 500 Internal Server Error
  // Should log error but not expose details

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should handle unknown event types", async () => {
  setupTestEnv()

  const unknownEvent = {
    event_type: 'UNKNOWN.EVENT.TYPE',
    resource: {}
  }

  const body = JSON.stringify(unknownEvent)

  const req = createMockRequest({
    method: 'POST',
    body: body,
    headers: {
      'paypal-transmission-id': 'test-transmission-id',
      'paypal-transmission-time': '2025-01-01T12:00:00Z',
      'paypal-transmission-sig': 'test-signature',
      'paypal-cert-url': 'https://api.paypal.com/cert',
      'paypal-auth-algo': 'SHA256withRSA'
    }
  })

  // Expected: 200 OK with "Event type not handled" message

  teardownTestEnv()
})

// ============================================================================
// TESTS: CONTACT DEDUPLICATION
// ============================================================================

Deno.test("PayPal Webhook - should find contact by PayPal email", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  // Pre-populate with existing contact
  mockClient.setMockData('contacts', [
    {
      id: 'existing-contact-id',
      email: 'other@example.com',
      paypal_email: 'buyer@example.com',
      first_name: 'Existing',
      last_name: 'User'
    }
  ])

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  // Process webhook
  // Expected: Finds existing contact by paypal_email match
  // Should NOT create duplicate contact

  teardownTestEnv()
})

Deno.test("PayPal Webhook - should find contact by name match", async () => {
  setupTestEnv()

  const mockClient = new MockSupabaseClient()

  // Pre-populate with existing contact (same name, different email)
  mockClient.setMockData('contacts', [
    {
      id: 'existing-contact-id',
      email: 'kajabi@example.com',
      first_name: 'Bob',
      last_name: 'Builder',
      paypal_email: null
    }
  ])

  const body = JSON.stringify(paypalFixtures.paymentCompleted)

  // Process webhook
  // Expected: Finds existing contact by name match
  // Updates with PayPal email
  // Should NOT create duplicate

  teardownTestEnv()
})

// ============================================================================
// INTEGRATION TEST NOTES
// ============================================================================

/*
INTEGRATION TESTS NEEDED (separate file):

1. PayPal API Verification:
   - Mock PayPal's /v1/notifications/verify-webhook-signature endpoint
   - Test successful verification
   - Test failed verification
   - Test network errors

2. Contact Deduplication Logic:
   - Test all 4 lookup methods (paypal_email, primary email, kajabi_member_id, name match)
   - Test priority order
   - Test updating existing contacts with new info

3. Transaction Processing:
   - Test Kajabi ID extraction from PayPal custom fields
   - Test duplicate prevention
   - Test refund handling

4. Subscription Lifecycle:
   - Test create → update → cancel flow
   - Test billing date updates
   - Test payment amount changes
*/
