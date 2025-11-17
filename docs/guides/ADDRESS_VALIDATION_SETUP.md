# ADDRESS VALIDATION SETUP GUIDE

**Status:** Ready to validate 571 US shipping addresses
**Export File:** `/tmp/shipping_addresses_for_validation.csv`

---

## Quick Start - 3 Options

### Option 1: SmartyStreets (RECOMMENDED) ⭐

**Pros:**
- Fastest setup (5 minutes)
- 250 free lookups/month (no credit card)
- Most complete data (DPV, geocoding, county, RDI, vacant)
- After free tier: $4-9 for 571 addresses

**Setup:**

1. **Sign up** (5 minutes):
   - Go to: https://www.smarty.com/pricing/us-address-verification
   - Click "Start Free Trial"
   - No credit card required for free tier

2. **Get credentials**:
   - Log in to dashboard
   - Go to "API Keys" section
   - Copy your "Auth ID" and "Auth Token"

3. **Set environment variables**:
   ```bash
   export SMARTY_AUTH_ID='your_auth_id_here'
   export SMARTY_AUTH_TOKEN='your_auth_token_here'
   ```

4. **Run validation**:
   ```bash
   cd /workspaces/starhouse-database-v2
   python3 scripts/validate_addresses_smarty.py
   ```

5. **Import results**:
   ```bash
   python3 scripts/import_usps_validation_shipping.py
   ```

---

### Option 2: USPS Web Tools API (FREE)

**Pros:**
- Completely free (unlimited)
- Official USPS data
- ZIP+4 standardization

**Cons:**
- Slower approval process (1-2 days)
- Limited data (no county, RDI, or geocoding)
- Rate limit: 5 requests/second

**Setup:**

1. **Register** (10 minutes + approval wait):
   - Go to: https://www.usps.com/business/web-tools-apis/
   - Click "Register"
   - Fill out form with business information
   - Wait for approval email (usually 1-2 days)

2. **Get User ID**:
   - Check your email for approval
   - Note your USPS User ID

3. **Set environment variable**:
   ```bash
   export USPS_USER_ID='your_user_id_here'
   ```

4. **Run validation**:
   ```bash
   cd /workspaces/starhouse-database-v2
   python3 scripts/validate_addresses_usps.py
   ```

5. **Import results**:
   ```bash
   python3 scripts/import_usps_validation_shipping.py
   ```

**Note:** USPS validation will take longer (571 addresses ÷ 4 req/sec = ~2.4 minutes)

---

### Option 3: Commercial Bulk Upload

**For quick one-time validation:**

1. **Download CSV**:
   ```bash
   cp /tmp/shipping_addresses_for_validation.csv ~/Downloads/
   ```

2. **Upload to service**:
   - **Lob.com**: https://dashboard.lob.com/ (Instant, $23 for 571)
   - **Melissa Data**: https://www.melissa.com/quickstart (24h, $11-29)
   - **PostGrid**: https://postgrid.com/ (Instant, varies)

3. **Download results** as CSV to `/tmp/shipping_addresses_validated.csv`

4. **Import**:
   ```bash
   python3 scripts/import_usps_validation_shipping.py
   ```

---

## Detailed Instructions: SmartyStreets Setup

Since SmartyStreets is the fastest and most comprehensive option, here's a detailed walkthrough:

### Step 1: Create Account

1. Open browser to: https://www.smarty.com/pricing/us-address-verification
2. Click "Start Free Trial" button
3. Fill in:
   - Email address
   - Password
   - Company name (can be "StarHouse" or your name)
4. Click "Create Account"
5. Verify email if required

### Step 2: Get API Credentials

1. Log in to: https://www.smarty.com/account/keys
2. You'll see a table with "Website Key" and "Secret Keys"
3. Under "Secret Keys" section:
   - Click "Create new" if no keys exist
   - Give it a name like "StarHouse CRM"
   - Copy the "Auth ID" (looks like: `12345678-9abc-def0-1234-56789abcdef0`)
   - Copy the "Auth Token" (looks like: `AbCdEfGhIjKlMnOpQrStUvWx`)

### Step 3: Set Environment Variables

**Option A: For this session only:**
```bash
export SMARTY_AUTH_ID='12345678-9abc-def0-1234-56789abcdef0'
export SMARTY_AUTH_TOKEN='AbCdEfGhIjKlMnOpQrStUvWx'
```

**Option B: Permanently (add to .bashrc or .zshrc):**
```bash
echo 'export SMARTY_AUTH_ID="12345678-9abc-def0-1234-56789abcdef0"' >> ~/.bashrc
echo 'export SMARTY_AUTH_TOKEN="AbCdEfGhIjKlMnOpQrStUvWx"' >> ~/.bashrc
source ~/.bashrc
```

**Option C: Add to .env file:**
```bash
# Add to /workspaces/starhouse-database-v2/.env
SMARTY_AUTH_ID=12345678-9abc-def0-1234-56789abcdef0
SMARTY_AUTH_TOKEN=AbCdEfGhIjKlMnOpQrStUvWx
```

Then before running:
```bash
source /workspaces/starhouse-database-v2/.env
```

### Step 4: Test Connection

Test with first 5 addresses:
```bash
head -6 /tmp/shipping_addresses_for_validation.csv > /tmp/test_addresses.csv
python3 scripts/validate_addresses_smarty.py /tmp/test_addresses.csv /tmp/test_results.csv
```

