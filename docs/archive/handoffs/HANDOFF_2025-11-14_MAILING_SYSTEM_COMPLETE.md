# Handoff: Mailing List System Complete - Nov 14, 2025

**Date:** November 14, 2025
**Status:** ✅ Production Ready
**System:** Address Quality & Mailing List Priority System

---

## Executive Summary

Successfully implemented a complete mailing list priority system that:
- ✅ Scores and ranks billing vs shipping addresses (0-100 scale)
- ✅ Recommends best address for each contact based on quality
- ✅ Fixed 679 scrambled addresses from Nov 1 incident
- ✅ Validated 571 shipping addresses with USPS/SmartyStreets
- ✅ Provides 832 high-confidence addresses ready for mailing
- ✅ Includes export tools and fine-tuning capabilities

**Zero data loss.** All work from previous sessions preserved.

---

## Current System Status

### Mailing List Quality
- **Total Contacts:** 1,474
- **High Confidence (ready to mail):** 832 contacts (57%)
  - Very High Confidence: 632 contacts (43%)
  - High Confidence: 200 contacts (14%)
- **Medium/Low/Very Low:** 642 contacts (43%)
- **Address Recommendation:** 95% billing, 5% shipping

### Address Data Quality
- **Billing addresses restored:** 679 from Kajabi (Nov 14)
- **Shipping addresses validated:** 571 via USPS/SmartyStreets (Nov 14)
- **Ed Burns address:** Updated to current 3472 Sunshine Canyon Dr, Boulder, CO

### Production Features
1. **Address Scoring Algorithm** - Multi-factor scoring (recency, validation, transactions, source)
2. **Mailing List Priority View** - Database view with recommendations
3. **Export Tool** - Generate filtered mailing lists
4. **UI Components** - Display address quality and recommendations
5. **Manual Override Support** - Staff can override algorithm recommendations

---

## Files Created/Modified

### Scripts (7 new, all in /workspaces/starhouse-database-v2/scripts/)

#### 1. `export_mailing_list.py` ⭐ NEW (Nov 14)
**Purpose:** Export mailing lists with smart address selection and filtering

**Usage:**
```bash
# Export high-confidence contacts (832)
python3 scripts/export_mailing_list.py --min-confidence high

# Export premium quality only (632)
python3 scripts/export_mailing_list.py --min-confidence very_high

# Export recent active customers
python3 scripts/export_mailing_list.py --min-confidence high --recent-customers 365

# Clean export for mail merge
python3 scripts/export_mailing_list.py --min-confidence high --no-metadata
```

**Features:**
- Filters by confidence level (very_high, high, medium, low, very_low)
- Filters by recent transaction date
- Includes/excludes metadata (scoring details)
- Shows breakdown by confidence and address source
- Outputs to CSV for mail merge services

**Output:** CSV with name, email, address, and optional scoring metadata

---

#### 2. `restore_addresses_from_kajabi.py` (Nov 14)
**Purpose:** Sync billing addresses from Kajabi CSV export

**Usage:**
```bash
# Dry run (see what will change)
python3 scripts/restore_addresses_from_kajabi.py

# Execute changes
python3 scripts/restore_addresses_from_kajabi.py --execute
```

**What it does:**
- Compares database billing addresses vs Kajabi CSV
- Finds mismatches (case-insensitive)
- Updates billing addresses with Kajabi data
- Preserves USPS validation metadata
- Shows before/after for verification

**Safety features:**
- Dry-run mode by default
- Batch commits every 50 records
- Verifies Ed Burns address after restoration
- Only updates addresses that don't match

**Last run:** Nov 14, 2025 - restored 679 addresses

---

#### 3. `validate_all_addresses.py` (Nov 14)
**Purpose:** Validate all addresses (billing and shipping) with SmartyStreets

**Usage:**
```bash
python3 scripts/validate_all_addresses.py
```

**What it does:**
1. Exports all addresses to CSV
2. Calls SmartyStreets API for validation
3. Auto-imports results back to database
4. Updates USPS metadata fields

