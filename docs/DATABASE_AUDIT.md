# StarHouse Platform - Database Audit

**Phase 1, Day 2-3 Audit**
**Date:** 2025-11-22
**Author:** Claude Code

---

## Executive Summary

The StarHouse database is in **good health** with solid fundamentals. Core tables have proper primary keys, foreign keys, indexes, and RLS policies. The main areas needing attention are:

1. **Performance concern**: `staff_members` table has 99% sequential scans (missing index usage)
2. **Backup table cleanup**: 11 backup tables without PKs should be cleaned up
3. **Source tracking gap**: 129 contacts lack external identity tracking
4. **Schema bloat**: Many legacy columns on `contacts` table (100+ columns)

**Overall Assessment**: Foundation is solid enough to proceed with donors module. Fix the staff_members performance issue first.

---

## 1. Row Count Comparison (CSV vs Database)

### Core Tables

| Table | Database | CSV Export | Notes |
|-------|----------|------------|-------|
| contacts | **7,210** | 5,621 | +1,589 since export |
| transactions | **12,665** | 4,371 | +8,294 since export |
| contact_tags | **10,275** | 8,796 | +1,479 since export |
| subscriptions | **327** | 264 | +63 since export |
| contact_emails | **7,570** | N/A | Multi-email support |
| external_identities | **11,043** | N/A | Source tracking |
| contact_roles | **6,007** | N/A | Role tracking |
| products | **109** | 27 | +82 since export |
| tags | **128** | 98 | +30 since export |

### Transaction Breakdown by Source

| Source | Count | Total Amount | Date Range |
|--------|-------|--------------|------------|
| Kajabi | 4,403 | $273,903 | 2020-12 to 2025-11 |
| Ticket Tailor | 4,280 | $114,309 | 2020-02 to 2025-11 |
| PayPal | 3,982 | $22,856 | 2020-05 to 2025-11 |
| **Total** | **12,665** | **$411,068** | |

### Subscription Status

| Status | Count | Total MRR |
|--------|-------|-----------|
| Active | 138 | $17,446 |
| Canceled | 138 | $12,459 |
| Expired | 51 | $9,741 |
| **Total** | **327** | |

---

## 2. Schema Issues Found

### Tables Without Primary Keys (11)

All are backup tables - not critical but should be cleaned up:

```
backup_legacy_program_partner_corrections
backup_phone_duplicate_merge_20251109
backup_program_partner_audit_log
backup_program_partner_contacts
backup_subscriptions_paypal_cleanup_20251109
contact_emails_backup_20251110
contacts_backup_20251115_203330_ncoa
contacts_backup_20251115_203615_ncoa
contacts_backup_20251115_210133_exceptions
contacts_backup_20251115_215640_ncoa
contacts_backup_20251115_enrichment
```

### Foreign Key Relationships (✓ Well-Structured)

22 foreign key relationships properly defined:

| Child Table | Column | References |
|-------------|--------|------------|
| contact_emails | contact_id | contacts.id |
| contact_names | contact_id | contacts.id |
| contact_notes | contact_id | contacts.id |
| contact_products | contact_id | contacts.id |
| contact_products | product_id | products.id |
| contact_roles | contact_id | contacts.id |
| contact_tags | contact_id | contacts.id |
| contact_tags | tag_id | tags.id |
| external_identities | contact_id | contacts.id |
| subscriptions | contact_id | contacts.id |
| subscriptions | membership_product_id | membership_products.id |
| subscriptions | product_id | products.id |
| transactions | contact_id | contacts.id |
| transactions | product_id | products.id |
| transactions | subscription_id | subscriptions.id |
| webhook_events | contact_id | contacts.id |
| webhook_events | subscription_id | subscriptions.id |
| webhook_events | transaction_id | transactions.id |

### Contacts Table Schema Bloat

The `contacts` table has **100+ columns** including:
- Core fields (email, name, phone, address)
- Legacy PayPal fields (paypal_email, paypal_first_name, paypal_business_name, etc.)
- USPS validation fields (billing_usps_*, shipping_usps_*)
- Duplicate tracking (potential_duplicate_group, is_alias_of)
- Deprecated arrays (tags, secondary_emails)