Expected output:
```
======================================================================
ADDRESS VALIDATION - SMARTYSTREETS
======================================================================
Input file:     /tmp/test_addresses.csv
Output file:    /tmp/test_results.csv
Progress file:  /tmp/smarty_validation_progress.csv
Rate limit:     10 requests/second

Reading input addresses...
  ✓ Loaded 5 addresses
...
======================================================================
VALIDATION COMPLETE
======================================================================
Total addresses:        5
Successfully validated: 5
Failed validation:      0
Success rate:           100.0%
```

### Step 5: Run Full Validation

If test succeeded:
```bash
python3 scripts/validate_addresses_smarty.py
```

This will:
- Process all 571 addresses
- Take ~1 minute (10 addresses/second)
- Save progress every 10 records
- Create `/tmp/shipping_addresses_validated.csv`

### Step 6: Import to Database

```bash
python3 scripts/import_usps_validation_shipping.py
```

Expected output:
```
======================================================================
IMPORT COMPLETE
======================================================================
Total validation records:     571
Successfully matched:         550
Contacts updated:             550
Failed USPS validation:       21
...
Total contacts with USPS-validated shipping addresses: 550
```

---

## Troubleshooting

### Error: "Authentication failed"

**SmartyStreets:**
- Check that `SMARTY_AUTH_ID` and `SMARTY_AUTH_TOKEN` are set correctly
- Verify credentials in dashboard: https://www.smarty.com/account/keys
- Make sure you copied the full Auth ID and Token (no spaces)

**USPS:**
- Check that `USPS_USER_ID` is set correctly
- Verify you received the approval email
- Wait 24-48 hours after registration if just registered

### Error: "Payment required"

**SmartyStreets:**
- You've used your 250 free lookups this month
- Add a payment method to continue
- Cost: $0.007-0.015 per lookup ($4-9 for 571 addresses)

### Error: "Rate limit exceeded"

- The script includes built-in rate limiting
- If this occurs, wait 1 minute and resume
- The progress file saves every 10 records, so you won't lose data

### Script stops mid-validation

**Resume from where it left off:**
```bash
# SmartyStreets
python3 scripts/validate_addresses_smarty.py

# USPS
python3 scripts/validate_addresses_usps.py
```

The scripts automatically detect the progress file and resume.

---

## Validation Output Format

The validation scripts create a CSV with these columns:

| Column | Example | Description |
|--------|---------|-------------|
| `[sequence]` | `1` | Row number for matching |
| `ValidationFlag` | `OK` or `ERROR` | Overall status |
| `[dpv_match_code]` | `Y` | Y=confirmed, N=not found, S=missing secondary, D=missing unit |
| `[delivery_line_1]` | `2909 25th St` | Standardized address line 1 |
| `[city_name]` | `Sacramento` | Standardized city |
| `[state_abbreviation]` | `CA` | State code |
| `[full_zipcode]` | `95818-3421` | ZIP+4 code |
| `[county_name]` | `Sacramento County` | County name (SmartyStreets only) |
| `[latitude]` | `38.5647` | Geocoded latitude (SmartyStreets only) |
| `[longitude]` | `-121.4876` | Geocoded longitude (SmartyStreets only) |
| `[precision]` | `Zip9` | Geocoding accuracy |
| `[rdi]` | `Residential` | Residential or Commercial |
| `[dpv_vacant]` | `N` | Y if property is vacant |
| `[active]` | `Y` | Y if active delivery point |

---

## Cost Comparison

| Service | Setup Time | Processing Time | Cost | Data Completeness |
|---------|-----------|-----------------|------|-------------------|
| **SmartyStreets** | 5 min | 1 min | $0-9 | ⭐⭐⭐⭐⭐ (100%) |
| **USPS Web Tools** | 2 days | 2.4 min | $0 | ⭐⭐⭐ (60%) |
| **Lob.com** | Instant | Instant | $23 | ⭐⭐⭐⭐⭐ (100%) |
| **Melissa Data** | Instant | 24 hours | $11-29 | ⭐⭐⭐⭐⭐ (100%) |

**Recommendation:** Start with SmartyStreets for fastest results and best data quality.

---

## What Happens After Import

Once you run `import_usps_validation_shipping.py`:

1. **Database updated:**
   - 571 contacts get shipping USPS validation data
   - `shipping_usps_validated_at` timestamp set to NOW()
   - `shipping_usps_dpv_match_code`, lat/long, county, etc. populated

2. **Mailing list scores improve:**
   ```sql
   SELECT * FROM mailing_list_stats;
   ```
   - Average score increases by ~5-10 points
   - 50-100 more contacts reach "high confidence"
   - Better address selection (shipping may beat billing for some contacts)

3. **New capabilities unlocked:**
   - Geographic proximity queries (50 miles from Boulder, etc.)
   - Vacant address detection (people who moved)
   - Residential vs commercial segmentation

4. **Export improved mailing list:**
   ```sql
   COPY (
     SELECT * FROM mailing_list_export
     WHERE confidence IN ('very_high', 'high')
     ORDER BY last_name, first_name
   ) TO '/tmp/mailing_list_high_confidence_v2.csv' CSV HEADER;
   ```

---

## Next Steps After Validation

See: [PHASE2_SHIPPING_VALIDATION.md](PHASE2_SHIPPING_VALIDATION.md) for:
- Sample queries (geographic analysis, vacant detection)
- Phase 3 planning (UI integration, source backfilling)
- ROI analysis and cost-benefit

---

**Last Updated:** 2025-11-14
**Status:** Ready to run
**Recommended:** SmartyStreets (Option 1)
