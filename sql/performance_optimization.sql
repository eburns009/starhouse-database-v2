-- ============================================================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- Run these to get your database humming!
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PHASE 1: DIAGNOSTIC QUERIES (Run these first to see current state)
-- ----------------------------------------------------------------------------

-- Query 1: Enable performance tracking
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Query 2: View slowest queries
SELECT
  substring(query, 1, 80) as query_preview,
  calls,
  mean_exec_time::numeric(10,2) as avg_ms,
  max_exec_time::numeric(10,2) as max_ms,
  stddev_exec_time::numeric(10,2) as stddev_ms,
  (mean_exec_time * calls)::numeric(10,2) as total_time_ms
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
  AND query NOT LIKE '%pg_catalog%'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Query 3: Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as times_used,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Query 4: Find tables doing sequential scans (BAD!)
SELECT
  schemaname,
  tablename,
  seq_scan as sequential_scans,
  seq_tup_read as rows_read_sequentially,
  idx_scan as index_scans,
  CASE
    WHEN seq_scan > 0 THEN (seq_tup_read::float / seq_scan)::numeric(10,2)
    ELSE 0
  END as avg_rows_per_seq_scan
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND seq_scan > 0
ORDER BY seq_tup_read DESC;

-- Query 5: Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
  pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- Query 6: Check connection pool status
SELECT
  count(*) as total_connections,
  count(*) FILTER (WHERE state = 'active') as active,
  count(*) FILTER (WHERE state = 'idle') as idle,
  count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
FROM pg_stat_activity
WHERE datname = current_database();

-- ----------------------------------------------------------------------------
-- PHASE 2: ADD MISSING INDEXES (High Impact Performance Boost!)
-- ----------------------------------------------------------------------------

-- These indexes will make your queries MUCH faster
-- CONCURRENTLY means no downtime - database stays available

