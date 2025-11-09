-- ============================================================================
-- WEBHOOK SECURITY SCHEMA
-- ============================================================================
-- Purpose: Track webhook events for idempotency, audit, and security
-- Created: 2025-10-31
-- Priority: P0 - CRITICAL SECURITY
-- ============================================================================

-- Extension for UUID generation (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- WEBHOOK EVENTS TABLE - Idempotency & Audit Trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_events (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Idempotency & Identification
    webhook_id text UNIQUE NOT NULL,           -- External webhook ID from provider
    request_id uuid NOT NULL DEFAULT uuid_generate_v4(), -- Internal request tracking
    source text NOT NULL,                       -- 'kajabi', 'paypal', 'ticket-tailor'
    event_type text NOT NULL,                   -- e.g., 'order.created', 'PAYMENT.SALE.COMPLETED'

    -- Security Tracking
    ip_address text,                            -- Requester IP
    user_agent text,                            -- Requester user agent
    signature_valid boolean NOT NULL DEFAULT false,
    signature_header text,                      -- Signature from request (for debugging)

    -- Replay Attack Prevention
    webhook_timestamp timestamptz,              -- Timestamp from webhook headers
    received_at timestamptz NOT NULL DEFAULT now(),

    -- Processing Status
    status text NOT NULL DEFAULT 'processing',  -- processing, success, failed, duplicate
    processed_at timestamptz NOT NULL DEFAULT now(),
    processing_duration_ms integer,             -- How long processing took
    error_message text,                         -- Error details if failed
    error_code text,                            -- Structured error code

    -- Payload Security
    payload_hash text NOT NULL,                 -- SHA-256 hash for duplicate detection
    payload_size integer,                       -- Size in bytes

    -- Related Records (for audit trail)
    contact_id uuid REFERENCES contacts(id) ON DELETE SET NULL,
    transaction_id uuid REFERENCES transactions(id) ON DELETE SET NULL,
    subscription_id uuid REFERENCES subscriptions(id) ON DELETE SET NULL,

    -- Audit Timestamps
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT webhook_events_source_check CHECK (source IN ('kajabi', 'paypal', 'ticket-tailor')),
    CONSTRAINT webhook_events_status_check CHECK (status IN ('processing', 'success', 'failed', 'duplicate')),
    CONSTRAINT webhook_events_duration_check CHECK (processing_duration_ms IS NULL OR processing_duration_ms >= 0)
);

-- ============================================================================
-- INDEXES for Performance
-- ============================================================================

-- Primary lookup by webhook_id (idempotency check)
CREATE INDEX idx_webhook_events_webhook_id ON webhook_events(webhook_id);

-- Lookup by request_id (debugging)
CREATE INDEX idx_webhook_events_request_id ON webhook_events(request_id);

-- Lookup by source and event type (analytics)
CREATE INDEX idx_webhook_events_source_type ON webhook_events(source, event_type);

-- Lookup recent events
CREATE INDEX idx_webhook_events_received_at ON webhook_events(received_at DESC);

-- Find failed events
CREATE INDEX idx_webhook_events_failed ON webhook_events(status, received_at DESC)
WHERE status = 'failed';

-- Find duplicates
CREATE INDEX idx_webhook_events_duplicates ON webhook_events(status, received_at DESC)
WHERE status = 'duplicate';

-- Security analysis - invalid signatures
CREATE INDEX idx_webhook_events_invalid_sig ON webhook_events(signature_valid, received_at DESC)
WHERE signature_valid = false;

-- Replay attack detection - check recent webhooks with same payload
CREATE INDEX idx_webhook_events_payload_hash ON webhook_events(payload_hash, received_at DESC);

-- Auto-cleanup query optimization
CREATE INDEX idx_webhook_events_cleanup ON webhook_events(received_at)
WHERE received_at < now() - INTERVAL '30 days';

-- Foreign key indexes for audit trail
CREATE INDEX idx_webhook_events_contact_id ON webhook_events(contact_id)
WHERE contact_id IS NOT NULL;
CREATE INDEX idx_webhook_events_transaction_id ON webhook_events(transaction_id)
WHERE transaction_id IS NOT NULL;
CREATE INDEX idx_webhook_events_subscription_id ON webhook_events(subscription_id)
WHERE subscription_id IS NOT NULL;

-- ============================================================================
-- TRIGGER for updated_at
-- ============================================================================

CREATE TRIGGER webhook_events_set_updated_at
    BEFORE UPDATE ON webhook_events
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if webhook was recently processed (idempotency)
CREATE OR REPLACE FUNCTION is_webhook_processed(p_webhook_id text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM webhook_events
        WHERE webhook_id = p_webhook_id
        AND status IN ('success', 'duplicate')
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to check for replay attacks (timestamp too old)
CREATE OR REPLACE FUNCTION is_replay_attack(p_webhook_timestamp timestamptz)
RETURNS boolean AS $$
BEGIN
    -- Reject if timestamp is more than 5 minutes old
    IF p_webhook_timestamp < now() - INTERVAL '5 minutes' THEN
        RETURN true;
    END IF;

    -- Reject if timestamp is in the future (clock skew > 1 minute)
    IF p_webhook_timestamp > now() + INTERVAL '1 minute' THEN
        RETURN true;
    END IF;

    RETURN false;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to detect duplicate payloads (same hash within 1 hour)
CREATE OR REPLACE FUNCTION is_duplicate_payload(p_payload_hash text, p_source text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM webhook_events
        WHERE payload_hash = p_payload_hash
        AND source = p_source
        AND received_at > now() - INTERVAL '1 hour'
        AND status = 'success'
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get webhook statistics
CREATE OR REPLACE FUNCTION get_webhook_stats(p_hours integer DEFAULT 24)
RETURNS TABLE (
    source text,
    total_webhooks bigint,
    successful bigint,
    failed bigint,
    duplicates bigint,
    avg_duration_ms numeric,
    invalid_signatures bigint
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        w.source,
        COUNT(*) as total_webhooks,
        COUNT(*) FILTER (WHERE w.status = 'success') as successful,
        COUNT(*) FILTER (WHERE w.status = 'failed') as failed,
        COUNT(*) FILTER (WHERE w.status = 'duplicate') as duplicates,
        ROUND(AVG(w.processing_duration_ms), 2) as avg_duration_ms,
        COUNT(*) FILTER (WHERE w.signature_valid = false) as invalid_signatures
    FROM webhook_events w
    WHERE w.received_at > now() - (p_hours || ' hours')::interval
    GROUP BY w.source
    ORDER BY w.source;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- AUTO-CLEANUP OLD RECORDS (Keep 30 days)
-- ============================================================================

-- Function to delete old webhook events
CREATE OR REPLACE FUNCTION cleanup_old_webhook_events()
RETURNS integer AS $$
DECLARE
    deleted_count integer;
BEGIN
    DELETE FROM webhook_events
    WHERE received_at < now() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RAISE NOTICE 'Cleaned up % old webhook events', deleted_count;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS for Documentation
-- ============================================================================

COMMENT ON TABLE webhook_events IS 'Audit trail and idempotency tracking for all webhook events';
COMMENT ON COLUMN webhook_events.webhook_id IS 'External webhook ID from provider (unique, used for idempotency)';
COMMENT ON COLUMN webhook_events.request_id IS 'Internal UUID for request tracing and correlation';
COMMENT ON COLUMN webhook_events.payload_hash IS 'SHA-256 hash of webhook payload for duplicate detection';
COMMENT ON COLUMN webhook_events.signature_valid IS 'Whether webhook signature was verified successfully';
COMMENT ON COLUMN webhook_events.processing_duration_ms IS 'Time taken to process webhook in milliseconds';

COMMENT ON FUNCTION is_webhook_processed IS 'Check if webhook was already processed (idempotency)';
COMMENT ON FUNCTION is_replay_attack IS 'Detect replay attacks based on timestamp (>5 min old or >1 min future)';
COMMENT ON FUNCTION is_duplicate_payload IS 'Detect duplicate payloads within 1 hour window';
COMMENT ON FUNCTION get_webhook_stats IS 'Get webhook processing statistics for monitoring';
COMMENT ON FUNCTION cleanup_old_webhook_events IS 'Delete webhook events older than 30 days';

-- ============================================================================
-- VIEWS for Monitoring
-- ============================================================================

-- View: Recent failed webhooks
CREATE OR REPLACE VIEW v_failed_webhooks AS
SELECT
    request_id,
    webhook_id,
    source,
    event_type,
    error_code,
    error_message,
    ip_address,
    received_at,
    processing_duration_ms
FROM webhook_events
WHERE status = 'failed'
ORDER BY received_at DESC
LIMIT 100;

COMMENT ON VIEW v_failed_webhooks IS 'Recent failed webhooks for troubleshooting';

-- View: Security alerts (invalid signatures, replay attacks)
CREATE OR REPLACE VIEW v_webhook_security_alerts AS
SELECT
    request_id,
    webhook_id,
    source,
    event_type,
    ip_address,
    signature_valid,
    webhook_timestamp,
    received_at,
    CASE
        WHEN signature_valid = false THEN 'INVALID_SIGNATURE'
        WHEN webhook_timestamp < received_at - INTERVAL '5 minutes' THEN 'REPLAY_ATTACK'
        WHEN webhook_timestamp > received_at + INTERVAL '1 minute' THEN 'FUTURE_TIMESTAMP'
        ELSE 'UNKNOWN'
    END as alert_type
FROM webhook_events
WHERE signature_valid = false
   OR webhook_timestamp < received_at - INTERVAL '5 minutes'
   OR webhook_timestamp > received_at + INTERVAL '1 minute'
ORDER BY received_at DESC
LIMIT 100;

COMMENT ON VIEW v_webhook_security_alerts IS 'Security alerts for webhooks (invalid signatures, replay attacks)';

-- ============================================================================
-- SAMPLE QUERIES for Monitoring
-- ============================================================================

-- Get webhook statistics for last 24 hours
-- SELECT * FROM get_webhook_stats(24);

-- Find recent failures
-- SELECT * FROM v_failed_webhooks LIMIT 10;

-- Find security issues
-- SELECT * FROM v_webhook_security_alerts LIMIT 10;

-- Check if specific webhook was processed
-- SELECT is_webhook_processed('webhook_12345');

-- Get processing time percentiles
-- SELECT
--     source,
--     PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY processing_duration_ms) as p50_ms,
--     PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_duration_ms) as p95_ms,
--     PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY processing_duration_ms) as p99_ms
-- FROM webhook_events
-- WHERE received_at > now() - INTERVAL '24 hours'
--   AND processing_duration_ms IS NOT NULL
-- GROUP BY source;

-- Cleanup old events (run weekly)
-- SELECT cleanup_old_webhook_events();

-- ============================================================================
-- SUCCESS
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ Webhook security schema created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - webhook_events table with idempotency tracking';
    RAISE NOTICE '  - 11 indexes for performance and security';
    RAISE NOTICE '  - 4 helper functions for security checks';
    RAISE NOTICE '  - 2 monitoring views';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Deploy updated webhook functions';
    RAISE NOTICE '  2. Set WEBHOOK_ENVIRONMENT=production';
    RAISE NOTICE '  3. Monitor v_webhook_security_alerts';
    RAISE NOTICE '  4. Set up weekly cleanup_old_webhook_events() job';
    RAISE NOTICE '';
END $$;
