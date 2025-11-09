# Weekly Data Import Guide

**Last Updated:** 2025-11-08
**Process:** Manual weekly data import from Kajabi and PayPal
**Time Required:** 15-20 minutes
**Frequency:** Weekly (recommended: Monday mornings)

---

## Quick Start

```bash
# 1. Export data from Kajabi and PayPal (see below)

# 2. Run dry-run to preview changes
python3 scripts/weekly_import_all.py --dry-run

# 3. If dry-run looks good, execute
python3 scripts/weekly_import_all.py --execute
```

---

## Overview

Since webhooks are disabled, we manually import data weekly to keep the database synchronized with Kajabi and PayPal.

### What Gets Imported

| Source | Data Imported | Updates |
|--------|---------------|---------|
| **Kajabi** | New subscriptions, contacts, offers/products | Subscription status changes, contact enrichment |
| **PayPal** | Transactions, contact info, addresses, phone numbers | Contact enrichment with PayPal data |

### Import Order

The imports run in this order:
1. **Kajabi first** - Creates subscriptions and base contact records
2. **PayPal second** - Enriches contacts with transactions and addresses

---

## Part 1: Export Files from Each System

### 📘 Kajabi Export

**What to Export:** Subscriptions list
**File Name:** `data/kajabi_subscriptions_YYYY_MM_DD.csv`
**Format:** CSV

#### Step-by-Step Export Instructions

1. **Log into Kajabi**
   - Go to https://app.kajabi.com
   - Enter your Kajabi admin credentials

2. **Navigate to Subscriptions**
   - Click on **"People"** in the left sidebar
   - Click on **"Subscriptions"**

