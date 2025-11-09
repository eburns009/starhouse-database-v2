-- ============================================================================
-- STEP 1: DIAGNOSTICS - Run this first to see current state
-- ============================================================================
-- Copy and paste this entire section into Supabase SQL Editor

-- Enable performance tracking
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slowest queries (shows what's currently slow)
SELECT
  substring(query, 1, 80) as query_preview,
  calls,
  mean_exec_time::numeric(10,2) as avg_ms,
  max_exec_time::numeric(10,2) as max_ms,
  (mean_exec_time * calls)::numeric(10,2) as total_time_ms
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
  AND query NOT LIKE '%pg_catalog%'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Check which indexes exist and are being used
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as times_used,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find tables doing sequential scans (this is BAD for performance!)
SELECT
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

-- Check table sizes
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS total_size,
  pg_size_pretty(pg_relation_size('public.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;

-- Check connection pool status
SELECT
  count(*) as total_connections,
  count(*) FILTER (WHERE state = 'active') as active,
  count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity
WHERE datname = current_database();
