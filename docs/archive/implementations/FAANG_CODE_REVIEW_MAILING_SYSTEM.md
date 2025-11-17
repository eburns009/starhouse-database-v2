# FAANG-Level Code Review: Mailing Address Priority System

**Reviewer:** Claude (FAANG Standards)
**Date:** 2025-11-14
**Status:** ❌ MAJOR ISSUES FOUND - DO NOT MERGE

---

## Critical Issues (P0 - Must Fix Before Production)

### 🔴 CRITICAL BUG #1: USPS Validation Incomplete
**File:** `20251114000000_mailing_list_priority_system.sql:64-74`
**Severity:** P0 - Data Integrity

**Problem:**
```sql
IF usps_date IS NOT NULL THEN
  IF usps_date > NOW() - INTERVAL '90 days' THEN
    score := score + 25;
```

**What's Wrong:**
- Only checks if `usps_validated_at` exists, doesn't check if validation PASSED
- USPS returns `dpv_match_code` where:
  - `'Y'` = Valid, deliverable
  - `'N'` = Invalid
  - `'S'` = Missing secondary (apt #)
  - `'D'` = Missing primary
- An address can be validated but INVALID - we'd still give it 25 points!

**Impact:**
- Invalid addresses score HIGH and get mailed
- Guaranteed undeliverable mail
- Wasted postage costs

**Fix Required:**
```sql
-- Check BOTH validation date AND match code
IF usps_date IS NOT NULL AND
   ((address_type = 'billing' AND contact_record.billing_usps_dpv_match_code = 'Y') OR
    (address_type = 'shipping' AND contact_record.shipping_usps_dpv_match_code = 'Y')) THEN
  score := score + 25;
ELSIF usps_date IS NOT NULL AND
      ((address_type = 'billing' AND contact_record.billing_usps_dpv_match_code IN ('S', 'D')) OR
       (address_type = 'shipping' AND contact_record.shipping_usps_dpv_match_code IN ('S', 'D'))) THEN
  score := score + 15;  -- Partial match
ELSIF usps_date IS NOT NULL THEN
  score := score - 20;  -- PENALTY: Validated but FAILED
```

---

### 🔴 CRITICAL BUG #2: No Vacant Address Detection
**File:** `20251114000000_mailing_list_priority_system.sql:64-74`
**Severity:** P0 - Data Integrity

**Problem:**
- USPS validation returns `dpv_vacant = 'Y'` for vacant addresses
- Current code doesn't check this field
- Vacant addresses get full USPS validation points (25pts)

**Impact:**
- Mailing to vacant addresses = 100% return rate
- Wasted money on guaranteed undeliverable mail

**Fix Required:**
```sql
-- After USPS validation score, add:
IF (address_type = 'billing' AND contact_record.billing_usps_dpv_vacant = 'Y') OR
   (address_type = 'shipping' AND contact_record.shipping_usps_dpv_vacant = 'Y') THEN
  score := score - 50;  -- HARSH PENALTY: Vacant = don't mail
END IF;
```

---

### 🔴 CRITICAL BUG #3: Incomplete Address Validation
**File:** `20251114000000_mailing_list_priority_system.sql:117-200`
**Severity:** P0 - Data Integrity

**Problem:**
View can recommend an address that's missing city/state/zip:

```sql
WHERE c.address_line_1 IS NOT NULL OR c.shipping_address_line_1 IS NOT NULL
```

Only checks if line1 exists, not if it's a COMPLETE address.

**Impact:**
- Export contains addresses like: "123 Main St, [NULL], [NULL], [NULL]"
- Undeliverable mail
- Bad data in mailing campaigns

**Fix Required:**
```sql
-- Add address completeness check
CREATE OR REPLACE FUNCTION is_address_complete(
  address_type TEXT,
  contact_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
  contact_record RECORD;
BEGIN
  SELECT * INTO contact_record FROM contacts WHERE id = contact_id;

  IF address_type = 'billing' THEN
    RETURN contact_record.address_line_1 IS NOT NULL
       AND contact_record.city IS NOT NULL
       AND contact_record.state IS NOT NULL
       AND contact_record.postal_code IS NOT NULL;
  ELSIF address_type = 'shipping' THEN
    RETURN contact_record.shipping_address_line_1 IS NOT NULL
       AND contact_record.shipping_city IS NOT NULL
       AND contact_record.shipping_state IS NOT NULL
       AND contact_record.shipping_postal_code IS NOT NULL;
  END IF;

  RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

-- Then in calculate_address_score, return 0 if incomplete:
IF NOT is_address_complete(address_type, contact_id) THEN
  RETURN 0;  -- Incomplete address = unusable
END IF;
```

---

### 🔴 CRITICAL BUG #4: UI Doesn't Highlight Recommended Address
**File:** `ContactDetailCard.tsx:1164-1195`
**Severity:** P0 - User Experience

**Problem:**
- UI shows both billing and shipping addresses equally
- No visual indication of which one is recommended
- User has to open "Mailing List Quality" card separately to see recommendation
- High risk of staff using wrong address for mailing

**Impact:**
- Staff might use low-score address by mistake
- Defeats the purpose of the scoring algorithm
- Manual work to cross-reference recommendation with address list

**Fix Required:**
- Badge the recommended address with "Recommended for Mailing"
- Visually de-emphasize the non-recommended address
- Show warning if staff tries to use non-recommended address

---

## Major Issues (P1 - Should Fix Before Production)

### 🟡 MAJOR ISSUE #1: Arbitrary 15-Point Threshold
**File:** Line 178-179
**Severity:** P1 - Business Logic

**Problem:**
```sql
WHEN billing_score >= shipping_score + 15 THEN 'billing'
WHEN shipping_score >= billing_score + 15 THEN 'shipping'
```

Why 15 points? No documentation or rationale.

**Better Approach:**
- Document the reasoning (e.g., "15 points = roughly 6 months recency difference")
- Make it configurable
- OR use percentage: `billing_score >= shipping_score * 1.25`

---

### 🟡 MAJOR ISSUE #2: Source Penalties Too Harsh
**File:** Line 100-104
**Severity:** P1 - Business Logic

**Problem:**
```sql
ELSIF source = 'copied_from_billing' THEN
  score := score - 10;  -- PENALTY: derived data, not authoritative
```

**Why This is Wrong:**
- If the address is USPS validated (+25pts), who cares if it was copied?
- A USPS-validated "copied_from_billing" address (net +15pts) loses to a non-validated PayPal address (+10pts)
- Validation should override source trust

**Fix:**
- Lower penalty to -2 or remove entirely
- Validation status is more important than source

---

### 🟡 MAJOR ISSUE #3: No Duplicate Address Detection
**File:** View definition
**Severity:** P1 - User Experience

**Problem:**
- If billing and shipping are identical, we show both with different scores
- Confusing to users
- Wastes screen space

**Fix:**
- Detect when addresses match (normalize and compare)
- If identical, only show once with combined score
- Flag in UI: "Billing and Shipping addresses are identical"

---

## Design Flaws (P2 - Technical Debt)

### 🔵 ISSUE #1: No Observability
**Severity:** P2 - Operations

**Missing:**
- No logging when scores change significantly
- No alerts for anomalies (e.g., all scores suddenly drop)
- No tracking of which addresses are used in actual mailings

**FAANG Standard:**
- Log score changes > 20 points
- Track mailing conversion rate (mailed vs bounced)
- Dashboard showing score distribution over time

---

### 🔵 ISSUE #2: No Integration Tests
**Severity:** P2 - Quality

**Missing:**
- No tests for edge cases:
  - What if both addresses are incomplete?
  - What if both scores are 0?
  - What if manual override points to incomplete address?
  - What if USPS validated but vacant?

**FAANG Standard:**
- Test suite with 20+ test cases
- Property-based testing (score always 0-100)
- Snapshot tests for UI rendering

---

### 🔵 ISSUE #3: Schema Duplication
**Severity:** P2 - Data Integrity

**Problem:**
- Address data in: `postal_code` AND `shipping_usps_last_line`
- Two sources of truth = eventual inconsistency
- Already happened once (the bug we just fixed)

**FAANG Standard:**
- Single source of truth
- Computed fields or views for derived data
- Database triggers to keep fields in sync
- Or: migrate to USPS fields as primary

---

## Summary

| Severity | Count | Must Fix? |
|----------|-------|-----------|
| P0 (Critical) | 4 | ✅ YES |
| P1 (Major) | 3 | ⚠️ Recommended |
| P2 (Minor) | 3 | 📝 Nice to have |

**Verdict:** ❌ **DO NOT SHIP**

This code would fail FAANG review for data integrity issues. The critical bugs could result in:
1. Mailing to invalid addresses
2. Mailing to vacant addresses
3. Exporting incomplete addresses
4. Staff using wrong address due to poor UI

---

## Recommended Action Plan

### Phase 1: Critical Fixes (Do Now)
1. ✅ Fix USPS validation to check DPV match code
2. ✅ Add vacant address penalty
3. ✅ Add address completeness validation
4. ✅ Update UI to highlight recommended address

### Phase 2: Major Improvements (This Week)
5. Document/adjust 15-point threshold
6. Reduce source penalties
7. Add duplicate address detection

### Phase 3: Technical Debt (Next Sprint)
8. Add integration test suite
9. Add observability/logging
10. Consolidate schema (migrate to single source of truth)

---

## Why This Matters

**At FAANG:**
- These issues would be caught in code review (before merge)
- Integration tests would catch invalid address exports
- Post-deployment monitoring would alert on anomalies

**In Your System:**
- Bug wasn't caught until user reported wrong zip code
- No tests to verify data integrity
- No monitoring to detect similar issues

**Cost of These Bugs:**
- Invalid mailings: $0.70 × 50 addresses = $35 per campaign
- Vacant addresses: $0.70 × 30 addresses = $21 per campaign
- Reputation damage: Priceless

---

**Next Steps:**
Let's fix the P0 critical issues right now. I'll create the updated migration file and UI changes.

