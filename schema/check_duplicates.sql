-- ============================================================================
-- CHECK FOR DUPLICATES - Quick Status Check
-- ============================================================================

-- Quick duplicate count
SELECT
  'transactions' as table_type,
  COUNT(*) as total_records,
  COUNT(DISTINCT kajabi_transaction_id) as unique_kajabi_ids,
  COUNT(*) - COUNT(DISTINCT kajabi_transaction_id) as duplicate_count
FROM transactions
WHERE kajabi_transaction_id IS NOT NULL

UNION ALL

SELECT
  'subscriptions' as table_type,
  COUNT(*) as total_records,
  COUNT(DISTINCT kajabi_subscription_id) as unique_kajabi_ids,
  COUNT(*) - COUNT(DISTINCT kajabi_subscription_id) as duplicate_count
FROM subscriptions
WHERE kajabi_subscription_id IS NOT NULL;

-- ============================================================================
-- If duplicates found, show details
-- ============================================================================

-- Show duplicate transactions (if any)
SELECT
  'DUPLICATE TRANSACTION' as issue,
  kajabi_transaction_id,
  COUNT(*) as count,
  STRING_AGG(id::text, ', ') as transaction_ids,
  STRING_AGG(amount::text, ', ') as amounts
FROM transactions
WHERE kajabi_transaction_id IS NOT NULL
GROUP BY kajabi_transaction_id
HAVING COUNT(*) > 1;

-- Show duplicate subscriptions (if any)
SELECT
  'DUPLICATE SUBSCRIPTION' as issue,
  kajabi_subscription_id,
  COUNT(*) as count,
  STRING_AGG(id::text, ', ') as subscription_ids,
  STRING_AGG(status, ', ') as statuses
FROM subscriptions
WHERE kajabi_subscription_id IS NOT NULL
GROUP BY kajabi_subscription_id
HAVING COUNT(*) > 1;
