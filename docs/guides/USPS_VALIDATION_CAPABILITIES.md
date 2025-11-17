# USPS Address Validation - Complete Capabilities Guide

**Current Status:** 739 billing addresses validated (48% of addresses)  
**Shipping Status:** 0 validated (opportunity for Phase 2)

---

## What USPS Validation Provides

USPS validation connects to the official United States Postal Service database to verify and standardize addresses. Here's everything it gives you:

---

### 1. ✅ **Address Verification (Deliverability)**

**Field:** `billing_usps_dpv_match_code` (Delivery Point Validation)

**What it means:**

| Code | Meaning | Count | % | Action |
|------|---------|-------|---|--------|
| **Y** | Confirmed - address exists | 688 | 93% | ✅ Safe to mail |
| **N** | Not confirmed - address doesn't exist | 1 | 0.1% | ❌ Don't mail |
| **S** | Missing secondary (apt/suite #) | 19 | 2.6% | ⚠️ May bounce - verify |
| **D** | Secondary not confirmed | 21 | 2.8% | ⚠️ May bounce - verify |

**Use Case:** Filter out undeliverable addresses before expensive mailings
```sql
SELECT * FROM contacts 
WHERE billing_usps_dpv_match_code = 'Y' -- Only confirmed addresses
AND billing_usps_vacant = false;         -- Not vacant
```

---

### 2. 📝 **Address Standardization**

**Fields:** 
- `billing_usps_delivery_line_1` - USPS corrected address
- `billing_usps_delivery_line_2` - Apartment/suite (if applicable)
- `billing_usps_last_line` - City, State ZIP+4

**What USPS fixes:**
- Abbreviations: "Street" → "St", "Avenue" → "Ave"
- Capitalization: "boulder" → "Boulder"
- Misspellings: "Collrado" → "Colorado"
- ZIP+4 codes: "80302" → "80302-7511"
- Directionals: "North Main" → "N Main"

**Example:**
```
Your Input:    703 cottonwood creek drive, dripping springs tx 78620
USPS Corrects: 703 Cottonwood Creek Dr
               Dripping Springs TX 78620-1234
```

**Use Case:** Bulk mail discounts require USPS-standardized addresses
```sql
-- Get USPS standardized addresses for bulk mail
SELECT 
    billing_usps_delivery_line_1,
    billing_usps_delivery_line_2,
    billing_usps_last_line
FROM contacts
WHERE billing_usps_dpv_match_code = 'Y';
```

---

### 3. 🏠 **Vacant Property Detection**

**Field:** `billing_usps_vacant` (boolean)

**Stats:**
- Vacant: 21 addresses (2.8%)
- Occupied: 718 addresses (97.2%)

**What it means:**
- **TRUE** - USPS identifies property as vacant
- **FALSE** - Property is occupied/active

**Use Cases:**
- Filter out vacant properties to reduce waste
- Identify contacts who may have moved
- Trigger "address update needed" workflow

```sql
-- Find contacts with vacant addresses
SELECT 
    email,
    first_name,
    last_name,
    address_line_1,
    city,
    state,
    billing_usps_validated_at
FROM contacts
WHERE billing_usps_vacant = true
ORDER BY billing_usps_validated_at DESC;

-- Our data: 21 vacant addresses to investigate
```

---

### 4. 🏢 **Residential vs Commercial**

**Field:** `billing_usps_rdi` (Residential Delivery Indicator)

**Stats:**
- Residential: 702 (95%)
- Commercial: 21 (2.8%)
- Unknown: 16 (2.2%)

**Use Cases:**
- Segment mailings by type
- Different postage rates for commercial
- Tailor messaging (home vs business)

```sql
-- Separate residential from commercial
SELECT 
    billing_usps_rdi as address_type,
    COUNT(*) as count
FROM contacts
WHERE billing_usps_validated_at IS NOT NULL
GROUP BY billing_usps_rdi;
```

---

### 5. 🎯 **Precision Level**

**Field:** `billing_usps_precision`

**Stats:**
- **Zip9** (ZIP+4): 653 (88%) - Most precise
- **Zip5** (5-digit ZIP): 45 (6%) - Less precise
- **Street**: 0 (0%)
- **Other**: 41 (6%)

**What it means:**

| Level | Precision | Example | Use Case |
|-------|-----------|---------|----------|
| **Zip9** | Specific building/unit | 80302-7511 | Best for automation |
| **Zip5** | General area | 80302 | Acceptable |
| **Street** | Street level only | Boulder CO | Needs review |
| **City** | City level only | Boulder | Unreliable |

**Use Case:** Filter by precision for high-value mailings
```sql
SELECT * FROM contacts
WHERE billing_usps_precision = 'Zip9'  -- Highest precision
AND billing_usps_dpv_match_code = 'Y';
```

---

### 6. 🗺️ **Geocoding (Latitude/Longitude)**

**Fields:**
- `billing_usps_latitude` (numeric)
- `billing_usps_longitude` (numeric)

**Stats:** 738 of 739 addresses geocoded (99.9%)

**Coordinates Example:**
```
Ed Burns (Boulder): 40.0178°N, 105.2797°W
```

**Use Cases:**

**A. Distance-Based Segmentation**
```sql
-- Find contacts within 50 miles of StarHouse (3472 Sunshine Canyon)
SELECT 
    email,
    first_name,
    last_name,
    billing_usps_latitude,
    billing_usps_longitude,
    -- Calculate distance using Haversine formula
    (
        3959 * acos(
            cos(radians(40.0178)) * cos(radians(billing_usps_latitude)) * 
            cos(radians(billing_usps_longitude) - radians(-105.2797)) + 
            sin(radians(40.0178)) * sin(radians(billing_usps_latitude))
        )
    ) as distance_miles
FROM contacts
WHERE billing_usps_latitude IS NOT NULL
HAVING distance_miles < 50
ORDER BY distance_miles;
```

**B. Territory Assignment**
```sql
-- Assign contacts to regional coordinators
SELECT 
    CASE 
        WHEN billing_usps_latitude > 40.0 THEN 'North Team'
        ELSE 'South Team'
    END as territory,
    COUNT(*) as contacts
FROM contacts
WHERE billing_usps_latitude IS NOT NULL
GROUP BY territory;
```

**C. Map Visualization**
Export lat/long to Google Maps, Tableau, etc. for visual analysis.

---

### 7. 📍 **County Information**

**Field:** `billing_usps_county`

**Examples:**
- Boulder County, Colorado
- Denver County, Colorado
- Travis County, Texas

**Use Cases:**
- Tax jurisdiction reporting
- Regional analysis
- Political district mapping
- Service area coverage

```sql
-- Top counties by contact count
SELECT 
    billing_usps_county as county,
    COUNT(*) as contacts
FROM contacts
WHERE billing_usps_county IS NOT NULL
GROUP BY billing_usps_county
ORDER BY contacts DESC
LIMIT 10;
```

---

### 8. 🔔 **Active Delivery Point**

**Field:** `billing_usps_active` (boolean)

**Stats:** 739 active (100%)

**What it means:**
- **TRUE** - Delivery point is currently active
- **FALSE** - Delivery point inactive (rare)

**Use Case:** Extra confirmation address is valid
```sql
WHERE billing_usps_active = true
```

---

### 9. 📋 **Validation Footnotes**

**Field:** `billing_usps_footnotes`

**Common messages:**
- "Standardized" - Address was reformatted
- "Fixed abbreviations" - Changed St to Street, etc.
- "Matched street and city and state" - Verified against USPS database
- "Confirmed entire address" - Full delivery point validation
- "Added ZIP+4" - Enhanced with 4-digit extension

**Use Case:** Audit trail for address changes
```sql
SELECT 
    email,
    address_line_1 as original,
    billing_usps_delivery_line_1 as corrected,
    billing_usps_footnotes as what_changed
FROM contacts
WHERE billing_usps_footnotes LIKE '%Fixed%'
LIMIT 10;
```

---

### 10. ⏰ **Validation Timestamp**

**Field:** `billing_usps_validated_at`

**Current Range:** Nov 1-4, 2025

**Use Cases:**
- Track when addresses were last verified
- Trigger re-validation after X months
- Audit trail for compliance

```sql
-- Addresses validated over 6 months ago (none yet in your data)
SELECT COUNT(*)
FROM contacts
WHERE billing_usps_validated_at < NOW() - INTERVAL '6 months';

-- When to re-validate
SELECT 
    COUNT(*) as addresses_to_revalidate
FROM contacts
WHERE billing_usps_validated_at < NOW() - INTERVAL '12 months'
OR (address_line_1 IS NOT NULL AND billing_usps_validated_at IS NULL);
```

---

## What You CAN DO With USPS Validation

### 1. 💰 **Reduce Mailing Costs**

**Problem:** Undeliverable mail wastes money
**Solution:** Only mail to confirmed addresses

```sql
-- Export only deliverable addresses
COPY (
    SELECT 
        first_name, last_name,
        billing_usps_delivery_line_1 as address,
        billing_usps_last_line as city_state_zip
    FROM contacts
    WHERE billing_usps_dpv_match_code = 'Y'
    AND billing_usps_vacant = false
) TO '/tmp/deliverable_only.csv' CSV HEADER;

-- Savings: ~2.8% fewer pieces (21 vacant + undeliverable)
```

---

### 2. 📬 **Qualify for USPS Bulk Mail Discounts**

**Requirement:** Addresses must be CASS-certified (standardized)
**Discount:** Up to 7¢ per piece for automation rates

```sql
-- Export USPS-standardized addresses
SELECT 
    billing_usps_delivery_line_1,
    billing_usps_delivery_line_2,
    billing_usps_last_line
FROM contacts
WHERE billing_usps_dpv_match_code = 'Y'
AND billing_usps_precision = 'Zip9';

-- 653 addresses qualify for automation rates
```

**Savings Example:**
- 653 pieces × $0.07 savings = $45.71 per mailing
- 12 mailings/year = $548 annual savings

---

### 3. 🎯 **Segment by Geography**

**A. Find Local Contacts (within 50 miles)**
```sql
-- Events at StarHouse - invite locals only
SELECT * FROM contacts
WHERE (
    3959 * acos(
        cos(radians(40.0178)) * cos(radians(billing_usps_latitude)) * 
        cos(radians(billing_usps_longitude) - radians(-105.2797)) + 
        sin(radians(40.0178)) * sin(radians(billing_usps_latitude))
    )
) < 50;
```

**B. Target by City/County**
```sql
-- Boulder County residents only
SELECT * FROM contacts
WHERE billing_usps_county = 'Boulder';
```

---

### 4. 🏚️ **Identify Contacts Who Moved**

```sql
-- Vacant addresses = possible moves
SELECT 
    email,
    first_name,
    last_name,
    address_line_1,
    billing_usps_validated_at,
    last_transaction_date
FROM contacts
WHERE billing_usps_vacant = true
ORDER BY last_transaction_date DESC;

-- 21 contacts to reach out to for address update
```

**Action:** Email campaign "Have you moved? Update your address for our newsletter"

---

### 5. 📊 **Data Quality Reporting**

```sql
-- Address quality dashboard
SELECT 
    COUNT(*) as total_addresses,
    COUNT(CASE WHEN billing_usps_dpv_match_code = 'Y' THEN 1 END) as deliverable,
    COUNT(CASE WHEN billing_usps_vacant = true THEN 1 END) as vacant,
    COUNT(CASE WHEN billing_usps_precision = 'Zip9' THEN 1 END) as high_precision,
    ROUND(
        100.0 * COUNT(CASE WHEN billing_usps_dpv_match_code = 'Y' THEN 1 END) / COUNT(*),
        1
    ) as deliverable_pct
FROM contacts
WHERE address_line_1 IS NOT NULL;
```

---

### 6. 🗺️ **Map Visualization**

Export to mapping tools:
```sql
COPY (
    SELECT 
        email,
        first_name || ' ' || last_name as name,
        billing_usps_latitude as lat,
        billing_usps_longitude as lng,
        billing_usps_delivery_line_1 as address,
        city || ', ' || state as location
    FROM contacts
    WHERE billing_usps_latitude IS NOT NULL
) TO '/tmp/contact_map.csv' CSV HEADER;
```

Upload to:
- Google My Maps
- Tableau
- Power BI
- Custom mapping solutions

**Use Cases:**
- Visualize member distribution
- Plan regional events
- Territory management

---

### 7. 🔄 **Automated Address Updates**

**Strategy:** Replace user-entered addresses with USPS-corrected ones

```sql
-- Update addresses with USPS standardized versions
UPDATE contacts
SET 
    address_line_1 = billing_usps_delivery_line_1,
    address_line_2 = billing_usps_delivery_line_2,
    postal_code = REGEXP_REPLACE(
        billing_usps_last_line, 
        '.* ([0-9]{5}-[0-9]{4})$', 
        '\1'
    )
WHERE billing_usps_dpv_match_code = 'Y'
AND billing_usps_delivery_line_1 IS NOT NULL;

-- Result: All addresses now match USPS standards
```

⚠️ **Caution:** Only do this if you trust USPS data over user input. Review discrepancies first.

---

### 8. 🚫 **Suppress Undeliverable Addresses**

```sql
-- Create "do not mail" list
CREATE VIEW undeliverable_addresses AS
SELECT 
    email,
    first_name,
    last_name,
    address_line_1,
    CASE 
        WHEN billing_usps_dpv_match_code = 'N' THEN 'Address not found'
        WHEN billing_usps_vacant = true THEN 'Property vacant'
        WHEN billing_usps_dpv_match_code = 'S' THEN 'Missing apartment number'
        WHEN billing_usps_dpv_match_code = 'D' THEN 'Apartment number invalid'
    END as reason
FROM contacts
WHERE billing_usps_dpv_match_code IN ('N', 'S', 'D')
OR billing_usps_vacant = true;

-- 41 addresses to exclude from mailings
```

---

## What You CANNOT Do (Limitations)

### ❌ **1. Validate International Addresses**

USPS only validates **US addresses**. 
- Canada, UK, Australia, etc. = No validation
- Your data has international addresses - they won't get validated

**Workaround:** Use separate services (Canada Post, Royal Mail, etc.)

---

### ❌ **2. Verify Current Occupant**

**USPS tells you:**
- ✅ Address exists and is deliverable
- ✅ Property is vacant or occupied

**USPS does NOT tell you:**
- ❌ If the specific person still lives there
- ❌ If mail will reach them
- ❌ If they moved recently

**Example:** Ed Burns' PA address
- USPS says: "✅ Deliverable"
- Reality: Ed moved 7 years ago
- Someone else might live there now

**Solution:** Track "last_transaction_date" + USPS validation together (your mailing list algorithm does this!)

---

### ❌ **3. Real-Time Updates**

**How it works:**
- Validation is a **batch process** (run periodically)
- Not real-time as addresses change

**Solution:** Re-validate every 6-12 months
```sql
-- Addresses due for re-validation
SELECT COUNT(*)
FROM contacts
WHERE billing_usps_validated_at < NOW() - INTERVAL '12 months';
```

---

### ❌ **4. Email Validation**

USPS only validates **physical addresses**, not email addresses.

**Solution:** Use separate email validation service (BriteVerify, ZeroBounce, etc.)

---

## Your Current USPS Validation Status

### Billing Addresses

| Metric | Count | % |
|--------|-------|---|
| **Total billing addresses** | 1,538 | 100% |
| **USPS validated** | 739 | 48% ✅ |
| **Not validated** | 799 | 52% ⚠️ |
| **Confirmed deliverable (Y)** | 688 | 93% of validated |
| **Vacant** | 21 | 2.8% of validated |
| **High precision (ZIP+4)** | 653 | 88% of validated |
| **Geocoded** | 738 | 99.9% of validated |

### Shipping Addresses

| Metric | Count | % |
|--------|-------|---|
| **Total shipping addresses** | 1,219 | 100% |
| **USPS validated** | 0 | 0% ❌ |
| **Opportunity** | 1,219 | 100% |

---

## Recommended Actions

### Immediate (High Value)

1. **Validate Shipping Addresses**
   - 0% validated currently
   - Would improve 1,219 addresses
   - Especially important for Ed Burns-type cases

2. **Export High-Quality Mailing List**
   ```sql
   -- 688 confirmed deliverable addresses
   SELECT * FROM contacts
   WHERE billing_usps_dpv_match_code = 'Y'
   AND billing_usps_vacant = false;
   ```

3. **Investigate 21 Vacant Addresses**
   - Reach out for address updates
   - May have moved

### Short-Term (1-2 Weeks)

4. **Validate Remaining 799 Billing Addresses**
   - 52% not yet validated
   - Use existing USPS validation script

5. **Update Mailing List Algorithm**
   - Add `billing_usps_vacant` penalty (-30 points)
   - Boost `billing_usps_precision = 'Zip9'` (+5 points)

### Ongoing (Monthly)

6. **Re-Validation Schedule**
   - Re-validate addresses every 12 months
   - USPS data changes ~2-3% annually

7. **Monitor Return Mail**
   - When mail bounces, update:
   ```sql
   UPDATE contacts 
   SET billing_usps_dpv_match_code = 'N'
   WHERE email = 'bounced@example.com';
   ```

---

## Cost-Benefit Analysis

### Current Investment
- **Script:** Already built (`import_usps_validation_safe.py`)
- **USPS API:** Free for CASS certification
- **Time:** ~1 hour to run validation on 1,538 addresses

### Potential Savings

**Annual Mailing Budget Example:**
- 12 mailings/year
- 750 recipients
- $0.73 postage each
- **Total:** $6,570/year

**With USPS Validation:**
- Automation discount: -$0.07/piece = -$630/year
- Avoid undeliverable (2.8%): -$184/year
- **Savings:** $814/year (12.4% reduction)

**ROI:** Pays for itself in first mailing

---

## Summary

### What USPS Validation GIVES You:

✅ Address exists (deliverability confirmation)  
✅ Standardized format (bulk mail discounts)  
✅ Vacant detection (avoid waste)  
✅ Residential vs commercial  
✅ ZIP+4 precision codes  
✅ Latitude/longitude (mapping)  
✅ County information  
✅ Active delivery point confirmation  
✅ Validation audit trail  

### What You CAN DO:

💰 Reduce mailing costs  
📬 Qualify for bulk discounts  
🎯 Geographic segmentation  
🏚️ Identify moves  
📊 Data quality reporting  
🗺️ Map visualization  
🔄 Automated corrections  
🚫 Suppress bad addresses  

### What You CANNOT DO:

❌ International validation  
❌ Verify current occupant  
❌ Real-time updates  
❌ Email validation  

---

**Your Next Step:** Validate the 1,219 shipping addresses (currently 0% validated)

**Estimated Impact:** Would improve address selection for ~600 contacts with both billing and shipping addresses.

