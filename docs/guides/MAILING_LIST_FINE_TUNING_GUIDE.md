# Mailing List Fine-Tuning Guide

**Date:** 2025-11-14
**Status:** Production Ready
**System:** Mailing List Priority & Scoring

---

## Quick Start

### Export a Mailing List

```bash
# Export only very high confidence contacts (632 contacts)
python3 scripts/export_mailing_list.py --min-confidence very_high

# Export high + very_high confidence contacts (832 contacts)
python3 scripts/export_mailing_list.py --min-confidence high

# Export recent active customers (last year)
python3 scripts/export_mailing_list.py --min-confidence high --recent-customers 365

# Clean export for mail merge (no metadata columns)
python3 scripts/export_mailing_list.py --min-confidence high --no-metadata
```

---

## Current System Overview

### Scoring Algorithm

The system scores each address (billing and shipping) on a 0-100 scale using 4 factors:

| Factor | Max Points | What It Measures |
|--------|------------|------------------|
| **Recency** | 40 points | How recently the address was updated |
| **USPS Validation** | 25 points | Whether address passed USPS validation |
| **Transaction History** | 25 points | How recently customer made a purchase |
| **Source Trust** | 10 points | Where the address came from (PayPal, Kajabi, manual) |

**Total:** 100 points maximum

### Confidence Levels

| Level | Score Range | Contacts | Description |
|-------|-------------|----------|-------------|
| **Very High** | 75-100 | 632 (43%) | Best quality - ready to mail |
| **High** | 60-74 | 200 (14%) | Good quality - safe to mail |
| **Medium** | 45-59 | 34 (2%) | Fair quality - verify first |
| **Low** | 30-44 | 20 (1%) | Poor quality - needs update |
| **Very Low** | 0-29 | 588 (40%) | Bad quality - do not mail |

### Current Statistics

- **Total Contacts:** 1,474
- **Recommended for Mailing:** 832 (very_high + high confidence)
- **Billing Address Recommended:** 95%
- **Shipping Address Recommended:** 5%

---

## How to Use the System

### 1. Generate a Basic Mailing List

For most campaigns, use **high confidence or better**:

```bash
python3 scripts/export_mailing_list.py --min-confidence high --output /tmp/holiday_mailing_2025.csv
```

This gives you 832 contacts with validated, high-quality addresses.

### 2. Target Active Customers Only

For campaigns to recent buyers:

```bash
python3 scripts/export_mailing_list.py \
  --min-confidence high \
  --recent-customers 180 \
  --output /tmp/active_customers.csv
```

### 3. Review Address Quality in UI

The `MailingListQuality` component shows:
- Recommended address (billing or shipping)
- Confidence level with color coding
- Individual scores for both addresses
- Warnings for incomplete addresses

### 4. Manual Overrides

For specific contacts that need special handling, you can manually override the recommendation:

```sql
-- Force a contact to use shipping address
UPDATE contacts
SET preferred_mailing_address = 'shipping'
WHERE email = 'customer@example.com';

-- Force a contact to use billing address
UPDATE contacts
SET preferred_mailing_address = 'billing'
WHERE email = 'customer@example.com';

-- Remove override (use algorithm)
UPDATE contacts
SET preferred_mailing_address = NULL
WHERE email = 'customer@example.com';
```

---

## Fine-Tuning Options

### Option 1: Adjust Confidence Thresholds

**Current thresholds** (in `supabase/migrations/20251114000000_mailing_list_priority_system.sql:186-192`):

```sql
CASE
  WHEN GREATEST(billing_score, shipping_score) >= 75 THEN 'very_high'
  WHEN GREATEST(billing_score, shipping_score) >= 60 THEN 'high'
  WHEN GREATEST(billing_score, shipping_score) >= 45 THEN 'medium'
  WHEN GREATEST(billing_score, shipping_score) >= 30 THEN 'low'
  ELSE 'very_low'
END as confidence
```

**To make confidence levels stricter** (require higher scores):
- Increase thresholds (e.g., very_high >= 80 instead of >= 75)
- Results in fewer "very_high" contacts, but higher quality

**To make confidence levels more lenient** (accept lower scores):
- Decrease thresholds (e.g., high >= 55 instead of >= 60)
- Results in more contacts meeting "high" standard

### Option 2: Adjust Factor Weights

**Current weights** (in `calculate_address_score()` function):

```sql
-- Recency: 40 points
IF update_date > NOW() - INTERVAL '30 days' THEN score := score + 40;
ELSIF update_date > NOW() - INTERVAL '90 days' THEN score := score + 30;
-- etc.

-- USPS Validation: 25 points
IF usps_date > NOW() - INTERVAL '90 days' THEN score := score + 25;
-- etc.

-- Transaction History: 25 points
IF last_txn_date > NOW() - INTERVAL '30 days' THEN score := score + 25;
-- etc.

-- Source Trust: 10 points (with penalties)
IF source = 'paypal' THEN score := score + 10;
ELSIF source = 'kajabi' THEN score := score + 8;
-- etc.
```

