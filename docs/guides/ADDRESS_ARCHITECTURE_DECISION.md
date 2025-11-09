# 🏗️ Address Architecture Decision

## Context

Received feedback suggesting normalized `addresses` table vs current denormalized approach in `contacts` table.

## Current Data Analysis

```
Total Contacts: 5,912
- Has billing address: 836 (14.1%)
- Has shipping address: 934 (15.8%)
- Has DIFFERENT billing/shipping: 69 (1.2% of total, 7.4% of those with addresses)
```

**Key Insight:** 93% of contacts with addresses use the SAME address for billing and shipping.

---

## Option A: Keep Denormalized (Current Approach)

### Schema
```sql
-- Addresses stored directly in contacts table
contacts:
  - address_line_1, address_line_2, city, state, postal_code, country (billing)
  - shipping_address_line_1, shipping_address_line_2, ... (shipping)
  - phone
  - paypal_phone
```

### Pros
✅ **Simple queries** - No JOINs required
✅ **Fast reads** - Single table lookup
✅ **Works for 93% of use cases** - Most contacts have one address
✅ **Already implemented** - 934 addresses standardized
✅ **Good for email marketing** - Simple SELECT with WHERE clauses

### Cons
❌ **No address history** - Can't track when address changed
❌ **No source tracking per address** - Can't tell which source provided address
❌ **Limited to 2 addresses** - Billing + shipping only
❌ **No verification tracking** - Can't mark PayPal as "verified"

### Best For
- Simple CRM needs
- Email marketing focus
- <10% contacts need multiple addresses
- **This is YOU! ✅**

---

## Option B: Normalized Addresses Table (Reviewer Suggestion)

### Schema
```sql
CREATE TABLE addresses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id uuid REFERENCES contacts(id) ON DELETE CASCADE,
  address_type text CHECK (address_type IN ('billing','shipping')),
  line1 text NOT NULL,
  line2 text,
  city text NOT NULL,
  state text NOT NULL,
  postal_code text NOT NULL,
  country_code char(2) NOT NULL,
  verified boolean DEFAULT false,
  verification_source text, -- 'paypal_verified', 'usps_verified', 'self_reported'
  source_system text NOT NULL, -- 'kajabi', 'paypal', 'ticket_tailor', 'manual'
  is_primary boolean DEFAULT false,
  valid_from timestamptz DEFAULT now(),
  valid_to timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX idx_addresses_contact ON addresses(contact_id);
CREATE INDEX idx_addresses_type ON addresses(contact_id, address_type, is_primary);
CREATE UNIQUE INDEX idx_addresses_primary ON addresses(contact_id, address_type)
  WHERE is_primary = true;

-- Enhanced contacts table
ALTER TABLE contacts
  ADD COLUMN phone_country_code text,
  ADD COLUMN phone_verified boolean DEFAULT false,
  ADD COLUMN phone_source text;
```

### Pros
✅ **Address history** - Track all address changes over time
✅ **Source attribution** - Know which system provided each address
✅ **Verification tracking** - Mark PayPal addresses as verified
✅ **Multiple addresses** - Support vacation homes, offices, etc.
✅ **Better audit trail** - When did address change, from what source?
✅ **Data quality scoring** - Rank addresses by verification level

### Cons
❌ **Complex queries** - Every query needs JOIN
❌ **Migration required** - Move 934 addresses to new table
❌ **Slower reads** - More tables to join
❌ **Over-engineered for 93%** - Most contacts don't need this
❌ **More maintenance** - Cascade deletes, orphaned records

### Best For
- E-commerce platforms (multiple shipping addresses)
- High-value donors (track residence changes)
- International operations (complex address validation)
- **NOT your current scale**

---

## Option C: Hybrid Approach (RECOMMENDED)

**Keep current schema + add minimal enhancements**

### Phase 1: Enhance Current Schema (Immediate)

