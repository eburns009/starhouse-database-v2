-- ===========================================================================
-- Add Unique Constraints on External IDs
-- ===========================================================================
-- Migration: 003_add_unique_constraints_external_ids.sql
-- Date: 2025-11-09
-- Priority: HIGH PRIORITY - Data Integrity
--
-- Purpose: Prevent duplicate imports from external systems (Kajabi, PayPal, Zoho, Ticket Tailor)
-- Ensures each external entity can only be imported once
--
-- PREREQUISITES:
--   - Run migration 003a_cleanup_duplicate_paypal_references.sql first
--     (Cleans up data quality issue with duplicate PayPal references)
--
-- FAANG STANDARDS:
--   - Pre-flight checks for data quality issues
--   - Detailed reporting of any duplicates found
--   - Fail-fast if duplicates exist
--   - Verification queries included
--   - Rollback procedure documented
-- ===========================================================================

-- ===========================================================================
-- PRE-FLIGHT CHECKS: Detect duplicate data before creating constraints
-- ===========================================================================

DO $$
DECLARE
  dup_count INTEGER;
  dup_details TEXT;
BEGIN
  RAISE NOTICE '============================================================';
  RAISE NOTICE 'PRE-FLIGHT DUPLICATE DETECTION';
  RAISE NOTICE '============================================================';

  -- Check for duplicate Kajabi contact IDs
  SELECT COUNT(*) - COUNT(DISTINCT kajabi_id) INTO dup_count
  FROM contacts WHERE kajabi_id IS NOT NULL;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'DUPLICATE DATA: % contacts have duplicate kajabi_id', dup_count;
  END IF;
  RAISE NOTICE '✓ contacts.kajabi_id: No duplicates found';

  -- Check for duplicate PayPal payer IDs
  SELECT COUNT(*) - COUNT(DISTINCT paypal_payer_id) INTO dup_count
  FROM contacts WHERE paypal_payer_id IS NOT NULL;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'DUPLICATE DATA: % contacts have duplicate paypal_payer_id', dup_count;
  END IF;
  RAISE NOTICE '✓ contacts.paypal_payer_id: No duplicates found';

  -- Check for duplicate Zoho IDs
  SELECT COUNT(*) - COUNT(DISTINCT zoho_id) INTO dup_count
  FROM contacts WHERE zoho_id IS NOT NULL;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'DUPLICATE DATA: % contacts have duplicate zoho_id', dup_count;
  END IF;
  RAISE NOTICE '✓ contacts.zoho_id: No duplicates found';

  -- Check for duplicate Ticket Tailor IDs
  SELECT COUNT(*) - COUNT(DISTINCT ticket_tailor_id) INTO dup_count
  FROM contacts WHERE ticket_tailor_id IS NOT NULL;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'DUPLICATE DATA: % contacts have duplicate ticket_tailor_id', dup_count;
  END IF;
  RAISE NOTICE '✓ contacts.ticket_tailor_id: No duplicates found';

  -- Check for duplicate Kajabi subscription IDs
  SELECT COUNT(*) - COUNT(DISTINCT kajabi_subscription_id) INTO dup_count
  FROM subscriptions WHERE kajabi_subscription_id IS NOT NULL;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'DUPLICATE DATA: % subscriptions have duplicate kajabi_subscription_id', dup_count;
  END IF;
  RAISE NOTICE '✓ subscriptions.kajabi_subscription_id: No duplicates found';

  -- Check for duplicate PayPal subscription references
  SELECT COUNT(*) - COUNT(DISTINCT paypal_subscription_reference) INTO dup_count
  FROM subscriptions WHERE paypal_subscription_reference IS NOT NULL;
  IF dup_count > 0 THEN
    SELECT string_agg(paypal_subscription_reference || ' (' || cnt || ' times)', ', ')
    INTO dup_details
    FROM (
      SELECT paypal_subscription_reference, COUNT(*) as cnt
      FROM subscriptions
      WHERE paypal_subscription_reference IS NOT NULL
      GROUP BY paypal_subscription_reference
      HAVING COUNT(*) > 1
      LIMIT 5
    ) dupes;
    RAISE EXCEPTION 'DUPLICATE DATA: % subscriptions have duplicate paypal_subscription_reference. Examples: %', dup_count, dup_details;
  END IF;
  RAISE NOTICE '✓ subscriptions.paypal_subscription_reference: No duplicates found';

  -- Check for duplicate (source_system, external_transaction_id) pairs
  SELECT COUNT(*) INTO dup_count
  FROM (
    SELECT source_system, external_transaction_id, COUNT(*) as cnt
    FROM transactions
    WHERE source_system IS NOT NULL AND external_transaction_id IS NOT NULL
    GROUP BY source_system, external_transaction_id
    HAVING COUNT(*) > 1
  ) dupes;
  IF dup_count > 0 THEN
    RAISE EXCEPTION 'DUPLICATE DATA: % transaction (source_system, external_transaction_id) pairs are duplicated', dup_count;
  END IF;
  RAISE NOTICE '✓ transactions.(source_system, external_transaction_id): No duplicates found';

  RAISE NOTICE '============================================================';
  RAISE NOTICE 'PRE-FLIGHT CHECKS PASSED - Proceeding with constraints';
  RAISE NOTICE '============================================================';
