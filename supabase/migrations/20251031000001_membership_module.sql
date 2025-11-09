-- ============================================
-- MEMBERSHIP MODULE
-- Non-Profit Database - StarHouse
-- ============================================
-- Purpose: Track active members, subscription status, and membership lifecycle
-- Key Question: "Is this person a current member RIGHT NOW?"

-- ============================================
-- 1. MEMBERSHIP STATUS VIEW
-- ============================================
-- This view answers: "Who is currently a member?"

CREATE OR REPLACE VIEW v_membership_status AS
SELECT
    c.id AS contact_id,
    c.email,
    c.first_name,
    c.last_name,

    -- Subscription Details
    s.id AS subscription_id,
    s.kajabi_subscription_id,
    s.status AS subscription_status,
    s.amount AS membership_fee,
    s.billing_cycle,
    s.start_date,
    s.next_billing_date,
    s.cancellation_date,

    -- Membership Status Logic
    CASE
        -- Active: Has active subscription with future billing date
        WHEN s.status = 'active'
         AND s.next_billing_date >= CURRENT_DATE
        THEN 'ACTIVE'

        -- Grace Period: Subscription active but payment overdue (< 7 days)
        WHEN s.status = 'active'
         AND s.next_billing_date < CURRENT_DATE
         AND s.next_billing_date >= CURRENT_DATE - INTERVAL '7 days'
        THEN 'GRACE_PERIOD'

        -- Overdue: Payment more than 7 days late
        WHEN s.status = 'active'
         AND s.next_billing_date < CURRENT_DATE - INTERVAL '7 days'
        THEN 'OVERDUE'

        -- Cancelled: Was member, cancelled
        WHEN s.status = 'canceled'
         AND s.cancellation_date IS NOT NULL
        THEN 'CANCELLED'

        -- Paused: Subscription paused
        WHEN s.status = 'paused'
        THEN 'PAUSED'

        -- Expired: Subscription ended
        WHEN s.status = 'expired'
        THEN 'EXPIRED'

        -- Never Member: Contact exists but no subscription
        ELSE 'NOT_MEMBER'
    END AS membership_status,

    -- Days until next billing (negative = overdue)
    CASE
        WHEN s.next_billing_date IS NOT NULL
        THEN (s.next_billing_date - CURRENT_DATE)
        ELSE NULL
    END AS days_until_billing,

    -- Member since (first subscription start date)
    s.start_date AS member_since,

    -- Lifetime value (total paid)
    COALESCE(
        (SELECT SUM(t.amount)
         FROM transactions t
         WHERE t.contact_id = c.id
           AND t.subscription_id = s.id
           AND t.status = 'completed'),
        0
    ) AS lifetime_value,

    -- Last payment date
    (SELECT MAX(t.transaction_date)
     FROM transactions t
     WHERE t.contact_id = c.id
       AND t.subscription_id = s.id
       AND t.status = 'completed') AS last_payment_date,

    -- Payment processor
    s.payment_processor,

    -- Timestamps
    c.created_at AS contact_created_at,
    s.created_at AS subscription_created_at,
    s.updated_at AS subscription_updated_at

FROM contacts c
LEFT JOIN subscriptions s ON c.id = s.contact_id
    -- Get most recent subscription per contact
    AND s.id = (
        SELECT s2.id
        FROM subscriptions s2
        WHERE s2.contact_id = c.id
        ORDER BY s2.created_at DESC
        LIMIT 1
    )
ORDER BY c.last_name, c.first_name;

-- Add helpful comment
COMMENT ON VIEW v_membership_status IS 'Real-time membership status for all contacts. Use this to check if someone is currently a member.';

-- ============================================
-- 2. ACTIVE MEMBERS VIEW (Simplified)
-- ============================================
-- Quick view: ONLY show current active members

CREATE OR REPLACE VIEW v_active_members AS
SELECT
    contact_id,
    email,
    first_name,
    last_name,
    membership_status,
    membership_fee,
    billing_cycle,
    next_billing_date,
    member_since,
    lifetime_value,
    last_payment_date
FROM v_membership_status
WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
ORDER BY last_name, first_name;

COMMENT ON VIEW v_active_members IS 'Current active members only (excludes cancelled, expired, non-members)';

-- ============================================
-- 3. MEMBERSHIP METRICS VIEW
-- ============================================
-- Dashboard statistics

