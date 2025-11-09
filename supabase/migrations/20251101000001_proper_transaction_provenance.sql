-- ============================================================================
-- Migration: Proper Transaction Provenance Model
-- ============================================================================
-- Purpose: Replace kajabi_transaction_id overloading with clean provenance
-- Impact: Eliminates naming confusion, prevents hidden collisions, enables
--         deterministic reporting
-- Date: 2025-11-01
-- Expert Review: Implements feedback on provenance model
-- ============================================================================

-- Step 1: Add proper provenance columns
ALTER TABLE transactions
  ADD COLUMN IF NOT EXISTS source_system TEXT,
  ADD COLUMN IF NOT EXISTS external_transaction_id TEXT,
  ADD COLUMN IF NOT EXISTS external_order_id TEXT,
  ADD COLUMN IF NOT EXISTS raw_source JSONB;

-- Step 2: Backfill source_system from existing data
-- No default! Force explicit classification
UPDATE transactions
SET source_system = CASE
  WHEN payment_processor ILIKE '%paypal%' THEN 'paypal'
  WHEN payment_processor ILIKE '%ticket%' THEN 'ticket_tailor'
  WHEN payment_processor ILIKE '%kajabi%' THEN 'kajabi'
  WHEN payment_method = 'paypal' THEN 'paypal'
  WHEN payment_method = 'ticket_tailor' THEN 'ticket_tailor'
  WHEN payment_method = 'kajabi' THEN 'kajabi'
  -- Fallback to kajabi for existing data only
  ELSE 'kajabi'
END
WHERE source_system IS NULL;

-- Step 3: Backfill external_transaction_id from kajabi_transaction_id
-- This is the actual provider's transaction ID
UPDATE transactions
SET external_transaction_id = COALESCE(
  external_transaction_id,
  kajabi_transaction_id
)
WHERE external_transaction_id IS NULL;

-- Step 4: Backfill external_order_id from order_number
UPDATE transactions
SET external_order_id = COALESCE(
  external_order_id,
  NULLIF(order_number, '')
)
WHERE external_order_id IS NULL;

-- Step 5: Make source_system required (after backfill verified)
-- No default! Handlers MUST set this explicitly
ALTER TABLE transactions
  ALTER COLUMN source_system SET NOT NULL;

-- Step 6: Add check constraint with consistent source literals
ALTER TABLE transactions
  ADD CONSTRAINT transactions_source_system_check
  CHECK (source_system IN ('kajabi', 'paypal', 'ticket_tailor'));

-- Step 7: Drop old unique constraint on kajabi_transaction_id (if exists)
DO $$
BEGIN
  ALTER TABLE transactions
    DROP CONSTRAINT IF EXISTS transactions_kajabi_transaction_id_key;
EXCEPTION
  WHEN undefined_object THEN NULL;
END $$;

DROP INDEX IF EXISTS transactions_kajabi_transaction_id_key;
DROP INDEX IF EXISTS ux_transactions_kajabi_transaction_id;

-- Step 8: Create proper unique constraint on provenance
-- This is the canonical idempotency guard
-- Partial index to allow NULL during migration/cutover
CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_source_external
  ON transactions (source_system, external_transaction_id)
  WHERE external_transaction_id IS NOT NULL;

-- Step 9: Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_source_system
  ON transactions (source_system)
  WHERE status = 'completed';

CREATE INDEX IF NOT EXISTS idx_transactions_source_date
  ON transactions (source_system, transaction_date DESC)
  WHERE status = 'completed';

-- Step 10: Create index for duplicate detection
CREATE INDEX IF NOT EXISTS idx_transactions_contact_amount_date
  ON transactions (contact_id, amount, transaction_date)
  WHERE status = 'completed';

-- ============================================================================
-- Views for Monitoring & Reporting
-- ============================================================================

