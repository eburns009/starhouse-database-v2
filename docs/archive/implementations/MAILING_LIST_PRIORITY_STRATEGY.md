# MAILING LIST ADDRESS PRIORITY STRATEGY
**Date:** 2025-11-14  
**Problem:** Need reliable mailing addresses when contacts have multiple addresses  
**Example Case:** Ed Burns - Southampton PA (old, 7+ years) vs Boulder CO (current)

---

## Executive Summary

**Challenge:** 6,878 contacts, 22% have billing addresses, 18% have shipping addresses. Need a priority system to choose the BEST mailing address.

**Solution:** Multi-factor scoring algorithm based on:
1. Address update timestamps
2. Transaction usage dates
3. USPS validation status
4. Address source (PayPal vs Kajabi vs manual)
5. Verification flags

**Result:** Confidence-scored mailing list with "most likely current" address for each contact.

---

## Current Data Quality Assessment

### Address Coverage

| Metric | Count | % of Total |
|--------|-------|------------|
| Total contacts | 6,878 | 100% |
| **Has billing address** | 1,538 | 22% |
| **Has shipping address** | 1,219 | 18% |
| Has transaction history | 878 | 13% |
| Has both billing & shipping | ~659 | ~10% (estimated) |

### Validation Status

| Validation Type | Billing | Shipping |
|----------------|---------|----------|
| `address_verified` flag | 688 (45%) | 150 (12%) |
| USPS validated | 739 (48%) | 0 (0%) |
| Has update timestamp | 827 (54%) | 837 (69%) |

**Key Insight:** Billing addresses are MUCH better validated than shipping addresses.

---

## Problem Case Study: Ed Burns

**Email:** eburns009@gmail.com

### Address #1: Southampton, PA (Billing)
```
Address: 1144 Rozel Ave, Southampton, PA 18966
Source: unknown_legacy
Verified: TRUE
USPS Validated: 2025-11-04 (validated!)
Last Updated: 2025-11-01
Status: Ed hasn't lived here for 7 years ❌
```

### Address #2: Boulder, CO (Shipping)
```
Address: PO Box 4547, Boulder, CO 80302
Source: copied_from_billing
Verified: FALSE
USPS Validated: Never
Last Updated: 2025-11-01
Status: Ed's CURRENT address ✅
```

### Problem Analysis

1. **USPS validation doesn't mean "current residence"**
   - PA address is valid (mailbox exists)
   - But Ed doesn't live there anymore
   - USPS validation = "deliverable" ≠ "recipient lives here"

2. **Shipping address marked as `copied_from_billing`**
   - Not from PayPal (contradicts earlier finding)
   - Never USPS validated
   - Shows as "Non-Confirmed"

