-- ============================================================================
-- FIX: Add Missing Unique Constraints for Data Integrity
-- ============================================================================
-- Purpose: Prevent duplicate transactions and subscriptions from multiple webhooks
-- Date: 2025-10-31
-- Priority: CRITICAL
-- ============================================================================

-- STEP 1: Check for existing duplicates before adding constraints
-- ============================================================================

-- Check for duplicate transactions
DO $$
DECLARE
  duplicate_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO duplicate_count
  FROM (
    SELECT kajabi_transaction_id
    FROM transactions
    WHERE kajabi_transaction_id IS NOT NULL
    GROUP BY kajabi_transaction_id
    HAVING COUNT(*) > 1
  ) duplicates;

  IF duplicate_count > 0 THEN
    RAISE WARNING 'Found % duplicate transaction IDs - manual cleanup required before adding constraint', duplicate_count;
  ELSE
    RAISE NOTICE 'No duplicate transaction IDs found - safe to add constraint';
  END IF;
END $$;

-- Check for duplicate subscriptions
DO $$
DECLARE
  duplicate_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO duplicate_count
  FROM (
    SELECT kajabi_subscription_id
    FROM subscriptions
    WHERE kajabi_subscription_id IS NOT NULL
    GROUP BY kajabi_subscription_id
    HAVING COUNT(*) > 1
  ) duplicates;

  IF duplicate_count > 0 THEN
    RAISE WARNING 'Found % duplicate subscription IDs - manual cleanup required before adding constraint', duplicate_count;
  ELSE
    RAISE NOTICE 'No duplicate subscription IDs found - safe to add constraint';
  END IF;
END $$;

-- ============================================================================
-- STEP 2: Add unique constraints (only if no duplicates found)
-- ============================================================================

-- Add unique constraint to transactions.kajabi_transaction_id
-- This prevents PayPal + Kajabi from creating duplicate transaction records
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'ux_transactions_kajabi_id'
    AND conrelid = 'transactions'::regclass
  ) THEN
    ALTER TABLE transactions
      ADD CONSTRAINT ux_transactions_kajabi_id
      UNIQUE (kajabi_transaction_id);
    RAISE NOTICE '✅ Added unique constraint: ux_transactions_kajabi_id';
  ELSE
    RAISE NOTICE 'ℹ️  Constraint ux_transactions_kajabi_id already exists';
  END IF;
END $$;

COMMENT ON CONSTRAINT ux_transactions_kajabi_id ON transactions IS
  'Prevents duplicate transactions when multiple webhooks (PayPal + Kajabi) send same transaction';

-- Add unique constraint to subscriptions.kajabi_subscription_id
-- This prevents duplicate subscription records from multiple sources
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'ux_subscriptions_kajabi_id'
    AND conrelid = 'subscriptions'::regclass
  ) THEN
    ALTER TABLE subscriptions
      ADD CONSTRAINT ux_subscriptions_kajabi_id
      UNIQUE (kajabi_subscription_id);
    RAISE NOTICE '✅ Added unique constraint: ux_subscriptions_kajabi_id';
  ELSE
    RAISE NOTICE 'ℹ️  Constraint ux_subscriptions_kajabi_id already exists';
  END IF;
END $$;

COMMENT ON CONSTRAINT ux_subscriptions_kajabi_id ON subscriptions IS
  'Prevents duplicate subscriptions when multiple webhooks send same subscription';

-- ============================================================================
-- STEP 3: Verify constraints were added
-- ============================================================================

-- List all unique constraints on transactions
SELECT
  conname AS constraint_name,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'transactions'::regclass
  AND contype = 'u';

-- List all unique constraints on subscriptions
SELECT
  conname AS constraint_name,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'subscriptions'::regclass
  AND contype = 'u';

-- ============================================================================
-- OPTIONAL: Query to find duplicates if warnings appeared above
-- ============================================================================

-- Uncomment these if you need to find and clean up duplicates:

-- SELECT
--   kajabi_transaction_id,
--   COUNT(*) as count,
--   ARRAY_AGG(id) as transaction_ids,
--   ARRAY_AGG(contact_id) as contact_ids,
--   ARRAY_AGG(amount) as amounts,
--   ARRAY_AGG(created_at ORDER BY created_at) as created_dates
-- FROM transactions
-- WHERE kajabi_transaction_id IS NOT NULL
-- GROUP BY kajabi_transaction_id
-- HAVING COUNT(*) > 1
-- ORDER BY count DESC;

-- SELECT
--   kajabi_subscription_id,
--   COUNT(*) as count,
--   ARRAY_AGG(id) as subscription_ids,
--   ARRAY_AGG(contact_id) as contact_ids,
--   ARRAY_AGG(status) as statuses,
--   ARRAY_AGG(created_at ORDER BY created_at) as created_dates
-- FROM subscriptions
-- WHERE kajabi_subscription_id IS NOT NULL
-- GROUP BY kajabi_subscription_id
-- HAVING COUNT(*) > 1
-- ORDER BY count DESC;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '✅ Unique constraints added successfully!';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Verify webhook UPSERTs now work correctly';
  RAISE NOTICE '2. Test by sending duplicate webhook events';
  RAISE NOTICE '3. Confirm only one record is created/updated';
  RAISE NOTICE '';
END $$;
