# PHASE 2: SHIPPING ADDRESS USPS VALIDATION

**Date:** 2025-11-14
**Status:** Ready for USPS Validation Service
**Previous Phase:** [Phase 1 - Mailing List Priority System](MAILING_LIST_IMPLEMENTATION_COMPLETE.md)

---

## Overview

Phase 1 identified a critical data quality gap: **0% of shipping addresses are USPS validated** compared to 48% of billing addresses. This Phase 2 implementation prepares 571 US shipping addresses for USPS validation to improve mailing list confidence scores.

---

## Current Status

### Shipping Address Validation Coverage

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total shipping addresses** | 1,219 | 100% |
| Already validated | 0 | 0% |
| **Need validation** | 1,219 | 100% |
| US addresses (can validate) | 571 | 47% |
| International (cannot validate) | 648 | 53% |

### Impact on Mailing List Quality

From Phase 1 statistics:
- **1,085 contacts (56%)** have "very low" confidence scores
- Primary reason: Lack of USPS validation
- **Expected improvement:** Validating 571 shipping addresses will significantly boost confidence scores

---

## What Was Prepared

### 1. ✅ Database Schema Verification

Confirmed all required shipping USPS fields exist in `contacts` table:

| Column | Data Type | Purpose |
|--------|-----------|---------|
| `shipping_usps_validated_at` | timestamp | When validation occurred |
| `shipping_usps_dpv_match_code` | text | Delivery point validation (Y/N/S/D) |
| `shipping_usps_precision` | text | Geocoding accuracy (Zip9/Zip8/Zip7/etc) |
| `shipping_usps_delivery_line_1` | text | USPS-standardized address line 1 |
| `shipping_usps_delivery_line_2` | text | USPS-standardized address line 2 |
| `shipping_usps_last_line` | text | City, State ZIP+4 |
| `shipping_usps_latitude` | numeric | Geocoded latitude |
| `shipping_usps_longitude` | numeric | Geocoded longitude |
| `shipping_usps_county` | text | County name |
| `shipping_usps_rdi` | text | Residential/Commercial indicator |
| `shipping_usps_footnotes` | text | Validation notes |
| `shipping_usps_vacant` | boolean | Vacant property flag |
| `shipping_usps_active` | boolean | Active delivery point |

---

### 2. ✅ Export CSV for Validation

**File Created:** `/tmp/shipping_addresses_for_validation.csv`

**Contents:**
- 571 US shipping addresses
- Includes email for safe matching
- Sorted by last name, first name
- Sequence numbers for row matching

**Sample Records:**

```
sequence,email,firstname,lastname,addressline1,city,state,postalcode,country
1,lorraineabate@comcast.net,Lorraine,Abate,2909 25th Street,Sacramento,CA,95818,US
2,abdnor@comcast.net,Leanne,Abdnor,128 Iroquois Drive,Boulder,CO,80303,US
3,kitgord@whidbey.com,Kathryn,Adams,742 Decker Ave,Langley,WA,98260,US
```

---

### 3. ✅ Import Script Created

**File:** `scripts/import_usps_validation_shipping.py`

**Features:**
- Safe matching by email address (no fuzzy matching)
- Updates shipping USPS fields (not billing)
- Handles validation failures gracefully
- Progress reporting every 25 records
- Detailed statistics and sample output

**Key Safety Features:**
1. Matches by sequence number to original export
2. Updates by email (unique key)
3. Rollback on errors
4. Verification of updated record counts

---

## Next Steps: Using USPS Validation Service

### Step 1: Upload to USPS Service

**File to upload:** `/tmp/shipping_addresses_for_validation.csv`

**USPS Service Options:**
1. **USPS Web Tools API** (free, rate-limited)
2. **SmartyStreets** (commercial, bulk processing)
3. **Lob.com** (commercial, comprehensive)
4. **Melissa Data** (commercial, global coverage)

**Required Output Fields:**
- `[sequence]` - Row number (for matching)
- `ValidationFlag` - OK/ERROR status
- `[dpv_match_code]` - Y/N/S/D match code
- `[delivery_line_1]` - Standardized address
- `[delivery_line_2]` - Standardized line 2
- `[city_name]` - Standardized city
- `[state_abbreviation]` - State code
- `[full_zipcode]` - ZIP+4 code
- `[county_name]` - County
- `[latitude]` - Geocoded latitude
- `[longitude]` - Geocoded longitude
- `[precision]` - Geocoding accuracy
- `[rdi]` - Residential/Commercial
- `[dpv_vacant]` - Y if vacant
- `[active]` - Y if active delivery point
- `[notes]` / `[summary]` - Validation notes