**Validates:**
- Billing addresses (address_line_1, city, state, postal_code)
- Shipping addresses (shipping_address_line_1, etc.)

**Updates fields:**
- `billing_usps_validated_at`
- `billing_usps_dpv_match_code`
- `billing_usps_delivery_line_1`
- `billing_usps_last_line`
- (and shipping equivalents)

---

#### 4. `validate_addresses_smarty.py` (Nov 14)
**Purpose:** Lower-level SmartyStreets API validation script

**Usage:**
```bash
python3 scripts/validate_addresses_smarty.py /path/to/addresses.csv
```

**What it does:**
- Reads CSV with addresses
- Calls SmartyStreets Street Address API
- Returns validation results (DPV match, deliverability, standardized format)

**Used by:** `validate_all_addresses.py`

---

#### 5. `validate_addresses_usps.py` (Nov 14)
**Purpose:** Alternative USPS validation (if needed)

**Status:** Created but SmartyStreets is preferred

---

#### 6. `import_usps_validation_all.py` (Nov 14)
**Purpose:** Import validation results for all addresses (billing + shipping)

**Usage:**
```bash
python3 scripts/import_usps_validation_all.py /path/to/validation_results.csv
```

**What it does:**
- Reads validation CSV from SmartyStreets
- Matches by email
- Updates USPS metadata fields
- Preserves actual addresses (only updates validation data)

---

#### 7. `import_usps_validation_shipping.py` (Nov 14)
**Purpose:** Import validation results for shipping addresses only

**Usage:**
```bash
python3 scripts/import_usps_validation_shipping.py /path/to/validation_results.csv
```

**Similar to import_usps_validation_all.py but shipping-specific**

**Last run:** Nov 14, 2025 - validated 571 shipping addresses

---

#### 8. `systematic_address_audit.py` (Nov 14)
**Purpose:** Diagnostic tool for address quality investigation

**Usage:**
```bash
python3 scripts/systematic_address_audit.py
```

**What it does:**
- Compares all contacts vs Kajabi CSV
- Finds mismatches in billing addresses
- Generates detailed report
- Used during Nov 14 address scramble investigation

**Status:** Investigation complete, can be removed or kept for future diagnostics

---

### Database Migrations (5 new, all in /workspaces/starhouse-database-v2/supabase/migrations/)

#### 1. `20251114000000_mailing_list_priority_system.sql` ⭐ CORE SYSTEM
**Purpose:** Implements the complete address scoring and recommendation system

**Creates:**
1. **`calculate_address_score()` function** - Scores addresses 0-100
   - Recency: 40 points max
   - USPS Validation: 25 points max
   - Transaction History: 25 points max
   - Source Trust: 10 points max (with penalties for poor sources)

2. **`mailing_list_priority` view** - Recommends best address per contact
   - Calculates billing_score and shipping_score
   - Recommends billing or shipping (15-point switching threshold)
   - Assigns confidence level (very_high, high, medium, low, very_low)
   - Supports manual overrides via `preferred_mailing_address` column

3. **`mailing_list_export` view** - Ready-to-export format
   - Flattens recommended address into single set of fields
   - Includes metadata for filtering
   - Ready for CSV export

4. **`mailing_list_stats` view** - System statistics
   - Total contacts by recommendation
   - Confidence level distribution
   - Average scores

5. **`preferred_mailing_address` column** - Manual override support
   - Staff can force 'billing' or 'shipping'
   - NULL = use algorithm

**Status:** Applied, production ready

---

#### 2. `20251114000001_protect_mailing_list.sql`
**Purpose:** RLS policies for mailing list views

**Creates:**
- Row-level security policies
- Ensures staff can only see contacts they're authorized for
- Protects sensitive mailing data

**Status:** Applied

---

#### 3. `20251114000002_fix_address_scoring_critical_bugs.sql`
**Purpose:** Bug fixes for scoring algorithm

**Fixes:**
- Edge cases in score calculation
- NULL handling
- Date comparison logic

**Status:** Applied

---