**Recommendation**: Consider normalizing legacy fields into separate tables (done for emails → contact_emails, external IDs → external_identities).

---

## 3. Data Quality Metrics

### Contact Completeness

| Field | Count | Percentage |
|-------|-------|------------|
| Email | 7,210 | **100.0%** |
| First Name | 7,086 | **98.3%** |
| Last Name | 6,542 | **90.7%** |
| Phone | 3,011 | 41.8% |
| Address | 2,029 | 28.1% |

**Key Insight**: Email and name coverage is excellent. Phone and address are enrichment opportunities, not blockers.

### Duplicate Check

- **Duplicate emails**: ✓ None found
- **Duplicate external identities**: ✓ None found

### Orphaned Records

- **Transactions without contacts**: 0 ✓
- **Subscriptions without contacts**: 0 ✓

### Source Tracking Gap

- **Contacts without external identity**: 129 (1.8%)

These 129 contacts may have been created manually or through imports that didn't populate external_identities.

---

## 4. RLS (Row Level Security) Status

### Summary

- **Enabled**: 22 tables
- **Disabled**: 21 tables (all are backup/utility tables)

### Core Tables (All Protected ✓)

| Table | RLS | Policies |
|-------|-----|----------|
| contacts | ✓ | admin_delete, staff_insert, staff_read, staff_update, service_role |
| transactions | ✓ | admin_delete, staff_modify, staff_read, staff_update, service_role, verified_staff_* |
| subscriptions | ✓ | admin_delete, staff_modify, staff_read, staff_update, service_role, verified_staff_* |
| contact_emails | ✓ | insert, select, update |
| contact_tags | ✓ | staff_full_access, service_role |
| contact_roles | ✓ | insert, select, update |
| contact_notes | ✓ | delete, insert, select, update |
| external_identities | ✓ | insert, select, update |
| products | ✓ | admin_delete, staff_modify, staff_read, staff_update |
| tags | ✓ | admin_delete, staff_modify, staff_read, staff_update |
| staff_members | ✓ | admin_add, admin_delete, admin_update, staff_view |

### Tables Without RLS (Expected - Backup/Utility)

All 21 tables without RLS are:
- Backup tables (contacts_backup_*, *_backup)
- Import utilities (import_lock_rules, import_audit_log, import_conflicts)

---

## 5. Performance Concerns

### Critical: staff_members Table

| Table | Seq Scans | Index Scans | Index Usage |
|-------|-----------|-------------|-------------|
| **staff_members** | 893,369 | 8,019 | **0.9%** |

**Issue**: 99% sequential scans on a table with only 1 row. This indicates inefficient queries hitting auth checks repeatedly.

**Likely Cause**: RLS policies checking staff membership on every query without using proper indexes.

### Good Performance (Index Usage > 90%)

| Table | Seq Scans | Index Scans | Index Usage |
|-------|-----------|-------------|-------------|
| contacts | 16,090 | 4,240,741 | **99.6%** |
| contact_emails | 564 | 330,822 | **99.8%** |
| subscriptions | 551 | 200,991 | **99.7%** |
| contact_tags | 88 | 42,704 | **99.8%** |
| contact_names | 40 | 81,440 | **100.0%** |
| transactions | 5,819 | 97,768 | **94.4%** |
| external_identities | 87 | 18,821 | **99.5%** |
| contact_roles | 135 | 8,858 | **98.5%** |
| tags | 1,148 | 13,718 | **92.3%** |
| webhook_events | 301 | 3,034 | **91.0%** |

### Table Sizes

| Table | Total Size | Data | Indexes |
|-------|------------|------|---------|
| contacts | 17 MB | 4.2 MB | 12 MB |
| transactions | 16 MB | 7.3 MB | 9.5 MB |
| contact_emails | 8.3 MB | 1.1 MB | 7.1 MB |
| contact_names | 5.3 MB | 0.8 MB | 4.4 MB |
| external_identities | 4.8 MB | 1.4 MB | 3.4 MB |
| contact_tags | 3.6 MB | 0.8 MB | 2.7 MB |
| contact_roles | 2.7 MB | 0.9 MB | 1.7 MB |