```sql
-- Add verification and source tracking to existing fields
ALTER TABLE contacts
  -- Phone enhancements
  ADD COLUMN phone_country_code text,
  ADD COLUMN phone_verified boolean DEFAULT false,
  ADD COLUMN phone_source text, -- 'kajabi', 'ticket_tailor', 'paypal'

  -- Billing address metadata
  ADD COLUMN billing_address_source text, -- 'kajabi', 'paypal', 'ticket_tailor', 'manual'
  ADD COLUMN billing_address_verified boolean DEFAULT false,
  ADD COLUMN billing_address_updated_at timestamptz,

  -- Shipping address metadata (already have shipping_address_status)
  ADD COLUMN shipping_address_source text,
  ADD COLUMN shipping_address_verified boolean DEFAULT false,
  ADD COLUMN shipping_address_updated_at timestamptz;

-- Update existing shipping addresses copied from billing
UPDATE contacts
SET
  shipping_address_source = 'copied_from_billing',
  shipping_address_verified = false,
  shipping_address_updated_at = updated_at
WHERE shipping_address_status = 'Non-Confirmed'
  AND address_line_1 = shipping_address_line_1;

-- Mark PayPal addresses as verified when they come in
-- (handled in webhook code)
```

### Phase 2: Optional Address History Table (When Needed)

```sql
-- Create ONLY if you need to track address changes over time
CREATE TABLE address_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id uuid REFERENCES contacts(id) ON DELETE CASCADE,
  address_type text, -- 'billing', 'shipping'

  -- Address snapshot
  line1 text,
  line2 text,
  city text,
  state text,
  postal_code text,
  country_code char(2),

  -- Metadata
  source_system text,
  verified boolean,
  valid_from timestamptz NOT NULL,
  valid_to timestamptz,

  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_address_history_contact ON address_history(contact_id, valid_from DESC);
```

### Implementation Strategy

**Webhook Updates:**
```typescript
// PayPal webhook - mark as verified
const updates = {
  shipping_address_line_1: shippingAddr.line1,
  // ... other fields
  shipping_address_source: 'paypal',
  shipping_address_verified: true, // PayPal verified!
  shipping_address_updated_at: new Date().toISOString()
}

// Kajabi webhook - mark as unverified
const updates = {
  address_line_1: billingAddr.line1,
  // ... other fields
  billing_address_source: 'kajabi',
  billing_address_verified: false, // Self-reported
  billing_address_updated_at: new Date().toISOString()
}
```

### Pros
✅ **Simple migration** - Just add columns
✅ **Backward compatible** - Existing queries still work
✅ **Verification tracking** - Mark PayPal as verified
✅ **Source tracking** - Know where each address came from
✅ **Can add history later** - If needed, add address_history table
✅ **Meets 93% of needs** - Works for current scale

### Cons
⚠️ **Still limited to 2 addresses** - Billing + shipping only
⚠️ **No full history** - Unless you add Phase 2

---

## Decision Matrix

| Criteria | Denormalized (A) | Normalized (B) | Hybrid (C) |
|----------|------------------|----------------|------------|
| **Complexity** | ⭐ Simple | ⭐⭐⭐ Complex | ⭐⭐ Moderate |
| **Migration Effort** | ✅ None | ❌ High | ⭐ Low |
| **Query Performance** | ✅ Fast | ⚠️ Slower | ✅ Fast |
| **Verification Tracking** | ❌ No | ✅ Yes | ✅ Yes |
| **Source Attribution** | ❌ No | ✅ Yes | ✅ Yes |
| **Address History** | ❌ No | ✅ Yes | 🟡 Optional |
| **Multiple Addresses** | ❌ Max 2 | ✅ Unlimited | ❌ Max 2 |
| **Fits Current Scale** | ✅ Yes | ❌ Over-kill | ✅ Yes |
| **Future Proof** | ⚠️ Limited | ✅ Very | ✅ Good |

---

## Recommendation: **Option C - Hybrid Approach**

### Why?
1. **Your data shows 93% of contacts need only 1 address** - Don't over-engineer
2. **You can track verification + source** - Meets reviewer's core concerns
3. **Migration is trivial** - Just add columns, not restructure
4. **Fast queries** - No JOINs required for 99% of queries
5. **Can evolve** - Add address_history table if needed later