-- View: Potential duplicate transactions (improved with provenance)
CREATE OR REPLACE VIEW v_potential_duplicate_transactions AS
WITH pairs AS (
  SELECT
    t1.id AS transaction_1_id,
    t2.id AS transaction_2_id,
    c.email,
    c.first_name,
    c.last_name,
    t1.source_system AS source_1,
    t2.source_system AS source_2,
    t1.external_transaction_id AS external_id_1,
    t2.external_transaction_id AS external_id_2,
    t1.external_order_id AS order_id_1,
    t2.external_order_id AS order_id_2,
    t1.amount,
    t1.currency,
    t1.transaction_date AS date_1,
    t2.transaction_date AS date_2,
    ABS(EXTRACT(EPOCH FROM (t1.transaction_date - t2.transaction_date))) AS seconds_apart
  FROM transactions t1
  JOIN transactions t2 ON
    t1.contact_id = t2.contact_id
    AND t1.id < t2.id
    AND t1.amount = t2.amount
    AND t1.currency = t2.currency
    AND t1.transaction_date::date = t2.transaction_date::date
  JOIN contacts c ON t1.contact_id = c.id
  WHERE
    t1.status = 'completed'
    AND t2.status = 'completed'
)
SELECT
  *,
  CASE
    -- Same source, same external ID = bug in handler (shouldn't happen with unique constraint)
    WHEN source_1 = source_2 AND external_id_1 = external_id_2 THEN 'exact_duplicate'
    -- Same source, different IDs within 5 minutes = likely duplicate
    WHEN source_1 = source_2 AND seconds_apart < 300 THEN 'same_source_duplicate'
    -- Different sources, both have IDs, within 1 hour = possible double count
    WHEN source_1 <> source_2 AND external_id_1 IS NOT NULL AND external_id_2 IS NOT NULL AND seconds_apart < 3600 THEN 'cross_source_duplicate'
    -- One or both missing external IDs = manual review needed
    WHEN external_id_1 IS NULL OR external_id_2 IS NULL THEN 'missing_provenance'
    ELSE 'unlikely_duplicate'
  END AS duplicate_likelihood
FROM pairs
WHERE seconds_apart < 3600;

COMMENT ON VIEW v_potential_duplicate_transactions IS
'Detects potential duplicate transactions using proper provenance fields. Uses external_transaction_id for accurate matching.';

-- View: Revenue by source (canonical)
CREATE OR REPLACE VIEW v_revenue_by_source AS
SELECT
  source_system,
  COUNT(*) as transaction_count,
  COUNT(DISTINCT contact_id) as unique_customers,
  SUM(amount) FILTER (WHERE transaction_type != 'refund') as gross_revenue,
  SUM(amount) FILTER (WHERE transaction_type = 'refund') as refunds,
  SUM(amount) FILTER (WHERE transaction_type != 'refund') +
    SUM(amount) FILTER (WHERE transaction_type = 'refund') as net_revenue,
  AVG(amount) FILTER (WHERE transaction_type != 'refund') as avg_transaction,
  MIN(transaction_date) as first_transaction,
  MAX(transaction_date) as last_transaction
FROM transactions
WHERE status = 'completed'
GROUP BY source_system
ORDER BY net_revenue DESC;

COMMENT ON VIEW v_revenue_by_source IS
'Canonical revenue report by source system. Uses proper source_system field for deterministic results.';

-- View: Transactions missing provenance (data quality check)
CREATE OR REPLACE VIEW v_transactions_missing_provenance AS
SELECT
  id,
  contact_id,
  source_system,
  external_transaction_id,
  external_order_id,
  amount,
  transaction_date,
  created_at,
  CASE
    WHEN external_transaction_id IS NULL THEN 'missing_external_transaction_id'
    WHEN source_system IS NULL THEN 'missing_source_system'
    ELSE 'unknown_issue'
  END as issue
FROM transactions
WHERE
  external_transaction_id IS NULL
  OR source_system IS NULL
ORDER BY created_at DESC;

COMMENT ON VIEW v_transactions_missing_provenance IS
'Data quality check: Transactions missing proper provenance fields. Should be zero in production.';

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Check for near-duplicate transactions (Kajabi → PayPal merge)
CREATE OR REPLACE FUNCTION find_probable_duplicate_transaction(
  p_contact_id UUID,
  p_amount NUMERIC,
  p_transaction_date TIMESTAMPTZ,
  p_source_system TEXT,
  p_window_minutes INTEGER DEFAULT 10
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  v_existing_id UUID;
BEGIN
  -- Find a transaction from a DIFFERENT source with same contact, amount, and within time window
  SELECT id INTO v_existing_id
  FROM transactions
  WHERE
    contact_id = p_contact_id
    AND amount = p_amount
    AND source_system <> p_source_system
    AND status = 'completed'
    AND ABS(EXTRACT(EPOCH FROM (transaction_date - p_transaction_date))) < (p_window_minutes * 60)
  ORDER BY transaction_date
  LIMIT 1;

  RETURN v_existing_id;
END;
$$;

COMMENT ON FUNCTION find_probable_duplicate_transaction IS
'Finds probable duplicate transaction from different source within time window. Used by PayPal handler to merge with Kajabi transactions.';

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN transactions.source_system IS
'Source system that created this transaction: kajabi | paypal | ticket_tailor. REQUIRED, no default.';

COMMENT ON COLUMN transactions.external_transaction_id IS
'Provider-specific transaction ID (e.g., Kajabi txn_123, PayPal PAYID-ABC, Ticket Tailor booking_xyz). Used for idempotency.';

COMMENT ON COLUMN transactions.external_order_id IS
'Provider-specific order/reference number. Optional, for cross-referencing.';

COMMENT ON COLUMN transactions.raw_source IS
'Redacted raw webhook payload (JSONB). For debugging and audit. PII removed, truncated to 16KB.';

COMMENT ON COLUMN transactions.kajabi_transaction_id IS
'DEPRECATED: Legacy field overloaded across all sources. Use external_transaction_id instead. Will be removed in future migration.';

-- ============================================================================
-- Verification Queries (run after migration)
-- ============================================================================

/*
-- 1. Verify all transactions have source_system
SELECT COUNT(*) as total, COUNT(source_system) as with_source
FROM transactions;
-- Should return: total = with_source

-- 2. Verify all transactions have external_transaction_id
SELECT COUNT(*) as total, COUNT(external_transaction_id) as with_external_id
FROM transactions;
-- Should return: total = with_external_id

-- 3. Check distribution by source
SELECT source_system, COUNT(*) as count, SUM(amount) as revenue
FROM transactions
WHERE status = 'completed' AND transaction_type != 'refund'
GROUP BY source_system
ORDER BY revenue DESC;

-- 4. Find any duplicates
SELECT * FROM v_potential_duplicate_transactions
WHERE duplicate_likelihood IN ('exact_duplicate', 'same_source_duplicate')
LIMIT 10;
-- Should return 0 rows

-- 5. Check for missing provenance
SELECT * FROM v_transactions_missing_provenance LIMIT 10;
-- Should return 0 rows

-- 6. Revenue by source (canonical report)
SELECT * FROM v_revenue_by_source;
*/

-- ============================================================================
-- Rollback Plan (if needed)
-- ============================================================================

/*
-- To rollback this migration:

DROP VIEW IF EXISTS v_potential_duplicate_transactions;
DROP VIEW IF EXISTS v_revenue_by_source;
DROP VIEW IF EXISTS v_transactions_missing_provenance;
DROP FUNCTION IF EXISTS find_probable_duplicate_transaction;

DROP INDEX IF EXISTS ux_transactions_source_external;
DROP INDEX IF EXISTS idx_transactions_source_system;
DROP INDEX IF EXISTS idx_transactions_source_date;
DROP INDEX IF EXISTS idx_transactions_contact_amount_date;

ALTER TABLE transactions
  DROP CONSTRAINT IF EXISTS transactions_source_system_check;

ALTER TABLE transactions
  DROP COLUMN IF EXISTS source_system,
  DROP COLUMN IF EXISTS external_transaction_id,
  DROP COLUMN IF EXISTS external_order_id,
  DROP COLUMN IF EXISTS raw_source;
*/

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '✅ Migration completed: Proper transaction provenance model';
  RAISE NOTICE '   - Added: source_system (required, no default)';
  RAISE NOTICE '   - Added: external_transaction_id (provider txn ID)';
  RAISE NOTICE '   - Added: external_order_id (optional)';
  RAISE NOTICE '   - Added: raw_source (JSONB for debugging)';
  RAISE NOTICE '   - Unique constraint: (source_system, external_transaction_id)';
  RAISE NOTICE '   - Views created: v_potential_duplicate_transactions, v_revenue_by_source';
  RAISE NOTICE '   - Helper function: find_probable_duplicate_transaction()';
  RAISE NOTICE '   ';
  RAISE NOTICE '⚠️  NEXT STEPS:';
  RAISE NOTICE '   1. Update webhook handlers to use new fields';
  RAISE NOTICE '   2. Test idempotency with all three sources';
  RAISE NOTICE '   3. Run verification queries above';
  RAISE NOTICE '   4. Monitor v_potential_duplicate_transactions weekly';
  RAISE NOTICE '   5. Deprecate kajabi_transaction_id after migration complete';
END $$;