**Total database size**: ~60 MB (very small, no concern)

### Dead Rows

| Table | Dead Rows | % of Total |
|-------|-----------|------------|
| transactions | 440 | 3.5% |
| contact_roles | 349 | 5.8% |
| contact_products | 297 | 21.9% |
| contacts | 258 | 3.6% |
| products | 55 | 50.5% |

**Recommendation**: Run `VACUUM ANALYZE` on tables with high dead row percentages.

---

## 6. Recommended Fixes

### P0 - Critical (Fix Immediately)

#### 1. Staff Members Performance Issue

**Problem**: 893K sequential scans on staff_members table causing performance degradation.

**Solution**: Analyze RLS policies and add composite index:

```sql
-- Check what queries are hitting staff_members
SELECT schemaname, relname, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables
WHERE relname = 'staff_members';

-- Add composite index for common lookups
CREATE INDEX IF NOT EXISTS idx_staff_members_role_email
ON staff_members(role, email);

-- Reset stats after fix
SELECT pg_stat_reset_single_table_counters('staff_members'::regclass);
```

### P1 - High (Fix This Week)

#### 2. Vacuum Dead Rows

```sql
-- Run vacuum on tables with dead rows
VACUUM ANALYZE transactions;
VACUUM ANALYZE contact_roles;
VACUUM ANALYZE contact_products;
VACUUM ANALYZE contacts;
VACUUM ANALYZE products;
```

#### 3. Investigate 129 Contacts Without Source Tracking

```sql
-- Find contacts without external_identities
SELECT id, email, first_name, last_name, created_at, source_system
FROM contacts c
WHERE NOT EXISTS (
    SELECT 1 FROM external_identities ei
    WHERE ei.contact_id = c.id
)
ORDER BY created_at DESC
LIMIT 50;
```

### P2 - Medium (Fix Before Donors Module)

#### 4. Clean Up Backup Tables

Consider dropping or archiving these 11 backup tables:

```sql
-- Archive or drop old backup tables
-- First export to CSV if needed, then:
DROP TABLE IF EXISTS backup_legacy_program_partner_corrections;
DROP TABLE IF EXISTS backup_phone_duplicate_merge_20251109;
DROP TABLE IF EXISTS backup_program_partner_audit_log;
-- etc.
```

#### 5. Document Schema

The `contacts` table has grown to 100+ columns. Create a schema documentation showing:
- Which columns are actively used
- Which are deprecated (moved to contact_emails, external_identities)
- Which should be migrated or removed

### P3 - Low (Nice to Have)

#### 6. Consider Normalizing PayPal Fields

The contacts table still has PayPal-specific columns:
- paypal_email
- paypal_first_name
- paypal_last_name
- paypal_business_name
- paypal_payer_id

These could be moved to external_identities.metadata for cleaner schema.

---

## 7. Assessment for Donors Module

### Foundation Quality: ✓ Ready

| Requirement | Status | Notes |
|-------------|--------|-------|
| Contact matching | ✓ | Email-based dedup working, no duplicates |
| Transaction tracking | ✓ | 12,665 transactions with source_system |
| Source provenance | ✓ | Kajabi/PayPal/Ticket Tailor separated |
| Data integrity | ✓ | No orphaned records |
| Security (RLS) | ✓ | All core tables protected |
| Performance | ⚠️ | Fix staff_members issue first |

### What's Needed for Donors

1. **Donations table** - Not yet created (transactions table tracks payments, not donations specifically)
2. **QuickBooks integration** - Import script exists but not connected
3. **JotForm integration** - No scripts found
4. **Tax receipt tracking** - Not in schema

### Recommendation

**Proceed with donors module planning.** The Contacts module is solid. Fix the staff_members performance issue during Week 1 (1 day), then begin donors schema design.

---

## 8. Audit Script

The audit was performed using [scripts/audit_database.py](../scripts/audit_database.py). Run with:

```bash
python3 scripts/audit_database.py
```

---

**End of Database Audit Report**