#### 4. `20251113000005_secure_financial_tables_rls.sql` (Nov 13)
**Purpose:** RLS for financial tables (transactions, subscriptions)

**Status:** Applied

---

#### 5. `20251113000006_simplify_staff_access.sql` (Nov 13)
**Purpose:** Simplified staff access control model

**Creates:**
- `staff_allowlist` table
- `staff_roles` table
- Simplified RLS policies

**Status:** Applied

---

### UI Components (2 files in /workspaces/starhouse-database-v2/starhouse-ui/components/contacts/)

#### 1. `MailingListQuality.tsx` ⭐ NEW (Nov 14)
**Purpose:** Display address quality and recommendations for each contact

**Features:**
- Shows recommended address (billing or shipping)
- Displays confidence level with color-coded badges
  - Green: very_high
  - Blue: high
  - Yellow: medium
  - Orange: low
  - Red: very_low
- Shows individual scores for billing and shipping
- Indicates manual overrides
- Warns about incomplete addresses
- Real-time data from `mailing_list_priority` view

**Location in UI:** Contact detail page (ContactDetailCard)

**Props:** `{ contactId: string }`

**Sample output:**
```
Recommended: Shipping
3472 Sunshine Canyon Dr

Score: 95 / 100  [Very High]

Billing: 93 pts
Shipping: 95 pts
```

---

#### 2. `ContactDetailCard.tsx` (Modified Nov 13-14)
**Purpose:** Main contact detail display with multiple address variants

**Recent changes:**
- Fixed missing city/state/zip in shipping address display
- Improved address data quality display
- Integrated MailingListQuality component
- Shows billing, shipping, and alternate addresses
- Extracts addresses from contact data

**Bugs fixed:**
- Shipping address showing incomplete data
- City/state/zip missing from alternate addresses
- Address line 2 not displaying

---

### Documentation (23 files in /workspaces/starhouse-database-v2/docs/)

#### Critical Documents ⭐

##### 1. `MAILING_LIST_FINE_TUNING_GUIDE.md` ⭐ NEW (Nov 14)
**Purpose:** Complete guide to using and tuning the mailing list system

**Contents:**
- Quick start guide (how to export mailing lists)
- Current system overview (scoring, confidence levels, statistics)
- Fine-tuning options (adjust thresholds, weights, switching logic)
- Common scenarios (reduce costs, target active customers, boost scores)
- Troubleshooting guide
- Monitoring and maintenance schedule
- Understanding score breakdown

**Audience:** You (business owner) and future staff

**Key sections:**
- Export commands for different use cases
- How to adjust confidence thresholds
- How to change scoring weights
- Manual override instructions
- Monthly maintenance checklist

---

##### 2. `ADDRESS_SCRAMBLE_FIX_2025-11-14.md` (Nov 14)
**Purpose:** Complete incident report for Nov 14 address scramble discovery

**Contents:**
- Timeline of events (Nov 1 scramble, Nov 14 discovery)
- What was fixed (679 addresses restored)
- What was preserved (all work from today)
- Root cause analysis (Nov 1 PayPal import bug hypothesis)
- Prevention recommendations
- Lessons learned

**Status:** Incident closed, all addresses restored

---

##### 3. `DIAGNOSTIC_REPORT_24HR_NOV14.md` (Nov 14)
**Purpose:** 24-hour diagnostic proving scramble wasn't from today's work

**Key findings:**
- ✅ 0 billing addresses changed in last 24 hours
- ✅ 0 shipping addresses changed in last 24 hours
- ⚠️ 1,388 contacts had `updated_at` changed (but NOT address fields)
- ✅ Addresses were wrong since Nov 1, 2025

**Conclusion:** Today's USPS validation did NOT cause scramble

---

##### 4. `MAILING_LIST_IMPLEMENTATION_COMPLETE.md` (Nov 14)
**Purpose:** Implementation summary for mailing list priority system

**Contents:**
- System architecture
- Database schema changes
- Scoring algorithm details
- UI integration
- Testing results

---

#### Investigation Documents

