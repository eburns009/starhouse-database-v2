# 🚀 QUICK START - V2 (FAANG-Grade)

## ⚡ 3-Step Deployment

### Step 1: Apply Schema (5 min)
```bash
1. Open: https://supabase.com/dashboard/project/lnagadkqejnopgfxwlkb/sql/new
2. Upload: starhouse_schema_v2.sql
3. Click: "Run"
4. Verify: "Success. No rows returned"
```

### Step 2: Test Import (15 min)
```
Import these 7 files IN ORDER via Table Editor:
1. v2_contacts_sample.csv        → contacts (10 rows)
2. v2_tags_sample.csv            → tags (10 rows)
3. v2_products_sample.csv        → products (10 rows)
4. v2_contact_tags_sample.csv    → contact_tags (10 rows)
5. v2_contact_products_sample.csv → contact_products (10 rows)
6. v2_subscriptions_sample.csv   → subscriptions (10 rows)
7. v2_transactions_sample.csv    → transactions (10 rows)

Validate:
SELECT 
  (SELECT COUNT(*) FROM contacts) as contacts,
  (SELECT COUNT(*) FROM tags) as tags,
  (SELECT COUNT(*) FROM products) as products;
-- Should return: 10, 10, 10
```

### Step 3: Production Import (30 min)
```sql
-- Clear test data first:
TRUNCATE TABLE transactions, subscriptions, contact_products, 
               contact_tags, products, tags, contacts CASCADE;

-- Import same 7 files (production versions):
1. v2_contacts.csv        → 5,620 rows
2. v2_tags.csv            → 97 rows
3. v2_products.csv        → 26 rows
4. v2_contact_tags.csv    → 8,795 rows
5. v2_contact_products.csv → 1,352 rows
6. v2_subscriptions.csv   → 263 rows
7. v2_transactions.csv    → 4,370 rows

Validate:
SELECT 
  'contacts' as table, COUNT(*) as rows, 5620 as expected FROM contacts
UNION ALL
  SELECT 'tags', COUNT(*), 97 FROM tags
UNION ALL
  SELECT 'products', COUNT(*), 26 FROM products
UNION ALL
  SELECT 'contact_tags', COUNT(*), 8795 FROM contact_tags
UNION ALL
  SELECT 'contact_products', COUNT(*), 1352 FROM contact_products
UNION ALL
  SELECT 'subscriptions', COUNT(*), 263 FROM subscriptions
UNION ALL
  SELECT 'transactions', COUNT(*), 4370 FROM transactions;
-- All "rows" should match "expected"
```

---

## ✅ What You Get

### Architecture
- ✅ UUID primary keys (immutable)
- ✅ Case-insensitive emails (citext)
- ✅ DB-level enums (type safety)
- ✅ Foreign key constraints
- ✅ Unique constraints (no duplicates)
- ✅ Auto-updating timestamps
- ✅ Email validation
- ✅ 35+ indexes

### Data
- ✅ 5,620 contacts (zero duplicates)
- ✅ 97 tags (to consolidate to ~20)
- ✅ 26 products
- ✅ 10,147 relationships (all valid)
- ✅ 263 subscriptions
- ✅ 4,370 transactions

---

## 🔍 Quick Validation

```sql
-- No orphans (should return all 0)
SELECT 
  'orphaned contact_tags' as check_name, 
  COUNT(*) FROM contact_tags ct 
  LEFT JOIN contacts c ON ct.contact_id = c.id 
  WHERE c.id IS NULL
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

-- Check enum values
SELECT DISTINCT status FROM subscriptions;
-- Expected: active, canceled

SELECT DISTINCT status FROM transactions;
-- Expected: completed, failed, pending

SELECT DISTINCT transaction_type FROM transactions;
-- Expected: purchase, subscription, refund
```

---

## 📖 Full Documentation

- **V2_DEPLOYMENT_GUIDE.md** - Comprehensive step-by-step
- **V2_SUMMARY.md** - What changed from V1
- **starhouse_schema_v2.sql** - Complete database schema

---

## 🚨 Common Issues

**Import fails with "invalid UUID"**
→ Using old v1 files. Use v2_*.csv files!

**Import fails with "enum not found"**
→ Schema not applied. Run starhouse_schema_v2.sql first!

**Import fails with "foreign key violation"**
→ Wrong import order. Follow order exactly!

---

## 🎯 You're Ready!

Total time: ~50 minutes  
Result: Production-grade database ✨

**Start with Step 1! 🚀**
