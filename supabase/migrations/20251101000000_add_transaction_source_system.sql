-- ============================================================================
-- Migration: Add source_system to transactions table
-- ============================================================================
-- Purpose: Prevent transaction ID collisions between Kajabi, PayPal, and Ticket Tailor
-- Impact: Allows same transaction ID from different sources
-- Date: 2025-11-01
-- ============================================================================

-- Step 1: Add source_system column (nullable initially)
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS source_system TEXT;

-- Step 2: Populate existing data based on payment_processor
-- This is a best-effort migration for existing data
UPDATE transactions
SET source_system = CASE
  WHEN payment_processor = 'Kajabi' THEN 'kajabi'
  WHEN payment_processor = 'PayPal' THEN 'paypal'
  WHEN payment_processor = 'Ticket Tailor' THEN 'ticket_tailor'
  WHEN payment_method = 'kajabi' THEN 'kajabi'
  WHEN payment_method = 'paypal' THEN 'paypal'
  WHEN payment_method = 'ticket_tailor' THEN 'ticket_tailor'
  ELSE 'kajabi' -- Default to kajabi for unknown
END
WHERE source_system IS NULL;

-- Step 3: Make column NOT NULL with default
ALTER TABLE transactions
ALTER COLUMN source_system SET DEFAULT 'kajabi',
ALTER COLUMN source_system SET NOT NULL;

-- Step 4: Add check constraint
ALTER TABLE transactions
ADD CONSTRAINT transactions_source_system_check
CHECK (source_system IN ('kajabi', 'paypal', 'ticket_tailor'));

-- Step 5: Drop old unique constraint on kajabi_transaction_id (if exists)
-- Note: This may not exist if it was never created as unique
DO $$
BEGIN
  ALTER TABLE transactions
  DROP CONSTRAINT IF EXISTS transactions_kajabi_transaction_id_key;
EXCEPTION
  WHEN undefined_object THEN
    -- Constraint doesn't exist, that's fine
    NULL;
END $$;

-- Also drop any unique index on just kajabi_transaction_id
DROP INDEX IF EXISTS transactions_kajabi_transaction_id_key;
DROP INDEX IF EXISTS ux_transactions_kajabi_transaction_id;

-- Step 6: Create composite unique index
-- This allows same transaction ID from different sources
CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_source_id
ON transactions(source_system, kajabi_transaction_id);

-- Step 7: Add index for filtering by source_system (performance)
CREATE INDEX IF NOT EXISTS idx_transactions_source_system
ON transactions(source_system);

-- Step 8: Add composite index for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_source_status
ON transactions(source_system, status)
WHERE status = 'completed';

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON COLUMN transactions.source_system IS
'Source system that created this transaction: kajabi, paypal, or ticket_tailor';

COMMENT ON INDEX ux_transactions_source_id IS
'Ensures uniqueness of transaction IDs within each source system, allows same ID from different sources';

-- ============================================================================
-- Verification Queries (run after migration)
-- ============================================================================

/*
-- Check that all transactions have source_system populated
SELECT COUNT(*) as total, COUNT(source_system) as with_source
FROM transactions;
-- Should return: total = with_source

-- Check distribution by source
SELECT source_system, COUNT(*) as count
FROM transactions
GROUP BY source_system
ORDER BY count DESC;

-- Verify unique constraint works
-- This should succeed (different sources, same ID):
INSERT INTO transactions (contact_id, kajabi_transaction_id, source_system, amount, status)
VALUES (
  (SELECT id FROM contacts LIMIT 1),
  'test_123',
  'kajabi',
  10.00,
  'completed'
);

INSERT INTO transactions (contact_id, kajabi_transaction_id, source_system, amount, status)
VALUES (
  (SELECT id FROM contacts LIMIT 1),
  'test_123',
  'paypal',
  10.00,
  'completed'
);

-- Clean up test data
DELETE FROM transactions WHERE kajabi_transaction_id = 'test_123';

-- This should fail (same source, same ID):
INSERT INTO transactions (contact_id, kajabi_transaction_id, source_system, amount, status)
VALUES (
  (SELECT id FROM contacts LIMIT 1),
  'duplicate_test',
  'kajabi',
  10.00,
  'completed'
);

-- Try to insert duplicate (should fail)
INSERT INTO transactions (contact_id, kajabi_transaction_id, source_system, amount, status)
VALUES (
  (SELECT id FROM contacts LIMIT 1),
  'duplicate_test',
  'kajabi',
  20.00,
  'completed'
);
-- Should error: duplicate key value violates unique constraint

-- Clean up
DELETE FROM transactions WHERE kajabi_transaction_id = 'duplicate_test';
*/

-- ============================================================================
-- Rollback Plan (if needed)
-- ============================================================================

/*
-- To rollback this migration:

-- Drop new indexes
DROP INDEX IF EXISTS ux_transactions_source_id;
DROP INDEX IF EXISTS idx_transactions_source_system;
DROP INDEX IF EXISTS idx_transactions_source_status;

-- Drop constraint
ALTER TABLE transactions
DROP CONSTRAINT IF EXISTS transactions_source_system_check;

-- Drop column
ALTER TABLE transactions
DROP COLUMN IF EXISTS source_system;

-- Recreate old unique constraint (if it existed)
-- CREATE UNIQUE INDEX IF NOT EXISTS transactions_kajabi_transaction_id_key
-- ON transactions(kajabi_transaction_id);
*/

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

-- Log completion
DO $$
BEGIN
  RAISE NOTICE '✅ Migration completed: Added source_system to transactions';
  RAISE NOTICE '   - Column added and populated';
  RAISE NOTICE '   - Unique constraint updated: (source_system, kajabi_transaction_id)';
  RAISE NOTICE '   - Indexes created for performance';
  RAISE NOTICE '⚠️  Next step: Update webhook handlers to set source_system';
END $$;