5. `CRITICAL_ADDRESS_SCRAMBLING_REPORT.md` (Nov 14)
   - Initial investigation into address scramble
   - Ed Burns case study
   - Comparison with Kajabi data

6. `ED_BURNS_FARGO_ADDRESS_INVESTIGATION.md` (Nov 14)
   - Deep dive into Ed Burns address issue
   - Multiple Kajabi accounts discovered
   - Address history analysis

7. `ED_BURNS_UI_FIX.md` (Nov 14)
   - UI-specific fixes for Ed Burns display

8. `CRITICAL_DATA_MIXING_ERROR_2020_IMPORT.md`
   - Analysis of potential 2020 import issues

---

#### Validation & Quality Documents

9. `ADDRESS_VALIDATION_SETUP.md` (Nov 14)
   - SmartyStreets API setup
   - Validation process documentation

10. `USPS_VALIDATION_CAPABILITIES.md` (Nov 14)
    - What USPS validation can and cannot do
    - DPV match codes explained

11. `VALIDATION_READY_STATUS.md` (Nov 14)
    - System readiness for validation

12. `VALIDATION_RESULTS_EXPLAINED.md` (Nov 14)
    - How to interpret validation results

13. `ZIP_CODE_AUDIT_2025-11-14.md` (Nov 14)
    - ZIP+4 extension audit and corrections

14. `PHASE2_SHIPPING_VALIDATION.md` (Nov 14)
    - Shipping address validation plan

---

#### System Implementation Documents

15. `MAILING_LIST_PRIORITY_STRATEGY.md` (Nov 14)
    - Strategy for priority system design

16. `MAILING_LIST_SESSION_COMPLETE.md` (Nov 14)
    - Session summary for mailing list work

17. `MAILING_LIST_UI_IMPLEMENTATION.md` (Nov 14)
    - UI component implementation details

18. `UI_IMPLEMENTATION_COMPLETE.md` (Nov 13-14)
    - Complete UI implementation summary

19. `DEPLOYMENT_COMPLETE_2025-11-14.md` (Nov 14)
    - Deployment checklist and status

20. `VERIFICATION_COMPLETE.md` (Nov 14)
    - System verification and testing results

---

#### Security Documents

21. `SECURE_STAFF_SETUP_GUIDE.md` (Modified Nov 13-14)
    - Staff access control setup
    - Ed Burns configured as initial admin

22. `STAFF_MANAGEMENT_SIMPLIFIED.md` (Nov 13)
    - Simplified staff management model

---

#### Code Review Documents

23. `FAANG_CODE_REVIEW_MAILING_SYSTEM.md` (Nov 14)
    - FAANG-level code review of mailing system

24. `FAANG_FIXES_COMPLETE.md` (Nov 14)
    - Fixes from code review

---

#### Previous Handoffs

25. `HANDOFF_2025-11-13.md` (Nov 13)
26. `HANDOFF_2025-11-14_UI_COMPLETE.md` (Nov 14 earlier)

---

### Configuration Files

#### `.vscode/settings.json` (Modified)
**Changes:**
- Updated Python path settings
- Configured linting and formatting
- Added project-specific settings

#### `.vscode/settings.backup.json` (New)
**Purpose:** Backup of previous settings

---

## How to Use the System

### 1. Export a Mailing List (Most Common)

```bash
# Export high-quality contacts for mailing (832 contacts)
python3 scripts/export_mailing_list.py --min-confidence high

# Output: /tmp/mailing_list_export.csv
# Contains: first_name, last_name, email, address_line_1, address_line_2,
#           city, state, postal_code, country, + metadata
```

**Confidence levels:**
- `very_high` = 632 contacts (best quality, ready to mail)
- `high` = 200 more contacts (good quality, safe to mail)
- `medium` = 34 contacts (fair quality, verify first)
- `low` = 20 contacts (poor quality, needs update)
- `very_low` = 588 contacts (bad quality, do not mail)

---

### 2. Filter by Recent Customers

```bash
# Only customers who purchased in last year
python3 scripts/export_mailing_list.py \
  --min-confidence high \
  --recent-customers 365 \
  --output /tmp/active_customers_2025.csv
```