3. **Last transaction: 2025-10-05**
   - Recent purchase
   - Which address was used? Unknown (transactions don't store addresses)

### The Challenge

**How do we know Boulder is current when:**
- It has LOWER validation score than Southampton
- It's marked as "copied" and "non-confirmed"
- We have no transaction address history

**Answer:** We need HUMAN INTELLIGENCE + DATA SIGNALS

---

## Available Data Fields for Prioritization

### Timestamps (Most Important)

| Field | What It Tells Us | Coverage |
|-------|-----------------|----------|
| `billing_address_updated_at` | When billing address last changed | 827 (54%) |
| `shipping_address_updated_at` | When shipping address last changed | 837 (69%) |
| `last_transaction_date` | Most recent purchase | 878 (13%) |
| `billing_usps_validated_at` | When USPS validated billing | 739 (48% of billing) |
| `first_transaction_date` | Customer since... | 878 (13%) |
| `updated_at` | Contact record last touched | 6,878 (100%) |

### Verification Flags

| Field | What It Tells Us | Coverage |
|-------|-----------------|----------|
| `billing_address_verified` | Address confirmed somehow | 688 (45% of billing) |
| `shipping_address_verified` | Shipping confirmed | 150 (12% of shipping) |
| `billing_usps_validated_at` | USPS says deliverable | 739 (48%) |
| `shipping_usps_validated_at` | USPS shipping validation | 0 (0%) |

### Source Tracking (Unreliable)

| Field | What It Tells Us | Coverage |
|-------|-----------------|----------|
| `billing_address_source` | Where it came from | ~0% populated |
| `shipping_address_source` | Where it came from | ~10 records (PayPal) |
| `shipping_address_status` | PayPal status | Some records |

**Problem:** Source tracking was added recently, not backfilled.

---

## Address Priority Algorithm (Proposed)

### Scoring System (0-100 points)

Each address (billing vs shipping) gets scored on multiple factors:

#### Factor 1: Recency (40 points max)

**Last Updated Timestamp:**
- Updated in last 30 days: +40 points
- Updated in last 90 days: +30 points
- Updated in last 180 days: +20 points
- Updated in last 365 days: +10 points
- Older than 1 year: +0 points
- No timestamp: +0 points

**Logic:** More recently updated = more likely to be current

#### Factor 2: Validation (25 points max)

**USPS Validated:**
- USPS validated in last 90 days: +25 points
- USPS validated in last 365 days: +20 points
- USPS validated but older: +10 points
- Never validated: +0 points

**Address Verified Flag:**
- If verified: +5 points (bonus if no USPS)

**Logic:** Validated addresses are deliverable, but dated validation matters less

#### Factor 3: Transaction Usage (25 points max)

**Last Transaction Date:**
- Transaction in last 30 days: +25 points
- Transaction in last 90 days: +20 points
- Transaction in last 180 days: +15 points
- Transaction in last 365 days: +10 points
- Transaction older: +5 points
- No transactions: +0 points

**Logic:** If customer is actively purchasing, address is likely current

#### Factor 4: Source Trust (10 points)

**Address Source:**
- `paypal` (from payment): +10 points
- `kajabi` (from enrollment): +8 points
- `manual` (staff entry): +7 points
- `copied_from_billing`: +3 points
- `unknown_legacy`: +0 points

**Logic:** PayPal addresses are from actual transactions (best signal)

### Priority Decision Tree

```
FOR EACH CONTACT:
  IF has_billing_address:
    billing_score = calculate_score(billing_*)
  ELSE:
    billing_score = 0
    
  IF has_shipping_address:
    shipping_score = calculate_score(shipping_*)
  ELSE:
    shipping_score = 0
    
  IF billing_score >= shipping_score + 15:  # 15 point threshold
    primary_address = billing
    confidence = "HIGH" if billing_score > 60 else "MEDIUM"
  ELSE IF shipping_score >= billing_score + 15:
    primary_address = shipping
    confidence = "HIGH" if shipping_score > 60 else "MEDIUM"
  ELSE:
    # Scores within 15 points = tie
    primary_address = billing  # Default to billing on tie
    confidence = "LOW - VERIFY NEEDED"
    
  IF primary_address_score < 30:
    confidence = "VERY LOW - MANUAL REVIEW"
```

### Confidence Levels

| Score | Confidence | Action |
|-------|-----------|--------|
| 75-100 | Very High | Safe to mail |
| 60-74 | High | Safe to mail |
| 45-59 | Medium | Mail but monitor returns |
| 30-44 | Low | Verify before expensive mailings |
| 0-29 | Very Low | Manual review required |

---

## Ed Burns Scored Example

### Billing Address (Southampton, PA)
```
Recency:
  - Updated 2025-11-01 (13 days ago): +40 points
Validation:
  - USPS validated 2025-11-04 (10 days ago): +25 points
  - Verified flag TRUE: +0 (already has USPS)
Transaction:
  - Last transaction 2025-10-05 (40 days ago): +20 points
Source:
  - unknown_legacy: +0 points
  
TOTAL: 85 points (Very High confidence)
```

### Shipping Address (Boulder, CO)
```
Recency:
  - Updated 2025-11-01 (13 days ago): +40 points
Validation:
  - Never USPS validated: +0 points
  - Verified flag FALSE: +0 points
Transaction:
  - Last transaction 2025-10-05 (40 days ago): +20 points
Source:
  - copied_from_billing: +3 points
  
TOTAL: 63 points (High confidence)
```

### Decision

**Algorithm says:** Billing (85) > Shipping (63) → Use Southampton PA ❌

**WRONG!** This is exactly the problem.

### Why Algorithm Failed

1. **USPS validation gave false confidence** (+25 points to wrong address)
2. **No "address change" signal** - both updated same day
3. **Transaction doesn't tell us WHICH address was used**
4. **Source "copied_from_billing" is a red flag we didn't weight enough**

---

## Enhanced Algorithm (v2)

### Additional Signals Needed

#### 1. Address Change Detection

```sql
-- Detect if an address was CHANGED vs just re-validated
-- Track in audit_log when address fields change vs just timestamps
```

**If billing was recently CHANGED (not just updated):** -20 points (old address phased out)  
**If shipping was recently ADDED/CHANGED:** +20 points (new address established)

#### 2. Source Trust Refinement

```
copied_from_billing: -10 points (RED FLAG - derived, not authoritative)
unknown_legacy: -5 points (old data, uncertain)
paypal: +15 points (from actual transaction)
```

#### 3. Address Type Heuristics

```
IF shipping is PO Box AND billing is street address:
  shipping +10 points (people use PO boxes for delivery preference)
  
IF billing looks abandoned (USPS vacant flag):
  billing -30 points
  
IF addresses in different cities:
  # One is likely old
  Favor the one with recent transaction
```

#### 4. Staff Override Field

Add to contacts table:
```sql
ALTER TABLE contacts ADD COLUMN preferred_mailing_address TEXT;
-- Values: 'billing', 'shipping', 'other'
-- NULL = use algorithm
```

### Ed Burns with Enhanced Algorithm

```
Billing (Southampton):
  Base: 85 points
  - "unknown_legacy" penalty: -5
  - Different city from shipping: inspect transaction...
  TOTAL: 80 points

Shipping (Boulder):
  Base: 63 points
  - "copied_from_billing" penalty: -10
  - PO Box bonus (delivery preference): +10
  - Staff member address (3472 Sunshine Canyon): +15 (if we add this rule)
  TOTAL: 78 points
```

**Still wrong**, but closer. We need the human override.

---

## Recommended Implementation Plan

### Phase 1: Immediate (This Week)

**1. Create Mailing List View**

```sql
CREATE OR REPLACE VIEW mailing_list_priority AS
SELECT 
  c.id,
  c.email,
  c.first_name,
  c.last_name,
  
  -- Billing address
  c.address_line_1 as billing_line1,
  c.address_line_2 as billing_line2,
  c.city as billing_city,
  c.state as billing_state,
  c.postal_code as billing_zip,
  
  -- Shipping address
  c.shipping_address_line_1 as shipping_line1,
  c.shipping_address_line_2 as shipping_line2,
  c.shipping_city,
  c.shipping_state,
  c.shipping_postal_code as shipping_zip,
  
  -- Scoring factors
  c.billing_address_updated_at,
  c.shipping_address_updated_at,
  c.billing_usps_validated_at,
  c.billing_address_verified,
  c.shipping_address_verified,
  c.last_transaction_date,
  c.billing_address_source,
  c.shipping_address_source,
  
  -- Calculated scores (using function)
  calculate_address_score('billing', c.*) as billing_score,
  calculate_address_score('shipping', c.*) as shipping_score,
  
  -- Priority decision
  CASE 
    WHEN calculate_address_score('billing', c.*) >= 
         calculate_address_score('shipping', c.*) + 15 
    THEN 'billing'
    WHEN calculate_address_score('shipping', c.*) >= 
         calculate_address_score('billing', c.*) + 15 
    THEN 'shipping'
    ELSE 'billing'  -- Tie goes to billing
  END as recommended_address,
  
  -- Confidence
  CASE 
    WHEN GREATEST(
      calculate_address_score('billing', c.*),
      calculate_address_score('shipping', c.*)
    ) >= 75 THEN 'very_high'
    WHEN GREATEST(...) >= 60 THEN 'high'
    WHEN GREATEST(...) >= 45 THEN 'medium'
    WHEN GREATEST(...) >= 30 THEN 'low'
    ELSE 'very_low'
  END as confidence
  
FROM contacts c
WHERE c.address_line_1 IS NOT NULL OR c.shipping_address_line_1 IS NOT NULL;
```

**2. Create Scoring Function**

```sql
CREATE OR REPLACE FUNCTION calculate_address_score(
  address_type TEXT,  -- 'billing' or 'shipping'
  contact contacts
) RETURNS INTEGER AS $$
DECLARE
  score INTEGER := 0;
  update_date TIMESTAMP;
  usps_date TIMESTAMP;
  verified BOOLEAN;
  source TEXT;
BEGIN
  -- Get the right fields based on type
  IF address_type = 'billing' THEN
    update_date := contact.billing_address_updated_at;
    usps_date := contact.billing_usps_validated_at;
    verified := contact.billing_address_verified;
    source := contact.billing_address_source;
  ELSE
    update_date := contact.shipping_address_updated_at;
    usps_date := contact.shipping_usps_validated_at;
    verified := contact.shipping_address_verified;
    source := contact.shipping_address_source;
  END IF;
  
  -- Factor 1: Recency (40 points)
  IF update_date IS NOT NULL THEN
    IF update_date > NOW() - INTERVAL '30 days' THEN
      score := score + 40;
    ELSIF update_date > NOW() - INTERVAL '90 days' THEN
      score := score + 30;
    ELSIF update_date > NOW() - INTERVAL '180 days' THEN
      score := score + 20;
    ELSIF update_date > NOW() - INTERVAL '365 days' THEN
      score := score + 10;
    END IF;
  END IF;
  
  -- Factor 2: USPS Validation (25 points)
  IF usps_date IS NOT NULL THEN
    IF usps_date > NOW() - INTERVAL '90 days' THEN
      score := score + 25;
    ELSIF usps_date > NOW() - INTERVAL '365 days' THEN
      score := score + 20;
    ELSE
      score := score + 10;
    END IF;
  ELSIF verified THEN
    score := score + 5;
  END IF;
  
  -- Factor 3: Transaction recency (25 points)
  IF contact.last_transaction_date IS NOT NULL THEN
    IF contact.last_transaction_date > NOW() - INTERVAL '30 days' THEN
      score := score + 25;
    ELSIF contact.last_transaction_date > NOW() - INTERVAL '90 days' THEN
      score := score + 20;
    ELSIF contact.last_transaction_date > NOW() - INTERVAL '180 days' THEN
      score := score + 15;
    ELSIF contact.last_transaction_date > NOW() - INTERVAL '365 days' THEN
      score := score + 10;
    ELSE
      score := score + 5;
    END IF;
  END IF;
  
  -- Factor 4: Source trust (10 points)
  IF source = 'paypal' THEN
    score := score + 10;
  ELSIF source = 'kajabi' THEN
    score := score + 8;
  ELSIF source = 'manual' THEN
    score := score + 7;
  ELSIF source = 'copied_from_billing' THEN
    score := score - 10;  -- PENALTY!
  ELSIF source = 'unknown_legacy' THEN
    score := score - 5;   -- PENALTY!
  END IF;
  
  RETURN score;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

**3. Export Mailing List**

```sql
-- Get high-confidence mailing list
COPY (
  SELECT 
    first_name,
    last_name,
    email,
    CASE 
      WHEN recommended_address = 'billing' THEN billing_line1
      ELSE shipping_line1
    END as address_line_1,
    CASE 
      WHEN recommended_address = 'billing' THEN billing_line2
      ELSE shipping_line2
    END as address_line_2,
    CASE 
      WHEN recommended_address = 'billing' THEN billing_city
      ELSE shipping_city
    END as city,
    CASE 
      WHEN recommended_address = 'billing' THEN billing_state
      ELSE shipping_state
    END as state,
    CASE 
      WHEN recommended_address = 'billing' THEN billing_zip
      ELSE shipping_zip
    END as postal_code,
    recommended_address as source_type,
    confidence
  FROM mailing_list_priority
  WHERE confidence IN ('very_high', 'high')
  ORDER BY last_name, first_name
) TO '/tmp/mailing_list_high_confidence.csv' CSV HEADER;
```

### Phase 2: Quality Improvement (Next 2 Weeks)

**1. Add Preferred Address Override**

```sql
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS preferred_mailing_address TEXT;
COMMENT ON COLUMN contacts.preferred_mailing_address IS 
  'Staff override: billing, shipping, or NULL to use algorithm';
```

**2. Manual Review Process**

```sql
-- Export low-confidence contacts for manual review
SELECT * FROM mailing_list_priority
WHERE confidence IN ('low', 'very_low')
ORDER BY last_transaction_date DESC NULLS LAST;
```

**3. USPS Validate Shipping Addresses**

Run script similar to `import_usps_validation_safe.py` but for shipping addresses.

**4. Backfill Source Tracking**

```sql
-- Infer sources from external_identities
UPDATE contacts c
SET 
  billing_address_source = 'kajabi',
  billing_address_updated_at = COALESCE(billing_address_updated_at, c.created_at)
FROM external_identities ei
WHERE c.id = ei.contact_id
AND ei.system = 'kajabi'
AND c.billing_address_source IS NULL;

-- Mark PayPal shipping addresses
UPDATE contacts
SET shipping_address_source = 'paypal'
WHERE shipping_address_source IS NULL
AND shipping_address_verified = true;
```

### Phase 3: Ongoing Maintenance (Continuous)

**1. Webhook Updates**

Ensure PayPal/Kajabi webhooks set:
- `*_address_source`
- `*_address_updated_at`
- `*_address_verified`

**2. Staff UI**

Add "Preferred Mailing Address" field to contact edit form.

**3. Return Mail Handling**

When mail returns:
```sql
UPDATE contacts 
SET 
  billing_address_verified = FALSE,
  billing_usps_validated_at = NULL
WHERE email = 'returned@example.com';
```

**4. Periodic Re-validation**

Monthly job: Re-validate addresses older than 6 months.

---

## Validation of All Fields (Audit)

### Currently Validated

| Field | Validation Type | Status |
|-------|----------------|--------|
| `billing_usps_validated_at` | USPS API | ✅ 739 records |
| `billing_address_verified` | DPV match code | ✅ 688 records |
| `billing_usps_*` (many fields) | USPS data | ✅ Comprehensive |

### Missing Validation

| Field | Current State | Needed |
|-------|---------------|--------|
| `shipping_usps_validated_at` | NULL (0 records) | ❌ USPS validation needed |
| `shipping_address_verified` | Only 150 records | ❌ Needs validation |
| `*_address_source` | Mostly NULL | ❌ Backfill needed |
| `*_address_updated_at` | 54-69% populated | ⚠️ Incomplete |

### Recommendation

**Priority 1:** USPS validate all shipping addresses  
**Priority 2:** Backfill source tracking  
**Priority 3:** Ensure all new addresses get timestamps/sources via webhooks

---

## Key Insights & Answers

### Q: Is shipping or billing better for mailing?

**A: Depends, but generally BILLING is more reliable:**

| Factor | Billing | Shipping |
|--------|---------|----------|
| Validation coverage | 48% USPS validated | 0% USPS validated |
| Verification rate | 45% | 12% |
| Update timestamps | 54% | 69% |
| **Recommendation** | **Better for most** | Only if high-scoring |

**Exception:** If shipping score is 15+ points higher, use shipping.

### Q: Are there dates beyond import dates?

**A: YES!** Multiple timestamp fields:

- `billing_address_updated_at` - When billing changed (827 records)
- `shipping_address_updated_at` - When shipping changed (837 records)
- `last_transaction_date` - Most recent purchase (878 records)
- `billing_usps_validated_at` - USPS validation date (739 records)

**These are NOT import dates** - they track actual address lifecycle events.

### Q: Are all fields validated?

**A: NO.**

**Well Validated:**
- ✅ Billing addresses (48% USPS, 45% verified)
- ✅ USPS metadata (DPV, precision, county, lat/long)

**Poorly Validated:**
- ❌ Shipping addresses (0% USPS, 12% verified)
- ❌ Source tracking (mostly NULL)
- ❌ Address update timestamps (46-54% missing)

**Action:** Run USPS validation on shipping, backfill sources, enforce webhooks to populate metadata.

---

## Next Steps

**Immediate Actions:**

1. ✅ Review this strategy document
2. ⏳ Implement Phase 1 (SQL view + scoring function)
3. ⏳ Export high-confidence mailing list
4. ⏳ Manual review low-confidence addresses
5. ⏳ Fix Ed Burns' preferred address (manual override)

**Week 2:**

6. Run USPS validation on shipping addresses
7. Backfill source tracking
8. Add `preferred_mailing_address` column

**Ongoing:**

9. Update webhooks to populate all metadata fields
10. Build UI for staff to mark preferred addresses
11. Monitor return mail and update validation

---

## Files Referenced

1. `/workspaces/starhouse-database-v2/scripts/import_usps_validation_safe.py`
2. Database schema: `contacts` table
3. This document

---

**Strategy Status:** ✅ Complete and Ready for Review  
**Recommendation:** Start with Phase 1 SQL implementation, then manual review of Ed Burns case

