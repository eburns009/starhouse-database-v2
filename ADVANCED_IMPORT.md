# 🚀 ADVANCED IMPORT OPTIONS - Faster Bulk Loads

## 📊 Import Method Comparison

| Method | Speed | Best For | Limitations |
|--------|-------|----------|-------------|
| **Supabase UI** | Slow (10-15 min) | Small datasets (<1000 rows) | Browser timeouts, manual |
| **SQL COPY** | Fast (30 sec) | Medium datasets (1k-100k) | Requires file upload |
| **Supabase CLI** | Fastest (10 sec) | Large datasets (100k+) | Requires CLI install |

---

## 🔥 **Method 1: SQL COPY (Recommended for V2)**

**Pros:** 10-20x faster than UI, reliable, no browser timeouts  
**Cons:** Requires uploading CSVs to server

### Steps:

**1. Upload CSVs to Supabase Storage (if available)**
```bash
# Via Supabase Dashboard:
# Storage → Create bucket "imports" → Upload all v2_*.csv files
```

**2. Run COPY commands via SQL Editor**
```sql
-- Import contacts (fastest!)
COPY contacts (
  id, email, first_name, last_name, phone,
  address_line_1, address_line_2, city, state, postal_code, country,
  email_subscribed, source_system, kajabi_id, kajabi_member_id,
  ticket_tailor_id, zoho_id, quickbooks_id, mailchimp_id, notes,
  created_at, updated_at
)
FROM '/path/to/v2_contacts.csv'
WITH (FORMAT CSV, HEADER true, ENCODING 'UTF-8', NULL '');

-- Repeat for all 7 tables...
```

**3. Analyze for query optimization**
```sql
ANALYZE;
```

**Estimated Time:** 
- UI Import: 30-45 minutes
- COPY: 2-5 minutes ⚡
- **10x faster!**

---

## 🔧 **Method 2: Supabase CLI (Fastest)**

**Pros:** Fastest method, scriptable, reliable  
**Cons:** Requires local CLI installation

### Setup:

```bash
# Install Supabase CLI
npm install -g supabase

# Or via Homebrew
brew install supabase/tap/supabase

# Link to project
supabase link --project-ref lnagadkqejnopgfxwlkb
```

### Import via CLI:

```bash
# Method A: Direct SQL execution
supabase db execute < /path/to/import_script.sql

# Method B: Use psql directly
psql postgresql://postgres:***REMOVED***@***REMOVED***:5432/postgres \
  -c "\COPY contacts FROM '/path/to/v2_contacts.csv' CSV HEADER"

# Method C: Bulk script (import all 7 files)
./bulk_import.sh
```

**Estimated Time:** 30 seconds - 2 minutes ⚡⚡

---

## 📝 **Method 3: Idempotent Staging Pattern**

**Use Case:** Re-running imports, incremental updates, avoiding duplicates

```sql
-- 1. Create staging table
CREATE TEMP TABLE staging_contacts AS 
SELECT * FROM contacts WHERE false;

-- 2. Load into staging
COPY staging_contacts FROM '/path/to/v2_contacts.csv' 
WITH (FORMAT CSV, HEADER true, ENCODING 'UTF-8', NULL '');

-- 3. Upsert with conflict handling
INSERT INTO contacts 
SELECT * FROM staging_contacts
ON CONFLICT (email) DO UPDATE SET
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name,
  phone = COALESCE(EXCLUDED.phone, contacts.phone),  -- Keep existing if new is NULL
  address_line_1 = EXCLUDED.address_line_1,
  updated_at = now()
WHERE 
  -- Only update if something actually changed
  contacts.first_name IS DISTINCT FROM EXCLUDED.first_name
  OR contacts.last_name IS DISTINCT FROM EXCLUDED.last_name;

-- 4. Clean up
DROP TABLE staging_contacts;

-- 5. Analyze
ANALYZE contacts;
```

**Benefits:**
- ✅ Safe to re-run (idempotent)
- ✅ Handles updates to existing records
- ✅ Can merge new data without deleting old
- ✅ Preserves non-NULL values

---

## 📋 **Complete Bulk Import Script**

Save as `bulk_import.sh`:

