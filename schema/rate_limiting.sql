-- ============================================================================
-- RATE LIMITING - Postgres Token Bucket Implementation
-- ============================================================================
-- Purpose: Prevent DoS attacks and webhook flooding without external services
-- Design: Token bucket algorithm entirely in PostgreSQL
-- Priority: P0 - CRITICAL (blocks production deployment)
-- ============================================================================

-- ============================================================================
-- Rate Limit Tracking Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_rate_limits (
    source text NOT NULL,              -- 'kajabi', 'paypal', 'ticket-tailor'
    bucket_key text NOT NULL,          -- Groups traffic (IP address or provider key)
    tokens numeric NOT NULL,           -- Current available tokens
    last_refill timestamptz NOT NULL,  -- Last time bucket was refilled
    capacity int NOT NULL,             -- Maximum tokens (burst capacity)
    refill_rate numeric NOT NULL,      -- Tokens per second (sustained rate)

    PRIMARY KEY (source, bucket_key),

    -- Constraints
    CONSTRAINT rate_limit_tokens_nonnegative CHECK (tokens >= 0),
    CONSTRAINT rate_limit_capacity_positive CHECK (capacity > 0),
    CONSTRAINT rate_limit_refill_positive CHECK (refill_rate > 0)
);

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_rate_limits_last_refill
  ON webhook_rate_limits (last_refill);

COMMENT ON TABLE webhook_rate_limits IS
  'Token bucket rate limiting. One row per (source, bucket_key). Tokens refill at refill_rate per second up to capacity.';

-- ============================================================================
-- Initialize Default Rate Limits
-- ============================================================================

-- Kajabi: Moderate limits (educational platform, predictable traffic)
INSERT INTO webhook_rate_limits (source, bucket_key, tokens, last_refill, capacity, refill_rate)
VALUES ('kajabi', 'default', 120, now(), 120, 1.0)
ON CONFLICT (source, bucket_key) DO NOTHING;

-- PayPal: Higher limits (payment processor, can have legitimate bursts)
INSERT INTO webhook_rate_limits (source, bucket_key, tokens, last_refill, capacity, refill_rate)
VALUES ('paypal', 'default', 200, now(), 200, 2.0)
ON CONFLICT (source, bucket_key) DO NOTHING;

-- Ticket Tailor: Moderate limits (event ticketing, can spike during sales)
INSERT INTO webhook_rate_limits (source, bucket_key, tokens, last_refill, capacity, refill_rate)
VALUES ('ticket-tailor', 'default', 150, now(), 150, 1.5)
ON CONFLICT (source, bucket_key) DO NOTHING;

-- Unknown sources: Very restrictive (likely attack or misconfiguration)
INSERT INTO webhook_rate_limits (source, bucket_key, tokens, last_refill, capacity, refill_rate)
VALUES ('unknown', 'default', 60, now(), 60, 1.0)
ON CONFLICT (source, bucket_key) DO NOTHING;

-- ============================================================================
-- Atomic Token Checkout Function
-- ============================================================================