-- Optimize contact queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_updated_at_desc
  ON contacts(updated_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_total_spent_desc
  ON contacts(total_spent DESC NULLS LAST)
  WHERE total_spent > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_last_transaction
  ON contacts(last_transaction_date DESC NULLS LAST)
  WHERE last_transaction_date IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_transaction_count
  ON contacts(transaction_count DESC NULLS LAST)
  WHERE transaction_count > 0;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_source_email
  ON contacts(source_system, email);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_active_subscription
  ON contacts(has_active_subscription)
  WHERE has_active_subscription = TRUE;

-- Optimize transaction queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_contact_date
  ON transactions(contact_id, transaction_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_status_date
  ON transactions(status, transaction_date DESC)
  WHERE status IN ('completed', 'pending');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_date_amount
  ON transactions(transaction_date DESC, amount DESC)
  WHERE status = 'completed';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_type_status
  ON transactions(transaction_type, status);

-- Optimize subscription queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_contact_status
  ON subscriptions(contact_id, status)
  WHERE status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_status
  ON subscriptions(status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_next_billing
  ON subscriptions(next_billing_date)
  WHERE status = 'active' AND next_billing_date IS NOT NULL;

-- Optimize tag/product junction tables
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_tags_tag_contact
  ON contact_tags(tag_id, contact_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_products_product_contact
  ON contact_products(product_id, contact_id);

-- ----------------------------------------------------------------------------
-- PHASE 3: UPDATE STATISTICS (Helps query planner make better decisions)
-- ----------------------------------------------------------------------------

-- Update statistics for all tables
ANALYZE contacts;
ANALYZE transactions;
ANALYZE subscriptions;
ANALYZE products;
ANALYZE tags;
ANALYZE contact_tags;
ANALYZE contact_products;

-- ----------------------------------------------------------------------------
-- PHASE 4: CHECK FOR DATA INTEGRITY ISSUES
-- ----------------------------------------------------------------------------

-- Check for orphaned transactions (transactions without contacts)
SELECT
  'Orphaned Transactions' as issue_type,
  COUNT(*) as count
FROM transactions
WHERE contact_id NOT IN (SELECT id FROM contacts);

-- Check for orphaned subscriptions
SELECT
  'Orphaned Subscriptions' as issue_type,
  COUNT(*) as count
FROM subscriptions
WHERE contact_id NOT IN (SELECT id FROM contacts);

-- Check for orphaned contact_tags
SELECT
  'Orphaned Contact Tags' as issue_type,
  COUNT(*) as count
FROM contact_tags
WHERE contact_id NOT IN (SELECT id FROM contacts);

-- Check for contacts with inconsistent transaction totals
SELECT
  'Inconsistent Contact Totals' as issue_type,
  COUNT(*) as count
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

-- ----------------------------------------------------------------------------
-- PHASE 5: CREATE PERFORMANCE MONITORING VIEW
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_system_health AS
SELECT
  -- Connection metrics
  (SELECT count(*) FROM pg_stat_activity) as total_connections,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') as idle_in_transaction,

  -- Business metrics
  (SELECT count(*) FROM contacts) as total_contacts,
  (SELECT count(*) FROM contacts WHERE transaction_count > 0) as paying_customers,
  (SELECT count(*) FROM transactions WHERE status = 'completed') as completed_transactions,
  (SELECT COALESCE(SUM(amount), 0)::numeric(10,2) FROM transactions WHERE status = 'completed') as total_revenue,
  (SELECT count(*) FROM subscriptions WHERE status = 'active') as active_subscriptions,

  -- Performance metrics
  (SELECT COALESCE(avg(mean_exec_time), 0)::numeric(10,2)
   FROM pg_stat_statements
   WHERE query NOT LIKE '%pg_stat%') as avg_query_time_ms,

  (SELECT COALESCE(max(mean_exec_time), 0)::numeric(10,2)
   FROM pg_stat_statements
   WHERE query NOT LIKE '%pg_stat%') as max_avg_query_time_ms,

  -- Database size
  (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size,

  -- Timestamp
  NOW() as snapshot_time;

-- Query the health view anytime:
-- SELECT * FROM v_system_health;

-- ----------------------------------------------------------------------------
-- PHASE 6: CREATE USEFUL PERFORMANCE VIEWS
-- ----------------------------------------------------------------------------

-- View: Top 20 slowest queries
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT
  substring(query, 1, 100) as query_preview,
  calls,
  mean_exec_time::numeric(10,2) as avg_ms,
  max_exec_time::numeric(10,2) as max_ms,
  (mean_exec_time * calls)::numeric(10,2) as total_time_ms,
  rows::bigint as rows_returned
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
  AND query NOT LIKE '%pg_catalog%'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- View: Index efficiency
CREATE OR REPLACE VIEW v_index_usage AS
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  CASE
    WHEN idx_scan = 0 THEN 'UNUSED INDEX - Consider dropping'
    WHEN idx_scan < 100 THEN 'Low usage'
    ELSE 'Good usage'
  END as usage_assessment
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- View: Table bloat and maintenance needs
CREATE OR REPLACE VIEW v_table_maintenance AS
SELECT
  schemaname,
  tablename,
  n_live_tup as live_rows,
  n_dead_tup as dead_rows,
  CASE
    WHEN n_live_tup > 0
    THEN (n_dead_tup::float / n_live_tup * 100)::numeric(5,2)
    ELSE 0
  END as dead_row_percent,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze,
  CASE
    WHEN n_dead_tup > 1000 AND (n_dead_tup::float / NULLIF(n_live_tup, 0) > 0.1)
    THEN 'Needs VACUUM'
    WHEN last_analyze < NOW() - INTERVAL '7 days'
    THEN 'Needs ANALYZE'
    ELSE 'OK'
  END as maintenance_recommendation
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC;

-- ----------------------------------------------------------------------------
-- QUICK PERFORMANCE CHECK SCRIPT
-- Run this anytime to see system health
-- ----------------------------------------------------------------------------

-- One-liner performance check
SELECT
  'System Health' as metric_category,
  json_build_object(
    'total_contacts', (SELECT count(*) FROM contacts),
    'paying_customers', (SELECT count(*) FROM contacts WHERE transaction_count > 0),
    'total_revenue', (SELECT COALESCE(SUM(amount), 0)::numeric(10,2) FROM transactions WHERE status = 'completed'),
    'active_subscriptions', (SELECT count(*) FROM subscriptions WHERE status = 'active'),
    'avg_query_time_ms', (SELECT COALESCE(avg(mean_exec_time), 0)::numeric(10,2) FROM pg_stat_statements WHERE query NOT LIKE '%pg_stat%'),
    'active_connections', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active'),
    'database_size', (SELECT pg_size_pretty(pg_database_size(current_database())))
  ) as metrics;

-- ============================================================================
-- DONE! Your database should be much faster now.
--
-- Next steps:
-- 1. Run "SELECT * FROM v_system_health;" to see overall health
-- 2. Run "SELECT * FROM v_slow_queries;" to find remaining slow queries
-- 3. Run "SELECT * FROM v_index_usage;" to verify indexes are being used
-- 4. Monitor performance over next few days
-- ============================================================================
