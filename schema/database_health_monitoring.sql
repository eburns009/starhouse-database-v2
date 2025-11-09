-- ============================================================================
-- DATABASE HEALTH MONITORING - FAANG Production Standards
-- ============================================================================
-- Purpose: Real-time health checks, alerts, and metrics for production
-- Priority: P0 - Critical for observability
-- ============================================================================

-- ============================================================================
-- Health Check View - Overall Database Health
-- ============================================================================

CREATE OR REPLACE VIEW v_database_health AS
WITH contact_stats AS (
    SELECT
        COUNT(*) as total_contacts,
        COUNT(*) FILTER (WHERE created_at > now() - INTERVAL '24 hours') as contacts_added_today,
        COUNT(*) FILTER (WHERE updated_at > now() - INTERVAL '24 hours') as contacts_updated_today
    FROM contacts
),
duplicate_check AS (
    SELECT COUNT(*) as name_duplicates
    FROM (
        SELECT LOWER(TRIM(first_name)), LOWER(TRIM(last_name))
        FROM contacts
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
          AND first_name <> '' AND last_name <> ''
        GROUP BY LOWER(TRIM(first_name)), LOWER(TRIM(last_name))
        HAVING COUNT(*) > 1
    ) dupes
),
orphaned_data AS (
    SELECT
        (SELECT COUNT(*) FROM transactions WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE contacts.id = transactions.contact_id)) as orphaned_transactions,
        (SELECT COUNT(*) FROM subscriptions WHERE NOT EXISTS (SELECT 1 FROM contacts WHERE contacts.id = subscriptions.contact_id)) as orphaned_subscriptions
),
transaction_stats AS (
    SELECT
        COUNT(*) as total_transactions,
        COUNT(*) FILTER (WHERE transaction_date > CURRENT_DATE - INTERVAL '7 days') as transactions_last_7_days,
        SUM(amount) FILTER (WHERE transaction_date > CURRENT_DATE - INTERVAL '30 days') as revenue_last_30_days
    FROM transactions
    WHERE status = 'completed'
),
webhook_health AS (
    SELECT
        COUNT(*) FILTER (WHERE received_at > now() - INTERVAL '24 hours') as webhooks_last_24h,
        COUNT(*) FILTER (WHERE status = 'failed' AND received_at > now() - INTERVAL '24 hours') as failed_webhooks_24h,
        COUNT(*) FILTER (WHERE signature_valid = false AND received_at > now() - INTERVAL '24 hours') as invalid_signatures_24h,
        AVG(processing_duration_ms) FILTER (WHERE received_at > now() - INTERVAL '1 hour') as avg_processing_ms_1h
    FROM webhook_events
)
SELECT
    -- Overall Health Status
    CASE
        WHEN od.orphaned_transactions > 0 OR od.orphaned_subscriptions > 0 THEN 'CRITICAL'
        WHEN dc.name_duplicates > 10 THEN 'WARNING'
        WHEN wh.failed_webhooks_24h::float / NULLIF(wh.webhooks_last_24h, 0) > 0.05 THEN 'WARNING'
        WHEN wh.invalid_signatures_24h > 5 THEN 'WARNING'
        ELSE 'HEALTHY'
    END as overall_status,

    -- Contact Metrics
    cs.total_contacts,
    cs.contacts_added_today,
    cs.contacts_updated_today,

    -- Data Quality
    dc.name_duplicates,
    od.orphaned_transactions,
    od.orphaned_subscriptions,

    -- Transaction Metrics
    ts.total_transactions,
    ts.transactions_last_7_days,
    ROUND(ts.revenue_last_30_days, 2) as revenue_last_30_days,

    -- Webhook Metrics
    wh.webhooks_last_24h,
    wh.failed_webhooks_24h,
    wh.invalid_signatures_24h,
    ROUND(wh.avg_processing_ms_1h, 2) as avg_webhook_processing_ms,

    -- Alerts
    ARRAY_REMOVE(ARRAY[
        CASE WHEN od.orphaned_transactions > 0 THEN 'ORPHANED_TRANSACTIONS: ' || od.orphaned_transactions END,
        CASE WHEN od.orphaned_subscriptions > 0 THEN 'ORPHANED_SUBSCRIPTIONS: ' || od.orphaned_subscriptions END,
        CASE WHEN dc.name_duplicates > 10 THEN 'HIGH_DUPLICATE_COUNT: ' || dc.name_duplicates END,
        CASE WHEN wh.failed_webhooks_24h::float / NULLIF(wh.webhooks_last_24h, 0) > 0.05
             THEN 'HIGH_WEBHOOK_FAILURE_RATE: ' || ROUND((wh.failed_webhooks_24h::float / wh.webhooks_last_24h * 100)::numeric, 2) || '%' END,
        CASE WHEN wh.invalid_signatures_24h > 5 THEN 'SECURITY_ALERT: ' || wh.invalid_signatures_24h || ' invalid signatures' END
    ], NULL) as active_alerts,

    -- Timestamp
    now() as checked_at

