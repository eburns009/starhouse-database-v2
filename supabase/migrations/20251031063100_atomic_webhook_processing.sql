-- ============================================================================
-- ATOMIC WEBHOOK PROCESSING FUNCTION
-- ============================================================================
-- Purpose: Strongest guard against interleaving logic and race conditions
-- Priority: P0 - CRITICAL (per expert review)
-- ============================================================================

-- Transactional webhook processing (atomic check + insert)
CREATE OR REPLACE FUNCTION process_webhook_atomically(
    p_source text,
    p_provider_event_id text,
    p_request_id uuid,
    p_nonce text,
    p_event_type text,
    p_payload_hash text,
    p_signature_valid boolean
)
RETURNS TABLE (
    is_duplicate boolean,
    webhook_event_id uuid,
    message text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_event_id uuid;
    v_is_duplicate boolean := false;
    v_message text;
BEGIN
    -- Step 1: Try to insert webhook_event with unique constraint
    -- If duplicate, this will fail and we catch it
    BEGIN
        INSERT INTO webhook_events (
            webhook_id,              -- External webhook ID from provider
            provider_event_id,       -- Also populate this for the unique constraint
            source,
            request_id,
            event_type,
            payload_hash,
            signature_valid,
            status,
            received_at
        )
        VALUES (
            p_provider_event_id,     -- Use provider event ID as webhook_id
            p_provider_event_id,     -- Also set provider_event_id
            p_source,
            p_request_id,
            p_event_type,
            p_payload_hash,
            p_signature_valid,
            'processing',
            now()
        )
        RETURNING id INTO v_event_id;

        v_message := 'New webhook event recorded';

    EXCEPTION WHEN unique_violation THEN
        -- Duplicate detected - this is idempotent success
        v_is_duplicate := true;

        SELECT id INTO v_event_id
        FROM webhook_events
        WHERE source = p_source
        AND (
            provider_event_id = p_provider_event_id
            OR request_id = p_request_id
            OR webhook_id = p_provider_event_id
        )
        LIMIT 1;

        v_message := 'Duplicate webhook detected (idempotent)';
    END;

    -- Step 2: If not duplicate, check and record nonce
    IF NOT v_is_duplicate AND p_nonce IS NOT NULL THEN
        IF is_nonce_used(p_source, p_nonce) THEN
            v_is_duplicate := true;
            v_message := 'Duplicate nonce detected (replay attack blocked)';

            -- Update webhook event status
            UPDATE webhook_events
            SET status = 'duplicate',
                error_message = 'Replay attack detected - nonce already used'
            WHERE id = v_event_id;
        ELSE
            -- Record nonce
            PERFORM record_nonce(p_source, p_nonce);
        END IF;
    END IF;

    -- Return result
    RETURN QUERY SELECT v_is_duplicate, v_event_id, v_message;
END;
$$;

COMMENT ON FUNCTION process_webhook_atomically IS
  'Atomically check idempotency and record webhook event. Prevents race conditions. SECURITY DEFINER with search_path=public for safety.';