DROP VIEW IF EXISTS v_membership_metrics CASCADE;
CREATE VIEW v_membership_metrics AS
SELECT
    -- Total counts by status
    COUNT(*) FILTER (WHERE membership_status = 'ACTIVE') AS active_members,
    COUNT(*) FILTER (WHERE membership_status = 'GRACE_PERIOD') AS grace_period_members,
    COUNT(*) FILTER (WHERE membership_status = 'OVERDUE') AS overdue_members,
    COUNT(*) FILTER (WHERE membership_status = 'PAUSED') AS paused_members,
    COUNT(*) FILTER (WHERE membership_status = 'CANCELLED') AS cancelled_members,
    COUNT(*) FILTER (WHERE membership_status = 'EXPIRED') AS expired_members,
    COUNT(*) FILTER (WHERE membership_status = 'NOT_MEMBER') AS non_members,

    -- Monthly vs Yearly breakdown (active only)
    COUNT(*) FILTER (
        WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
          AND billing_cycle ILIKE '%month%'
    ) AS monthly_members,
    COUNT(*) FILTER (
        WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
          AND billing_cycle ILIKE '%year%'
    ) AS yearly_members,

    -- Revenue metrics (active members only)
    SUM(membership_fee) FILTER (
        WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
    ) AS monthly_recurring_revenue,

    SUM(lifetime_value) FILTER (
        WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
    ) AS total_lifetime_value,

    -- Average metrics
    ROUND(AVG(membership_fee) FILTER (
        WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
    ), 2) AS avg_membership_fee,

    -- Churn tracking
    COUNT(*) FILTER (
        WHERE membership_status = 'CANCELLED'
          AND cancellation_date >= CURRENT_DATE - INTERVAL '30 days'
    ) AS cancelled_last_30_days,

    -- New members
    COUNT(*) FILTER (
        WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
          AND member_since >= CURRENT_DATE - INTERVAL '30 days'
    ) AS new_members_last_30_days,

    -- At-risk members (billing soon, might not renew)
    COUNT(*) FILTER (
        WHERE membership_status = 'ACTIVE'
          AND next_billing_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
    ) AS renewing_next_7_days,

    -- Update timestamp
    CURRENT_TIMESTAMP AS last_updated

FROM v_membership_status;

COMMENT ON VIEW v_membership_metrics IS 'Key membership metrics for dashboard and reporting';

-- ============================================
-- 4. HELPER FUNCTIONS
-- ============================================

-- Function: Check if contact is current member
CREATE OR REPLACE FUNCTION is_current_member(p_contact_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM v_membership_status
        WHERE contact_id = p_contact_id
          AND membership_status IN ('ACTIVE', 'GRACE_PERIOD')
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_current_member IS 'Returns TRUE if contact is a current active member';

-- Function: Get membership status for contact
CREATE OR REPLACE FUNCTION get_membership_status(p_contact_id UUID)
RETURNS TEXT AS $$
BEGIN
    RETURN (
        SELECT membership_status
        FROM v_membership_status
        WHERE contact_id = p_contact_id
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_membership_status IS 'Returns membership status string for a contact';

-- Function: Get all active member emails (for email blasts)
CREATE OR REPLACE FUNCTION get_active_member_emails()
RETURNS TABLE(email TEXT, first_name TEXT, last_name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.email::TEXT,
        v.first_name,
        v.last_name
    FROM v_active_members v
    WHERE v.email IS NOT NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_active_member_emails IS 'Returns emails of all active members (for mailing lists)';

-- ============================================
-- 5. USEFUL QUERIES (Examples)
-- ============================================

-- Query: All active members
-- SELECT * FROM v_active_members;

-- Query: Membership dashboard
-- SELECT * FROM v_membership_metrics;

-- Query: Members expiring in next 30 days
-- SELECT * FROM v_membership_status
-- WHERE membership_status = 'ACTIVE'
--   AND next_billing_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
-- ORDER BY next_billing_date;

-- Query: Check if specific person is member
-- SELECT is_current_member('contact-uuid-here');

-- Query: Get status for specific person
-- SELECT get_membership_status('contact-uuid-here');

-- Query: Overdue members (need follow-up)
-- SELECT * FROM v_membership_status
-- WHERE membership_status = 'OVERDUE'
-- ORDER BY next_billing_date;

-- Query: Members by billing cycle
-- SELECT
--     billing_cycle,
--     COUNT(*) as member_count,
--     SUM(membership_fee) as total_revenue
-- FROM v_active_members
-- GROUP BY billing_cycle;

-- Query: New members this month
-- SELECT * FROM v_membership_status
-- WHERE membership_status IN ('ACTIVE', 'GRACE_PERIOD')
--   AND member_since >= DATE_TRUNC('month', CURRENT_DATE)
-- ORDER BY member_since DESC;

-- Query: Cancelled members (for win-back campaign)
-- SELECT * FROM v_membership_status
-- WHERE membership_status = 'CANCELLED'
--   AND cancellation_date >= CURRENT_DATE - INTERVAL '60 days'
-- ORDER BY cancellation_date DESC;