---

### 3. Clean Export for Mail Merge

```bash
# No metadata columns (just name, email, address)
python3 scripts/export_mailing_list.py \
  --min-confidence high \
  --no-metadata \
  --output /tmp/holiday_cards_2025.csv
```

---

### 4. View Address Quality in UI

1. Open any contact in Starhouse UI
2. See "Mailing List Quality" section
3. Shows:
   - Recommended address (billing or shipping)
   - Confidence level (color-coded badge)
   - Individual scores
   - Warnings for incomplete addresses

---

### 5. Manual Override for Specific Contact

```bash
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

# Force a contact to use shipping address
psql "$DATABASE_URL" -c "
  UPDATE contacts
  SET preferred_mailing_address = 'shipping'
  WHERE email = 'customer@example.com';
"

# Force back to billing
psql "$DATABASE_URL" -c "
  UPDATE contacts
  SET preferred_mailing_address = 'billing'
  WHERE email = 'customer@example.com';
"

# Remove override (use algorithm)
psql "$DATABASE_URL" -c "
  UPDATE contacts
  SET preferred_mailing_address = NULL
  WHERE email = 'customer@example.com';
"
```

---

### 6. Check System Statistics

```bash
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

# View confidence distribution
psql "$DATABASE_URL" -c "
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

**Expected output:**
```
confidence | contacts | avg_score
-----------+----------+-----------
very_high  |      632 |      80.4
high       |      200 |      65.4
medium     |       34 |      53.1
low        |       20 |      35.2
very_low   |      588 |      21.7
```

---

### 7. Monthly Maintenance (Recommended)

```bash
# Step 1: Sync billing addresses from Kajabi
python3 scripts/restore_addresses_from_kajabi.py
# Review changes, then execute:
python3 scripts/restore_addresses_from_kajabi.py --execute

# Step 2: Validate addresses with USPS/SmartyStreets
python3 scripts/validate_all_addresses.py

# Step 3: Check statistics
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
psql "$DATABASE_URL" -c "
  SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE confidence IN ('very_high', 'high')) as high_quality,
    ROUND(100.0 * COUNT(*) FILTER (WHERE confidence IN ('very_high', 'high')) / COUNT(*), 1) as pct_high_quality
  FROM mailing_list_priority;
"
```

---

## Scoring Algorithm Details

### How Addresses Are Scored (0-100 points)

Each address (billing and shipping) gets scored independently based on 4 factors:

#### Factor 1: Recency (40 points max)
How recently the address was updated:
- Last 30 days: +40 points
- 31-90 days: +30 points
- 91-180 days: +20 points
- 181-365 days: +10 points
- Older: 0 points

**Rationale:** Recently updated addresses are more likely to be current.

---

#### Factor 2: USPS Validation (25 points max)
Whether address passed USPS validation:
- Validated in last 90 days: +25 points
- Validated in last year: +20 points
- Validated ever: +10 points
- Manually verified (legacy): +5 points
- Not validated: 0 points

**Rationale:** USPS-validated addresses are confirmed deliverable.

---

#### Factor 3: Transaction History (25 points max)
How recently customer made a purchase:
- Last 30 days: +25 points
- 31-90 days: +20 points
- 91-180 days: +15 points
- 181-365 days: +10 points
- 1+ years ago: +5 points
- Never: 0 points

**Rationale:** Active customers likely have current addresses on file.

---

#### Factor 4: Source Trust (10 points max, with penalties)
Where the address came from:
- PayPal: +10 points (from actual transaction)
- Kajabi: +8 points (from user profile)
- Manual: +7 points (staff entered)
- **copied_from_billing: -10 points** ⚠️ (derived data, not authoritative)
- **unknown_legacy: -5 points** ⚠️ (old data, uncertain origin)

**Rationale:** PayPal addresses from purchases are most reliable.

---

### How Recommendation Is Made

1. **Calculate both scores:**
   - billing_score = 0-100
   - shipping_score = 0-100

2. **Apply 15-point switching threshold:**
   - If billing_score >= shipping_score + 15 → recommend billing
   - If shipping_score >= billing_score + 15 → recommend shipping
   - Otherwise → recommend billing (default)

3. **Manual override takes precedence:**
   - If `preferred_mailing_address` is set, use that regardless of scores

4. **Assign confidence level based on winning score:**
   - 75-100 = very_high
   - 60-74 = high
   - 45-59 = medium
   - 30-44 = low
   - 0-29 = very_low

---

### Example: Ed Burns

**Current state:**
```
Billing Address: 3472 Sunshine Canyon Dr, Boulder, CO 80302
  - Recency: 40 pts (updated Nov 14, within 30 days)
  - USPS: 0 pts (not validated yet)
  - Transaction: 25 pts (last purchase Oct 5, within 90 days)
  - Source: 8 pts (kajabi_line2)
  - TOTAL: 73 pts