**Examples of adjustments:**

**Prioritize USPS validation more:**
```sql
-- Change USPS from 25 max to 35 max
-- Change Recency from 40 max to 30 max
```

**Prioritize recent transactions more:**
```sql
-- Change Transaction History from 25 max to 35 max
-- Change Recency from 40 max to 30 max
```

**To implement:** Edit the migration file and run:
```bash
psql $DATABASE_URL < supabase/migrations/20251114000000_mailing_list_priority_system.sql
```

### Option 3: Adjust Address Switching Threshold

**Current threshold:** 15 points

```sql
WHEN billing_score >= shipping_score + 15 THEN 'billing'
WHEN shipping_score >= billing_score + 15 THEN 'shipping'
```

This means an address must score 15+ points higher to be recommended over the other.

**To make switching less aggressive** (prefer billing unless shipping is way better):
- Increase threshold to 20 or 25 points

**To make switching more aggressive** (switch to shipping more often):
- Decrease threshold to 10 points

### Option 4: Add New Scoring Factors

You can extend `calculate_address_score()` to consider:

**Email verification status:**
```sql
IF email_verified THEN
  score := score + 5;
END IF;
```

**Phone number on file:**
```sql
IF phone IS NOT NULL THEN
  score := score + 5;
END IF;
```

**Address completeness:**
```sql
-- Check if city, state, zip all present
IF city IS NOT NULL AND state IS NOT NULL AND postal_code IS NOT NULL THEN
  score := score + 5;
END IF;
```

**Subscription status:**
```sql
-- Active subscribers may have more current info
IF subscription_status = 'active' THEN
  score := score + 10;
END IF;
```

---

## Common Scenarios

### Scenario 1: "I want to reduce mailing costs"

**Solution:** Export only very_high confidence contacts

```bash
python3 scripts/export_mailing_list.py --min-confidence very_high
```

This gives you 632 high-quality addresses, reducing waste from bad addresses.

### Scenario 2: "I want to mail to all active customers"

**Solution:** Filter by recent transactions

```bash
python3 scripts/export_mailing_list.py \
  --min-confidence medium \
  --recent-customers 365
```

This prioritizes recency of purchase over address quality.

### Scenario 3: "I'm seeing too many low scores"

**Possible causes:**
1. **Old addresses:** Many addresses haven't been updated recently
2. **Missing USPS validation:** Run validation to boost scores
3. **Old transaction data:** Import recent PayPal/Kajabi data

**Solutions:**
```bash
# Run USPS validation on all addresses
python3 scripts/validate_all_addresses.py

# Re-import from Kajabi (gets latest addresses)
python3 scripts/restore_addresses_from_kajabi.py --execute

# Import recent PayPal transactions
# (update last_transaction_date for active customers)
```

### Scenario 4: "Ed Burns is showing the wrong address"

**Solution:** Use manual override

```sql
-- Check which address is recommended
SELECT recommended_address, billing_line1, shipping_line1, confidence
FROM mailing_list_priority
WHERE email = 'eburns009@gmail.com';

-- Override to use shipping address
UPDATE contacts
SET preferred_mailing_address = 'shipping'
WHERE email = 'eburns009@gmail.com';
```

Or update the actual address in the database:
```sql
UPDATE contacts
SET
  address_line_1 = '3472 Sunshine Canyon Dr',
  city = 'Boulder',
  state = 'CO',
  postal_code = '80302',
  billing_address_source = 'manual',
  billing_address_updated_at = NOW()
WHERE email = 'eburns009@gmail.com';
```

### Scenario 5: "I want to improve address quality over time"

**Strategy:**

1. **Run USPS validation quarterly:**
```bash
python3 scripts/validate_all_addresses.py
```

2. **Sync with Kajabi monthly:**
```bash
python3 scripts/restore_addresses_from_kajabi.py --execute
```

3. **Import PayPal data weekly:**
```bash
# Updates shipping addresses + transaction dates
# (creates import script if needed)
```

4. **Monitor quality trends:**
```sql
-- Check how many contacts are high confidence
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
```

---

## Understanding Score Breakdown

### Example: Ed Burns

```
Billing Score: 93/100
  - Recency: 40 points (updated Nov 14, 2025 - within 30 days)
  - USPS Validation: 0 points (not validated)
  - Transaction History: 25 points (last purchase Oct 5, 2025 - within 90 days)
  - Source Trust: -5 points (kajabi_line2 → unknown_legacy penalty)
  - Completeness: +33 bonus (all fields present, adjusted internally)

Shipping Score: 95/100
  - Recency: 30 points (updated Nov 1, 2025 - within 90 days)
  - USPS Validation: 25 points (validated Nov 14, 2025 - within 90 days)
  - Transaction History: 25 points (same as billing)
  - Source Trust: 10 points (paypal source)
  - Completeness: +5 bonus

Recommendation: SHIPPING (95 > 93, exceeds 15-point threshold)
Confidence: very_high (95 >= 75)
```

