-- ============================================================================
-- FIX DATA INTEGRITY ISSUES
-- ============================================================================
-- Based on comprehensive verification test results
-- Fixes: is_annual flags, membership levels, subscription flags
-- ============================================================================

BEGIN;

\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'FIX 1: is_annual Flag Correction'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- Fix subscriptions where is_annual doesn't match the amount
-- Fix annual subscriptions
WITH updated AS (
    UPDATE subscriptions s
    SET is_annual = TRUE
    FROM membership_products mp
    WHERE s.membership_product_id = mp.id
      AND s.status = 'active'
      AND s.amount = mp.annual_price
      AND (s.is_annual = FALSE OR s.is_annual IS NULL)
    RETURNING s.id
)
SELECT '✅ Fixed is_annual flag for annual subscriptions' as result,
       COUNT(*) as rows_updated
FROM updated;

-- Fix monthly subscriptions
WITH updated AS (
    UPDATE subscriptions s
    SET is_annual = FALSE
    FROM membership_products mp
    WHERE s.membership_product_id = mp.id
      AND s.status = 'active'
      AND s.amount = mp.monthly_price
      AND s.is_annual = TRUE
    RETURNING s.id
)
SELECT '✅ Fixed is_annual flag for monthly subscriptions' as result,
       COUNT(*) as rows_updated
FROM updated;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'FIX 2: Contact Membership Level Sync'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- Update contacts where membership_level doesn't match their active subscription
-- Strategy: Use the highest-tier active subscription if multiple exist
WITH ranked_subscriptions AS (
    SELECT
        c.id as contact_id,
        c.email,
        c.membership_level as current_level,
        mp.membership_level as correct_level,
        mp.sort_order,
        s.amount,
        ROW_NUMBER() OVER (
            PARTITION BY c.id
            ORDER BY mp.sort_order DESC, s.amount DESC
        ) as rn
    FROM contacts c
    JOIN subscriptions s ON c.id = s.contact_id
    JOIN membership_products mp ON s.membership_product_id = mp.id
    WHERE s.status = 'active'
      AND c.has_active_subscription = TRUE
      AND c.membership_level != mp.membership_level
),
updated AS (
    UPDATE contacts c
    SET membership_level = rs.correct_level
    FROM ranked_subscriptions rs
    WHERE c.id = rs.contact_id
      AND rs.rn = 1
    RETURNING c.id
)
SELECT '✅ Synced contact membership_level with active subscriptions' as result,
       COUNT(*) as rows_updated
FROM updated;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'FIX 3: has_active_subscription Flag Correction'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- Set has_active_subscription = TRUE for contacts with active subscriptions
WITH updated AS (
    UPDATE contacts c
    SET has_active_subscription = TRUE
    WHERE EXISTS (
        SELECT 1
        FROM subscriptions s
        WHERE s.contact_id = c.id
          AND s.status = 'active'
    )
    AND c.has_active_subscription = FALSE
    RETURNING c.id
)
SELECT '✅ Fixed has_active_subscription = TRUE' as result,
       COUNT(*) as rows_updated
FROM updated;

-- Set has_active_subscription = FALSE for contacts without active subscriptions
WITH updated AS (
    UPDATE contacts c
    SET has_active_subscription = FALSE,
        membership_level = NULL  -- Clear membership level if no active subscription
    WHERE NOT EXISTS (
        SELECT 1
        FROM subscriptions s
        WHERE s.contact_id = c.id
          AND s.status = 'active'
    )
    AND c.has_active_subscription = TRUE
    RETURNING c.id
)
SELECT '✅ Fixed has_active_subscription = FALSE' as result,
       COUNT(*) as rows_updated
FROM updated;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'FIX 4: PayPal Reference Format (Information Only)'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- Note: Many subscriptions have kajabi_subscription_id stored in paypal_subscription_reference
-- This is expected - Kajabi subscriptions that use PayPal for payment
-- We keep both fields for cross-referencing

SELECT
    'PayPal format (I-XXX)' as reference_type,
    COUNT(*) FILTER (WHERE paypal_subscription_reference ~ '^I-') as count
FROM subscriptions
WHERE paypal_subscription_reference IS NOT NULL
UNION ALL
SELECT
    'Kajabi numeric format' as reference_type,
    COUNT(*) FILTER (WHERE paypal_subscription_reference ~ '^[0-9]+$') as count
FROM subscriptions
WHERE paypal_subscription_reference IS NOT NULL
UNION ALL
SELECT
    'Total with reference' as reference_type,
    COUNT(*) as count
FROM subscriptions
WHERE paypal_subscription_reference IS NOT NULL;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'VERIFICATION: Run Tests Again'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- Test 1: is_annual flag
SELECT
    'Test 1' as test,
    'is_annual flag consistency' as description,
    COUNT(*) FILTER (WHERE
        (s.is_annual = TRUE AND s.amount = mp.annual_price) OR
        (s.is_annual = FALSE AND s.amount = mp.monthly_price) OR
        s.is_annual IS NULL
    ) as pass,
    COUNT(*) FILTER (WHERE
        (s.is_annual = TRUE AND s.amount != mp.annual_price) OR
        (s.is_annual = FALSE AND s.amount != mp.monthly_price)
    ) as fail,
    CASE
        WHEN COUNT(*) FILTER (WHERE
            (s.is_annual = TRUE AND s.amount != mp.annual_price) OR
            (s.is_annual = FALSE AND s.amount != mp.monthly_price)
        ) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions s
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active';

-- Test 2: membership_level match
SELECT
    'Test 2' as test,
    'Contact level matches subscription' as description,
    COUNT(*) FILTER (WHERE c.membership_level = mp.membership_level) as pass,
    COUNT(*) FILTER (WHERE c.membership_level != mp.membership_level) as fail,
    CASE
        WHEN COUNT(*) FILTER (WHERE c.membership_level != mp.membership_level) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM contacts c
JOIN subscriptions s ON c.id = s.contact_id
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active' AND c.has_active_subscription = TRUE;

-- Test 3: has_active_subscription flag
SELECT
    'Test 3' as test,
    'has_active_subscription accuracy' as description,
    COUNT(*) FILTER (WHERE
        (c.has_active_subscription = TRUE AND EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        )) OR
        (c.has_active_subscription = FALSE AND NOT EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        ))
    ) as pass,
    COUNT(*) FILTER (WHERE
        (c.has_active_subscription = TRUE AND NOT EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        )) OR
        (c.has_active_subscription = FALSE AND EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        ))
    ) as fail,
    CASE
        WHEN COUNT(*) FILTER (WHERE
            (c.has_active_subscription = TRUE AND NOT EXISTS(
                SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
            )) OR
            (c.has_active_subscription = FALSE AND EXISTS(
                SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
            ))
        ) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM contacts c;

COMMIT;

\echo ''
\echo '╔══════════════════════════════════════════════════════════════════════════╗'
\echo '║                   DATA INTEGRITY FIXES COMPLETE                          ║'
\echo '╚══════════════════════════════════════════════════════════════════════════╝'