3. **Export Subscriptions**
   - Click **"Export"** button (top right)
   - Select **"Export All Subscriptions"**
   - Format: **CSV**
   - **Important:** Include ALL columns (don't customize)

4. **Download and Save**
   - Download the CSV file
   - Rename it to: `kajabi_subscriptions_YYYY_MM_DD.csv`
     - Example: `kajabi_subscriptions_2025_11_08.csv`
   - Save to: `starhouse-database-v2/data/`

5. **Verify File Contents**
   - Open the CSV and check for these columns:
     ```
     Kajabi Subscription ID
     Customer Email
     Customer Name
     Customer ID
     Offer ID
     Offer Title
     Amount
     Currency
     Interval
     Status
     Created At
     Next Payment Date
     Canceled On
     Trial Ends On
     Provider
     Coupon Used
     ```

#### Expected Output

- **File size:** 50-100 KB (for ~400 subscriptions)
- **Row count:** One row per subscription
- **Active subscriptions:** Should match Kajabi dashboard count

---

### 💰 PayPal Export

**What to Export:** Activity/Transactions
**File Name:** `data/paypal_export_YYYY_MM_DD.txt`
**Format:** Tab-delimited text (.txt or .tsv)

#### Step-by-Step Export Instructions

1. **Log into PayPal Business**
   - Go to https://www.paypal.com/businessmanage
   - Enter your PayPal Business credentials

2. **Navigate to Activity**
   - Click **"Activity"** in the top menu
   - Click **"Statements"** (left sidebar)

3. **Create Custom Statement**
   - Click **"Activity download"** or **"Custom"**
   - Select date range:
     - **For first-time import:** Last 90 days
     - **For weekly imports:** Last 7-14 days
     - **Important:** Use date range slightly overlapping previous week to catch late updates

4. **Configure Export Settings**
   - Format: **"Tab delimited"** or **"Comma delimited"**
   - Data type: **"All activity"** (or "All transactions")
   - Include: **All available columns**

5. **Download and Save**
   - Click **"Create Report"** or **"Download"**
   - Wait for file to generate (may take a minute)
   - Download the .txt or .csv file
   - Rename to: `paypal_export_YYYY_MM_DD.txt`
     - Example: `paypal_export_2025_11_08.txt`
   - Save to: `starhouse-database-v2/data/`

6. **Verify File Contents**
   - File should be **tab-delimited** (columns separated by tabs)
   - Check for these columns:
     ```
     Date
     Time
     Transaction ID
     From Email Address
     Name
     Type
     Status
     Currency
     Gross
     Fee
     Net
     Contact Phone Number
     Address Line 1
     Town/City
     State/Province/Region/County/Territory/Prefecture/Republic
     Zip/Postal Code
     Country
     Item Title
     Invoice Number
     Receipt ID
     Reference Txn ID
     ```

#### Expected Output

- **File size:** Varies (100 KB - 5 MB depending on volume)
- **Row count:** One row per transaction
- **Transaction types:** Subscription Payment, Payment, Refund, etc.

---

## Part 2: Run the Import

### Prerequisites

- [ ] Kajabi CSV file exported and saved
- [ ] PayPal TXT file exported and saved
- [ ] Connected to database
- [ ] Python 3 installed with required packages

### Step 1: Dry-Run (Preview Changes)

**Always run dry-run first** to preview what will be imported.

```bash
# Navigate to project directory
cd /workspaces/starhouse-database-v2

# Run dry-run with default file locations
python3 scripts/weekly_import_all.py --dry-run

# OR with custom file paths
python3 scripts/weekly_import_all.py \
  --kajabi data/kajabi_subscriptions_2025_11_08.csv \
  --paypal data/paypal_export_2025_11_08.txt \
  --dry-run
```

**What to Look For:**
- ✅ Number of new subscriptions
- ✅ Number of new contacts
- ✅ Number of new transactions
- ✅ Number of contacts enriched
- ❌ Error count (should be 0 or very low)

**Sample Output:**
```
================================================================================
  WEEKLY DATA IMPORT - DRY RUN MODE
================================================================================

Started: 2025-11-08 10:00:00
Mode: DRY RUN

⚠️  DRY RUN MODE - No changes will be saved

================================================================================
  PRE-FLIGHT: Checking Files
================================================================================

✅ Kajabi subscriptions file found: data/kajabi_subscriptions.csv (51,234 bytes)
✅ PayPal transactions file found: data/paypal_export.txt (234,567 bytes)

✅ All files present

================================================================================
  STEP 1: Importing Kajabi Subscriptions
================================================================================

...

📋 Subscriptions:
  Processed: 421
  New: 15
  Updated: 8
  Skipped: 398

📇 Contacts:
  Created: 12
  Updated: 3

...

================================================================================
  STEP 2: Importing PayPal Transactions
================================================================================

...

💰 Transactions:
  New: 45
  Skipped (duplicates): 12

📇 Contacts:
  Matched existing: 42
  Created new: 3
  Enriched: 38

...

================================================================================
  IMPORT COMPLETE
================================================================================

Results:
  ✅ KAJABI: SUCCESS
  ✅ PAYPAL: SUCCESS

Finished: 2025-11-08 10:05:23

🔄 DRY RUN COMPLETE - No changes were saved
Run with --execute to apply changes
```

### Step 2: Review Dry-Run Results

**Check:**
1. **New subscription count** - Does it make sense?
   - Expect 5-20 new subscriptions per week
   - If 0: Maybe no new subscriptions this week (OK)
   - If 100+: Check date range - might be including old data

2. **New contact count** - Does it make sense?
   - Expect 3-15 new contacts per week
   - Should be <= new subscriptions count

3. **New transaction count** - Does it make sense?
   - Expect 20-60 transactions per week
   - Includes: payments, refunds, subscription renewals

4. **Error count** - Should be 0 or very few
   - A few errors OK (invalid emails, malformed data)
   - 10+ errors: Check file format

**If Something Looks Wrong:**
- Check file date ranges
- Check file formats
- Run individual imports with `--dry-run`:
  ```bash
  python3 scripts/weekly_import_kajabi.py --dry-run
  python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --dry-run
  ```

### Step 3: Execute Import

Once dry-run looks good:

```bash
# Execute with default files
python3 scripts/weekly_import_all.py --execute

# OR with custom file paths
python3 scripts/weekly_import_all.py \
  --kajabi data/kajabi_subscriptions_2025_11_08.csv \
  --paypal data/paypal_export_2025_11_08.txt \
  --execute
```

**Expected Duration:** 2-5 minutes

**Watch For:**
- ✅ "Changes committed to database" messages
- ✅ SUCCESS status for each import
- ❌ Any FAILED statuses (investigate errors)

---

## Part 3: Verify Import

After import completes, verify data was imported correctly.

### Quick Database Checks

```bash
# Check recent subscriptions
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -c "SELECT COUNT(*), status FROM subscriptions WHERE updated_at > NOW() - INTERVAL '1 hour' GROUP BY status;"

# Check recent transactions
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -c "SELECT COUNT(*), source_system FROM transactions WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY source_system;"

# Check recent contacts
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -c "SELECT COUNT(*) FROM contacts WHERE created_at > NOW() - INTERVAL '1 hour';"
```

### Spot Check

Pick 2-3 random contacts from the import and verify:
1. Their subscription shows in database
2. Their transactions are recorded
3. Contact info looks correct

---

## Troubleshooting

### Problem: "File not found"

**Cause:** File not in expected location or wrong filename

**Fix:**
```bash
# Check files exist
ls -lh data/kajabi_subscriptions*.csv
ls -lh data/paypal_export*.txt

# Use --kajabi and --paypal flags to specify exact paths
python3 scripts/weekly_import_all.py \
  --kajabi data/your_actual_file.csv \
  --paypal data/your_actual_file.txt \
  --dry-run
```

### Problem: "Invalid email format" errors

**Cause:** Some contacts have malformed emails in source system

**Fix:**
- A few errors (<5) are normal - skip them
- Many errors: Check source file, may be corrupted
- Import will skip invalid rows and continue

### Problem: "Duplicate key violation"

**Cause:** Trying to import data that already exists

**Fix:**
- This is normal! Import scripts use `ON CONFLICT DO NOTHING`
- Data will be skipped, no errors
- Check "Skipped" count in output

### Problem: "Connection refused" or database errors

**Cause:** Database connection issue

**Fix:**
```bash
# Test database connection
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -c "SELECT NOW();"

# If connection fails, check:
# - VPN connected (if required)
# - Credentials correct
# - Database accessible
```

### Problem: Dry-run shows 0 new records

**Possible Causes:**
1. **No new data** - Completely normal if quiet week
2. **Already imported** - Data from this time period already in database
3. **Wrong date range** - Export date range doesn't include new data

**Fix:**
- Check last import date
- Verify export date ranges cover period since last import
- OK to re-run, duplicate detection will skip existing data

### Problem: Script crashes or hangs

**Fix:**
1. **Check file size** - Very large files (>50MB) may take longer
   ```bash
   ls -lh data/paypal_export.txt
   ```

2. **Run individual imports** to isolate issue:
   ```bash
   python3 scripts/weekly_import_kajabi.py --dry-run
   python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --dry-run
   ```

3. **Check Python dependencies:**
   ```bash
   pip3 install psycopg2-binary
   ```

---

## Advanced Usage

### Import Only One Source

```bash
# Kajabi only
python3 scripts/weekly_import_all.py --skip-paypal --execute

# PayPal only
python3 scripts/weekly_import_all.py --skip-kajabi --execute
```

### Run Individual Scripts

```bash
# Kajabi only
python3 scripts/weekly_import_kajabi.py --execute

# PayPal only
python3 scripts/weekly_import_paypal.py --file data/paypal_export.txt --execute
```

### Custom Date Ranges

For PayPal, export with specific date range:
- Last 7 days: Weekly imports
- Last 30 days: Monthly reconciliation
- Last 90 days: Quarterly audit
- Custom range: For backfilling missing data

---

## Best Practices

### 1. Weekly Schedule

**Recommended:** Monday mornings (10 AM)
- Captures weekend activity
- Fresh start to the week
- Time to investigate any issues

### 2. File Naming Convention

Always use date-stamped filenames:
```
kajabi_subscriptions_2025_11_08.csv
paypal_export_2025_11_08.txt
```

Benefits:
- Easy to track which files have been processed
- Can re-run previous imports if needed
- Clear audit trail

### 3. Keep Export Files

Don't delete export files after import:
- Move to `data/archive/` folder
- Keep for 90 days minimum
- Useful for troubleshooting or audits

```bash
# Archive processed files
mkdir -p data/archive
mv data/kajabi_subscriptions_2025_11_08.csv data/archive/
mv data/paypal_export_2025_11_08.txt data/archive/
```

### 4. Always Dry-Run First

**Never skip dry-run!**
- Preview changes before committing
- Catch issues early
- Understand what will be imported

### 5. Overlapping Date Ranges

For PayPal exports, use slightly overlapping date ranges:
- Week 1: Nov 1-7
- Week 2: Nov 6-13 (2 days overlap)
- Week 3: Nov 12-19 (2 days overlap)

Benefits:
- Catches late-posted transactions
- Duplicate detection prevents double-import
- Ensures no data gaps

---

## File Format Reference

### Kajabi CSV Format

**Encoding:** UTF-8
**Delimiter:** Comma (,)
**Headers:** First row
**Date Format:** `Nov 28, 2025`
**Amount Format:** `$242.00`

**Required Columns:**
- Kajabi Subscription ID
- Customer Email
- Customer Name
- Offer ID
- Offer Title
- Amount
- Status

### PayPal TXT Format

**Encoding:** UTF-8
**Delimiter:** Tab (\t)
**Headers:** First row
**Date Format:** `MM/DD/YYYY`
**Time Format:** `HH:MM:SS`
**Amount Format:** `123.45` (no symbols)

**Required Columns:**
- Transaction ID
- From Email Address
- Name
- Type
- Status
- Gross
- Currency

---

## Checklist: Weekly Import

Use this checklist every week:

### Monday Morning Import

- [ ] **Export Kajabi subscriptions**
  - [ ] All subscriptions export
  - [ ] Save as `kajabi_subscriptions_YYYY_MM_DD.csv`
  - [ ] File in `data/` directory

- [ ] **Export PayPal transactions**
  - [ ] Last 7-14 days
  - [ ] Tab-delimited format
  - [ ] Save as `paypal_export_YYYY_MM_DD.txt`
  - [ ] File in `data/` directory

- [ ] **Run dry-run**
  - [ ] `python3 scripts/weekly_import_all.py --dry-run`
  - [ ] Review counts (subscriptions, contacts, transactions)
  - [ ] Check error count (should be low)

- [ ] **Execute import**
  - [ ] `python3 scripts/weekly_import_all.py --execute`
  - [ ] Wait for completion (2-5 minutes)
  - [ ] Verify SUCCESS messages

- [ ] **Spot check database**
  - [ ] Check 2-3 new subscriptions
  - [ ] Verify transactions imported
  - [ ] Confirm contact data looks correct

- [ ] **Archive files**
  - [ ] Move CSVs to `data/archive/`
  - [ ] Note import completion in log/notes

---

## Getting Help

### Quick Reference

| Issue | Solution |
|-------|----------|
| File not found | Check filename and path with `ls data/` |
| Database connection failed | Test with `psql -c "SELECT NOW();"` |
| Import has errors | Check error messages, usually safe to continue |
| Duplicate data warnings | Normal! Scripts skip duplicates automatically |
| Slow import | Large files take longer, check file size with `ls -lh` |

### Contact

For technical issues or questions:
- Check this guide first
- Review error messages
- Check logs in terminal output

---

**Last Updated:** 2025-11-08
**Version:** 2.0 (Optimized for weekly manual imports)
