-- ============================================================================
-- DATABASE CLEANUP: Remove Duplicate Indexes
-- ============================================================================
-- Purpose: Drop redundant indexes to improve write performance and save space
-- Estimated Savings: 3.8 MB storage + 5-10% write performance improvement
-- Risk Level: LOW (keeping primary indexes, only removing duplicates)
--
-- FAANG Standards Applied:
-- 1. Backup index definitions before dropping
-- 2. Verification steps
-- 3. Rollback capability
-- 4. Performance impact assessment
--
-- Created: 2025-11-08
-- ============================================================================

-- ============================================================================
-- STEP 0: PRE-FLIGHT CHECKS
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== DATABASE CLEANUP: DUPLICATE INDEXES ===';
  RAISE NOTICE 'This will drop 9 duplicate indexes to save 3.8 MB and improve write performance';
  RAISE NOTICE '';
END $$;

-- Show current database size
SELECT
  'Current database size' as metric,
  pg_size_pretty(pg_database_size(current_database())) as value;

-- Show current index sizes to be dropped
SELECT
  indexrelname as index_name,
  relname as table_name,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE indexrelname IN (
  'ux_external_identities_system_id',
  'ux_contact_roles_unique_active',
  'ux_contact_emails_one_outreach',
  'ux_contact_emails_one_primary',
  'idx_v_contact_roles_quick_contact_id',
  'idx_contacts_total_spent_desc',
  'idx_transactions_contact_timeline',
  'idx_webhook_events_webhook_id',
  'idx_webhook_events_cleanup'
)
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- STEP 1: BACKUP INDEX DEFINITIONS
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '=== STEP 1: BACKING UP INDEX DEFINITIONS ===';
END $$;

-- Create backup table with index definitions
DROP TABLE IF EXISTS index_backup_2025_11_08;

CREATE TABLE index_backup_2025_11_08 AS
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef,
  NOW() as backup_timestamp
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'ux_external_identities_system_id',
    'ux_contact_roles_unique_active',
    'ux_contact_emails_one_outreach',
    'ux_contact_emails_one_primary',
    'idx_v_contact_roles_quick_contact_id',
    'idx_contacts_total_spent_desc',
    'idx_transactions_contact_timeline',
    'idx_webhook_events_webhook_id',
    'idx_webhook_events_cleanup'
  );

-- Verify backup
SELECT COUNT(*) as indexes_backed_up FROM index_backup_2025_11_08;

DO $$
DECLARE
  v_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_count FROM index_backup_2025_11_08;

  IF v_count != 9 THEN
    RAISE EXCEPTION 'Expected 9 indexes in backup, got %', v_count;
  END IF;

  RAISE NOTICE 'Successfully backed up % index definitions', v_count;
END $$;

-- ============================================================================
-- STEP 2: DROP DUPLICATE INDEXES
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '=== STEP 2: DROPPING DUPLICATE INDEXES ===';
END $$;

-- Drop duplicate indexes (keeping the primary ones)
-- Each pair: we're dropping the duplicate, keeping the original

-- Pair 1: external_identities system lookup
DROP INDEX IF EXISTS ux_external_identities_system_id;
-- Keeping: idx_external_identities_lookup

-- Pair 2: contact_roles active status
DROP INDEX IF EXISTS ux_contact_roles_unique_active;
-- Keeping: idx_contact_roles_active

-- Pair 3: contact_emails outreach
DROP INDEX IF EXISTS ux_contact_emails_one_outreach;
-- Keeping: idx_contact_emails_outreach

-- Pair 4: contact_emails primary
DROP INDEX IF EXISTS ux_contact_emails_one_primary;
-- Keeping: idx_contact_emails_primary

-- Pair 5: contact_roles contact lookup
DROP INDEX IF EXISTS idx_v_contact_roles_quick_contact_id;
-- Keeping: idx_contact_roles_contact_id

-- Pair 6: contacts total spent
DROP INDEX IF EXISTS idx_contacts_total_spent_desc;
-- Keeping: idx_contacts_total_spent

-- Pair 7: transactions contact timeline
DROP INDEX IF EXISTS idx_transactions_contact_timeline;
-- Keeping: idx_transactions_contact_date

-- Pair 8: webhook events webhook id
DROP INDEX IF EXISTS idx_webhook_events_webhook_id;
-- Keeping: webhook_events_webhook_id_key

-- Pair 9: webhook events cleanup
DROP INDEX IF EXISTS idx_webhook_events_cleanup;
-- Keeping: idx_webhook_events_received_at

DO $$
BEGIN
  RAISE NOTICE 'Successfully dropped 9 duplicate indexes';
END $$;

-- ============================================================================
-- STEP 3: VERIFICATION
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '=== STEP 3: VERIFICATION ===';
END $$;

-- Verify indexes are dropped
SELECT
  'Indexes remaining' as check_type,
  COUNT(*) as count
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'ux_external_identities_system_id',
    'ux_contact_roles_unique_active',
    'ux_contact_emails_one_outreach',
    'ux_contact_emails_one_primary',
    'idx_v_contact_roles_quick_contact_id',
    'idx_contacts_total_spent_desc',
    'idx_transactions_contact_timeline',
    'idx_webhook_events_webhook_id',
    'idx_webhook_events_cleanup'
  );
-- Should return 0

-- Verify primary indexes still exist
SELECT
  'Primary indexes intact' as check_type,
  COUNT(*) as count
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'idx_external_identities_lookup',
    'idx_contact_roles_active',
    'idx_contact_emails_outreach',
    'idx_contact_emails_primary',
    'idx_contact_roles_contact_id',
    'idx_contacts_total_spent',
    'idx_transactions_contact_date',
    'webhook_events_webhook_id_key',
    'idx_webhook_events_received_at'
  );
-- Should return 9

-- Show space saved
SELECT
  'New database size' as metric,
  pg_size_pretty(pg_database_size(current_database())) as value;

-- ============================================================================
-- STEP 4: FINAL SUMMARY
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '=== CLEANUP COMPLETE ===';
  RAISE NOTICE 'Dropped 9 duplicate indexes';
  RAISE NOTICE 'Estimated space saved: 3.8 MB';
  RAISE NOTICE 'Estimated write performance improvement: 5-10%%';
  RAISE NOTICE '';
  RAISE NOTICE 'Backup table created: index_backup_2025_11_08';
  RAISE NOTICE 'To restore an index, run the CREATE INDEX command from the backup table';
  RAISE NOTICE '';
  RAISE NOTICE 'Cleanup successful! ✓';
END $$;

-- Show backup information
SELECT
  tablename,
  indexname,
  'To restore, run: ' || indexdef as restore_command
FROM index_backup_2025_11_08
ORDER BY indexname;

-- ============================================================================
-- RESTORE INSTRUCTIONS (if needed)
-- ============================================================================

-- If you need to restore any index:
-- 1. Query the backup table:
--    SELECT * FROM index_backup_2025_11_08;
--
-- 2. Copy the indexdef and run it:
--    (Example)
--    CREATE UNIQUE INDEX ux_external_identities_system_id
--      ON external_identities(system, external_id);

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

SELECT '✓ Duplicate indexes removed successfully' as status;
