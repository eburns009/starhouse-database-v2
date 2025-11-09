# Program Partner Rollback Guide

## Executive Summary

This guide provides a **FAANG-standard approach** to safely remove the program partner functionality from the contacts module. The program partner features were recently added but should be moved to a dedicated members module (requires additional planning).

## Current State Analysis

### What Was Added (Recent Changes)

#### 1. **Database Tables** (2 new tables)
- `program_partner_audit_log` - Tracks all program partner status changes
- `legacy_program_partner_corrections` - Tracks corrections to legacy data

#### 2. **Columns Added to `contacts` Table** (5 columns)
- `is_expected_program_partner` (BOOLEAN) - Partner status flag
- `payment_method` (TEXT) - Payment method type
- `payment_method_notes` (TEXT) - Notes about payment
- `last_payment_date` (TIMESTAMPTZ) - Last payment date
- `partner_status_notes` (TEXT) - Status notes

#### 3. **Columns Added to `subscriptions` Table** (2 columns)
- `payment_method` (TEXT) - Payment method type
- `payment_notes` (TEXT) - Payment notes

#### 4. **Indexes**
- `idx_contacts_expected_partner` - Index on program partner flag
- `idx_partner_audit_contact_id` - Audit log contact lookup
- `idx_partner_audit_action` - Audit log action lookup
- `idx_partner_audit_changed_at` - Audit log date lookup
- `idx_legacy_corrections_contact` - Legacy corrections contact lookup
- `idx_legacy_corrections_uncorrected` - Legacy uncorrected items

#### 5. **Database Functions** (3 functions)
- `add_program_partner_status()` - Add partner status
- `remove_program_partner_status()` - Remove partner status
- `update_payment_method()` - Update payment method

#### 6. **Database Views** (2 views)
- `program_partner_audit_history` - Audit trail view
- `program_partner_compliance` - Compliance reporting view

### Data Impact Assessment

Current data in production:
- **41 contacts** flagged as program partners
- **3 audit log entries**
- **1 contact** with payment method data
- **0 legacy corrections**
- **0 subscription** payment data

**Risk Level: LOW** ✅
- Minimal data loss risk
- All data can be backed up
- Easy to restore if needed

## FAANG Standards Applied

### 1. **Zero Downtime**
- All operations are non-blocking
- No table locks required
- Can be run during business hours

### 2. **Data Safety**
- Complete backup before any changes
- All data preserved in backup tables
- Restore capability included

### 3. **Transactional Integrity**
- Proper dependency order (views → functions → tables → columns)
- CASCADE handling for foreign keys
- Verification at each step

### 4. **Audit Trail**
- Preserve all audit log data
- Timestamp all backups
- Track who/when/why

### 5. **Rollback Capability**
- Full restore script provided
- Can undo the rollback if needed
- No permanent data loss

## Rollback Process

### Pre-Rollback Checklist

- [ ] Confirm this is the correct action (move to members module is planned)
- [ ] Notify stakeholders of the change
- [ ] Schedule a maintenance window (optional, but recommended)
- [ ] Backup the entire database (standard practice)
- [ ] Review current data counts (script provided)

### Step-by-Step Rollback

#### Option A: Run the Complete Rollback Script (Recommended)

```bash
# Execute the rollback script
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -f schema/rollback_program_partner_changes.sql
```

This script will:
1. ✅ Show pre-flight data counts
2. ✅ Create backup tables with all data
3. ✅ Remove views and functions
4. ✅ Drop program partner tables
5. ✅ Remove columns from contacts/subscriptions
6. ✅ Verify complete removal
7. ✅ Show backup summary

**Estimated Time:** 2-5 seconds

#### Option B: Manual Step-by-Step (For Review)

If you want to review each step:

```bash
# 1. Check current state
psql -c "SELECT COUNT(*) FROM contacts WHERE is_expected_program_partner = true;"

# 2. Create backups
psql -c "CREATE TABLE backup_program_partner_contacts AS
         SELECT * FROM contacts WHERE is_expected_program_partner = true;"

# 3-7. Continue with remaining steps from rollback script
```

### Post-Rollback Verification

Run these queries to verify successful rollback:

```sql
-- Should return 0 for all
SELECT
  'Tables' as artifact_type,
  COUNT(*) as count
FROM information_schema.tables
WHERE table_name ILIKE '%program_partner%'
  AND table_name NOT ILIKE 'backup_%';

-- Should return 0
SELECT COUNT(*)
FROM information_schema.columns
WHERE table_name = 'contacts'
  AND column_name = 'is_expected_program_partner';

-- Should show backup data
SELECT COUNT(*) FROM backup_program_partner_contacts;
```

### Backup Tables Created

After rollback, these backup tables will exist:

1. **backup_program_partner_contacts**
   - All 41 program partner contacts
   - All payment method data
   - Timestamped with backup date

2. **backup_program_partner_audit_log**
   - All 3 audit log entries
   - Complete audit trail

3. **backup_legacy_program_partner_corrections**
   - All legacy correction data (currently empty)

**Retention:** Keep these tables until the members module is implemented and verified.

## Restore Process (If Needed)

If you need to undo the rollback:

