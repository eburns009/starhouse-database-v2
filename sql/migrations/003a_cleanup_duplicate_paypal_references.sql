-- ===========================================================================
-- Data Quality Cleanup: Remove Invalid PayPal Subscription References
-- ===========================================================================
-- Migration: 003a_cleanup_duplicate_paypal_references.sql
-- Date: 2025-11-09
-- Priority: P1 - DATA QUALITY FIX (Required before 003)
--
-- ISSUE FOUND:
-- - 263 Kajabi subscriptions incorrectly have paypal_subscription_reference = '53819'
-- - These are legitimate Kajabi subscriptions imported on 2025-11-04
-- - Each has a unique kajabi_subscription_id (correct identifier)
-- - The '53819' value is a bug/placeholder from the import script
--
-- SOLUTION:
-- - NULL out paypal_subscription_reference for these records
-- - They should rely on kajabi_subscription_id as primary identifier
-- - Create backup before modification
-- - Add verification queries
-- ===========================================================================

BEGIN;

-- ===========================================================================
-- STEP 1: Create backup of affected records
-- ===========================================================================

CREATE TABLE IF NOT EXISTS backup_subscriptions_paypal_cleanup_20251109 AS
SELECT
  id,
  contact_id,
  kajabi_subscription_id,
  paypal_subscription_reference,
  status,
  start_date,
  payment_processor,
  created_at,
  now() as backup_timestamp
FROM subscriptions
WHERE paypal_subscription_reference = '53819';

-- Add comment to backup table
COMMENT ON TABLE backup_subscriptions_paypal_cleanup_20251109 IS
'Backup of 263 subscriptions with duplicate paypal_subscription_reference="53819" before cleanup on 2025-11-09.
These were Kajabi subscriptions incorrectly assigned same PayPal reference during Nov 4 import.';

-- ===========================================================================
-- STEP 2: Data Quality Report
-- ===========================================================================

DO $$
DECLARE
  affected_count INTEGER;
  unique_kajabi_ids INTEGER;
  unique_contacts INTEGER;
  active_subs INTEGER;
BEGIN
  -- Count affected records
  SELECT
    COUNT(*),
    COUNT(DISTINCT kajabi_subscription_id),
    COUNT(DISTINCT contact_id),
    COUNT(*) FILTER (WHERE status = 'active')
  INTO affected_count, unique_kajabi_ids, unique_contacts, active_subs
  FROM subscriptions
  WHERE paypal_subscription_reference = '53819';

  RAISE NOTICE '============================================================';
  RAISE NOTICE 'DATA QUALITY CLEANUP REPORT';
  RAISE NOTICE '============================================================';
  RAISE NOTICE 'Affected subscriptions: %', affected_count;
  RAISE NOTICE 'Unique Kajabi IDs: %', unique_kajabi_ids;
  RAISE NOTICE 'Unique contacts: %', unique_contacts;
  RAISE NOTICE 'Active subscriptions: %', active_subs;
  RAISE NOTICE 'Canceled subscriptions: %', (affected_count - active_subs);
  RAISE NOTICE '------------------------------------------------------------';
  RAISE NOTICE 'Action: Setting paypal_subscription_reference to NULL';
  RAISE NOTICE 'Reason: These are Kajabi subscriptions with incorrect PayPal reference';
  RAISE NOTICE 'Backup table: backup_subscriptions_paypal_cleanup_20251109';
  RAISE NOTICE '============================================================';
END $$;

-- ===========================================================================
-- STEP 3: Fix the data
-- ===========================================================================

UPDATE subscriptions
SET
  paypal_subscription_reference = NULL,
  updated_at = now()
WHERE paypal_subscription_reference = '53819';

-- ===========================================================================
-- STEP 4: Verification
-- ===========================================================================

DO $$
DECLARE
  remaining_duplicates INTEGER;
  backup_count INTEGER;
BEGIN
  -- Check no '53819' references remain
  SELECT COUNT(*) INTO remaining_duplicates
  FROM subscriptions
  WHERE paypal_subscription_reference = '53819';

  -- Verify backup exists
  SELECT COUNT(*) INTO backup_count
  FROM backup_subscriptions_paypal_cleanup_20251109;

  IF remaining_duplicates > 0 THEN
    RAISE EXCEPTION 'CLEANUP FAILED: % records still have paypal_subscription_reference=53819', remaining_duplicates;
  END IF;

  IF backup_count != 263 THEN
    RAISE EXCEPTION 'BACKUP INCOMPLETE: Expected 263 records, found %', backup_count;
  END IF;

  RAISE NOTICE '============================================================';
  RAISE NOTICE 'CLEANUP SUCCESSFUL';
  RAISE NOTICE '============================================================';
  RAISE NOTICE '✓ Cleaned 263 subscriptions';
  RAISE NOTICE '✓ Backup created with % records', backup_count;
  RAISE NOTICE '✓ No duplicate PayPal references remaining';
  RAISE NOTICE '============================================================';
END $$;

COMMIT;

-- ===========================================================================
-- ROLLBACK SCRIPT (if needed)
-- ===========================================================================

/*
-- TO ROLLBACK THIS CLEANUP:

BEGIN;

UPDATE subscriptions s
SET
  paypal_subscription_reference = b.paypal_subscription_reference,
  updated_at = now()
FROM backup_subscriptions_paypal_cleanup_20251109 b
WHERE s.id = b.id;

-- Verify rollback
SELECT COUNT(*) FROM subscriptions WHERE paypal_subscription_reference = '53819';
-- Should return: 263

COMMIT;
*/

-- ===========================================================================
-- Root Cause Analysis
-- ===========================================================================

/*
FINDINGS:
---------
1. All 263 affected subscriptions were imported on 2025-11-04 16:12:33
2. Each has a unique kajabi_subscription_id (correct identifier)
3. All have payment_processor = 'PayPal'
4. Span 234 unique contacts across 13 different products

ROOT CAUSE:
-----------
FOUND: scripts/import_kajabi_subscriptions.py line 146 (2025-11-09)

The import script blindly imported the "Provider ID" column from Kajabi's CSV export:
  'paypal_subscription_reference': provider_id if provider.lower() == 'paypal' else None

Kajabi's CSV export has "53819" in the "Provider ID" column for ALL 263 PayPal subscriptions.
This is NOT a unique subscription ID - likely a PayPal plan/profile ID or placeholder.

The bug: Importing a non-unique field from Kajabi and treating it as a unique subscription reference.

IMPACT:
-------
- Medium severity: Data integrity issue preventing unique constraint
- No data loss: All subscriptions have correct kajabi_subscription_id
- No user impact: Subscriptions still function correctly
- Blocks migration 003 (unique constraints)

ACTION ITEMS:
-------------
1. ✅ Clean existing data (this migration)
2. ✅ Found and fixed bug in scripts/import_kajabi_subscriptions.py (2025-11-09)
   - Changed line 146 to always set paypal_subscription_reference = None for Kajabi imports
   - Added detailed comment explaining why Kajabi's "Provider ID" cannot be trusted
3. ✅ Validation added: Kajabi imports now always set paypal_subscription_reference to NULL
4. [ ] Consider check constraint to prevent future occurrences (optional)
5. ✅ Run migration 003 after this cleanup

PREVENTION:
-----------
Consider adding a check constraint:
  ALTER TABLE subscriptions ADD CONSTRAINT check_paypal_reference_valid
    CHECK (
      (payment_processor = 'PayPal' AND paypal_subscription_reference IS NOT NULL)
      OR
      (payment_processor != 'PayPal' AND paypal_subscription_reference IS NULL)
    );
*/