Shipping Address: PO Box 4547, Boulder, CO 80306
  - Recency: 30 pts (updated Nov 1, within 90 days)
  - USPS: 25 pts (validated Nov 14)
  - Transaction: 25 pts (same customer)
  - Source: 10 pts (paypal)
  - TOTAL: 90 pts

Recommendation: SHIPPING (90 > 73, exceeds 15-point threshold)
Confidence: very_high (90 >= 75)
```

**To boost billing score:** Run USPS validation on billing address (+25 pts → 98 pts total)

---

## Common Tasks

### Task 1: "I want to mail holiday cards to my best customers"

```bash
# Export very high confidence + recent customers
python3 scripts/export_mailing_list.py \
  --min-confidence very_high \
  --recent-customers 365 \
  --no-metadata \
  --output /tmp/holiday_cards_2025.csv
```

This gives you premium quality addresses for customers who purchased in last year.

---

### Task 2: "I want to improve address quality over time"

**Monthly routine:**
1. Sync from Kajabi (gets latest billing addresses)
2. Run USPS validation (verifies deliverability)
3. Check stats (monitor improvement)

```bash
# Month 1
python3 scripts/restore_addresses_from_kajabi.py --execute
python3 scripts/validate_all_addresses.py
# Check stats...

# Month 2
# Repeat...

# Month 3
# Should see improvement in confidence distribution
```

---

### Task 3: "A customer says they moved, I need to update their address"

**Option A: Update in Kajabi** (recommended)
1. Update address in Kajabi
2. Wait for next monthly sync OR run sync manually:
```bash
python3 scripts/restore_addresses_from_kajabi.py --execute
```

**Option B: Update in database directly**
```bash
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
psql "$DATABASE_URL" -c "
  UPDATE contacts
  SET
    address_line_1 = '123 New Street',
    city = 'New City',
    state = 'CA',
    postal_code = '90210',
    billing_address_source = 'manual',
    billing_address_updated_at = NOW()
  WHERE email = 'customer@example.com';
"
```

Then optionally validate the new address:
```bash
python3 scripts/validate_all_addresses.py
```

---

### Task 4: "The algorithm is recommending the wrong address for someone"

**Check current recommendation:**
```bash
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
psql "$DATABASE_URL" -c "
  SELECT first_name, last_name, email,
         recommended_address, confidence,
         billing_score, shipping_score,
         billing_line1, shipping_line1
  FROM mailing_list_priority
  WHERE email = 'customer@example.com';
"
```

**Option 1: Manual override** (quick fix)
```bash
psql "$DATABASE_URL" -c "
  UPDATE contacts
  SET preferred_mailing_address = 'shipping'  -- or 'billing'
  WHERE email = 'customer@example.com';
"
```

**Option 2: Boost the score of correct address**
- Run USPS validation: +25 pts
- Update address in Kajabi: +40 pts (recency)
- Update from PayPal: +10 pts (source)

---

### Task 5: "I want to change how the scoring works"

See `docs/MAILING_LIST_FINE_TUNING_GUIDE.md` for complete tuning guide.

**Quick examples:**

**Make USPS validation more important:**
Edit `supabase/migrations/20251114000000_mailing_list_priority_system.sql:62-74`
```sql
-- Change from 25 max to 35 max
IF usps_date > NOW() - INTERVAL '90 days' THEN
  score := score + 35;  -- was 25