### Step 2: Download Validation Results

Save the USPS validation output as:
**`/tmp/shipping_addresses_validated.csv`**

### Step 3: Import Results

Run the import script:

```bash
cd /workspaces/starhouse-database-v2
python3 scripts/import_usps_validation_shipping.py
```

**Optional:** Specify custom file paths:

```bash
python3 scripts/import_usps_validation_shipping.py \
  /path/to/original.csv \
  /path/to/validated.csv
```

### Step 4: Verify Results

After import, check statistics:

```sql
-- Overall validation status
SELECT
    COUNT(*) as total_shipping,
    COUNT(shipping_usps_validated_at) as validated,
    ROUND(COUNT(shipping_usps_validated_at)::numeric / COUNT(*) * 100, 1) as pct_validated
FROM contacts
WHERE shipping_address_line_1 IS NOT NULL;

-- Validation quality breakdown
SELECT
    shipping_usps_dpv_match_code as match_code,
    COUNT(*) as count,
    CASE shipping_usps_dpv_match_code
        WHEN 'Y' THEN 'Confirmed - deliverable'
        WHEN 'N' THEN 'Not confirmed - not deliverable'
        WHEN 'S' THEN 'Confirmed - missing secondary'
        WHEN 'D' THEN 'Confirmed but missing unit number'
        ELSE 'Unknown'
    END as meaning
FROM contacts
WHERE shipping_usps_validated_at IS NOT NULL
GROUP BY shipping_usps_dpv_match_code
ORDER BY count DESC;

-- Vacant addresses (potential movers)
SELECT
    email,
    first_name || ' ' || last_name as name,
    shipping_address_line_1,
    shipping_city || ', ' || shipping_state || ' ' || shipping_postal_code as location
FROM contacts
WHERE shipping_usps_vacant = TRUE
ORDER BY last_name, first_name;
```

---

## Expected Impact on Mailing List Scores

### Current Scores (Phase 1)

From `mailing_list_stats` view:
- Average score: **27.8**
- Very low confidence: **1,085 contacts (56%)**
- High/very high confidence: **750 contacts (39%)**

### Projected Scores (After Phase 2)

**Scoring Algorithm Reminder:**
- USPS validation: **+25 points** (if validated within 90 days)
- Recency: up to +40 points
- Transaction history: up to +25 points
- Source trust: up to +10 points

**Expected Improvements:**

For contacts currently using **shipping addresses** (10 contacts):
- Current average score: ~50 (medium confidence)
- After validation: ~75 (very high confidence)
- Impact: +25 points from USPS validation

For contacts where **shipping score will exceed billing**:
- Scenario: Billing address is old (low recency score)
- But shipping address is recent + now USPS validated
- Impact: Algorithm may switch recommendation from billing to shipping

**Estimated Overall Impact:**
- Contacts improving to high confidence: +50-100 contacts
- Contacts with better address data: +571 contacts
- Average score increase: +5-10 points

---

## Database Objects to Update

### 1. Update Scoring Function

The `calculate_address_score()` function already checks `shipping_usps_validated_at`:

```sql
-- Line 38-40 in migration 20251114000000
ELSIF address_type = 'shipping' THEN
  usps_date := contact_record.shipping_usps_validated_at;
  verified := contact_record.shipping_address_verified;
```

✅ **No changes needed** - function already supports shipping USPS validation.

### 2. Verify View Updates

The `mailing_list_priority` view will automatically reflect new scores because:
1. It calls `calculate_address_score('shipping', c.id)` for all contacts
2. The function reads `shipping_usps_validated_at`
3. Views are not materialized - they query live data

✅ **No changes needed** - views will update automatically.

### 3. Refresh Statistics

After import, check updated statistics:

```sql
SELECT * FROM mailing_list_stats;
```

Compare to Phase 1 baseline:
- Total contacts: 1,922
- Average score: 27.8
- High confidence: 750 (39%)
- Very low confidence: 1,085 (56%)

---

## Sample Use Cases After Validation

### 1. Find Contacts Who Moved (Vacant Addresses)

```sql
SELECT
    c.email,
    c.first_name,
    c.last_name,
    c.shipping_address_line_1,
    c.shipping_city,
    c.shipping_state,
    c.shipping_postal_code,
    c.last_transaction_date
FROM contacts c
WHERE c.shipping_usps_vacant = TRUE
  AND c.last_transaction_date > NOW() - INTERVAL '2 years'
ORDER BY c.last_transaction_date DESC;
```

