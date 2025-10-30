# 🚀 STARHOUSE DATABASE V2 - FAANG-GRADE DEPLOYMENT

## ✅ Production-Ready Architecture

**All reviewer suggestions implemented:**
- ✅ UUID-based foreign keys (not email)
- ✅ Case-insensitive emails (citext)
- ✅ DB-level enums (subscription_status, payment_status, transaction_type)
- ✅ Unique constraints on junction tables
- ✅ Money as numeric(12,2) with currency
- ✅ Dates as timestamptz (not text)
- ✅ Source provenance tracking
- ✅ Auto-updating updated_at triggers
- ✅ Email format validation (CHECK constraint)
- ✅ Comprehensive indexes
- ✅ Data validation & sanitization

---

## 📁 Files Overview

### Schema
- **`starhouse_schema_v2.sql`** - Production database schema (FAANG-grade)

### Data Files (Production)
1. `v2_contacts.csv` - 5,620 contacts with UUID primary keys
2. `v2_tags.csv` - 97 tags with UUIDs
3. `v2_products.csv` - 26 products with UUIDs
4. `v2_contact_tags.csv` - 8,795 relationships (UUID FKs)
5. `v2_contact_products.csv` - 1,352 relationships (UUID FKs)
6. `v2_subscriptions.csv` - 263 subscriptions (UUID FKs)
7. `v2_transactions.csv` - 4,370 transactions (UUID FKs)

### Sample Files (10 rows each - Test First!)
- `v2_contacts_sample.csv`
- `v2_tags_sample.csv`
- `v2_products_sample.csv`
- `v2_contact_tags_sample.csv`
- `v2_contact_products_sample.csv`
- `v2_subscriptions_sample.csv`
- `v2_transactions_sample.csv`

---

## 🎯 Deployment Steps

### PHASE 1: Apply Schema (5 minutes)

**1.1 - Drop Old Schema (if exists)**
```sql
-- ⚠️ DANGER: This deletes ALL data!
-- Only run if you're starting fresh
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

**1.2 - Apply New Schema**

Via Supabase SQL Editor:
1. Go to: https://supabase.com/dashboard/project/lnagadkqejnopgfxwlkb/sql/new
2. Copy entire contents of `starhouse_schema_v2.sql`
3. Click "Run"
4. Verify success (should see "Success. No rows returned")

**1.3 - Verify Schema**
```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Expected output:
-- contact_products
-- contact_tags
-- contacts
-- products
-- subscriptions
-- tags
-- transactions

-- Check enums exist
SELECT typname 
FROM pg_type 
WHERE typtype = 'e';

-- Expected output:
-- payment_status
-- subscription_status
-- transaction_type

-- Check extensions
SELECT * FROM pg_extension;

-- Should include:
-- citext
-- uuid-ossp
```

---

### PHASE 2: Test Import (Sample Files - 15 minutes)

**Import in this exact order:**

```
1. v2_contacts_sample.csv        → contacts table (10 rows)
2. v2_tags_sample.csv            → tags table (10 rows)
3. v2_products_sample.csv        → products table (10 rows)
4. v2_contact_tags_sample.csv    → contact_tags table (10 rows)
5. v2_contact_products_sample.csv → contact_products table (10 rows)
6. v2_subscriptions_sample.csv   → subscriptions table (10 rows)
7. v2_transactions_sample.csv    → transactions table (10 rows)
```

**For Each File:**
1. Go to Table Editor: https://supabase.com/dashboard/project/lnagadkqejnopgfxwlkb/editor
2. Click the target table name
3. Click "Insert" → "Import data via spreadsheet"
4. Upload the sample CSV
5. **Verify column mapping** (should auto-detect)
6. Click "Import data"
7. **Verify row count**: `SELECT COUNT(*) FROM [table_name];`

**Test Validation Queries:**
```sql
-- All contacts have valid emails
SELECT email FROM contacts WHERE email !~* '^[^@\s]+@[^@\s]+\.[^@\s]+$';
-- Should return 0 rows

-- All contact_tags reference valid contacts
SELECT COUNT(*) 
FROM contact_tags ct 
LEFT JOIN contacts c ON ct.contact_id = c.id 
WHERE c.id IS NULL;
-- Should return 0

-- All subscriptions reference valid contacts
SELECT COUNT(*) 
FROM subscriptions s 
LEFT JOIN contacts c ON s.contact_id = c.id 
WHERE c.id IS NULL;
-- Should return 0

-- Check enum values
SELECT DISTINCT status FROM subscriptions;
-- Should only show: active, canceled

SELECT DISTINCT status FROM transactions;
-- Should only show: completed, failed, pending

SELECT DISTINCT transaction_type FROM transactions;
-- Should only show: purchase, subscription, refund