```bash
#!/bin/bash
# Bulk import script for StarHouse V2

DB_URL="postgresql://postgres:***REMOVED***@***REMOVED***:5432/postgres"
DATA_DIR="/path/to/outputs"

echo "🚀 Starting bulk import..."

# Import in correct order
psql $DB_URL -c "\COPY contacts FROM '${DATA_DIR}/v2_contacts.csv' CSV HEADER"
echo "✅ Contacts imported"

psql $DB_URL -c "\COPY tags FROM '${DATA_DIR}/v2_tags.csv' CSV HEADER"
echo "✅ Tags imported"

psql $DB_URL -c "\COPY products FROM '${DATA_DIR}/v2_products.csv' CSV HEADER"
echo "✅ Products imported"

psql $DB_URL -c "\COPY contact_tags FROM '${DATA_DIR}/v2_contact_tags.csv' CSV HEADER"
echo "✅ Contact-tags imported"

psql $DB_URL -c "\COPY contact_products FROM '${DATA_DIR}/v2_contact_products.csv' CSV HEADER"
echo "✅ Contact-products imported"

psql $DB_URL -c "\COPY subscriptions FROM '${DATA_DIR}/v2_subscriptions.csv' CSV HEADER"
echo "✅ Subscriptions imported"

psql $DB_URL -c "\COPY transactions FROM '${DATA_DIR}/v2_transactions.csv' CSV HEADER"
echo "✅ Transactions imported"

# Analyze for performance
psql $DB_URL -c "ANALYZE;"
echo "✅ Database analyzed"

echo "🎉 Import complete!"
```

Make executable and run:
```bash
chmod +x bulk_import.sh
./bulk_import.sh
```

---

## 🔍 **CSV Encoding Verification**

**Critical:** Ensure CSVs are UTF-8 encoded with Unix line endings

```bash
# Check encoding
file v2_contacts.csv
# Should show: "UTF-8 Unicode text"

# Convert if needed (macOS/Linux)
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv

# Check line endings
dos2unix v2_*.csv  # Convert Windows CRLF to Unix LF

# Verify NULL handling
# Empty strings in CSV should be properly interpreted as NULL
head -5 v2_contacts.csv | cat -A
# Look for commas with nothing between: ,,
```

---

## ⚡ **Performance Tips**

### Before Import:
```sql
-- Temporarily disable triggers for faster bulk load
ALTER TABLE contacts DISABLE TRIGGER ALL;
ALTER TABLE tags DISABLE TRIGGER ALL;
-- ... repeat for all tables

-- Import data here (3-5x faster)

-- Re-enable triggers
ALTER TABLE contacts ENABLE TRIGGER ALL;
ALTER TABLE tags ENABLE TRIGGER ALL;
-- ... repeat for all tables
```

### After Import:
```sql
-- Update table statistics (CRITICAL for query performance)
ANALYZE;

-- Or analyze specific tables
ANALYZE contacts;
ANALYZE transactions;

-- Verify index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
-- If idx_scan = 0, index is unused (might be unnecessary)
```

---

## 🚨 **Common Issues**

### "COPY command not supported"
**Solution:** UI doesn't support COPY. Use CLI or psql.

### "permission denied for COPY"
**Solution:** Use `\COPY` (client-side) instead of `COPY` (server-side):
```bash
psql $DB_URL -c "\COPY contacts FROM 'v2_contacts.csv' CSV HEADER"
```

### "extra data after last expected column"
**Solution:** CSV has more columns than table. Check column count:
```bash
head -1 v2_contacts.csv | tr ',' '\n' | wc -l
```

### "invalid input syntax for type uuid"
**Solution:** Using old V1 files. Ensure using v2_*.csv files with UUIDs.

---

## 📊 **Recommended Import Path**

For StarHouse V2 (~20,000 total rows):

1. **Use Supabase UI for sample files** (testing) ✅
2. **Use CLI/COPY for production files** (fastest) ⚡

**Total time comparison:**
- UI: 30-45 minutes
- CLI: 1-2 minutes
- **Savings: ~40 minutes!**

---

## ✅ **Validation After Import**

```sql
-- Row counts
SELECT 
  'contacts' as table, COUNT(*) as rows FROM contacts
UNION ALL SELECT 'tags', COUNT(*) FROM tags
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'contact_tags', COUNT(*) FROM contact_tags
UNION ALL SELECT 'contact_products', COUNT(*) FROM contact_products
UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL SELECT 'transactions', COUNT(*) FROM transactions;

-- Check for orphans
SELECT 'orphaned contact_tags' as issue, COUNT(*) 
FROM contact_tags ct 
LEFT JOIN contacts c ON ct.contact_id = c.id 
WHERE c.id IS NULL
UNION ALL
SELECT 'orphaned subscriptions', COUNT(*) 
FROM subscriptions s 
LEFT JOIN contacts c ON s.contact_id = c.id 
WHERE c.id IS NULL;
-- Both should return 0

-- Verify table statistics were updated
SELECT schemaname, tablename, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY tablename;
-- last_analyze should be recent
```

---

**Ready for fast bulk import! Use CLI method for 20x speedup.** ⚡
