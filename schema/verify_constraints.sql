-- ============================================================================
-- VERIFY: Unique Constraints and Check for Duplicates
-- ============================================================================

-- Check constraints on TRANSACTIONS table
SELECT
  'transactions' as table_name,
  conname AS constraint_name,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'transactions'::regclass
  AND contype = 'u'
ORDER BY conname;

-- Check constraints on SUBSCRIPTIONS table
SELECT
  'subscriptions' as table_name,
  conname AS constraint_name,
  pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'subscriptions'::regclass
  AND contype = 'u'
ORDER BY conname;

-- ============================================================================
-- Check for any existing duplicates in TRANSACTIONS
-- ============================================================================

SELECT
  'DUPLICATE TRANSACTIONS' as issue_type,
  kajabi_transaction_id,
  COUNT(*) as duplicate_count,
  ARRAY_AGG(id) as transaction_ids,
  ARRAY_AGG(contact_id) as contact_ids,
  ARRAY_AGG(amount) as amounts,
  ARRAY_AGG(created_at ORDER BY created_at) as created_dates
FROM transactions
WHERE kajabi_transaction_id IS NOT NULL
GROUP BY kajabi_transaction_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- ============================================================================
-- Check for any existing duplicates in SUBSCRIPTIONS
-- ============================================================================

SELECT
  'DUPLICATE SUBSCRIPTIONS' as issue_type,
  kajabi_subscription_id,
  COUNT(*) as duplicate_count,
  ARRAY_AGG(id) as subscription_ids,
  ARRAY_AGG(contact_id) as contact_ids,
  ARRAY_AGG(status) as statuses,
  ARRAY_AGG(created_at ORDER BY created_at) as created_dates
FROM subscriptions
WHERE kajabi_subscription_id IS NOT NULL
GROUP BY kajabi_subscription_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- ============================================================================
-- Summary Statistics
-- ============================================================================

SELECT
  'SUMMARY' as report_type,
  (SELECT COUNT(*) FROM transactions WHERE kajabi_transaction_id IS NOT NULL) as total_transactions_with_kajabi_id,
  (SELECT COUNT(*) FROM subscriptions WHERE kajabi_subscription_id IS NOT NULL) as total_subscriptions_with_kajabi_id,
  (SELECT COUNT(DISTINCT kajabi_transaction_id) FROM transactions WHERE kajabi_transaction_id IS NOT NULL) as unique_transaction_ids,
  (SELECT COUNT(DISTINCT kajabi_subscription_id) FROM subscriptions WHERE kajabi_subscription_id IS NOT NULL) as unique_subscription_ids;