**Purpose:** Identify recent customers whose shipping address is now vacant - they likely moved.

### 2. Geographic Proximity Analysis

```sql
-- Find all customers within 50 miles of Boulder, CO
-- (StarHouse location: 40.0150° N, 105.2705° W)
SELECT
    email,
    first_name || ' ' || last_name as name,
    shipping_city,
    shipping_state,
    ROUND(
        3959 * acos(
            cos(radians(40.0150)) *
            cos(radians(shipping_usps_latitude)) *
            cos(radians(shipping_usps_longitude) - radians(-105.2705)) +
            sin(radians(40.0150)) *
            sin(radians(shipping_usps_latitude))
        )
    ) as distance_miles
FROM contacts
WHERE shipping_usps_latitude IS NOT NULL
  AND shipping_usps_longitude IS NOT NULL
HAVING distance_miles <= 50
ORDER BY distance_miles;
```

**Purpose:** Local event marketing - invite nearby contacts to in-person events.

### 3. Residential vs Commercial Segmentation

```sql
SELECT
    shipping_usps_rdi as type,
    COUNT(*) as count,
    CASE shipping_usps_rdi
        WHEN 'Residential' THEN 'Home deliveries - OK for all mailings'
        WHEN 'Commercial' THEN 'Business address - consider B2B messaging'
        ELSE 'Unknown'
    END as notes
FROM contacts
WHERE shipping_usps_validated_at IS NOT NULL
GROUP BY shipping_usps_rdi
ORDER BY count DESC;
```

**Purpose:** Tailor messaging based on residential vs business recipients.

---

## Cost-Benefit Analysis

### Validation Costs (Estimated)

| Service | Cost per Address | Total for 571 | Notes |
|---------|-----------------|---------------|-------|
| **USPS Web Tools** | Free | $0 | 5 requests/sec limit, requires approval |
| **SmartyStreets** | $0.007-0.015 | $4-9 | Pay-as-you-go, instant setup |
| **Lob.com** | $0.04 | $23 | Includes full validation suite |
| **Melissa Data** | $0.02-0.05 | $11-29 | Global coverage available |

**Recommendation:** SmartyStreets ($4-9 total) - best balance of cost and ease of use.

### Expected Benefits

1. **Reduced Mailing Costs:**
   - Current undeliverable rate: ~2.8% (21 vacant addresses from billing)
   - Estimated shipping undeliverable: 16 addresses (2.8% of 571)
   - Cost to mail: ~$0.70/piece (postage + printing)
   - Savings: 16 × $0.70 = **$11.20 per mailing**

2. **Improved Confidence Scores:**
   - 50-100 contacts move to "high confidence"
   - Better decision-making for which address to use
   - Fewer returns due to bad addresses

3. **Enhanced Segmentation:**
   - Geographic proximity analysis for event marketing
   - Residential vs commercial targeting
   - Vacant address detection (movers list)

**Total First-Year Value:** $112+ (10 mailings × $11.20 savings) + improved targeting value

**ROI:** Break-even on first mailing campaign.

---

## Files Created

1. **Export CSV:** `/tmp/shipping_addresses_for_validation.csv` (571 records)
2. **Import Script:** `scripts/import_usps_validation_shipping.py`
3. **Documentation:** `docs/PHASE2_SHIPPING_VALIDATION.md` (this file)

---

## Phase 3 Preview

After shipping address validation is complete:

### 1. UI Integration
- Display recommended address in contact details
- Show confidence level with color coding
- Add "Preferred Mailing Address" dropdown
- Show both billing and shipping scores

### 2. Source Backfilling
- Populate `billing_address_source` from `external_identities`
- Populate `shipping_address_source` from webhook logs
- Improve source trust scoring accuracy

### 3. Periodic Re-validation
- Monthly re-validation of addresses older than 90 days
- Automated email notifications for vacant addresses
- Track address change history

---

## Summary

Phase 2 preparation is **complete and ready for execution**. The workflow is:

1. ✅ Export 571 US shipping addresses to CSV
2. ⏳ Upload to USPS validation service (manual step)
3. ⏳ Download validation results (manual step)
4. ⏳ Run import script to update database
5. ⏳ Verify improved mailing list statistics

**Next Action:** Upload `/tmp/shipping_addresses_for_validation.csv` to USPS validation service.

---

**Prepared:** 2025-11-14
**Ready for:** USPS Validation Service Upload
**Expected Completion:** After validation results are received
**Status:** ✅ Ready for Manual Steps