CREATE OR REPLACE FUNCTION checkout_rate_limit(
    p_source text,
    p_bucket_key text,
    p_default_capacity int DEFAULT 60,
    p_default_refill_rate numeric DEFAULT 1.0
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_now timestamptz := now();
    v_row webhook_rate_limits;
    v_elapsed numeric;
    v_new_tokens numeric;
BEGIN
    -- Ensure row exists (upsert with defaults)
    INSERT INTO webhook_rate_limits(source, bucket_key, tokens, last_refill, capacity, refill_rate)
    VALUES (p_source, p_bucket_key, p_default_capacity, v_now, p_default_capacity, p_default_refill_rate)
    ON CONFLICT (source, bucket_key) DO NOTHING;

    -- Lock target row for update (prevents race conditions)
    SELECT * INTO v_row
    FROM webhook_rate_limits
    WHERE source = p_source AND bucket_key = p_bucket_key
    FOR UPDATE;

    -- Calculate elapsed time since last refill
    v_elapsed := EXTRACT(EPOCH FROM (v_now - v_row.last_refill));

    -- Refill tokens based on elapsed time
    -- Formula: min(capacity, current_tokens + elapsed_seconds * refill_rate)
    v_new_tokens := LEAST(
        v_row.capacity::numeric,
        v_row.tokens + (v_elapsed * v_row.refill_rate)
    );

    -- Check if we have at least 1 token available
    IF v_new_tokens < 1 THEN
        -- No token available → THROTTLE
        -- Update bucket state even though we're rejecting (for accurate tracking)
        UPDATE webhook_rate_limits
        SET tokens = v_new_tokens,
            last_refill = v_now
        WHERE source = p_source AND bucket_key = p_bucket_key;

        RETURN FALSE;
    END IF;

    -- Token available → ALLOW and consume 1 token
    UPDATE webhook_rate_limits
    SET tokens = v_new_tokens - 1,
        last_refill = v_now
    WHERE source = p_source AND bucket_key = p_bucket_key;

    RETURN TRUE;
END;
$$;

COMMENT ON FUNCTION checkout_rate_limit IS
  'Atomically check and consume 1 token from rate limit bucket. Returns TRUE if allowed, FALSE if throttled. Uses token bucket algorithm with configurable burst capacity and sustained rate.';

-- ============================================================================
-- Rate Limit Info Function (for debugging)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_rate_limit_info(
    p_source text,
    p_bucket_key text
)
RETURNS TABLE (
    source text,
    bucket_key text,
    current_tokens numeric,
    capacity int,
    refill_rate numeric,
    last_refill timestamptz,
    seconds_until_next_token numeric,
    estimated_requests_per_minute numeric
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_now timestamptz := now();
    v_row webhook_rate_limits;
    v_elapsed numeric;
    v_new_tokens numeric;
BEGIN
    -- Get current state
    SELECT * INTO v_row
    FROM webhook_rate_limits
    WHERE webhook_rate_limits.source = p_source
      AND webhook_rate_limits.bucket_key = p_bucket_key;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Calculate current tokens (with refill)
    v_elapsed := EXTRACT(EPOCH FROM (v_now - v_row.last_refill));
    v_new_tokens := LEAST(
        v_row.capacity::numeric,
        v_row.tokens + (v_elapsed * v_row.refill_rate)
    );

    RETURN QUERY SELECT
        v_row.source,
        v_row.bucket_key,
        v_new_tokens as current_tokens,
        v_row.capacity,
        v_row.refill_rate,
        v_row.last_refill,
        CASE
            WHEN v_new_tokens >= 1 THEN 0
            ELSE (1 - v_new_tokens) / v_row.refill_rate
        END as seconds_until_next_token,
        v_row.refill_rate * 60 as estimated_requests_per_minute;
END;
$$;

COMMENT ON FUNCTION get_rate_limit_info IS
  'Get current rate limit status for debugging. Shows available tokens, capacity, refill rate, and estimated throughput.';

-- ============================================================================
-- Cleanup Function (remove stale rate limit entries)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_stale_rate_limits()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count integer;
BEGIN
    -- Remove entries not accessed in 7 days
    DELETE FROM webhook_rate_limits
    WHERE last_refill < now() - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

COMMENT ON FUNCTION cleanup_stale_rate_limits IS
  'Remove rate limit entries not accessed in 7 days. Run weekly via pg_cron.';

-- ============================================================================
-- Monitoring View
-- ============================================================================

CREATE OR REPLACE VIEW v_rate_limit_status AS
SELECT
    source,
    bucket_key,
    tokens,
    capacity,
    refill_rate,
    last_refill,
    CASE
        WHEN tokens < 1 THEN 'THROTTLED'
        WHEN tokens < capacity * 0.2 THEN 'LOW'
        WHEN tokens < capacity * 0.5 THEN 'MEDIUM'
        ELSE 'HEALTHY'
    END as status,
    ROUND(tokens * 100.0 / capacity, 2) as token_percentage,
    refill_rate * 60 as requests_per_minute,
    now() - last_refill as time_since_last_request
FROM webhook_rate_limits
ORDER BY
    CASE
        WHEN tokens < 1 THEN 1
        WHEN tokens < capacity * 0.2 THEN 2
        ELSE 3
    END,
    source,
    bucket_key;

COMMENT ON VIEW v_rate_limit_status IS
  'Real-time view of all rate limit buckets. Shows throttled/low/medium/healthy status.';

-- ============================================================================
-- Test Rate Limiting Function
-- ============================================================================

CREATE OR REPLACE FUNCTION test_rate_limiting()
RETURNS TABLE (
    test_name text,
    result text,
    details text
)
LANGUAGE plpgsql
AS $$
DECLARE
    test_source text := 'test';
    test_key text := 'test_' || EXTRACT(EPOCH FROM now())::text;
    allowed boolean;
    i integer;
    allowed_count integer := 0;
    denied_count integer := 0;
BEGIN
    -- Test 1: Create bucket with capacity 5, refill 1/s
    PERFORM checkout_rate_limit(test_source, test_key, 5, 1.0);

    RETURN QUERY SELECT
        'Setup'::text,
        'PASS'::text,
        'Created test bucket with capacity=5, refill=1/s'::text;

    -- Test 2: Burst allowance (should allow 5 requests immediately)
    FOR i IN 1..10 LOOP
        allowed := checkout_rate_limit(test_source, test_key, 5, 1.0);
        IF allowed THEN
            allowed_count := allowed_count + 1;
        ELSE
            denied_count := denied_count + 1;
        END IF;
    END LOOP;

    RETURN QUERY SELECT
        'Burst Capacity'::text,
        CASE WHEN allowed_count = 5 AND denied_count = 5 THEN 'PASS' ELSE 'FAIL' END,
        format('Allowed: %s, Denied: %s (expected 5/5)', allowed_count, denied_count);

    -- Test 3: Token refill after 2 seconds
    PERFORM pg_sleep(2);
    allowed_count := 0;
    denied_count := 0;

    FOR i IN 1..3 LOOP
        allowed := checkout_rate_limit(test_source, test_key, 5, 1.0);
        IF allowed THEN
            allowed_count := allowed_count + 1;
        ELSE
            denied_count := denied_count + 1;
        END IF;
    END LOOP;

    RETURN QUERY SELECT
        'Token Refill'::text,
        CASE WHEN allowed_count >= 2 THEN 'PASS' ELSE 'FAIL' END,
        format('After 2s wait: Allowed: %s, Denied: %s (expected ~2 allowed)', allowed_count, denied_count);

    -- Cleanup test data
    DELETE FROM webhook_rate_limits WHERE source = test_source AND bucket_key = test_key;

    RETURN QUERY SELECT
        'Cleanup'::text,
        'PASS'::text,
        'Test bucket removed'::text;
END;
$$;

COMMENT ON FUNCTION test_rate_limiting IS
  'Self-test for rate limiting. Creates test bucket, verifies burst capacity and refill behavior.';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ RATE LIMITING DEPLOYED!';
    RAISE NOTICE '';
    RAISE NOTICE 'Created:';
    RAISE NOTICE '  - webhook_rate_limits table (token bucket storage)';
    RAISE NOTICE '  - checkout_rate_limit() function (atomic token checkout)';
    RAISE NOTICE '  - get_rate_limit_info() function (debugging)';
    RAISE NOTICE '  - cleanup_stale_rate_limits() function (maintenance)';
    RAISE NOTICE '  - v_rate_limit_status view (monitoring)';
    RAISE NOTICE '  - test_rate_limiting() function (self-test)';
    RAISE NOTICE '';
    RAISE NOTICE 'Default Limits:';
    RAISE NOTICE '  - Kajabi: 120 burst, 1.0/s sustained (60/min)';
    RAISE NOTICE '  - PayPal: 200 burst, 2.0/s sustained (120/min)';
    RAISE NOTICE '  - Ticket Tailor: 150 burst, 1.5/s sustained (90/min)';
    RAISE NOTICE '  - Unknown: 60 burst, 1.0/s sustained (60/min)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Test: SELECT * FROM test_rate_limiting();';
    RAISE NOTICE '  2. Monitor: SELECT * FROM v_rate_limit_status;';
    RAISE NOTICE '  3. Update webhooks to call checkout_rate_limit()';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage in Edge Functions:';
    RAISE NOTICE '  const { data: allowed } = await supabase.rpc(''checkout_rate_limit'', {';
    RAISE NOTICE '    p_source: ''kajabi'',';
    RAISE NOTICE '    p_bucket_key: sourceIP || ''default''';
    RAISE NOTICE '  });';
    RAISE NOTICE '  if (!allowed) return new Response(''Too Many Requests'', { status: 429 });';
    RAISE NOTICE '';
END $$;