-- Verify UUID format
SELECT id FROM contacts WHERE id::text !~ '^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$';
-- Should return 0 rows
```

**✅ If all validations pass → Proceed to Phase 3**  
**❌ If any fail → Debug before continuing**

---

### PHASE 3: Production Import (30 minutes)

**3.1 - Clear Test Data**
```sql
-- Disable FK checks temporarily for faster deletion
SET session_replication_role = replica;

TRUNCATE TABLE transactions CASCADE;
TRUNCATE TABLE subscriptions CASCADE;
TRUNCATE TABLE contact_products CASCADE;
TRUNCATE TABLE contact_tags CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE tags CASCADE;
TRUNCATE TABLE contacts CASCADE;

-- Re-enable FK checks
SET session_replication_role = DEFAULT;

-- Verify all empty
SELECT 
  (SELECT COUNT(*) FROM contacts) as contacts,
  (SELECT COUNT(*) FROM tags) as tags,
  (SELECT COUNT(*) FROM products) as products,
  (SELECT COUNT(*) FROM contact_tags) as contact_tags,
  (SELECT COUNT(*) FROM contact_products) as contact_products,
  (SELECT COUNT(*) FROM subscriptions) as subscriptions,
  (SELECT COUNT(*) FROM transactions) as transactions;
-- All should be 0
```

**3.2 - Import Production Data (Same Order as Test)**

Use the same import process as Phase 2, but with full files:

```
1. v2_contacts.csv        → 5,620 rows
2. v2_tags.csv            → 97 rows
3. v2_products.csv        → 26 rows
4. v2_contact_tags.csv    → 8,795 rows
5. v2_contact_products.csv → 1,352 rows
6. v2_subscriptions.csv   → 263 rows
7. v2_transactions.csv    → 4,370 rows
```

**After each import, verify row count:**
```sql
SELECT 
  'contacts' as table_name, 
  COUNT(*) as actual_rows, 
  5620 as expected_rows,
  CASE WHEN COUNT(*) = 5620 THEN '✅' ELSE '❌' END as status
FROM contacts
UNION ALL
SELECT 'tags', COUNT(*), 97, CASE WHEN COUNT(*) = 97 THEN '✅' ELSE '❌' END FROM tags
UNION ALL
SELECT 'products', COUNT(*), 26, CASE WHEN COUNT(*) = 26 THEN '✅' ELSE '❌' END FROM products
UNION ALL
SELECT 'contact_tags', COUNT(*), 8795, CASE WHEN COUNT(*) = 8795 THEN '✅' ELSE '❌' END FROM contact_tags
UNION ALL
SELECT 'contact_products', COUNT(*), 1352, CASE WHEN COUNT(*) = 1352 THEN '✅' ELSE '❌' END FROM contact_products
UNION ALL
SELECT 'subscriptions', COUNT(*), 263, CASE WHEN COUNT(*) = 263 THEN '✅' ELSE '❌' END FROM subscriptions
UNION ALL
SELECT 'transactions', COUNT(*), 4370, CASE WHEN COUNT(*) = 4370 THEN '✅' ELSE '❌' END FROM transactions;
```

**3.3 - Run Comprehensive Validation**
```sql
-- No duplicate emails
SELECT email, COUNT(*) 
FROM contacts 
GROUP BY email 
HAVING COUNT(*) > 1;
-- Should return 0 rows

-- No orphaned junction records
SELECT 'orphaned contact_tags' as issue, COUNT(*) 
FROM contact_tags ct 
LEFT JOIN contacts c ON ct.contact_id = c.id 
LEFT JOIN tags t ON ct.tag_id = t.id
WHERE c.id IS NULL OR t.id IS NULL
UNION ALL
SELECT 'orphaned contact_products', COUNT(*) 
FROM contact_products cp 
LEFT JOIN contacts c ON cp.contact_id = c.id 
LEFT JOIN products p ON cp.product_id = p.id
WHERE c.id IS NULL OR p.id IS NULL
UNION ALL
SELECT 'orphaned subscriptions', COUNT(*) 
FROM subscriptions s 
LEFT JOIN contacts c ON s.contact_id = c.id 
WHERE c.id IS NULL
UNION ALL
SELECT 'orphaned transactions', COUNT(*) 
FROM transactions t 
LEFT JOIN contacts c ON t.contact_id = c.id 
WHERE c.id IS NULL;
-- All should return 0

-- Subscription status breakdown
SELECT status, COUNT(*) as count, 
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM subscriptions 
GROUP BY status 
ORDER BY count DESC;

-- Transaction status breakdown
SELECT status, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM transactions 
GROUP BY status 
ORDER BY count DESC;

-- Transaction type breakdown
SELECT transaction_type, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM transactions 
GROUP BY transaction_type 
ORDER BY count DESC;