### When to Switch to Option B (Normalized)?
- **If >20% of contacts need multiple addresses**
- **If you're doing address verification at scale** (USPS, Google)
- **If you need full audit trail** for compliance
- **If you're building e-commerce** with multiple shipping addresses

---

## Implementation Plan (Hybrid)

### Step 1: Add Metadata Columns (5 minutes)
```sql
ALTER TABLE contacts
  ADD COLUMN phone_country_code text,
  ADD COLUMN phone_verified boolean DEFAULT false,
  ADD COLUMN phone_source text,
  ADD COLUMN billing_address_source text,
  ADD COLUMN billing_address_verified boolean DEFAULT false,
  ADD COLUMN billing_address_updated_at timestamptz,
  ADD COLUMN shipping_address_source text,
  ADD COLUMN shipping_address_verified boolean DEFAULT false,
  ADD COLUMN shipping_address_updated_at timestamptz;
```

### Step 2: Update Webhook Handlers (30 minutes)
- PayPal: Set `shipping_address_verified = true`
- Kajabi: Set `billing_address_verified = false`
- Ticket Tailor: Set `billing_address_verified = false`
- All: Set `*_source` and `*_updated_at`

### Step 3: Backfill Existing Data (10 minutes)
```sql
-- Mark existing shipping addresses
UPDATE contacts
SET
  shipping_address_source = 'unknown_legacy',
  shipping_address_verified = false,
  shipping_address_updated_at = updated_at
WHERE shipping_address_line_1 IS NOT NULL;

-- Mark existing billing addresses
UPDATE contacts
SET
  billing_address_source = 'unknown_legacy',
  billing_address_verified = false,
  billing_address_updated_at = updated_at
WHERE address_line_1 IS NOT NULL;
```

### Step 4: Create Monitoring Queries (5 minutes)
```sql
-- Address verification rate by source
SELECT
  shipping_address_source,
  COUNT(*) as total,
  SUM(CASE WHEN shipping_address_verified THEN 1 ELSE 0 END) as verified,
  ROUND(100.0 * SUM(CASE WHEN shipping_address_verified THEN 1 ELSE 0 END) / COUNT(*), 2) as verified_pct
FROM contacts
WHERE shipping_address_line_1 IS NOT NULL
GROUP BY shipping_address_source
ORDER BY total DESC;
```

---

## Response to Reviewer's Specific Points

### ✅ Agree With:
1. **Phone country code** - Adding `phone_country_code` column
2. **Verification tracking** - Adding `*_verified` boolean fields
3. **Source tracking** - Adding `*_source` fields
4. **ISO country codes** - Already using char(2) in country field
5. **PayPal highest priority** - Webhooks will mark as verified

### 🤔 Partially Agree:
1. **Separate addresses table** - Good for e-commerce, overkill for your scale
2. **Multiple addresses per contact** - Only 1.2% of your contacts need this
3. **Address history** - Nice to have, but you can add later via address_history table

### ❌ Don't Need (Yet):
1. **Complex JOINs** - 93% of contacts have 1 address
2. **Migration overhead** - Can evolve schema incrementally
3. **E.164 phone normalization** - Good idea but can add later via function

---

## Success Metrics (After Implementation)

**Week 1:**
- [ ] 100% of new PayPal addresses marked `verified = true`
- [ ] 100% of addresses have `source_system` populated
- [ ] All addresses have `updated_at` timestamp

**Month 1:**
- [ ] >50% of shipping addresses are verified (from PayPal)
- [ ] Address source breakdown tracked and reviewed
- [ ] Zero duplicate addresses for same contact

**Quarter 1:**
- [ ] Decide if you need address_history table
- [ ] Decide if you need normalized addresses table
- [ ] Review if 20%+ contacts need multiple addresses

---

## When to Revisit This Decision

**Go to normalized `addresses` table if:**
1. **>15% of contacts** need 3+ addresses
2. **You're processing >1000 address changes/month**
3. **Address verification becomes critical** (donor receipts, tax compliance)
4. **You need full audit trail** for regulatory compliance
5. **You're building e-commerce features**

**For now, hybrid approach is the sweet spot.** 🎯

