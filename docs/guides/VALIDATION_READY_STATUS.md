# SHIPPING ADDRESS VALIDATION - READY TO RUN ✅

**Date:** 2025-11-14
**Phase:** 2 - Data Quality Improvement
**Status:** Scripts Ready, Waiting for API Credentials

---

## What's Complete ✅

### 1. Database Preparation ✅
- ✅ All 13 `shipping_usps_*` fields exist in contacts table
- ✅ Scoring function already supports shipping validation (lines 37-41)
- ✅ Views will auto-update when data is imported
- ✅ Import script tested and ready

### 2. Export Ready ✅
- ✅ **571 US shipping addresses** exported to CSV
- ✅ File: `/tmp/shipping_addresses_for_validation.csv`
- ✅ Includes email for safe matching
- ✅ Sequence numbers for row matching
- ✅ 648 international addresses excluded (USPS can't validate)

### 3. Validation Scripts Created ✅

**Option A: USPS Web Tools (Free)**
- ✅ Script: `scripts/validate_addresses_usps.py`
- ✅ Rate limiting: 4 requests/second
- ✅ Resumable (saves progress every 10 records)
- ✅ ETA: ~2.4 minutes for 571 addresses
- ⚠️ **Requires:** USPS User ID (free registration, 1-2 day approval)

**Option B: SmartyStreets (Recommended)**
- ✅ Script: `scripts/validate_addresses_smarty.py`
- ✅ Rate limiting: 10 requests/second
- ✅ Resumable (saves progress every 10 records)
- ✅ ETA: ~1 minute for 571 addresses
- ✅ More complete data (county, geocoding, RDI, vacant)
- ⚠️ **Requires:** SmartyStreets Auth ID + Token (instant setup, 250 free/month)

### 4. Import Script Ready ✅
- ✅ Script: `scripts/import_usps_validation_shipping.py`
- ✅ Safe matching by email (no fuzzy matching)
- ✅ Updates all 13 shipping USPS fields
- ✅ Progress reporting and error handling
- ✅ Tested with Phase 1 billing addresses

### 5. Documentation Complete ✅
- ✅ Phase 2 overview: `docs/PHASE2_SHIPPING_VALIDATION.md`
- ✅ Setup guide: `docs/ADDRESS_VALIDATION_SETUP.md`
- ✅ Cost-benefit analysis
- ✅ Post-validation queries and use cases

---

## What's Needed: API Credentials

To run validation, you need credentials for ONE of these services:

### Option 1: SmartyStreets (FASTEST - Recommended) ⭐

**Time to setup:** 5 minutes
**Time to validate:** 1 minute
**Cost:** Free for first 250 addresses, then $4-9 for remaining 321

**Setup Steps:**

1. **Sign up** (5 min):
   ```
   https://www.smarty.com/pricing/us-address-verification
   → Click "Start Free Trial"
   → No credit card required
   ```

2. **Get credentials**:
   ```
   Login → API Keys section
   → Copy "Auth ID" and "Auth Token"
   ```

3. **Set environment variables**:
   ```bash
   export SMARTY_AUTH_ID='your_auth_id'
   export SMARTY_AUTH_TOKEN='your_auth_token'
   ```

4. **Run validation**:
   ```bash
   python3 scripts/validate_addresses_smarty.py
   ```

**Done!** ✅

---

### Option 2: USPS Web Tools (100% FREE)

**Time to setup:** 10 minutes + 1-2 day approval wait
**Time to validate:** 2.4 minutes
**Cost:** $0 (unlimited free)

**Setup Steps:**

1. **Register** (10 min):
   ```
   https://www.usps.com/business/web-tools-apis/
   → Fill out registration form
   → Wait for approval email (1-2 days)
   ```

2. **Get User ID**:
   ```
   Check email for approval
   → Note your USPS User ID
   ```

3. **Set environment variable**:
   ```bash
   export USPS_USER_ID='your_user_id'
   ```

4. **Run validation**:
   ```bash
   python3 scripts/validate_addresses_usps.py
   ```

**Note:** USPS provides less data (no county, geocoding, or RDI)

---

## Quick Start Commands

Once you have credentials set, run these commands:

```bash
# Navigate to project
cd /workspaces/starhouse-database-v2

# Option A: SmartyStreets (if credentials set)
python3 scripts/validate_addresses_smarty.py

# Option B: USPS (if credentials set)
python3 scripts/validate_addresses_usps.py

# After validation completes, import results
python3 scripts/import_usps_validation_shipping.py

# Check improved stats
python3 << 'EOF'
import psycopg2
conn = psycopg2.connect("postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres")
cursor = conn.cursor()
cursor.execute("SELECT * FROM mailing_list_stats")
row = cursor.fetchone()
print(f"Total contacts: {row[0]}")
print(f"High confidence: {row[3] + row[4]} ({(row[3]+row[4])/row[0]*100:.1f}%)")
print(f"Average score: {row[9]}")
EOF
```

---

## Expected Results

### Before Validation (Current State)

```sql
SELECT * FROM mailing_list_stats;

total_contacts: 1,922
high_confidence: 750 (39%)
average_score: 27.8
```

### After Validation (Projected)

```sql
SELECT * FROM mailing_list_stats;

total_contacts: 1,922
high_confidence: 850-900 (44-47%)  ← +100-150 contacts
average_score: 33-35               ← +5-7 points
```

**Why?**
- 571 shipping addresses gain +25 points from USPS validation
- Contacts with recent shipping updates but old billing will switch to shipping
- Some contacts currently at 45-50 points (medium) jump to 70-75 (high)

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `/tmp/shipping_addresses_for_validation.csv` | 571 addresses to validate | ✅ Ready |
| `scripts/validate_addresses_usps.py` | USPS validation script | ✅ Ready (needs User ID) |
| `scripts/validate_addresses_smarty.py` | SmartyStreets validation script | ✅ Ready (needs Auth) |
| `scripts/import_usps_validation_shipping.py` | Import results to DB | ✅ Ready |
| `docs/PHASE2_SHIPPING_VALIDATION.md` | Phase 2 overview | ✅ Complete |
| `docs/ADDRESS_VALIDATION_SETUP.md` | Detailed setup guide | ✅ Complete |
| `docs/VALIDATION_READY_STATUS.md` | This file | ✅ Complete |

---

## Validation Script Features

Both scripts include:

✅ **Rate Limiting**
- USPS: 4 req/sec (conservative, limit is 5/sec)
- SmartyStreets: 10 req/sec (limit is 250/sec)

✅ **Progress Tracking**
- Saves every 10 records
- Resumable if interrupted
- Progress file: `/tmp/[service]_validation_progress.csv`

✅ **Error Handling**
- Continues on individual failures
- Logs error messages
- Final statistics report

✅ **Real-time Stats**
- Shows progress every 10 records
- Success/failure counts
- ETA calculation
- Requests per second rate

✅ **Output Format**
- Matches import script expectations
- Includes all required USPS fields
- Ready for direct import

---

## Testing Validation Scripts

You can test with a small sample before running the full 571:

```bash
# Create test file with first 5 addresses
head -6 /tmp/shipping_addresses_for_validation.csv > /tmp/test_addresses.csv

# Test SmartyStreets (if credentials set)
python3 scripts/validate_addresses_smarty.py \
  /tmp/test_addresses.csv \
  /tmp/test_results.csv

# Test USPS (if credentials set)
python3 scripts/validate_addresses_usps.py \
  /tmp/test_addresses.csv \
  /tmp/test_results.csv

# Check results
head -3 /tmp/test_results.csv
```

---

## Alternative: Manual Upload

If you don't want to use the API scripts, you can:

1. **Download CSV**:
   ```bash
   cp /tmp/shipping_addresses_for_validation.csv ~/Downloads/
   ```

2. **Upload to web service**:
   - Lob.com: https://dashboard.lob.com/ ($23, instant)
   - Melissa Data: https://www.melissa.com/quickstart ($11-29, 24hr)
   - ValidateAddress.com: Various pricing

3. **Download results** as CSV to `/tmp/shipping_addresses_validated.csv`

4. **Import**:
   ```bash
   python3 scripts/import_usps_validation_shipping.py
   ```

---

## Next Steps

**To complete Phase 2 validation:**

1. **Choose service** (SmartyStreets recommended for speed)

2. **Get credentials** (5 min for SmartyStreets, 1-2 days for USPS)

3. **Set environment variables**

4. **Run validation script** (~1-2 minutes)

5. **Import results** (~30 seconds)

6. **Verify improved stats**

**Then proceed to Phase 3:**
- UI integration (show scores and confidence in contact details)
- Source backfilling (populate address_source fields)
- Periodic re-validation (monthly updates)

---

## Summary

🎯 **Everything is ready to run**
⏱️ **Total time: 2-7 minutes** (after credentials obtained)
💰 **Total cost: $0-9** (depends on service choice)
📈 **Expected impact: +100-150 contacts to high confidence**

**All that's needed:** API credentials for one validation service.

**Recommendation:** Use SmartyStreets for fastest setup and most complete data.

---

**Prepared:** 2025-11-14
**Status:** ✅ Ready to Run
**Waiting for:** API Credentials (SmartyStreets or USPS)
