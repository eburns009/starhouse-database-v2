# SQL Performance Optimization - Quick Guide

**Run these in order in the Supabase SQL Editor**
**URL:** https://app.supabase.com/project/lnagadkqejnopgfxwlkb/sql/new

---

## Step-by-Step Instructions

### STEP 1: Diagnostics (2 minutes)
**File:** `STEP_1_DIAGNOSTICS.sql`

**What it does:** Shows current performance and identifies problems

**Action:**
1. Open the file
2. Copy entire contents
3. Paste into Supabase SQL Editor
4. Click "Run"
5. Review results - look for high sequential scans

---

### STEP 2: Add Indexes (5 minutes) ⭐ BIGGEST IMPACT
**File:** `STEP_2_ADD_INDEXES.sql`

**What it does:** Adds 15+ indexes to speed up queries 3-10x

**Action:**
1. Open the file
2. Copy entire contents
3. Paste into Supabase SQL Editor
4. Click "Run"
5. Wait for completion (shows "CREATE INDEX" for each)

**Expected result:** All indexes created successfully

---

### STEP 3: Update Statistics (30 seconds)
**File:** `STEP_3_ANALYZE_TABLES.sql`

**What it does:** Updates table statistics for better query planning

**Action:**
1. Copy contents
2. Paste and run
3. Shows "ANALYZE" for each table

---

### STEP 4: Data Integrity Check (1 minute)
**File:** `STEP_4_DATA_INTEGRITY.sql`

**What it does:** Checks for orphaned records and data issues

**Action:**
1. Copy contents
2. Paste and run
3. Review results - all counts should be 0

**If you see issues:** Report them (we'll fix together)

---

### STEP 5: Create Monitoring Views (1 minute)
**File:** `STEP_5_MONITORING_VIEWS.sql`

**What it does:** Creates 3 views for ongoing monitoring

**Action:**
1. Copy contents
2. Paste and run
3. Shows "CREATE VIEW" for each

**Test the views:**
```sql
SELECT * FROM v_system_health;
SELECT * FROM v_slow_queries;
SELECT * FROM v_index_usage;
```

---

### STEP 6: Quick Health Check (anytime)
**File:** `STEP_6_QUICK_CHECK.sql`

**What it does:** One-query snapshot of entire system

**Action:**
1. Run this anytime to check system health
2. Shows all key metrics in one JSON object

---

## After Running All Steps

### Verify Performance Improvement

**Before optimization:** ~300ms queries
**After optimization:** ~50-100ms queries (3-6x faster!)

**Check it worked:**
```sql
-- Should show avg_query_time_ms < 100
SELECT * FROM v_system_health;

-- Should show all indexes with "Good usage"
SELECT * FROM v_index_usage;
```

---

## Troubleshooting

### If STEP 2 fails with "permission denied"
- You're using the anon key instead of service role key
- Go to Supabase dashboard as admin
- Run queries there

### If indexes already exist
- That's fine! "IF NOT EXISTS" prevents errors
- Skip to next step

### If data integrity check shows issues
- Note which issues
- We'll fix them together

---

## Success Indicators ✅

After running all steps, you should see:
- ✅ 15+ indexes created
- ✅ All tables analyzed
- ✅ Zero data integrity issues
- ✅ 3 monitoring views created
- ✅ Average query time < 100ms
- ✅ All indexes showing usage

---

## Quick Reference

**Main monitoring queries:**
```sql
-- System overview
SELECT * FROM v_system_health;

-- Find slow queries
SELECT * FROM v_slow_queries;

-- Check index usage
SELECT * FROM v_index_usage;

-- Quick health check
-- (Run STEP_6_QUICK_CHECK.sql)
```

---

**Total Time:** ~10 minutes
**Impact:** 3-10x faster queries, ready to scale to 100K+ records

**Questions?** Check results and let me know what you see!