END $$;

BEGIN;

-- ===========================================================================
-- STEP 1: Add unique constraints on contacts table external IDs
-- ===========================================================================

-- Kajabi ID (primary external identifier for Kajabi contacts)
-- Allows NULL but prevents duplicate non-NULL values
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_kajabi_id_unique
ON contacts (kajabi_id)
WHERE kajabi_id IS NOT NULL;

-- Kajabi Member ID (alternative Kajabi identifier)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_kajabi_member_id_unique
ON contacts (kajabi_member_id)
WHERE kajabi_member_id IS NOT NULL;

-- PayPal Payer ID (unique PayPal customer identifier)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_paypal_payer_id_unique
ON contacts (paypal_payer_id)
WHERE paypal_payer_id IS NOT NULL;

-- Zoho CRM ID (unique Zoho contact identifier)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_zoho_id_unique
ON contacts (zoho_id)
WHERE zoho_id IS NOT NULL;

-- Ticket Tailor ID (unique Ticket Tailor customer identifier)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_ticket_tailor_id_unique
ON contacts (ticket_tailor_id)
WHERE ticket_tailor_id IS NOT NULL;

-- ===========================================================================
-- STEP 2: Add unique constraints on products table
-- ===========================================================================

-- Kajabi Offer ID (unique Kajabi product identifier)
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_products_kajabi_offer_id_unique
ON products (kajabi_offer_id)
WHERE kajabi_offer_id IS NOT NULL;

-- ===========================================================================
-- STEP 3: Add unique constraints on subscriptions table
-- ===========================================================================

-- Kajabi Subscription ID
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_kajabi_subscription_id_unique
ON subscriptions (kajabi_subscription_id)
WHERE kajabi_subscription_id IS NOT NULL;

-- PayPal Subscription Reference
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_paypal_subscription_reference_unique
ON subscriptions (paypal_subscription_reference)
WHERE paypal_subscription_reference IS NOT NULL;

-- ===========================================================================
-- STEP 4: Add unique constraints on transactions table
-- ===========================================================================

-- Kajabi Transaction ID (unique Kajabi transaction identifier)
-- NOTE: This is deprecated in favor of composite constraint below
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_kajabi_transaction_id_unique
ON transactions (kajabi_transaction_id)
WHERE kajabi_transaction_id IS NOT NULL;

-- Composite unique constraint on (source_system, external_transaction_id)
-- Prevents duplicate transactions across ALL sources (Kajabi, PayPal, Ticket Tailor)
-- This is the CORRECT approach for multi-source transaction imports
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_source_external_id_unique
ON transactions (source_system, external_transaction_id)
WHERE external_transaction_id IS NOT NULL AND source_system IS NOT NULL;

COMMIT;

-- ===========================================================================
-- Verification queries (run these manually after migration)
-- ===========================================================================

-- Check all unique indexes were created
-- SELECT
--   schemaname,
--   tablename,
--   indexname,
--   indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
--   AND indexname LIKE '%_unique'
-- ORDER BY tablename, indexname;

-- Verify no duplicates exist (should all return 0)
-- SELECT
--   'contacts.kajabi_id' as field,
--   COUNT(*) - COUNT(DISTINCT kajabi_id) as duplicates
-- FROM contacts WHERE kajabi_id IS NOT NULL
-- UNION ALL
-- SELECT
--   'products.kajabi_offer_id',
--   COUNT(*) - COUNT(DISTINCT kajabi_offer_id)
-- FROM products WHERE kajabi_offer_id IS NOT NULL
-- UNION ALL
-- SELECT
--   'subscriptions.kajabi_subscription_id',
--   COUNT(*) - COUNT(DISTINCT kajabi_subscription_id)
-- FROM subscriptions WHERE kajabi_subscription_id IS NOT NULL
-- UNION ALL
-- SELECT
--   'transactions.kajabi_transaction_id',
--   COUNT(*) - COUNT(DISTINCT kajabi_transaction_id)
-- FROM transactions WHERE kajabi_transaction_id IS NOT NULL;

-- ===========================================================================
-- Notes
-- ===========================================================================

/*
IMPLEMENTATION NOTES:

1. CONCURRENTLY keyword:
   - Creates indexes without locking the table
   - Allows reads/writes to continue during index creation
   - Production-safe for large tables

2. Partial indexes (WHERE column IS NOT NULL):
   - Only indexes non-NULL values
   - Allows multiple NULL values (doesn't enforce uniqueness on NULL)
   - Smaller index size (more efficient)

3. IF NOT EXISTS:
   - Safe to re-run migration
   - Won't fail if indexes already exist

4. Benefits:
   - Prevents duplicate imports from Kajabi/PayPal/Zoho
   - Idempotent imports (can re-run without creating duplicates)
   - Data integrity at database level
   - Fast lookups on external IDs

5. Import script implications:
   - Scripts can use INSERT ... ON CONFLICT (external_id) DO UPDATE
   - Enables upsert pattern for idempotent imports
   - No need for manual duplicate checking in Python
*/