-- Test views
SELECT * FROM v_contact_summary LIMIT 5;
SELECT * FROM v_active_subscriptions LIMIT 5;
SELECT * FROM v_potential_duplicate_contacts;
-- Should return 0 rows (no duplicates)
```

---

### PHASE 4: Enable Security (10 minutes)

**4.1 - Enable RLS**
```sql
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
```

**4.2 - Create Basic Policies**
```sql
-- Service role has full access (for admin operations)
CREATE POLICY "Service role full access" ON contacts
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON tags
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON products
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON contact_tags
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON contact_products
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON subscriptions
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON transactions
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Add more granular policies based on your auth requirements
-- Example: Users can view their own contact info
CREATE POLICY "Users view own contact" ON contacts
  FOR SELECT TO authenticated
  USING (auth.jwt()->>'email' = email);
```

---

## 🎉 SUCCESS CRITERIA

After deployment, you should have:

✅ **Architecture**
- UUID primary keys (immutable, deterministic)
- Case-insensitive email matching (citext)
- DB-level enum validation
- Foreign key integrity enforced
- Automatic timestamp updates
- Comprehensive indexes

✅ **Data Quality**
- 5,620 contacts (zero duplicates)
- 97 tags with UUID references
- 26 products with UUID references
- 8,795 contact-tag relationships (no orphans)
- 1,352 contact-product relationships (no orphans)
- 263 subscriptions (146 active, 117 canceled)
- 4,370 transactions (valid types and statuses)

✅ **Performance**
- Indexed lookups on all FKs
- Composite indexes for common queries
- Efficient junction table queries

✅ **Security**
- RLS enabled on all tables
- Service role access configured
- Ready for granular user policies

---

## 🔍 Key Architectural Improvements

### UUID Foreign Keys (vs Email)
**Old (V1):** `contact_tags.contact_email → contacts.email`  
**New (V2):** `contact_tags.contact_id → contacts.id (UUID)`

**Benefits:**
- Email changes don't break relationships
- Globally unique identifiers
- Better performance (UUID index vs text)
- Deterministic (same email = same UUID)

### Case-Insensitive Emails
**Old:** `bob@test.com` ≠ `Bob@Test.com` (duplicates possible)  
**New:** `citext` column type handles case automatically

### DB-Level Enums
**Old:** Any string allowed in status column  
**New:** Only valid enum values accepted by database

```sql
-- This will FAIL (good!):
INSERT INTO subscriptions (status) VALUES ('invalid_status');
-- ERROR: invalid input value for enum subscription_status: "invalid_status"
```

---

## 📊 Reporting Queries

```sql
-- Active subscriptions with revenue
SELECT 
  c.email,
  c.first_name || ' ' || c.last_name as name,
  p.name as product,
  s.amount,
  s.next_billing_date
FROM subscriptions s
JOIN contacts c ON s.contact_id = c.id
LEFT JOIN products p ON s.product_id = p.id
WHERE s.status = 'active'
ORDER BY s.next_billing_date;

-- Top customers by transaction volume
SELECT 
  c.email,
  c.first_name || ' ' || c.last_name as name,
  COUNT(t.id) as transaction_count,
  SUM(CASE WHEN t.transaction_type != 'refund' THEN t.amount ELSE 0 END) as total_spent
FROM contacts c
JOIN transactions t ON c.id = t.contact_id
GROUP BY c.id, c.email, c.first_name, c.last_name
ORDER BY total_spent DESC
LIMIT 20;

-- Tag distribution
SELECT 
  t.name as tag,
  COUNT(ct.contact_id) as contact_count
FROM tags t
LEFT JOIN contact_tags ct ON t.id = ct.tag_id
GROUP BY t.id, t.name
ORDER BY contact_count DESC;
```

---

## 🚨 Troubleshooting

### Import fails with "invalid UUID"
**Cause:** Non-UUID value in FK column  
**Fix:** Ensure using v2_*.csv files (not v1), which have proper UUIDs

### Import fails with "enum value not found"
**Cause:** Value not in enum definition  
**Fix:** Check enum mappings in schema, verify data processor ran correctly

### Import fails with "foreign key violation"
**Cause:** Wrong import order  
**Fix:** Must import in order: contacts → tags/products → junctions → subscriptions/transactions

### "duplicate key value" error
**Cause:** Trying to import twice without clearing  
**Fix:** Run TRUNCATE commands from Phase 3.1

---

## ✅ READY TO DEPLOY

**Estimated Total Time: ~1 hour**
- Schema: 5 min
- Test import: 15 min
- Production import: 30 min
- Security: 10 min

**Start with Phase 1 (Apply Schema), then test Phase 2 with samples!** 🚀
