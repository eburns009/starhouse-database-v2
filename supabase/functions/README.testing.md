# Testing Guide for Supabase Edge Functions

## Overview

This project uses **Deno Test** for testing Edge Functions. Tests are co-located with their functions for easy maintenance.

## Quick Start

### Install Deno

```bash
curl -fsSL https://deno.land/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"
```

### Run All Tests

```bash
# From project root
cd supabase/functions/kajabi-webhook
deno test --allow-env --allow-net index.test.ts
```

### Run Specific Test

```bash
deno test --allow-env --allow-net --filter "should reject invalid signature" index.test.ts
```

### Watch Mode (Re-run on Changes)

```bash
deno test --allow-env --allow-net --watch index.test.ts
```

## Test Structure

```
supabase/functions/
├── _shared/
│   ├── test-utils.ts          # Shared mocks and fixtures
│   └── webhook-security.ts     # Security utilities
├── kajabi-webhook/
│   ├── index.ts               # Handler implementation
│   ├── index.test.ts          # Tests
│   └── deno.json              # Deno config
├── paypal-webhook/
│   ├── index.ts
│   └── index.test.ts (TODO)
└── ticket-tailor-webhook/
    ├── index.ts
    └── index.test.ts (TODO)
```

## Test Categories

### Unit Tests (Current)
- Input validation
- Signature verification
- Sanitization functions
- Rate limiting logic

### Integration Tests (TODO)
- Database operations
- Atomic webhook processing
- Contact deduplication
- Transaction upserts

### End-to-End Tests (TODO)
- Real webhook payloads
- Full request/response cycle
- Error scenarios

## Writing Tests

### Example Test

```typescript
import { assertEquals } from "https://deno.land/std@0.168.0/testing/asserts.ts"
import { MockSupabaseClient, createMockRequest } from "../_shared/test-utils.ts"

Deno.test("My Feature - should work correctly", async () => {
  // Setup
  const mockClient = new MockSupabaseClient()
  mockClient.setMockData('contacts', [
    { id: '123', email: 'test@example.com' }
  ])

  // Execute
  const result = await myFunction(mockClient)

  // Assert
  assertEquals(result.success, true)
})
```

### Using Mock Supabase Client

```typescript
const mockClient = new MockSupabaseClient()

// Set mock data
mockClient.setMockData('contacts', [
  { id: 'uuid-1', email: 'test@example.com', first_name: 'John' }
])

// Query works like real Supabase client
const { data } = await mockClient
  .from('contacts')
  .select('*')
  .eq('email', 'test@example.com')
  .single()

// Check what methods were called
const calls = mockClient.getCalls()
console.log(calls) // [{ method: 'from', table: 'contacts' }, ...]
```

## CI/CD Integration

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request to `main`

See `.github/workflows/test.yml` for configuration.

## Current Test Coverage

### Kajabi Webhook: 16 tests
- ✅ Request validation (OPTIONS, POST, payload size)
- ✅ Signature verification (valid, invalid, missing)
- ✅ Rate limiting
- ✅ Event handling (order.created, tag.added)
- ✅ Input sanitization
- ✅ Error handling
- ✅ Timing attack prevention

### PayPal Webhook: 0 tests
- ⏳ TODO

### Ticket Tailor Webhook: 0 tests
- ⏳ TODO

### Shared Utilities: 0 tests
- ⏳ TODO

## Known Issues & Limitations

### Current Test Gaps
1. **No actual handler execution** - Tests verify requirements but don't yet call the actual handler
2. **No database integration** - Using mocks instead of real Supabase
3. **No process_webhook_atomically() tests** - Core security function not yet tested

### Next Steps
1. Refactor handlers to be testable (extract handler function from serve())
2. Add integration tests with real Supabase instance
3. Test atomic webhook processing
4. Add tests for PayPal and Ticket Tailor webhooks

## Debugging Tests

### Enable Debug Logging

```bash
DENO_LOG=debug deno test --allow-env --allow-net index.test.ts
```

### Run Single Test

```bash
deno test --allow-env --allow-net --filter "specific test name" index.test.ts
```

### Inspect Test Failures

Tests use Deno's built-in assertions which provide detailed error messages:

```
AssertionError: Values are not equal.

    [Diff] Actual / Expected

-   false
+   true
```

## Best Practices

1. **Test names should be descriptive** - "should reject invalid signature" not "test 1"
2. **One assertion per test** - Makes failures easy to diagnose
3. **Use fixtures** - Import from `test-utils.ts` for consistency
4. **Clean up after tests** - Restore environment variables
5. **Test edge cases** - Empty strings, null, undefined, malicious input

## Performance

```bash
# Run with coverage (requires --coverage flag)
deno test --allow-env --allow-net --coverage=coverage index.test.ts

# Generate coverage report
deno coverage coverage
```

## Resources

- [Deno Testing Docs](https://docs.deno.com/runtime/fundamentals/testing/)
- [Deno Assertions](https://deno.land/std/testing/asserts.ts)
- [Supabase Edge Functions](https://supabase.com/docs/guides/functions)
