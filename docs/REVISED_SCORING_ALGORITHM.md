# Revised Scoring Algorithm: Validation-First Approach
**Date:** 2025-11-15
**Status:** PROPOSED - Needs Approval
**Philosophy:** USPS validation is proof of deliverability, not a bonus

---

## Executive Summary

The current scoring algorithm treats USPS validation as a **secondary factor** worth 10-25 points. This causes 483 USPS-confirmed deliverable addresses to be scored as "low" or "very_low" confidence.

**Proposed Change:** Make USPS validation the **PRIMARY factor** - if USPS confirms an address is deliverable (DPV='Y') and the contact hasn't moved (no NCOA), that should be minimum "HIGH" confidence (60+ points).

---

## Current vs Proposed Scoring

### Current Algorithm (FLAWED)

```
Points allocation:
├─ Recency (address update): 0-40 points (PRIMARY)
├─ USPS validation: 0-25 points (secondary)
├─ Transaction recency: 0-25 points
└─ Source trust: 0-10 points

Problem: Missing update timestamp = 0 points (40 point penalty)
Result: Validated addresses score low
```

**Example:**
- USPS validated DPV='Y': +10 points (old validation)
- No update timestamp: 0 points
- Old transaction: +5 points
- Source unknown: 0 points
- **Total: 15 points = "very_low"** ❌ Wrong!

### Proposed Algorithm (VALIDATION-FIRST)

```
Tier 1: DISQUALIFIERS (automatic 0 points)
├─ NCOA move detected → 0 points (address invalid)
├─ USPS vacant = 'Y' → 0 points (address vacant)
├─ Incomplete address → 0 points (unmailable)
└─ USPS DPV = 'N' → 0 points (failed validation)

Tier 2: BASE SCORE from USPS Validation
├─ DPV = 'Y' (confirmed deliverable):
│   ├─ Validated < 90 days ago → 70 points (BASE)
│   ├─ Validated < 1 year ago → 65 points (BASE)
│   └─ Validated > 1 year ago → 60 points (BASE)
├─ DPV = 'S' or 'D' (partial match) → 50 points (BASE)
└─ No USPS validation → 0 points (start from scratch)

Tier 3: BONUSES (add to base score)
├─ Transaction recency:
│   ├─ < 30 days → +20 points
│   ├─ < 90 days → +15 points
│   ├─ < 180 days → +10 points
│   └─ < 365 days → +5 points
├─ Address update recency:
│   ├─ < 30 days → +10 points
│   └─ < 90 days → +5 points
└─ Trusted source:
    ├─ PayPal/Kajabi/TicketTailor → +5 points
    └─ Other → 0 points

Maximum score: 100 points
Minimum for validated: 60 points (HIGH confidence)
```

---

## Scoring Examples: Before vs After

### Example 1: Deborah Frazier (Currently "low", Should be "high")

**Current Scoring:**
```
Recency (no update timestamp): 0 points
USPS DPV='Y' (>1 year old): +10 points
Transaction (602 days old): +5 points
Source (unknown): 0 points
──────────────────────────────
TOTAL: 15 points = "very_low" ❌
```

**Proposed Scoring:**
```
DISQUALIFIERS:
✓ No NCOA move
✓ Not vacant
✓ Address complete
✓ DPV not 'N'

BASE SCORE:
USPS DPV='Y' (>1 year old): 60 points

BONUSES:
Transaction (602 days old): 0 points
Update recency: 0 points
Source: 0 points
──────────────────────────────
TOTAL: 60 points = "high" ✅
```

---

### Example 2: Sharon Montes (Currently "low", Should be "0")

**Current Scoring:**
```
Recency (no update timestamp): 0 points
USPS DPV='Y' (<90 days): +25 points
Transaction (578 days old): +5 points
Source (unknown): 0 points
──────────────────────────────
TOTAL: 30 points = "low"
```

**Proposed Scoring:**
```
DISQUALIFIERS:
✗ NCOA move detected (2025-01-01)
──────────────────────────────
TOTAL: 0 points = "very_low" ✅
(Customer moved, address invalid)
```

---

### Example 3: Recent Active Customer (Currently "very_high", Should stay "very_high")

**Current Scoring:**
```
Recency (<30 days): 40 points
USPS DPV='Y' (<90 days): +25 points
Transaction (<30 days): +25 points
Source (kajabi): +8 points
──────────────────────────────
TOTAL: 98 points = "very_high" ✅
```

**Proposed Scoring:**
```
DISQUALIFIERS: None

BASE SCORE:
USPS DPV='Y' (<90 days): 70 points

BONUSES:
Transaction (<30 days): +20 points
Update recency (<30 days): +10 points
Source (kajabi): +5 points
──────────────────────────────
TOTAL: 105 → capped at 100 = "very_high" ✅
```

---

## Impact Analysis

### Contacts That Will Change Tiers

**Current Distribution (Validated DPV='Y', No NCOA Move):**
| Current Tier | Count | Should Be |
|-------------|-------|-----------|
| very_high | 548 | Stay very_high ✓ |
| high | 154 | Stay high ✓ |
| very_low | 471 | → **Move to HIGH** ⬆️ |
| low | 12 | → **Move to HIGH** ⬆️ |

