-- ============================================================================
-- STEP 4: DATA INTEGRITY CHECKS - Find any data issues
-- ============================================================================
-- Copy and paste this entire section into Supabase SQL Editor

-- Check for orphaned transactions (transactions without contacts)
SELECT 'Orphaned Transactions' as issue_type, COUNT(*) as count
FROM transactions
WHERE contact_id NOT IN (SELECT id FROM contacts);

-- Check for orphaned subscriptions
SELECT 'Orphaned Subscriptions' as issue_type, COUNT(*) as count
FROM subscriptions
WHERE contact_id NOT IN (SELECT id FROM contacts);

-- Check for orphaned contact_tags
SELECT 'Orphaned Contact Tags' as issue_type, COUNT(*) as count
FROM contact_tags
WHERE contact_id NOT IN (SELECT id FROM contacts);

-- Check for contacts with inconsistent transaction totals
SELECT 'Inconsistent Contact Totals' as issue_type, COUNT(*) as count
FROM (
  SELECT
    c.id,
    c.email,
    c.total_spent as stored_total,
    COALESCE(SUM(t.amount), 0) as calculated_total,
    c.transaction_count as stored_count,
    COUNT(t.id) as calculated_count
  FROM contacts c
  LEFT JOIN transactions t ON c.id = t.contact_id AND t.status = 'completed'
  WHERE c.total_spent IS NOT NULL OR c.transaction_count IS NOT NULL
  GROUP BY c.id, c.email, c.total_spent, c.transaction_count
  HAVING
    ABS(COALESCE(c.total_spent, 0) - COALESCE(SUM(t.amount), 0)) > 0.01
    OR COALESCE(c.transaction_count, 0) != COUNT(t.id)
) inconsistent;
