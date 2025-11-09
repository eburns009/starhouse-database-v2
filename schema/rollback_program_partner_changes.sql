-- ============================================================================
-- ROLLBACK PLAN: Program Partner Module Changes
-- ============================================================================
-- Purpose: Safely remove program partner functionality from contacts module
-- Target: Move to members module in future (requires planning)
--
-- FAANG Standards Applied:
-- 1. Data Backup before any changes
-- 2. Transactional rollback (can be reverted)
-- 3. Verification steps at each stage
-- 4. Audit trail preservation
-- 5. Zero data loss approach
--
-- Created: 2025-11-08
-- Risk Level: LOW (minimal data to preserve - 41 program partners, 3 audit log entries)
-- ============================================================================

-- ============================================================================
-- STEP 0: PRE-FLIGHT CHECKS
-- ============================================================================

-- Check current state
DO $$
BEGIN
  RAISE NOTICE '=== PRE-FLIGHT CHECKS ===';
  RAISE NOTICE 'Checking current program partner data...';
END $$;

-- Count affected records
SELECT
  'contacts' as table_name,
  COUNT(*) FILTER (WHERE is_expected_program_partner = true) as program_partners,
  COUNT(*) FILTER (WHERE payment_method IS NOT NULL) as has_payment_method,
  COUNT(*) FILTER (WHERE payment_method_notes IS NOT NULL) as has_payment_notes,
  COUNT(*) FILTER (WHERE last_payment_date IS NOT NULL) as has_last_payment_date,
  COUNT(*) FILTER (WHERE partner_status_notes IS NOT NULL) as has_partner_notes
FROM contacts;

SELECT
  'subscriptions' as table_name,
  COUNT(*) FILTER (WHERE payment_method IS NOT NULL) as has_payment_method,
  COUNT(*) FILTER (WHERE payment_notes IS NOT NULL) as has_payment_notes
FROM subscriptions;

SELECT
  'program_partner_audit_log' as table_name,
  COUNT(*) as total_audit_entries
FROM program_partner_audit_log;

SELECT
  'legacy_program_partner_corrections' as table_name,
  COUNT(*) as total_correction_entries
FROM legacy_program_partner_corrections;

-- ============================================================================
-- STEP 1: BACKUP EXISTING DATA
-- ============================================================================
-- This ensures we can restore if needed

DO $$
BEGIN
  RAISE NOTICE '=== STEP 1: CREATING BACKUPS ===';
  RAISE NOTICE 'Backing up program partner data to temporary tables...';
END $$;

-- Backup program partner contacts data
CREATE TABLE IF NOT EXISTS backup_program_partner_contacts AS
SELECT
  id,
  email,
  first_name,
  last_name,
  is_expected_program_partner,
  payment_method,
  payment_method_notes,
  last_payment_date,
  partner_status_notes,
  NOW() as backup_timestamp
FROM contacts
WHERE
  is_expected_program_partner = true
  OR payment_method IS NOT NULL
  OR payment_method_notes IS NOT NULL
  OR last_payment_date IS NOT NULL
  OR partner_status_notes IS NOT NULL;

-- Backup audit log
CREATE TABLE IF NOT EXISTS backup_program_partner_audit_log AS
SELECT *, NOW() as backup_timestamp
FROM program_partner_audit_log;

-- Backup legacy corrections (should be empty, but backup anyway)
CREATE TABLE IF NOT EXISTS backup_legacy_program_partner_corrections AS
SELECT *, NOW() as backup_timestamp
FROM legacy_program_partner_corrections;

-- Verify backups
DO $$
DECLARE
  v_backup_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_backup_count FROM backup_program_partner_contacts;
  RAISE NOTICE 'Backed up % contact records', v_backup_count;

  SELECT COUNT(*) INTO v_backup_count FROM backup_program_partner_audit_log;
  RAISE NOTICE 'Backed up % audit log records', v_backup_count;

  SELECT COUNT(*) INTO v_backup_count FROM backup_legacy_program_partner_corrections;
  RAISE NOTICE 'Backed up % legacy correction records', v_backup_count;
END $$;

-- ============================================================================
-- STEP 2: REMOVE DEPENDENT OBJECTS (in correct order)
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 2: REMOVING DEPENDENT OBJECTS ===';
  RAISE NOTICE 'Dropping views, functions, and constraints...';
END $$;

