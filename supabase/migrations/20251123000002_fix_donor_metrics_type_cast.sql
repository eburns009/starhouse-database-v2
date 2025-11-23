-- ============================================================================
-- FIX: update_donor_metrics TYPE CASTING
-- ============================================================================
-- Migration: 20251123000002
-- Purpose: Fix donor_status enum type casting in update_donor_metrics function
-- Issue: CASE expression returns text but column expects donor_status enum
-- ============================================================================

-- Replace the function with proper type casting
CREATE OR REPLACE FUNCTION update_donor_metrics(p_donor_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_lifetime_amount NUMERIC;
    v_lifetime_count INTEGER;
    v_first_gift_date DATE;
    v_last_gift_date DATE;
    v_largest_gift NUMERIC;
    v_avg_gift NUMERIC;
BEGIN
    -- Calculate aggregate metrics from donation transactions
    SELECT
        COALESCE(SUM(CASE WHEN transaction_type != 'refund' THEN amount ELSE -ABS(amount) END), 0),
        COUNT(*) FILTER (WHERE transaction_type != 'refund'),
        MIN(transaction_date)::date,
        MAX(transaction_date)::date,
        MAX(CASE WHEN transaction_type != 'refund' THEN amount ELSE 0 END),
        CASE
            WHEN COUNT(*) FILTER (WHERE transaction_type != 'refund') > 0
            THEN AVG(CASE WHEN transaction_type != 'refund' THEN amount ELSE NULL END)
            ELSE 0
        END
    INTO
        v_lifetime_amount,
        v_lifetime_count,
        v_first_gift_date,
        v_last_gift_date,
        v_largest_gift,
        v_avg_gift
    FROM transactions
    WHERE contact_id = (SELECT contact_id FROM donors WHERE id = p_donor_id)
      AND is_donation = true;

    -- Update donor record with calculated metrics
    -- Note: is_major_donor is a generated column, so it updates automatically
    UPDATE donors
    SET
        lifetime_amount = v_lifetime_amount,
        lifetime_count = v_lifetime_count,
        first_gift_date = COALESCE(v_first_gift_date, first_gift_date),
        last_gift_date = COALESCE(v_last_gift_date, last_gift_date),
        largest_gift = v_largest_gift,
        average_gift = v_avg_gift,
        updated_at = now()
    WHERE id = p_donor_id;

    -- Update donor status based on giving history
    -- FIX: Explicitly cast text to donor_status enum
    UPDATE donors
    SET status = CASE
        WHEN lifetime_count = 0 THEN 'prospect'::donor_status
        WHEN lifetime_count = 1 THEN 'first_time'::donor_status
        WHEN last_gift_date >= now() - interval '12 months' THEN 'active'::donor_status
        WHEN last_gift_date >= now() - interval '24 months' THEN 'lapsed'::donor_status
        ELSE 'dormant'::donor_status
    END
    WHERE id = p_donor_id
      AND status NOT IN ('major', 'deceased'); -- Don't override these statuses

    -- Check for major donor status (is_major_donor is a generated column)
    UPDATE donors
    SET status = 'major'::donor_status
    WHERE id = p_donor_id
      AND lifetime_amount >= major_donor_threshold
      AND status != 'deceased';

END;
$$;

COMMENT ON FUNCTION update_donor_metrics(UUID) IS
'Calculate and update donor metrics from transaction history. Fixed type casting for donor_status enum.';