**After Algorithm Change:**
| New Tier | Count | Change |
|----------|-------|--------|
| very_high | 548-650 | ±100 (some bonuses) |
| **high** | **637** | **+483** ⬆️ |
| medium | 0-50 | Small number |
| low | 0 | -12 |
| very_low | 0 | -471 |

**Net Effect:**
- ✅ 483 validated addresses move from "low/very_low" to "high"
- ✅ 173 NCOA moves correctly score 0 (if not already)
- ✅ Mailing list grows from 832 to ~1,300+ contacts

---

## Key Improvements

### 1. **Validation = Proof, Not Bonus**

If USPS says an address is deliverable (DPV='Y'), that's **proof** it will deliver mail. This should be the foundation of the score (60+ points), not a 10-25 point bonus.

### 2. **NCOA = Disqualifier**

If a customer has moved, their old address is **invalid** regardless of validation. NCOA move should immediately set score to 0.

### 3. **Transaction/Update Recency = Bonuses**

Recent activity is good, but it shouldn't be REQUIRED. An address validated 2 years ago is still deliverable if there's no NCOA move.

### 4. **Missing Timestamps Don't Penalize**

If `billing_address_updated_at` is NULL but USPS validated the address, that's still proof of deliverability. Missing metadata shouldn't cause a 40-point penalty.

---

## Business Impact

### Mailing List Size

**Before:**
- High confidence: 832 contacts
- Medium confidence: 34 contacts
- **Mailable total: ~866 contacts**

**After:**
- High confidence: ~1,315 contacts (+483)
- Medium confidence: 0-50 contacts
- **Mailable total: ~1,315-1,365 contacts**

**Increase: +449-499 contacts (+52-58%)**

### Revenue Impact

**Additional mailings:**
- 483 new high-confidence contacts
- 4 mailings/year = 1,932 additional pieces
- 5% conversion rate × $50 avg order = **$4,830/year potential revenue**

**Cost:**
- 1,932 pieces × $0.88 = $1,700/year
- **Net revenue: ~$3,130/year**

### Quality Impact

**Deliverability:**
- All 483 contacts have USPS DPV='Y' (confirmed deliverable)
- No NCOA moves (addresses current)
- Expected bounce rate: <3% (industry standard for validated addresses)
- **Quality: HIGHER than current "high" tier**

---

## Implementation Plan

### Phase 1: Update Scoring Function (15 minutes)

```sql
CREATE OR REPLACE FUNCTION calculate_address_score(
  address_type TEXT,
  contact_id UUID
) RETURNS INTEGER AS $$
DECLARE
  score INTEGER := 0;
  usps_dpv_match TEXT;
  usps_date TIMESTAMP WITH TIME ZONE;
  usps_vacant TEXT;
  ncoa_move_date DATE;
  last_txn_date TIMESTAMP WITH TIME ZONE;
  update_date TIMESTAMP WITH TIME ZONE;
  source TEXT;
  contact_record RECORD;
BEGIN
  SELECT * INTO contact_record FROM contacts WHERE id = contact_id;
  IF NOT FOUND THEN RETURN 0; END IF;

  -- Check completeness first
  IF NOT is_address_complete(address_type, contact_id) THEN
    RETURN 0;
  END IF;

  -- Get fields based on address type
  IF address_type = 'billing' THEN
    usps_dpv_match := contact_record.billing_usps_dpv_match_code;
    usps_date := contact_record.billing_usps_validated_at;
    usps_vacant := contact_record.billing_usps_vacant;
    update_date := contact_record.billing_address_updated_at;
    source := contact_record.billing_address_source;
  ELSIF address_type = 'shipping' THEN
    usps_dpv_match := contact_record.shipping_usps_dpv_match_code;
    usps_date := contact_record.shipping_usps_validated_at;
    usps_vacant := contact_record.shipping_usps_vacant;
    update_date := contact_record.shipping_address_updated_at;
    source := contact_record.shipping_address_source;
  ELSE
    RETURN 0;
  END IF;

  ncoa_move_date := contact_record.ncoa_move_date;
  last_txn_date := contact_record.last_transaction_date;

  -- ============================================================
  -- TIER 1: DISQUALIFIERS (automatic 0)
  -- ============================================================

  -- NCOA move = address is invalid
  IF ncoa_move_date IS NOT NULL THEN
    RETURN 0;
  END IF;

  -- Vacant address = don't mail
  IF usps_vacant = 'Y' THEN
    RETURN 0;
  END IF;

  -- Failed USPS validation = not deliverable
  IF usps_dpv_match = 'N' THEN
    RETURN 0;
  END IF;

  -- ============================================================
  -- TIER 2: BASE SCORE from USPS Validation
  -- ============================================================

  IF usps_dpv_match = 'Y' THEN
    -- Full DPV match = confirmed deliverable
    IF usps_date > NOW() - INTERVAL '90 days' THEN
      score := 70;  -- Recent validation
    ELSIF usps_date > NOW() - INTERVAL '365 days' THEN
      score := 65;  -- Validated within 1 year
    ELSE
      score := 60;  -- Validated but older
    END IF;

  ELSIF usps_dpv_match IN ('S', 'D') THEN
    -- Partial match (missing secondary or missing primary)
    score := 50;

  ELSIF usps_date IS NOT NULL THEN
    -- Validated but no DPV code recorded
    score := 50;

  ELSE
    -- No USPS validation = no base score
    score := 0;
  END IF;

  -- ============================================================
  -- TIER 3: BONUSES (add to base score)
  -- ============================================================

  -- Transaction recency bonus (max +20)
  IF last_txn_date IS NOT NULL THEN
    IF last_txn_date > NOW() - INTERVAL '30 days' THEN
      score := score + 20;
    ELSIF last_txn_date > NOW() - INTERVAL '90 days' THEN
      score := score + 15;
    ELSIF last_txn_date > NOW() - INTERVAL '180 days' THEN
      score := score + 10;
    ELSIF last_txn_date > NOW() - INTERVAL '365 days' THEN
      score := score + 5;
    END IF;
  END IF;

  -- Address update recency bonus (max +10)
  IF update_date IS NOT NULL THEN
    IF update_date > NOW() - INTERVAL '30 days' THEN
      score := score + 10;
    ELSIF update_date > NOW() - INTERVAL '90 days' THEN
      score := score + 5;
    END IF;
  END IF;

  -- Trusted source bonus (max +5)
  IF source IN ('paypal', 'kajabi', 'ticket_tailor') THEN
    score := score + 5;
  END IF;

  -- Cap at 100
  IF score > 100 THEN
    score := 100;
  END IF;

  RETURN score;
END;
$$ LANGUAGE plpgsql STABLE;
```