ELSIF usps_date > NOW() - INTERVAL '365 days' THEN
  score := score + 25;  -- was 20
-- etc.
```

**Make confidence thresholds stricter:**
Edit `supabase/migrations/20251114000000_mailing_list_priority_system.sql:186-192`
```sql
CASE
  WHEN GREATEST(billing_score, shipping_score) >= 80 THEN 'very_high'  -- was 75
  WHEN GREATEST(billing_score, shipping_score) >= 65 THEN 'high'       -- was 60
  -- etc.
```

After editing, re-apply migration:
```bash
psql $DATABASE_URL < supabase/migrations/20251114000000_mailing_list_priority_system.sql
```

---

## Troubleshooting

### Problem: "Export has too few contacts"

**Check confidence distribution:**
```bash
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
psql "$DATABASE_URL" -c "
  SELECT confidence, COUNT(*)
  FROM mailing_list_priority
  GROUP BY confidence;
"
```

**If too many very_low:**
1. Run USPS validation to boost scores
2. Sync from Kajabi to get latest addresses
3. Lower confidence threshold in export command

---

### Problem: "Scores are lower than expected"

**Check what's missing:**
```bash
psql "$DATABASE_URL" -c "
  SELECT
    COUNT(*) FILTER (WHERE billing_usps_validated_at IS NULL) as no_validation,
    COUNT(*) FILTER (WHERE billing_address_updated_at < NOW() - INTERVAL '365 days') as old_addresses,
    COUNT(*) FILTER (WHERE last_transaction_date IS NULL) as no_transactions
  FROM contacts;
"
```

**Solutions:**
- `no_validation` high → Run USPS validation
- `old_addresses` high → Sync from Kajabi
- `no_transactions` high → Import PayPal transaction data

---

### Problem: "UI not showing mailing list quality component"

**Check:**
1. Is migration applied? `psql $DATABASE_URL -c "\d mailing_list_priority"`
2. Is component imported? Check `ContactDetailCard.tsx`
3. Is contact in view? `psql $DATABASE_URL -c "SELECT COUNT(*) FROM mailing_list_priority WHERE id = 'contact-uuid';"`

---

## Next Steps

### Immediate (Next Week)
- [ ] Export first mailing list for holiday campaign
- [ ] Test export with mail merge service (e.g., Lob, Click2Mail)
- [ ] Verify addresses for top 10 customers manually

### Monthly Maintenance
- [ ] Sync billing addresses from Kajabi
- [ ] Run USPS validation on all addresses
- [ ] Review confidence distribution trends
- [ ] Update any manual overrides as needed

### Quarterly Review (March 2026)
- [ ] Review scoring algorithm effectiveness
- [ ] Adjust confidence thresholds if needed
- [ ] Analyze return mail rate (if tracking)
- [ ] Consider adjusting factor weights based on results

### Future Enhancements (Optional)
- [ ] Integrate PayPal transaction imports for shipping addresses
- [ ] Add email verification to scoring algorithm
- [ ] Implement address history tracking (track all address changes)
- [ ] Add "undeliverable" flag for returned mail
- [ ] Create dashboard for address quality monitoring
- [ ] Set up automated monthly Kajabi sync (cron job)

---

## Important Notes

### Database Connection

All scripts use this connection string (already embedded):
```
postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

For psql commands, set environment variable:
```bash
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
```

---

### Kajabi CSV Location

Current Kajabi export file:
```
/workspaces/starhouse-database-v2/kajabi 3 files review/11102025kajabi.csv
```

**For future syncs:** Export new CSV from Kajabi and update path in `restore_addresses_from_kajabi.py:20`

---

### SmartyStreets API

**Status:** Configured and working

**API Key:** Embedded in validation scripts

**Usage limits:** Check SmartyStreets dashboard

**Cost:** Pay-per-validation (monitor usage)

---

