# Security Hardening Guide

**Priority:** 🔴 P0 (Critical)
**Last Updated:** October 30, 2025
**Estimated Time:** 2-3 days

---

## Table of Contents

1. [Overview](#overview)
2. [Critical Vulnerabilities](#critical-vulnerabilities)
3. [Webhook Signature Verification](#webhook-signature-verification)
4. [Secret Management](#secret-management)
5. [Rate Limiting](#rate-limiting)
6. [Input Validation](#input-validation)
7. [SQL Injection Prevention](#sql-injection-prevention)
8. [Error Message Sanitization](#error-message-sanitization)
9. [Security Headers](#security-headers)
10. [Checklist](#security-checklist)

---

## Overview

**Current Security Grade:** 4/10 ⚠️

This guide addresses critical security vulnerabilities that must be fixed before production deployment.

### Impact of Security Issues
- **Data Breach:** Exposed API keys could allow unauthorized database access
- **Fraud:** Unverified webhooks could inject fake transactions
- **DoS Attack:** No rate limiting allows resource exhaustion
- **Data Leakage:** Detailed error messages expose internal architecture

---

## Critical Vulnerabilities

### 1. No Webhook Signature Verification ⚠️ CRITICAL

**Current Risk:** Anyone can send fake webhook requests to your endpoints.

**Example Attack:**
```bash
# Attacker sends fake Kajabi order
curl -X POST https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/kajabi-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "order.created",
    "data": {
      "id": "fake-123",
      "email": "attacker@evil.com",
      "amount": 1000000,
      "status": "completed"
    }
  }'

# Result: Fake $1M transaction created in your database!
```

**Fix:** See [Webhook Authentication Guide](./WEBHOOK_AUTHENTICATION.md)

---

## Webhook Signature Verification

### Implementation Steps

#### 1. Kajabi Webhook Verification

**Add to `supabase/functions/kajabi-webhook/index.ts`:**

```typescript
import { createHmac } from "https://deno.land/std@0.168.0/node/crypto.ts";

const KAJABI_WEBHOOK_SECRET = Deno.env.get('KAJABI_WEBHOOK_SECRET');

function verifyKajabiSignature(
  payload: string,
  signature: string | null
): boolean {
  if (!signature || !KAJABI_WEBHOOK_SECRET) {
    return false;
  }

  const hmac = createHmac('sha256', KAJABI_WEBHOOK_SECRET);
  hmac.update(payload);
  const expectedSignature = hmac.digest('hex');

  return signature === expectedSignature;
}

serve(async (req) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Get raw body for signature verification
    const rawBody = await req.text();
    const signature = req.headers.get('X-Kajabi-Signature');

    // ⚠️ CRITICAL: Verify signature before processing
    if (!verifyKajabiSignature(rawBody, signature)) {
      console.error('Invalid webhook signature');
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: corsHeaders }
      );
    }

    // Now safe to parse and process
    const payload = JSON.parse(rawBody);
    // ... rest of webhook handling
  } catch (error) {
    // ... error handling
  }
});
```

#### 2. PayPal Webhook Verification

PayPal requires OAuth token verification:

```typescript
// supabase/functions/paypal-webhook/index.ts

async function verifyPayPalWebhook(
  payload: any,
  headers: Headers
): Promise<boolean> {
  const transmissionId = headers.get('PAYPAL-TRANSMISSION-ID');
  const transmissionTime = headers.get('PAYPAL-TRANSMISSION-TIME');
  const transmissionSig = headers.get('PAYPAL-TRANSMISSION-SIG');
  const certUrl = headers.get('PAYPAL-CERT-URL');
  const authAlgo = headers.get('PAYPAL-AUTH-ALGO');
  const webhookId = Deno.env.get('PAYPAL_WEBHOOK_ID');

  // Construct verification request
  const verificationBody = {
    transmission_id: transmissionId,
    transmission_time: transmissionTime,
    cert_url: certUrl,
    auth_algo: authAlgo,
    transmission_sig: transmissionSig,
    webhook_id: webhookId,
    webhook_event: payload
  };

  // Get PayPal OAuth token
  const token = await getPayPalAccessToken();

  // Verify with PayPal API
  const response = await fetch(
    'https://api.paypal.com/v1/notifications/verify-webhook-signature',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(verificationBody)
    }
  );

  const result = await response.json();
  return result.verification_status === 'SUCCESS';
}

async function getPayPalAccessToken(): Promise<string> {
  const clientId = Deno.env.get('PAYPAL_CLIENT_ID');
  const secret = Deno.env.get('PAYPAL_SECRET');
  const auth = btoa(`${clientId}:${secret}`);

  const response = await fetch(
    'https://api.paypal.com/v1/oauth2/token',
    {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: 'grant_type=client_credentials'
    }
  );

  const data = await response.json();
  return data.access_token;
}
```

#### 3. Ticket Tailor Webhook Verification

```typescript
// supabase/functions/ticket-tailor-webhook/index.ts

function verifyTicketTailorSignature(
  payload: string,
  signature: string | null
): boolean {
  if (!signature) return false;

  const secret = Deno.env.get('TICKET_TAILOR_WEBHOOK_SECRET');
  const hmac = createHmac('sha256', secret);
  hmac.update(payload);
  const expectedSignature = hmac.digest('hex');

  return signature === expectedSignature;
}
```

---

## Secret Management

### Current Issue
```typescript
// ❌ EXPOSED IN CODE
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

### Solution: Environment Variables

#### Step 1: Add to Supabase Dashboard

1. Go to: https://app.supabase.com/project/lnagadkqejnopgfxwlkb/settings/functions
2. Navigate to "Edge Functions" → "Environment Variables"
3. Add secrets:

```bash
KAJABI_WEBHOOK_SECRET=<get-from-kajabi-dashboard>
PAYPAL_CLIENT_ID=<get-from-paypal>
PAYPAL_SECRET=<get-from-paypal>
PAYPAL_WEBHOOK_ID=<get-from-paypal>
TICKET_TAILOR_WEBHOOK_SECRET=<get-from-ticket-tailor>
SUPABASE_SERVICE_ROLE_KEY=<from-supabase-settings>
```

#### Step 2: Rotate Exposed Keys

⚠️ **IMMEDIATE ACTION REQUIRED:**

1. Generate new Supabase anon key
2. Update `.env` file
3. Deploy new keys to production
4. Revoke old keys

#### Step 3: Update Web App

```bash
# web-app/.env (NOT committed to git!)
VITE_SUPABASE_URL=https://lnagadkqejnopgfxwlkb.supabase.co
VITE_SUPABASE_ANON_KEY=<new-key>
```

**Update `.gitignore`:**
```bash
# Add to .gitignore
.env
.env.local
.env.production
*.key
secrets/
```

---

## Rate Limiting

### Current Issue
No rate limiting → vulnerable to DoS attacks

### Solution: Edge Function Rate Limiting

```typescript
// Create: supabase/functions/_shared/rateLimit.ts

const rateLimitStore = new Map<string, { count: number; resetAt: number }>();

export function checkRateLimit(
  identifier: string,
  maxRequests: number = 100,
  windowMs: number = 60000 // 1 minute
): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const record = rateLimitStore.get(identifier);

  // Clean up old entries
  if (record && now > record.resetAt) {
    rateLimitStore.delete(identifier);
  }

  const current = rateLimitStore.get(identifier) || {
    count: 0,
    resetAt: now + windowMs
  };

  current.count++;
  rateLimitStore.set(identifier, current);

  return {
    allowed: current.count <= maxRequests,
    remaining: Math.max(0, maxRequests - current.count)
  };
}
```

**Usage in webhooks:**

```typescript
import { checkRateLimit } from '../_shared/rateLimit.ts';

serve(async (req) => {
  const ip = req.headers.get('x-forwarded-for') || 'unknown';
  const rateLimit = checkRateLimit(ip, 100, 60000);

  if (!rateLimit.allowed) {
    return new Response(
      JSON.stringify({ error: 'Rate limit exceeded' }),
      {
        status: 429,
        headers: {
          ...corsHeaders,
          'X-RateLimit-Remaining': String(rateLimit.remaining),
          'Retry-After': '60'
        }
      }
    );
  }

  // ... continue processing
});
```

---

## Input Validation

### Current Issue
Accepting untrusted input without validation

### Solution: Validation Library

```typescript
// Install: npm install zod

import { z } from 'https://deno.land/x/zod/mod.ts';

// Define schemas
const KajabiOrderSchema = z.object({
  id: z.string().min(1),
  email: z.string().email(),
  amount: z.number().positive(),
  currency: z.string().length(3),
  status: z.enum(['pending', 'completed', 'failed', 'refunded'])
});

// Validate incoming data
try {
  const validatedData = KajabiOrderSchema.parse(payload.data);
  // Safe to use validatedData
} catch (error) {
  console.error('Invalid payload:', error);
  return new Response(
    JSON.stringify({ error: 'Invalid payload format' }),
    { status: 400 }
  );
}
```

---

## SQL Injection Prevention

### Current Issue

```jsx
// ❌ VULNERABLE
query = query.or(`email.ilike.%${searchTerm}%`)
```

### Solution: Input Sanitization

```jsx
// ✅ FIXED
function sanitizeSearchTerm(term: string): string {
  // Only allow alphanumeric, @, ., _, -, and spaces
  return term.replace(/[^a-zA-Z0-9@._\-\s]/g, '');
}

const sanitizedSearch = sanitizeSearchTerm(searchTerm);
query = query.or(`email.ilike.%${sanitizedSearch}%,first_name.ilike.%${sanitizedSearch}%`);
```

**Even Better: Use Supabase's Built-in Escaping**

```jsx
// Supabase handles escaping automatically with textSearch
query = query.textSearch('email', searchTerm, {
  type: 'websearch',
  config: 'english'
});
```

---

## Error Message Sanitization

### Current Issue

```typescript
// ❌ Exposes internal details
return new Response(
  JSON.stringify({ error: error.message }), // Shows stack traces, DB errors
  { status: 500 }
);
```

### Solution: Generic Error Messages

```typescript
// ✅ FIXED
function sanitizeError(error: unknown): string {
  // Log detailed error server-side
  console.error('Internal error:', error);

  // Return generic message to client
  if (error instanceof ValidationError) {
    return 'Invalid request data';
  }
  if (error instanceof AuthenticationError) {
    return 'Unauthorized';
  }
  return 'Internal server error';
}

return new Response(
  JSON.stringify({
    error: sanitizeError(error),
    requestId: crypto.randomUUID() // For tracking in logs
  }),
  { status: 500 }
);
```

---

## Security Headers

### Add to All Webhook Responses

```typescript
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': "default-src 'self'",
  'Referrer-Policy': 'strict-origin-when-cross-origin'
};

return new Response(
  JSON.stringify(result),
  {
    status: 200,
    headers: { ...corsHeaders, ...securityHeaders }
  }
);
```

---

## Security Checklist

### Pre-Production Deployment

- [ ] Webhook signature verification implemented for all 3 platforms
- [ ] All API keys moved to environment variables
- [ ] Exposed keys rotated
- [ ] `.env` added to `.gitignore`
- [ ] Rate limiting enabled on all endpoints
- [ ] Input validation added (Zod schemas)
- [ ] SQL injection prevention implemented
- [ ] Error messages sanitized
- [ ] Security headers added
- [ ] HTTPS enforced (Supabase default)
- [ ] Database RLS policies tested
- [ ] Secret rotation schedule established (quarterly)

### Ongoing Security

- [ ] Weekly security audit of logs
- [ ] Monthly dependency updates (`npm audit`)
- [ ] Quarterly access key rotation
- [ ] Annual penetration testing
- [ ] Security incident response plan documented

---

## Testing Security

### Test Webhook Signature Verification

```bash
# Test with invalid signature (should fail)
curl -X POST https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/kajabi-webhook \
  -H "Content-Type: application/json" \
  -H "X-Kajabi-Signature: invalid-signature" \
  -d '{"event_type": "order.created"}'

# Expected: 401 Unauthorized
```

### Test Rate Limiting

```bash
# Send 101 requests in 1 minute (should block after 100)
for i in {1..101}; do
  curl -X POST https://your-webhook-url
done

# Request 101 should return: 429 Too Many Requests
```

---

## Rollout Plan

### Phase 1: Webhook Verification (Day 1)
1. Add signature verification code
2. Deploy to staging
3. Test with real webhook events
4. Deploy to production with monitoring

### Phase 2: Secret Management (Day 2)
1. Set up environment variables in Supabase
2. Update all functions to use env vars
3. Rotate exposed keys
4. Update web app `.env`

### Phase 3: Rate Limiting & Validation (Day 3)
1. Implement rate limiting middleware
2. Add Zod validation schemas
3. Deploy and monitor error rates

---

## Monitoring Security

After implementing these fixes, monitor:

1. **Failed signature verifications** (potential attacks)
2. **Rate limit hits** (suspicious IPs)
3. **Validation failures** (malformed payloads)
4. **Unauthorized access attempts**

Set up alerts for:
- More than 10 signature failures in 5 minutes
- Single IP hitting rate limits repeatedly
- Spike in 401/403 errors

---

## Next Steps

1. ✅ Read this guide
2. ➡️ Implement [Webhook Authentication](./WEBHOOK_AUTHENTICATION.md)
3. ➡️ Set up [Secret Management](./SECRET_MANAGEMENT.md)
4. ➡️ Configure monitoring for security events

---

**Critical:** Do not deploy to production until all checklist items are complete.
