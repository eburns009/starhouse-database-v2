-- ============================================================================
-- STEP 5: CREATE MONITORING VIEWS - Query these anytime for health checks
-- ============================================================================
-- Copy and paste this entire section into Supabase SQL Editor

-- System Health View (run: SELECT * FROM v_system_health;)
CREATE OR REPLACE VIEW v_system_health AS
SELECT
  (SELECT count(*) FROM pg_stat_activity) as total_connections,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
  (SELECT count(*) FROM contacts) as total_contacts,
  (SELECT count(*) FROM contacts WHERE transaction_count > 0) as paying_customers,
  (SELECT count(*) FROM transactions WHERE status = 'completed') as completed_transactions,
  (SELECT COALESCE(SUM(amount), 0)::numeric(10,2) FROM transactions WHERE status = 'completed') as total_revenue,
  (SELECT count(*) FROM subscriptions WHERE status = 'active') as active_subscriptions,
  (SELECT COALESCE(avg(mean_exec_time), 0)::numeric(10,2) FROM pg_stat_statements WHERE query NOT LIKE '%pg_stat%') as avg_query_time_ms,
  (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size,
  NOW() as snapshot_time;

-- Slow Queries View (run: SELECT * FROM v_slow_queries;)
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT
  substring(query, 1, 100) as query_preview,
  calls,
  mean_exec_time::numeric(10,2) as avg_ms,
  max_exec_time::numeric(10,2) as max_ms,
  (mean_exec_time * calls)::numeric(10,2) as total_time_ms
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
  AND query NOT LIKE '%pg_catalog%'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Index Usage View (run: SELECT * FROM v_index_usage;)
CREATE OR REPLACE VIEW v_index_usage AS
SELECT
  tablename,
  indexname,
  idx_scan as scans,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  CASE
    WHEN idx_scan = 0 THEN 'UNUSED - Consider dropping'
    WHEN idx_scan < 100 THEN 'Low usage'
    ELSE 'Good usage'
  END as usage_assessment
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
