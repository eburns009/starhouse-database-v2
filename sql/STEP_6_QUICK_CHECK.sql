-- ============================================================================
-- STEP 6: QUICK HEALTH CHECK - Run this anytime!
-- ============================================================================
-- Copy and paste this into Supabase SQL Editor to see everything at once

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