FROM contact_stats cs
CROSS JOIN duplicate_check dc
CROSS JOIN orphaned_data od
CROSS JOIN transaction_stats ts
CROSS JOIN webhook_health wh;

COMMENT ON VIEW v_database_health IS
  'Real-time database health dashboard. Shows overall status, metrics, and active alerts.';

-- ============================================================================
-- Daily Health Check Function (for scheduled monitoring)
-- ============================================================================

CREATE OR REPLACE FUNCTION daily_health_check()
RETURNS TABLE (
    metric text,
    value text,
    status text,
    threshold text,
    recommendation text
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_total_contacts bigint;
    v_name_duplicates bigint;
    v_orphaned_txns bigint;
    v_orphaned_subs bigint;
    v_failed_webhooks bigint;
    v_total_webhooks bigint;
    v_invalid_sigs bigint;
BEGIN
    -- Get current metrics
    SELECT
        total_contacts,
        name_duplicates,
        orphaned_transactions,
        orphaned_subscriptions,
        failed_webhooks_24h,
        webhooks_last_24h,
        invalid_signatures_24h
    INTO
        v_total_contacts,
        v_name_duplicates,
        v_orphaned_txns,
        v_orphaned_subs,
        v_failed_webhooks,
        v_total_webhooks,
        v_invalid_sigs
    FROM v_database_health;

    -- Contact count
    RETURN QUERY SELECT
        'Total Contacts'::text,
        v_total_contacts::text,
        CASE WHEN v_total_contacts > 0 THEN 'OK' ELSE 'CRITICAL' END,
        '> 0'::text,
        CASE WHEN v_total_contacts = 0 THEN 'Database appears empty!' ELSE 'Normal' END;

    -- Duplicate check
    RETURN QUERY SELECT
        'Name Duplicates'::text,
        v_name_duplicates::text,
        CASE
            WHEN v_name_duplicates = 0 THEN 'OK'
            WHEN v_name_duplicates <= 10 THEN 'WARNING'
            ELSE 'CRITICAL'
        END,
        '= 0 (best), <= 10 (acceptable)'::text,
        CASE
            WHEN v_name_duplicates = 0 THEN 'Perfect - no duplicates'
            WHEN v_name_duplicates <= 10 THEN 'Run duplicate analysis scripts'
            ELSE 'URGENT: Run batch merge scripts immediately'
        END;

    -- Orphaned transactions
    RETURN QUERY SELECT
        'Orphaned Transactions'::text,
        v_orphaned_txns::text,
        CASE WHEN v_orphaned_txns = 0 THEN 'OK' ELSE 'CRITICAL' END,
        '= 0'::text,
        CASE
            WHEN v_orphaned_txns = 0 THEN 'Perfect data integrity'
            ELSE 'URGENT: Run data integrity fix script'
        END;

    -- Orphaned subscriptions
    RETURN QUERY SELECT
        'Orphaned Subscriptions'::text,
        v_orphaned_subs::text,
        CASE WHEN v_orphaned_subs = 0 THEN 'OK' ELSE 'CRITICAL' END,
        '= 0'::text,
        CASE
            WHEN v_orphaned_subs = 0 THEN 'Perfect data integrity'
            ELSE 'URGENT: Run data integrity fix script'
        END;

    -- Webhook failure rate
    RETURN QUERY SELECT
        'Webhook Failures (24h)'::text,
        v_failed_webhooks || ' / ' || v_total_webhooks,
        CASE
            WHEN v_total_webhooks = 0 THEN 'OK'
            WHEN v_failed_webhooks::float / v_total_webhooks < 0.01 THEN 'OK'
            WHEN v_failed_webhooks::float / v_total_webhooks < 0.05 THEN 'WARNING'
            ELSE 'CRITICAL'
        END,
        '< 1% (OK), < 5% (WARNING)'::text,
        CASE
            WHEN v_total_webhooks = 0 THEN 'No recent webhooks'
            WHEN v_failed_webhooks::float / v_total_webhooks < 0.01 THEN 'Excellent webhook reliability'
            WHEN v_failed_webhooks::float / v_total_webhooks < 0.05 THEN 'Investigate webhook errors'
            ELSE 'URGENT: Check v_failed_webhooks view'
        END;

    -- Invalid signatures
    RETURN QUERY SELECT
        'Invalid Webhook Signatures (24h)'::text,
        v_invalid_sigs::text,
        CASE
            WHEN v_invalid_sigs = 0 THEN 'OK'
            WHEN v_invalid_sigs <= 5 THEN 'WARNING'
            ELSE 'CRITICAL'
        END,
        '= 0 (best), <= 5 (acceptable)'::text,
        CASE
            WHEN v_invalid_sigs = 0 THEN 'Perfect security posture'
            WHEN v_invalid_sigs <= 5 THEN 'Monitor for patterns'
            ELSE 'SECURITY ALERT: Check v_webhook_security_alerts'
        END;
END;
$$;

COMMENT ON FUNCTION daily_health_check IS
  'Comprehensive daily health check with pass/warn/fail status and recommendations. Run daily via cron.';

-- ============================================================================
-- Performance Metrics View
-- ============================================================================

CREATE OR REPLACE VIEW v_performance_metrics AS
SELECT
    -- Table sizes
    pg_size_pretty(pg_total_relation_size('contacts')) as contacts_size,
    pg_size_pretty(pg_total_relation_size('transactions')) as transactions_size,
    pg_size_pretty(pg_total_relation_size('subscriptions')) as subscriptions_size,
    pg_size_pretty(pg_total_relation_size('webhook_events')) as webhook_events_size,
    pg_size_pretty(pg_database_size(current_database())) as total_database_size,

    -- Row counts
    (SELECT COUNT(*) FROM contacts) as contact_count,
    (SELECT COUNT(*) FROM transactions) as transaction_count,
    (SELECT COUNT(*) FROM subscriptions) as subscription_count,
    (SELECT COUNT(*) FROM webhook_events) as webhook_event_count,

    -- Index usage
    (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE idx_scan = 0) as unused_indexes,

    -- Active connections
    (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,

    -- Cache hit ratio (should be > 99%)
    ROUND(
        100.0 * (
            SELECT SUM(blks_hit)
            FROM pg_stat_database
            WHERE datname = current_database()
        ) / NULLIF(
            (SELECT SUM(blks_hit) + SUM(blks_read)
             FROM pg_stat_database
             WHERE datname = current_database()),
            0
        ), 2
    ) as cache_hit_ratio_percent;

COMMENT ON VIEW v_performance_metrics IS
  'Database performance metrics: sizes, counts, index usage, connections, cache hit ratio.';

-- ============================================================================
-- Create Health Check Log Table (for trending)
-- ============================================================================

CREATE TABLE IF NOT EXISTS health_check_log (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    checked_at timestamptz NOT NULL DEFAULT now(),
    overall_status text NOT NULL,
    total_contacts bigint,
    name_duplicates bigint,
    orphaned_transactions bigint,
    orphaned_subscriptions bigint,
    webhooks_last_24h bigint,
    failed_webhooks_24h bigint,
    invalid_signatures_24h bigint,
    active_alerts text[],

    CONSTRAINT health_status_check CHECK (overall_status IN ('HEALTHY', 'WARNING', 'CRITICAL'))
);

CREATE INDEX IF NOT EXISTS idx_health_check_log_checked_at
    ON health_check_log (checked_at DESC);

COMMENT ON TABLE health_check_log IS
  'Historical health check results for trending and alerting. Populated by log_health_check() function.';

-- ============================================================================
-- Log Health Check Function (call this from cron)
-- ============================================================================

CREATE OR REPLACE FUNCTION log_health_check()
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    v_health_id uuid;
BEGIN
    INSERT INTO health_check_log (
        checked_at,
        overall_status,
        total_contacts,
        name_duplicates,
        orphaned_transactions,
        orphaned_subscriptions,
        webhooks_last_24h,
        failed_webhooks_24h,
        invalid_signatures_24h,
        active_alerts
    )
    SELECT
        checked_at,
        overall_status,
        total_contacts,
        name_duplicates,
        orphaned_transactions,
        orphaned_subscriptions,
        webhooks_last_24h,
        failed_webhooks_24h,
        invalid_signatures_24h,
        active_alerts
    FROM v_database_health
    RETURNING id INTO v_health_id;

    -- Cleanup old logs (keep 90 days)
    DELETE FROM health_check_log
    WHERE checked_at < now() - INTERVAL '90 days';

    RETURN v_health_id;
END;
$$;

COMMENT ON FUNCTION log_health_check IS
  'Log current health check results. Call hourly via pg_cron. Returns log entry ID.';

-- ============================================================================
-- Alerting View - Show Recent Problems
-- ============================================================================

CREATE OR REPLACE VIEW v_recent_health_alerts AS
SELECT
    checked_at,
    overall_status,
    active_alerts,
    total_contacts,
    name_duplicates,
    orphaned_transactions,
    orphaned_subscriptions,
    failed_webhooks_24h,
    invalid_signatures_24h
FROM health_check_log
WHERE overall_status IN ('WARNING', 'CRITICAL')
   OR array_length(active_alerts, 1) > 0
ORDER BY checked_at DESC
LIMIT 100;

COMMENT ON VIEW v_recent_health_alerts IS
  'Recent health check failures and warnings. Empty = all good!';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ DATABASE HEALTH MONITORING DEPLOYED!';
    RAISE NOTICE '';
    RAISE NOTICE 'Views Created:';
    RAISE NOTICE '  - v_database_health (real-time overall health)';
    RAISE NOTICE '  - v_performance_metrics (database performance)';
    RAISE NOTICE '  - v_recent_health_alerts (historical problems)';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions Created:';
    RAISE NOTICE '  - daily_health_check() (comprehensive status report)';
    RAISE NOTICE '  - log_health_check() (store results for trending)';
    RAISE NOTICE '';
    RAISE NOTICE 'Quick Check:';
    RAISE NOTICE '  SELECT * FROM v_database_health;';
    RAISE NOTICE '';
    RAISE NOTICE 'Daily Report:';
    RAISE NOTICE '  SELECT * FROM daily_health_check();';
    RAISE NOTICE '';
    RAISE NOTICE 'Performance Stats:';
    RAISE NOTICE '  SELECT * FROM v_performance_metrics;';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Set up pg_cron to run log_health_check() hourly';
    RAISE NOTICE '  2. Set up alerting based on v_recent_health_alerts';
    RAISE NOTICE '  3. Add to monitoring dashboard';
    RAISE NOTICE '';
END $$;