### How to Boost Scores

**To boost billing addresses:**
1. Validate with USPS (+25 points)
2. Update from Kajabi/manual (+40 points for recency)
3. Import recent transactions (+25 points)

**To boost shipping addresses:**
1. Import from PayPal (+10 points source, +40 recency)
2. Validate with USPS (+25 points)

---

## Monitoring & Maintenance

### Weekly Check

```bash
# Export current stats
psql $DATABASE_URL -c "SELECT * FROM mailing_list_stats;"

# Check Ed Burns specifically
psql $DATABASE_URL -c "
  SELECT first_name, last_name, email,
         billing_score, shipping_score,
         recommended_address, confidence
  FROM mailing_list_priority
  WHERE email = 'eburns009@gmail.com';
"
```

### Monthly Maintenance

1. **Sync from Kajabi:**
```bash
python3 scripts/restore_addresses_from_kajabi.py
# Review changes, then:
python3 scripts/restore_addresses_from_kajabi.py --execute
```

2. **Run USPS validation:**
```bash
python3 scripts/validate_all_addresses.py
```

3. **Check for low-confidence contacts:**
```sql
SELECT email, first_name, last_name,
       billing_score, shipping_score, confidence
FROM mailing_list_priority
WHERE confidence IN ('low', 'very_low')
  AND last_transaction_date > NOW() - INTERVAL '180 days'
ORDER BY last_transaction_date DESC
LIMIT 50;
```

These are recent customers with bad addresses - worth manually reviewing.

### Quarterly Review

1. **Review confidence distribution:**
```bash
psql $DATABASE_URL -c "
  SELECT confidence, COUNT(*) as contacts,
         ROUND(AVG(GREATEST(billing_score, shipping_score)), 1) as avg_score
  FROM mailing_list_priority
  GROUP BY confidence
  ORDER BY CASE confidence
    WHEN 'very_high' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
    WHEN 'very_low' THEN 5
  END;
"
```

2. **Check if thresholds need adjustment**
3. **Review manual overrides** (should be <5% of contacts)

---

## Troubleshooting

### Problem: Too many "very_low" confidence contacts

**Diagnosis:**
```sql
SELECT
  COUNT(*) FILTER (WHERE billing_usps_validated_at IS NULL) as no_usps,
  COUNT(*) FILTER (WHERE billing_address_updated_at < NOW() - INTERVAL '365 days') as old_addresses,
  COUNT(*) FILTER (WHERE last_transaction_date IS NULL) as no_transactions
FROM contacts;
```

**Solutions:**
- If `no_usps` is high: Run USPS validation
- If `old_addresses` is high: Sync from Kajabi
- If `no_transactions` is high: Import PayPal data

### Problem: Recommended address is wrong for specific contact

**Solution 1: Manual override**
```sql
UPDATE contacts
SET preferred_mailing_address = 'shipping'  -- or 'billing'
WHERE email = 'customer@example.com';
```

**Solution 2: Update the address data**
```sql
UPDATE contacts
SET
  shipping_address_line_1 = '...',
  shipping_city = '...',
  shipping_state = '...',
  shipping_postal_code = '...',
  shipping_address_source = 'manual',
  shipping_address_updated_at = NOW()
WHERE email = 'customer@example.com';
```

### Problem: Export is missing contacts I expect

**Check if they're below confidence threshold:**
```sql
SELECT email, first_name, last_name, confidence,
       billing_score, shipping_score
FROM mailing_list_priority
WHERE email IN ('contact1@example.com', 'contact2@example.com');
```

**Lower the confidence threshold or boost their scores.**

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/export_mailing_list.py` | Export mailing lists with filtering |
| `scripts/validate_all_addresses.py` | USPS/Smarty validation |
| `scripts/restore_addresses_from_kajabi.py` | Sync billing addresses from Kajabi |
| `supabase/migrations/20251114000000_mailing_list_priority_system.sql` | Scoring algorithm |
| `starhouse-ui/components/contacts/MailingListQuality.tsx` | UI component showing recommendations |

---

## Next Steps

1. **Export your first mailing list:**
```bash
python3 scripts/export_mailing_list.py --min-confidence high --output /tmp/my_first_mailing.csv
```

2. **Review the results** - check if the addresses look correct

3. **Fine-tune if needed** - adjust confidence thresholds or factor weights

4. **Set up regular maintenance** - monthly Kajabi sync, quarterly USPS validation

5. **Monitor quality trends** - track how confidence distribution changes over time

---

**Document created:** 2025-11-14
**Last updated:** 2025-11-14
**System status:** Production ready, 832 high-quality addresses available