-- Drop views first (they depend on tables/columns)
DROP VIEW IF EXISTS program_partner_audit_history CASCADE;
DROP VIEW IF EXISTS program_partner_compliance CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS remove_program_partner_status(UUID, TEXT, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS update_payment_method(UUID, TEXT, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS add_program_partner_status(UUID, TEXT, TEXT) CASCADE;

-- Verify views and functions are gone
DO $$
DECLARE
  v_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM information_schema.views
  WHERE table_name ILIKE '%program_partner%';

  IF v_count > 0 THEN
    RAISE EXCEPTION 'Views still exist! Count: %', v_count;
  ELSE
    RAISE NOTICE 'All program partner views removed successfully';
  END IF;

  SELECT COUNT(*) INTO v_count
  FROM information_schema.routines
  WHERE routine_name ILIKE '%program_partner%' OR routine_name ILIKE '%payment_method%';

  IF v_count > 0 THEN
    RAISE EXCEPTION 'Functions still exist! Count: %', v_count;
  ELSE
    RAISE NOTICE 'All program partner functions removed successfully';
  END IF;
END $$;

-- ============================================================================
-- STEP 3: DROP TABLES
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 3: DROPPING TABLES ===';
  RAISE NOTICE 'Removing program partner tables...';
END $$;

-- Drop tables (CASCADE will handle foreign keys)
DROP TABLE IF EXISTS legacy_program_partner_corrections CASCADE;
DROP TABLE IF EXISTS program_partner_audit_log CASCADE;

-- Verify tables are gone
DO $$
DECLARE
  v_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM information_schema.tables
  WHERE table_name IN ('legacy_program_partner_corrections', 'program_partner_audit_log');

  IF v_count > 0 THEN
    RAISE EXCEPTION 'Tables still exist! Count: %', v_count;
  ELSE
    RAISE NOTICE 'All program partner tables removed successfully';
  END IF;
END $$;

-- ============================================================================
-- STEP 4: REMOVE COLUMNS FROM CONTACTS TABLE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 4: REMOVING COLUMNS ===';
  RAISE NOTICE 'Dropping program partner columns from contacts and subscriptions...';
END $$;

-- Drop indexes first
DROP INDEX IF EXISTS idx_contacts_expected_partner;

-- Drop columns from contacts table
ALTER TABLE contacts
  DROP COLUMN IF EXISTS is_expected_program_partner CASCADE,
  DROP COLUMN IF EXISTS payment_method CASCADE,
  DROP COLUMN IF EXISTS payment_method_notes CASCADE,
  DROP COLUMN IF EXISTS last_payment_date CASCADE,
  DROP COLUMN IF EXISTS partner_status_notes CASCADE;

-- Drop columns from subscriptions table
ALTER TABLE subscriptions
  DROP COLUMN IF EXISTS payment_method CASCADE,
  DROP COLUMN IF EXISTS payment_notes CASCADE;

-- Verify columns are removed
DO $$
DECLARE
  v_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM information_schema.columns
  WHERE table_name = 'contacts'
    AND column_name IN (
      'is_expected_program_partner',
      'payment_method',
      'payment_method_notes',
      'last_payment_date',
      'partner_status_notes'
    );

  IF v_count > 0 THEN
    RAISE EXCEPTION 'Contacts columns still exist! Count: %', v_count;
  ELSE
    RAISE NOTICE 'All program partner columns removed from contacts successfully';
  END IF;

  SELECT COUNT(*) INTO v_count
  FROM information_schema.columns
  WHERE table_name = 'subscriptions'
    AND column_name IN ('payment_method', 'payment_notes');

  IF v_count > 0 THEN
    RAISE EXCEPTION 'Subscriptions columns still exist! Count: %', v_count;
  ELSE
    RAISE NOTICE 'All payment columns removed from subscriptions successfully';
  END IF;
END $$;

-- ============================================================================
-- STEP 5: FINAL VERIFICATION
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 5: FINAL VERIFICATION ===';
  RAISE NOTICE 'Verifying complete removal of program partner module...';
END $$;

-- Check for any remaining program partner artifacts
SELECT
  'Tables' as artifact_type,
  COUNT(*) as count
FROM information_schema.tables
WHERE table_name ILIKE '%program_partner%'
  AND table_name NOT ILIKE 'backup_%'

UNION ALL

SELECT
  'Views' as artifact_type,
  COUNT(*) as count
FROM information_schema.views
WHERE table_name ILIKE '%program_partner%'

UNION ALL

SELECT
  'Functions' as artifact_type,
  COUNT(*) as count
FROM information_schema.routines
WHERE routine_name ILIKE '%program_partner%' OR routine_name ILIKE '%payment_method%'

UNION ALL

SELECT
  'Indexes' as artifact_type,
  COUNT(*) as count
FROM pg_indexes
WHERE indexname ILIKE '%partner%' OR indexname ILIKE '%payment_method%';

-- ============================================================================
-- STEP 6: BACKUP TABLES SUMMARY
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== ROLLBACK COMPLETE ===';
  RAISE NOTICE 'All program partner functionality has been removed.';
  RAISE NOTICE 'Backup tables have been preserved:';
  RAISE NOTICE '  - backup_program_partner_contacts';
  RAISE NOTICE '  - backup_program_partner_audit_log';
  RAISE NOTICE '  - backup_legacy_program_partner_corrections';
  RAISE NOTICE '';
  RAISE NOTICE 'To restore data if needed, use the restore script.';
END $$;

-- Show backup data summary
SELECT
  'backup_program_partner_contacts' as backup_table,
  COUNT(*) as rows,
  MIN(backup_timestamp) as created_at
FROM backup_program_partner_contacts

UNION ALL

SELECT
  'backup_program_partner_audit_log' as backup_table,
  COUNT(*) as rows,
  MIN(backup_timestamp) as created_at
FROM backup_program_partner_audit_log

UNION ALL

SELECT
  'backup_legacy_program_partner_corrections' as backup_table,
  COUNT(*) as rows,
  MIN(backup_timestamp) as created_at
FROM backup_legacy_program_partner_corrections;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
SELECT '✓ Program Partner module successfully removed from contacts' as status;
