# Data Import Files - Folder Structure

This folder contains all import files for weekly data synchronization.

## Folder Structure

```
data/
├── current/          ← PUT THIS WEEK'S FILES HERE
│   ├── kajabi_contacts_2025_11_08.csv
│   ├── kajabi_subscriptions_2025_11_08.csv
│   ├── kajabi_sales_2025_11_08.csv
│   └── paypal_export_2025_11_08.txt
│
├── samples/          ← PUT SAMPLE FILES HERE (for testing/development)
│   ├── kajabi_contacts_sample.csv
│   ├── kajabi_subscriptions_sample.csv
│   ├── kajabi_sales_sample.csv
│   └── paypal_export_sample.txt
│
├── archive/          ← MOVE PROCESSED FILES HERE (after successful import)
│   ├── 2025-11-01/
│   ├── 2025-11-08/
│   └── 2025-11-15/
│
└── templates/        ← DOCUMENTATION AND EXAMPLES
    └── column_mapping.md

## Usage

### For Weekly Imports

1. **Export files from Kajabi and PayPal** (follow WEEKLY_IMPORT_GUIDE.md)

2. **Save to `current/` folder:**
   ```
   data/current/kajabi_contacts_2025_11_08.csv
   data/current/kajabi_subscriptions_2025_11_08.csv
   data/current/kajabi_sales_2025_11_08.csv
   data/current/paypal_export_2025_11_08.txt
   ```

3. **Run import:**
   ```bash
   python3 scripts/weekly_import_all.py \
     --kajabi-contacts data/current/kajabi_contacts_2025_11_08.csv \
     --kajabi-subscriptions data/current/kajabi_subscriptions_2025_11_08.csv \
     --kajabi-sales data/current/kajabi_sales_2025_11_08.csv \
     --paypal data/current/paypal_export_2025_11_08.txt \
     --dry-run
   ```

4. **After successful import, archive:**
   ```bash
   mkdir -p data/archive/2025-11-08
   mv data/current/*.csv data/current/*.txt data/archive/2025-11-08/
   ```

### For Development/Testing

**Put sample files in `samples/` folder:**
```
data/samples/kajabi_contacts_sample.csv
data/samples/kajabi_subscriptions_sample.csv
data/samples/kajabi_sales_sample.csv
data/samples/paypal_export_sample.txt
```

**Run with sample files:**
```bash
python3 scripts/weekly_import_all.py \
  --kajabi-contacts data/samples/kajabi_contacts_sample.csv \
  --kajabi-subscriptions data/samples/kajabi_subscriptions_sample.csv \
  --kajabi-sales data/samples/kajabi_sales_sample.csv \
  --paypal data/samples/paypal_export_sample.txt \
  --dry-run
```

## File Naming Convention

Always use date-stamped filenames:

```
kajabi_contacts_YYYY_MM_DD.csv
kajabi_subscriptions_YYYY_MM_DD.csv
kajabi_sales_YYYY_MM_DD.csv
paypal_export_YYYY_MM_DD.txt
```

Examples:
```
kajabi_contacts_2025_11_08.csv
kajabi_subscriptions_2025_11_08.csv
kajabi_sales_2025_11_08.csv
paypal_export_2025_11_08.txt
```

## Archive Organization

After processing, archive by date:

```
data/archive/
├── 2025-11-01/
│   ├── kajabi_contacts_2025_11_01.csv
│   ├── kajabi_subscriptions_2025_11_01.csv
│   ├── kajabi_sales_2025_11_01.csv
│   └── paypal_export_2025_11_01.txt
│
├── 2025-11-08/
│   ├── kajabi_contacts_2025_11_08.csv
│   ├── kajabi_subscriptions_2025_11_08.csv
│   ├── kajabi_sales_2025_11_08.csv
│   └── paypal_export_2025_11_08.txt
│
└── 2025-11-15/
    └── ...
```

**Retention:** Keep archived files for 90 days minimum (for auditing/troubleshooting).

## .gitignore

The following files are ignored by git (too large, contain sensitive data):
- `data/current/*.csv`
- `data/current/*.txt`
- `data/archive/**/*`

Sample files in `data/samples/` should be sanitized (fake/test data only).

## Quick Commands

```bash
# Create this week's folder
mkdir -p data/current

# Check files are ready
ls -lh data/current/

# Archive after successful import
mkdir -p data/archive/$(date +%Y-%m-%d)
mv data/current/* data/archive/$(date +%Y-%m-%d)/

# Clean up old archives (older than 90 days)
find data/archive/ -type d -mtime +90 -exec rm -rf {} \;
```

## Need Help?

See:
- **WEEKLY_IMPORT_GUIDE.md** - Complete import instructions
- **WEEKLY_IMPORT_QUICK_REFERENCE.md** - Quick reference card
- **IMPORT_SCRIPTS_SUMMARY.md** - Technical documentation