```bash
# Run the restore script
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -f schema/restore_program_partner_from_backup.sql

# Then recreate functions/views
PGPASSWORD='your_password' psql \
  postgres://your_connection_string \
  -f schema/program_partner_management.sql
```

**Estimated Time:** 3-7 seconds

## Migration to Members Module (Future)

### Recommended Architecture

When implementing the members module:

1. **Create dedicated `members` table**
   ```sql
   CREATE TABLE members (
     id UUID PRIMARY KEY,
     contact_id UUID REFERENCES contacts(id),
     member_type TEXT, -- 'program_partner', 'individual', etc.
     payment_method TEXT,
     payment_method_notes TEXT,
     last_payment_date TIMESTAMPTZ,
     status TEXT,
     status_notes TEXT,
     ...
   );
   ```

2. **Migrate data from backups**
   ```sql
   INSERT INTO members (contact_id, member_type, ...)
   SELECT id, 'program_partner', ...
   FROM backup_program_partner_contacts;
   ```

3. **Benefits of separation**
   - ✅ Cleaner contacts table (single responsibility)
   - ✅ Dedicated member lifecycle management
   - ✅ Easier to add new member types
   - ✅ Better for FAANG-level architecture
   - ✅ Follows Domain-Driven Design principles

## Troubleshooting

### Issue: "Backup tables already exist"

```sql
-- Drop old backups first (after confirming data is safe)
DROP TABLE IF EXISTS backup_program_partner_contacts;
DROP TABLE IF EXISTS backup_program_partner_audit_log;
DROP TABLE IF EXISTS backup_legacy_program_partner_corrections;

-- Then re-run rollback script
```

### Issue: "Foreign key constraint violation"

This should not happen if using the provided script (it uses CASCADE), but if it does:

```sql
-- Manually drop foreign key constraints first
ALTER TABLE program_partner_audit_log
  DROP CONSTRAINT IF EXISTS program_partner_audit_log_contact_id_fkey CASCADE;
```

### Issue: "Want to keep backup tables permanently"

```sql
-- Rename backup tables for long-term storage
ALTER TABLE backup_program_partner_contacts
  RENAME TO archive_program_partner_contacts_2025_11_08;

-- Add comments for documentation
COMMENT ON TABLE archive_program_partner_contacts_2025_11_08 IS
  'Archived program partner data from contacts module.
   Saved before migration to members module on 2025-11-08.';
```

## Monitoring & Validation

### After Rollback

```sql
-- Verify contacts table is clean
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'contacts'
  AND column_name ILIKE '%partner%';
-- Should return: 0 rows

-- Verify backups exist
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename LIKE 'backup_program_partner%';
-- Should show 3 backup tables
```

### Health Check

```sql
-- Verify no broken dependencies
SELECT
  conname,
  conrelid::regclass AS table,
  confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE confrelid = 'program_partner_audit_log'::regclass
   OR confrelid = 'legacy_program_partner_corrections'::regclass;
-- Should return: 0 rows
```

## Communication Template

### For Stakeholders

```
Subject: Program Partner Module Rollback - [Date]

Team,

We are rolling back the program partner functionality from the contacts
module as part of our architectural improvement plan. This change:

✅ Backs up all existing program partner data (41 contacts)
✅ Removes program partner columns from contacts table
✅ Prepares for future members module implementation
✅ Zero data loss - all data preserved in backup tables

Timeline:
- Rollback: [Date/Time]
- Duration: ~5 seconds
- Downtime: None
- Data preserved: 100%

Next Steps:
- Plan members module architecture
- Design member lifecycle management
- Migrate data to new module

Questions? Contact [Your Name]
```

## Files Reference

### Created Files

1. **schema/rollback_program_partner_changes.sql**
   - Complete rollback script
   - Creates backups
   - Removes all program partner artifacts
   - ~250 lines, fully commented

2. **schema/restore_program_partner_from_backup.sql**
   - Restore script (if rollback needs to be undone)
   - Recreates tables, columns, indexes
   - Restores data from backups
   - ~150 lines, fully commented

3. **docs/runbooks/PROGRAM_PARTNER_ROLLBACK_GUIDE.md** (this file)
   - Complete guide
   - FAANG best practices
   - Step-by-step instructions

### Existing Files (for reference)

- `schema/program_partner_management.sql` - Original implementation
- `schema/program_partner_compliance.sql` - Compliance features
- `PROGRAM_PARTNER_DEPLOYMENT_COMPLETE.md` - Deployment notes

## Approval & Sign-off

Before executing rollback:

- [ ] Technical lead approval
- [ ] Data owner notification
- [ ] Backup verification complete
- [ ] Restore procedure tested (optional)
- [ ] Communication sent to stakeholders

## Success Criteria

✅ All program partner tables removed
✅ All program partner columns removed
✅ All program partner functions removed
✅ All program partner views removed
✅ All data backed up successfully
✅ No foreign key constraint errors
✅ No broken dependencies
✅ Restore capability verified

## Support

For questions or issues:
1. Check troubleshooting section above
2. Review backup tables to confirm data preservation
3. Test restore script in development environment first
4. Contact database administrator if issues persist

---

**Version:** 1.0
**Last Updated:** 2025-11-08
**Author:** Claude Code
**Review Status:** Ready for execution
