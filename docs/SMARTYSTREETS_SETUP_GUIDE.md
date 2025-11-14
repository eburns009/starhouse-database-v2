# SmartyStreets Address Validation Setup Guide

**Purpose:** Validate the 69 newly imported Google Contacts addresses (and optionally other addresses)

**Cost:** FREE for first 250 addresses/month • $0.007-0.015 per address after free tier

---

## Quick Setup (5 minutes)

### Step 1: Sign Up for SmartyStreets

1. Go to: **https://www.smarty.com/pricing/us-address-verification**
2. Click **"Start Free Trial"** or **"Sign Up"**
3. Create account (no credit card required for free tier)
4. Complete email verification

### Step 2: Get API Credentials

1. Log into SmartyStreets dashboard
2. Navigate to: **API Keys** (usually in top menu or sidebar)
3. Find your credentials:
   - **Auth ID** (also called "Website Key" or "Auth ID")
   - **Auth Token** (also called "Secret" or "Auth Token")
4. Copy both values (you'll need them in next step)

### Step 3: Set Environment Variables

**Option A: Temporary (this session only)**
```bash
export SMARTY_AUTH_ID='your_auth_id_here'
export SMARTY_AUTH_TOKEN='your_auth_token_here'
```

**Option B: Permanent (recommended)**

Edit your `~/.bashrc` or `~/.zshrc`:
```bash
echo "export SMARTY_AUTH_ID='your_auth_id_here'" >> ~/.bashrc
echo "export SMARTY_AUTH_TOKEN='your_auth_token_here'" >> ~/.bashrc
source ~/.bashrc
```

Replace `your_auth_id_here` and `your_auth_token_here` with your actual credentials.

### Step 4: Verify Setup

```bash
echo $SMARTY_AUTH_ID
echo $SMARTY_AUTH_TOKEN
```

Both should display your credentials (not empty).

---

## Run Address Validation

### Dry-Run (Preview Only)

```bash
python3 scripts/validate_google_addresses_smarty.py
```

This will:
- Show which addresses will be validated
- Display validation results (valid/invalid)
- **NOT make any database changes**
- Help you verify everything works

### Live Validation (Update Database)

```bash
python3 scripts/validate_google_addresses_smarty.py --live
```

This will:
- Validate all 69 Google Contacts addresses
- Update database with validation results
- Add geocoding (lat/long), county, DPV codes
- Mark addresses as validated
- Flag vacant/invalid addresses

---

## What Gets Validated

**Priority 1: Google Contacts Addresses (69 contacts)**
- All addresses imported from `google_contacts` source
- Not yet validated (billing_usps_validated_at IS NULL)

**Results Include:**
- ✅ **Deliverability status** (DPV match code)
- ✅ **Standardized address** (USPS format)
- ✅ **Geocoding** (latitude/longitude)
- ✅ **County name**
- ✅ **Residential vs Commercial** (RDI)
- ✅ **Vacant flag**
- ✅ **Active/inactive status**

---

## Cost Breakdown

| Addresses | Free Tier | Paid Cost |
|-----------|-----------|-----------|
| **69 (Google)** | ✅ FREE | $0.48 - $1.04 |
| **100** | ✅ FREE | $0.70 - $1.50 |
| **250** | ✅ FREE | $1.75 - $3.75 |
| **500** | ❌ PAID | $3.50 - $7.50 |

**Current need:** 69 addresses = **100% FREE** (well within 250/month limit)

---

## Validation Output

### Database Fields Updated

```sql
billing_usps_validated_at       -- Timestamp of validation
billing_usps_dpv_match_code     -- Y/S/D/N (deliverability)
billing_usps_precision          -- Zip9, Zip8, Rooftop, etc.
billing_usps_delivery_line_1    -- Standardized street address
billing_usps_delivery_line_2    -- Apt/suite (if applicable)
billing_usps_last_line          -- City, State ZIP
billing_usps_latitude           -- Geocoded latitude
billing_usps_longitude          -- Geocoded longitude
billing_usps_county             -- County name
billing_usps_rdi                -- Residential/Commercial
billing_usps_footnotes          -- DPV footnotes (technical details)
billing_usps_vacant             -- true/false
billing_usps_active             -- true/false
```

### DPV Match Codes

| Code | Meaning | Action |
|------|---------|--------|
| **Y** | Full match | ✅ Address is valid and deliverable |
| **S** | Missing secondary (apt/suite) | ⚠️ Valid but incomplete |
| **D** | Missing primary and secondary | ⚠️ Partial match only |
| **N** | No match | ❌ Invalid address |

---

## Troubleshooting

### "Authentication failed"
- Double-check Auth ID and Auth Token
- Verify no extra spaces or quotes
- Re-export environment variables

### "Payment required"
- You've exceeded 250 lookups this month
- Either wait for next month (free tier resets)
- Or add payment method to account

### "No match found"
- Address is invalid/not in USPS database
- Check original address data
- May need manual correction

### "Rate limit exceeded"
- Script already has conservative rate limiting (5/sec)
- SmartyStreets allows up to 250/sec
- Shouldn't happen with 69 addresses

---

## Next Steps After Validation

1. **Review results:**
   ```sql
   SELECT email, address_line_1, city, state,
          billing_usps_dpv_match_code,
          billing_usps_vacant
   FROM contacts
   WHERE billing_address_source = 'google_contacts'
   ORDER BY billing_usps_dpv_match_code;
   ```

2. **Flag invalid addresses:**
   - DPV code 'N' = needs correction
   - Vacant = true = undeliverable
   - Manual review may be needed

3. **Update mailing list:**
   - Use validated addresses for campaigns
   - Exclude vacant/invalid addresses
   - Improve delivery success rate

4. **Optional: Validate more addresses**
   - You have ~180 free lookups left (250 - 69)
   - Can validate other billing addresses
   - Just modify the script query

---

## Alternative: USPS Web Tools (Free, No Limit)

If you prefer not to use SmartyStreets:

```bash
python3 scripts/validate_addresses_usps.py
```

**Pros:**
- Completely free (unlimited)
- Official USPS data

**Cons:**
- Requires separate USPS registration
- Slower (rate limited to 5/sec)
- Less detailed data (no geocoding)
- More complex setup

---

## Support

**SmartyStreets Documentation:**
- API Docs: https://www.smarty.com/docs/cloud/us-street-api
- Support: https://www.smarty.com/support

**Script Location:**
- `scripts/validate_google_addresses_smarty.py`
- `scripts/validate_addresses_smarty.py` (general purpose)
- `scripts/validate_addresses_usps.py` (alternative)

**Questions?**
- Check script output for detailed error messages
- Review this guide for common issues
- SmartyStreets has excellent customer support

---

**Ready to validate?** Set up your credentials and run the dry-run command!