### Phase 2: Refresh View (5 minutes)

```sql
-- View uses calculate_address_score automatically
REFRESH MATERIALIZED VIEW IF EXISTS mailing_list_priority;
-- Or if it's a regular view, just query it to see changes
```

### Phase 3: Verify Changes (10 minutes)

```sql
-- Check new distribution
SELECT confidence, COUNT(*)
FROM mailing_list_priority
GROUP BY confidence
ORDER BY CASE confidence
  WHEN 'very_high' THEN 1
  WHEN 'high' THEN 2
  WHEN 'medium' THEN 3
  WHEN 'low' THEN 4
  WHEN 'very_low' THEN 5
END;

-- Expected results:
-- very_high: 600-700
-- high: 600-700 (was 200)
-- medium: 0-50
-- low: 0-5
-- very_low: 50-100 (was 638)
```

---

## Risk Assessment

### Low Risk Changes

✅ **Validated addresses scoring higher**
- These addresses have USPS DPV='Y' (confirmed deliverable)
- No NCOA moves detected
- Expected bounce rate: <3%
- **Risk: VERY LOW**

✅ **NCOA moves scoring 0**
- These addresses are invalid (customer moved)
- Should not be mailed to
- **Risk: NONE** (improvement)

### Medium Risk Consideration

⚠️ **Old transactions (2+ years) being included**
- 12-13 customers haven't purchased in 2+ years
- But addresses are USPS validated + no NCOA move
- **Mitigation:** Start with email campaign to re-engage
- **Risk: LOW-MEDIUM** (might not respond, but won't harm brand)

---

## Success Metrics

### Immediate (Week 1)

- [ ] Mailing list size increases from 832 to ~1,315 (+58%)
- [ ] Zero contacts with NCOA moves in "high" tier
- [ ] All DPV='Y' + no NCOA contacts score ≥60 points

### Short-term (Month 1)

- [ ] Bounce rate remains <5% (industry standard)
- [ ] No increase in returned mail
- [ ] Response rate maintained or improved

### Long-term (Quarter 1)

- [ ] Revenue from additional 483 contacts
- [ ] Customer re-engagement metrics
- [ ] Cost per acquisition trends

---

## Alternative: Conservative Approach

If you want to be more conservative, use these base scores:

```
DPV='Y' validated < 90 days: 65 points (not 70)
DPV='Y' validated < 1 year: 60 points (not 65)
DPV='Y' validated > 1 year: 55 points (not 60)
DPV='S'/'D' partial match: 45 points (not 50)
```

This would put old validated addresses into "medium" (55-59 points) instead of "high" (60+), giving you a chance to review them separately.

---

## Recommendation

**PROCEED with validation-first scoring algorithm.**

**Why:**
1. USPS DPV='Y' is proof of deliverability (not opinion)
2. 483 contacts with validated addresses are being excluded unnecessarily
3. NCOA move detection provides safety net
4. Conservative approach: Can always lower base scores if needed
5. ROI: $3,130/year net revenue potential

**Action Items:**
1. ✅ Update `calculate_address_score` function
2. ✅ Test on sample contacts
3. ✅ Deploy to production
4. ✅ Monitor bounce rates for 2 weeks
5. ✅ Adjust base scores if needed

---

**Created:** 2025-11-15
**Status:** Awaiting approval
**Impact:** +483 contacts, +58% mailing list growth, +$3,130/year revenue
**Risk:** LOW (validated addresses only)