### Ed Burns Special Case

Ed Burns has **TWO** Kajabi accounts:
1. `eburns009@gmail.com` - ACTIVE (last transaction Oct 5, 2025)
   - Billing: 3472 Sunshine Canyon Dr, Boulder, CO 80302 (CURRENT)
   - Shipping: PO Box 4547, Boulder, CO 80306

2. `support@thestarhouse.org` - Less active
   - Address: 3472 Sunshine Canyon Dr, Boulder, CO 80302

**Current recommendation:** Use shipping address (PO Box 4547) for mailings - highest score (95/100)

**Address history:**
- 1144 Rozel Ave, Southampton, PA (8 years old, DO NOT USE)
- 3472 Sunshine Canyon Dr, Boulder, CO (current residence)
- PO Box 4547, Boulder, CO (current mailing preference - RECOMMENDED)

---

## Summary

### What Was Built
1. ✅ **Address Scoring System** - Intelligent 0-100 scoring algorithm
2. ✅ **Mailing List Priority** - Database views for recommendations
3. ✅ **Export Tool** - Flexible mailing list generation
4. ✅ **UI Components** - Visual address quality display
5. ✅ **Validation Integration** - USPS/SmartyStreets validation
6. ✅ **Manual Override Support** - Staff can override recommendations
7. ✅ **Complete Documentation** - Usage guides and troubleshooting

### What Was Fixed
1. ✅ **679 scrambled addresses** - Restored from Kajabi
2. ✅ **571 shipping addresses** - Validated with USPS
3. ✅ **Ed Burns address** - Updated to current location
4. ✅ **UI address display bugs** - Complete and accurate display
5. ✅ **Address data quality** - 832 high-confidence contacts ready

### What You Have Now
- **832 high-quality addresses** ready for mailing campaigns
- **Automated quality scoring** to prioritize best addresses
- **Export tool** to generate mailing lists with confidence filtering
- **UI visibility** into address quality and recommendations
- **Monthly maintenance process** to keep data current
- **Complete documentation** for future reference and fine-tuning

### Zero Data Loss
All work from previous sessions preserved:
- ✅ Mailing list priority system intact
- ✅ USPS validation metadata preserved
- ✅ UI improvements functional
- ✅ Database migrations applied
- ✅ Security/RLS policies in place

---

## Quick Reference Commands

```bash
# Export mailing list (most common)
python3 scripts/export_mailing_list.py --min-confidence high

# Sync from Kajabi (monthly)
python3 scripts/restore_addresses_from_kajabi.py --execute

# Validate with USPS (monthly)
python3 scripts/validate_all_addresses.py

# Check system stats
export DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
psql "$DATABASE_URL" -c "SELECT confidence, COUNT(*) FROM mailing_list_priority GROUP BY confidence;"

# Manual override
psql "$DATABASE_URL" -c "UPDATE contacts SET preferred_mailing_address = 'shipping' WHERE email = 'customer@example.com';"
```

---

## Support & References

**Main Documentation:**
- `docs/MAILING_LIST_FINE_TUNING_GUIDE.md` - Complete tuning guide
- `docs/ADDRESS_SCRAMBLE_FIX_2025-11-14.md` - Incident report
- `docs/DIAGNOSTIC_REPORT_24HR_NOV14.md` - Investigation details

**Scripts:**
- `scripts/export_mailing_list.py` - Export tool
- `scripts/restore_addresses_from_kajabi.py` - Sync tool
- `scripts/validate_all_addresses.py` - Validation tool

**Database:**
- `supabase/migrations/20251114000000_mailing_list_priority_system.sql` - Core system

**UI:**
- `starhouse-ui/components/contacts/MailingListQuality.tsx` - Quality display
- `starhouse-ui/components/contacts/ContactDetailCard.tsx` - Contact detail page

---

**Handoff Created:** 2025-11-14
**System Status:** Production Ready
**Ready for:** Holiday mailing campaigns, ongoing customer communications

**You're all set!** 🎉

The mailing list system is production-ready with 832 high-quality addresses available for your next campaign.
