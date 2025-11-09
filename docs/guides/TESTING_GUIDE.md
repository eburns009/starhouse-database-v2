# Testing Strategy & Implementation Guide

**Priority:** 🟠 P1 (High)
**Last Updated:** October 30, 2025
**Estimated Time:** 1-2 weeks
**Current Coverage:** 0% → Target: 80%+

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Testing Setup](#testing-setup)
4. [Unit Tests](#unit-tests)
5. [Integration Tests](#integration-tests)
6. [End-to-End Tests](#end-to-end-tests)
7. [Test Coverage Goals](#test-coverage-goals)
8. [Running Tests](#running-tests)
9. [CI Integration](#ci-integration)

---

## Overview

**Current State:** 0% test coverage ⚠️
**Target State:** 80% coverage minimum

### Why Testing Matters

Without tests, every code change is a risk:
- ❌ No confidence in refactoring
- ❌ Bugs discovered in production
- ❌ Slower development (manual testing)
- ❌ Difficult to onboard new developers

With tests:
- ✅ Fast feedback on changes
- ✅ Living documentation
- ✅ Safe refactoring
- ✅ Prevents regressions

---

## Testing Philosophy

### Testing Pyramid

```
        /\        5% - E2E Tests (slow, expensive)
       /  \
      /    \      15% - Integration Tests
     /      \
    /        \    80% - Unit Tests (fast, cheap)
   /          \
  --------------
```

### Test Priority

1. **Critical Path First**
   - Webhook processing (money-related)
   - Contact creation/deduplication
   - Transaction recording

2. **Business Logic**
   - Data validation
   - Calculations (totals, summaries)
   - Status transitions

3. **UI Components** (lower priority)
   - Form validation
   - Data display
   - User interactions

---

## Testing Setup

### 1. Webhook Functions (Deno)

**Install Deno** (if not already):
```bash
curl -fsSL https://deno.land/install.sh | sh
```

**Project Structure:**
```
supabase/functions/
├── kajabi-webhook/
│   ├── index.ts
│   └── index.test.ts          # ← Add this
├── paypal-webhook/
│   ├── index.ts
│   └── index.test.ts          # ← Add this
├── ticket-tailor-webhook/
│   ├── index.ts
│   └── index.test.ts          # ← Add this
└── _shared/
    ├── rateLimit.ts
    ├── rateLimit.test.ts      # ← Add this
    ├── validation.ts
    └── validation.test.ts     # ← Add this
```

### 2. Python Scripts

**Install pytest:**
```bash
cd /workspaces/starhouse-database-v2
python3 -m pip install pytest pytest-cov
```

**Project Structure:**
```
scripts/
├── update_contacts_from_transactions.py
├── test_update_contacts.py             # ← Add this
├── update_products_with_offers.py
├── test_update_products.py             # ← Add this
└── conftest.py                         # ← Shared fixtures
```

### 3. Web App (React)

**Install Vitest:**
```bash
cd web-app
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**Update `package.json`:**
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

**Create `vitest.config.js`:**
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/']
    }
  }
})
```

---

## Unit Tests

### Webhook Unit Tests

**Example: `supabase/functions/kajabi-webhook/index.test.ts`**

```typescript
import { assertEquals, assertRejects } from "https://deno.land/std@0.168.0/testing/asserts.ts";
import { handleOrder, findOrCreateContact, verifyKajabiSignature } from "./index.ts";

// Mock Supabase client
const mockSupabase = {
  from: (table: string) => ({
    select: () => ({
      eq: () => ({
        single: () => Promise.resolve({ data: null, error: null })
      })
    }),
    upsert: () => ({
      select: () => ({
        single: () => Promise.resolve({
          data: { id: 'mock-id', email: 'test@example.com' },
          error: null
        })
      })
    }),
    insert: () => ({
      select: () => Promise.resolve({ data: [], error: null })
    })
  })
};

Deno.test("handleOrder - creates transaction with valid payload", async () => {
  const mockPayload = {
    id: 'order-123',
    email: 'test@example.com',
    amount: '100.00',
    currency: 'USD',
    status: 'completed',
    first_name: 'John',
    last_name: 'Doe'
  };

  const result = await handleOrder(mockSupabase, mockPayload);

  assertEquals(result.message, 'Transaction processed');
  assertEquals(result.data !== null, true);
});

Deno.test("handleOrder - throws error with missing email", async () => {
  const mockPayload = {
    id: 'order-123',
    amount: '100.00'
    // Missing email
  };

  await assertRejects(
    async () => await handleOrder(mockSupabase, mockPayload),
    Error,
    "No email found"
  );
});

Deno.test("handleOrder - handles negative amounts", async () => {
  const mockPayload = {
    id: 'refund-123',
    email: 'test@example.com',
    amount: '-50.00', // Refund
    status: 'completed'
  };

  const result = await handleOrder(mockSupabase, mockPayload);
  assertEquals(result.message, 'Transaction processed');
});

Deno.test("verifyKajabiSignature - accepts valid signature", () => {
  const payload = JSON.stringify({ test: 'data' });
  const secret = 'test-secret';

  // Generate valid signature
  const hmac = createHmac('sha256', secret);
  hmac.update(payload);
  const signature = hmac.digest('hex');

  const result = verifyKajabiSignature(payload, signature, secret);
  assertEquals(result, true);
});

Deno.test("verifyKajabiSignature - rejects invalid signature", () => {
  const payload = JSON.stringify({ test: 'data' });
  const secret = 'test-secret';
  const badSignature = 'invalid-signature';

  const result = verifyKajabiSignature(payload, badSignature, secret);
  assertEquals(result, false);
});

Deno.test("findOrCreateContact - creates new contact", async () => {
  const payload = {
    email: 'newuser@example.com',
    first_name: 'Jane',
    last_name: 'Smith'
  };

  const contact = await findOrCreateContact(mockSupabase, payload);

  assertEquals(contact.email, 'newuser@example.com');
  assertEquals(contact.id !== null, true);
});

Deno.test("findOrCreateContact - returns existing contact", async () => {
  // Mock existing contact
  const existingContact = { id: 'existing-id', email: 'existing@example.com' };

  const mockSupabaseWithData = {
    from: () => ({
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({ data: existingContact, error: null })
        })
      })
    })
  };

  const payload = { email: 'existing@example.com' };
  const contact = await findOrCreateContact(mockSupabaseWithData, payload);

  assertEquals(contact.id, 'existing-id');
});
```

**Run Deno tests:**
```bash
cd supabase/functions
deno test --allow-env --allow-net
```

---

### Python Unit Tests

**Example: `scripts/test_update_contacts.py`**

```python
import pytest
from update_contacts_from_transactions import (
    compute_contact_summaries,
    read_transactions
)

def test_compute_summaries_groups_by_email():
    """Test that transactions are grouped correctly by email"""
    transactions = [
        {
            'Customer Email': 'test@example.com',
            'Amount': '50.00',
            'Status': 'succeeded',
            'Created At': '2025-01-01',
            'Payment Method': 'card',
            'Coupon Used': '',
            'Offer ID': 'offer-1',
            'Offer Title': 'Test Offer',
            'Address': '123 Main St',
            'Address 2': '',
            'City': 'Denver',
            'State': 'CO',
            'Zipcode': '80202',
            'Country': 'US',
            'Phone': '555-1234',
            'Customer Name': 'John Doe',
            'Type': 'purchase'
        },
        {
            'Customer Email': 'test@example.com',
            'Amount': '25.00',
            'Status': 'succeeded',
            'Created At': '2025-01-15',
            'Payment Method': 'card',
            'Coupon Used': 'SAVE10',
            'Offer ID': 'offer-1',
            'Offer Title': 'Test Offer',
            'Address': '123 Main St',
            'Address 2': '',
            'City': 'Denver',
            'State': 'CO',
            'Zipcode': '80202',
            'Country': 'US',
            'Phone': '555-1234',
            'Customer Name': 'John Doe',
            'Type': 'purchase'
        }
    ]

    summaries = compute_contact_summaries(transactions)

    assert 'test@example.com' in summaries
    assert summaries['test@example.com']['total_spent'] == 75.00
    assert summaries['test@example.com']['transaction_count'] == 2
    assert summaries['test@example.com']['total_coupons_used'] == 1

def test_compute_summaries_excludes_failed_transactions():
    """Test that failed transactions are excluded from calculations"""
    transactions = [
        {
            'Customer Email': 'test@example.com',
            'Amount': '50.00',
            'Status': 'failed',
            'Created At': '2025-01-01',
            'Payment Method': 'card',
            'Coupon Used': '',
            'Offer ID': '',
            'Offer Title': '',
            'Address': '',
            'Address 2': '',
            'City': '',
            'State': '',
            'Zipcode': '',
            'Country': '',
            'Phone': '',
            'Customer Name': '',
            'Type': 'purchase'
        }
    ]

    summaries = compute_contact_summaries(transactions)
    assert len(summaries) == 0

def test_compute_summaries_handles_refunds():
    """Test that refunds result in negative total_spent"""
    transactions = [
        {
            'Customer Email': 'test@example.com',
            'Amount': '100.00',
            'Status': 'succeeded',
            'Created At': '2025-01-01',
            # ... other fields
        },
        {
            'Customer Email': 'test@example.com',
            'Amount': '-100.00',  # Refund
            'Status': 'succeeded',
            'Created At': '2025-01-02',
            # ... other fields
        }
    ]

    summaries = compute_contact_summaries(transactions)
    assert summaries['test@example.com']['total_spent'] == 0.00
    assert summaries['test@example.com']['transaction_count'] == 2

def test_compute_summaries_picks_most_recent_address():
    """Test that the most recent address is used"""
    transactions = [
        {
            'Customer Email': 'test@example.com',
            'Amount': '50.00',
            'Status': 'succeeded',
            'Created At': '2025-01-01',
            'Address': '123 Old St',
            'City': 'OldCity',
            # ... other fields
        },
        {
            'Customer Email': 'test@example.com',
            'Amount': '25.00',
            'Status': 'succeeded',
            'Created At': '2025-01-15',
            'Address': '456 New St',
            'City': 'NewCity',
            # ... other fields
        }
    ]

    summaries = compute_contact_summaries(transactions)
    assert summaries['test@example.com']['address']['address_line_1'] == '456 New St'
    assert summaries['test@example.com']['address']['city'] == 'NewCity'

def test_email_case_insensitive():
    """Test that email comparison is case-insensitive"""
    transactions = [
        {'Customer Email': 'Test@Example.com', 'Amount': '50.00', 'Status': 'succeeded', ...},
        {'Customer Email': 'test@example.com', 'Amount': '25.00', 'Status': 'succeeded', ...}
    ]

    summaries = compute_contact_summaries(transactions)
    assert len(summaries) == 1  # Should merge
    assert summaries['test@example.com']['transaction_count'] == 2
```

**Run Python tests:**
```bash
pytest scripts/ -v --cov=scripts --cov-report=html
```

---

### React Component Tests

**Example: `web-app/src/components/__tests__/ContactsList.test.jsx`**

```jsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ContactsList from '../ContactsList';
import { supabase } from '../../lib/supabase';

// Mock Supabase
vi.mock('../../lib/supabase', () => ({
  supabase: {
    from: vi.fn()
  }
}));

describe('ContactsList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('displays loading state initially', () => {
    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          range: vi.fn().mockReturnValue(
            Promise.resolve({ data: [], count: 0 })
          )
        })
      })
    });

    render(<ContactsList />);
    expect(screen.getByText(/loading contacts/i)).toBeInTheDocument();
  });

  test('displays contacts after loading', async () => {
    const mockContacts = [
      {
        id: '1',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        source_system: 'kajabi',
        updated_at: '2025-01-01T00:00:00Z'
      }
    ];

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          range: vi.fn().mockReturnValue(
            Promise.resolve({ data: mockContacts, count: 1 })
          )
        }),
        eq: vi.fn().mockReturnThis()
      })
    });

    render(<ContactsList />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  test('filters contacts by search term', async () => {
    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          or: vi.fn().mockReturnValue({
            range: vi.fn().mockReturnValue(
              Promise.resolve({ data: [], count: 0 })
            )
          })
        })
      })
    });

    render(<ContactsList />);

    const searchInput = await screen.findByPlaceholderText(/search/i);
    fireEvent.change(searchInput, { target: { value: 'john' } });

    // Wait for debounce
    await waitFor(() => {
      expect(supabase.from).toHaveBeenCalled();
    }, { timeout: 600 });
  });

  test('opens contact details modal on row click', async () => {
    const mockContacts = [
      {
        id: '1',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        phone: '555-1234',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      }
    ];

    supabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        order: vi.fn().mockReturnValue({
          range: vi.fn().mockReturnValue(
            Promise.resolve({ data: mockContacts, count: 1 })
          )
        })
      })
    });

    render(<ContactsList />);

    await waitFor(() => {
      const row = screen.getByText('test@example.com').closest('tr');
      fireEvent.click(row);
    });

    expect(screen.getByText('Contact Details')).toBeInTheDocument();
    expect(screen.getByText('555-1234')).toBeInTheDocument();
  });

  test('exports to CSV', async () => {
    // Test CSV export functionality
    // ... implementation
  });
});
```

**Run React tests:**
```bash
cd web-app
npm test
```

---

## Integration Tests

Integration tests verify that components work together correctly.

**Example: Test full webhook flow**

```typescript
// supabase/functions/kajabi-webhook/integration.test.ts

import { assertEquals } from "https://deno.land/std@0.168.0/testing/asserts.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

Deno.test("Full webhook flow - order creates contact and transaction", async () => {
  // Use test database
  const supabase = createClient(
    Deno.env.get('TEST_SUPABASE_URL'),
    Deno.env.get('TEST_SUPABASE_KEY')
  );

  // Clean up test data
  await supabase.from('transactions').delete().eq('kajabi_transaction_id', 'test-order-123');
  await supabase.from('contacts').delete().eq('email', 'integration-test@example.com');

  // Send webhook request
  const response = await fetch('http://localhost:54321/functions/v1/kajabi-webhook', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${Deno.env.get('TEST_SUPABASE_KEY')}`
    },
    body: JSON.stringify({
      event_type: 'order.created',
      data: {
        id: 'test-order-123',
        email: 'integration-test@example.com',
        first_name: 'Integration',
        last_name: 'Test',
        amount: '99.99',
        currency: 'USD',
        status: 'completed'
      }
    })
  });

  assertEquals(response.status, 200);

  // Verify contact was created
  const { data: contact } = await supabase
    .from('contacts')
    .select('*')
    .eq('email', 'integration-test@example.com')
    .single();

  assertEquals(contact.first_name, 'Integration');
  assertEquals(contact.last_name, 'Test');

  // Verify transaction was created
  const { data: transaction } = await supabase
    .from('transactions')
    .select('*')
    .eq('kajabi_transaction_id', 'test-order-123')
    .single();

  assertEquals(transaction.amount, 99.99);
  assertEquals(transaction.contact_id, contact.id);

  // Clean up
  await supabase.from('transactions').delete().eq('id', transaction.id);
  await supabase.from('contacts').delete().eq('id', contact.id);
});
```

---

## Test Coverage Goals

### Minimum Coverage Requirements

| Component | Minimum Coverage | Current | Target |
|-----------|-----------------|---------|--------|
| Webhook Functions | 80% | 0% | 90% |
| Python Scripts | 70% | 0% | 80% |
| React Components | 60% | 0% | 70% |
| Critical Business Logic | 100% | 0% | 100% |

### Critical Paths (Must be 100%)

- ✅ Contact creation/deduplication
- ✅ Transaction recording
- ✅ Webhook signature verification
- ✅ Payment calculations
- ✅ Refund handling

---

## Running Tests

### All Tests

```bash
# Root directory script
./scripts/run-all-tests.sh
```

**Create `scripts/run-all-tests.sh`:**
```bash
#!/bin/bash
set -e

echo "🧪 Running all tests..."

echo "\n📦 Testing webhooks (Deno)..."
cd supabase/functions
deno test --allow-env --allow-net

echo "\n🐍 Testing Python scripts..."
cd ../../
pytest scripts/ -v --cov=scripts

echo "\n⚛️  Testing web app (React)..."
cd web-app
npm test -- --run

echo "\n✅ All tests passed!"
```

### Watch Mode (Development)

```bash
# Webhooks
cd supabase/functions
deno test --watch

# Python
pytest scripts/ --watch

# React
cd web-app
npm test
```

---

## CI Integration

**Create `.github/workflows/test.yml`:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-webhooks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: denoland/setup-deno@v1
        with:
          deno-version: v1.x
      - name: Run webhook tests
        run: |
          cd supabase/functions
          deno test --allow-env --allow-net

  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install pytest pytest-cov
      - name: Run Python tests
        run: pytest scripts/ -v --cov=scripts --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  test-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd web-app
          npm ci
      - name: Run tests
        run: |
          cd web-app
          npm test -- --run --coverage
```

---

## Next Steps

1. ✅ Set up testing frameworks
2. ➡️ Write tests for critical paths (webhooks)
3. ➡️ Add integration tests
4. ➡️ Configure CI pipeline
5. ➡️ Enforce coverage thresholds

**Start with:** Webhook signature verification tests (most critical)

---

**Related Docs:**
- [CI/CD Setup](./CICD_SETUP.md)
- [Code Quality Standards](../standards/CODE_QUALITY.md)
