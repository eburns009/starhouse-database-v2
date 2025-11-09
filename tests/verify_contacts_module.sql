-- ============================================================================
-- CONTACTS MODULE - COMPREHENSIVE VERIFICATION
-- ============================================================================
-- FAANG-Level Quality Testing
-- Verifies data integrity, consistency, and completeness
-- ============================================================================

\timing on

\echo ''
\echo '╔══════════════════════════════════════════════════════════════════════════╗'
\echo '║              CONTACTS MODULE - VERIFICATION TEST SUITE                   ║'
\echo '║                        FAANG Quality Standards                           ║'
\echo '╚══════════════════════════════════════════════════════════════════════════╝'
\echo ''

-- ============================================================================
-- TEST 1: DATA INTEGRITY - Subscriptions
-- ============================================================================
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 1: Subscription Data Integrity'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- 1.1: Active subscriptions must have membership_product_id
SELECT
    '1.1' as test_id,
    'Active subscriptions with membership_product_id' as test_name,
    COUNT(*) FILTER (WHERE membership_product_id IS NOT NULL) as pass_count,
    COUNT(*) FILTER (WHERE membership_product_id IS NULL) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE membership_product_id IS NULL) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions
WHERE status = 'active';

-- 1.2: Active subscriptions amount must match product price
SELECT
    '1.2' as test_id,
    'Subscription amount matches product price' as test_name,
    COUNT(*) FILTER (WHERE
        (s.amount = mp.monthly_price OR s.amount = mp.annual_price)
    ) as pass_count,
    COUNT(*) FILTER (WHERE
        s.amount != mp.monthly_price AND s.amount != mp.annual_price
    ) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE s.amount != mp.monthly_price AND s.amount != mp.annual_price) = 0
        THEN '✅ PASS'
        ELSE '⚠️  WARNING'
    END as result
FROM subscriptions s
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active';

-- 1.3: is_annual flag consistency check
SELECT
    '1.3' as test_id,
    'is_annual flag matches amount (annual vs monthly)' as test_name,
    COUNT(*) FILTER (WHERE
        (s.is_annual = TRUE AND s.amount = mp.annual_price) OR
        (s.is_annual = FALSE AND s.amount = mp.monthly_price) OR
        s.is_annual IS NULL
    ) as pass_count,
    COUNT(*) FILTER (WHERE
        (s.is_annual = TRUE AND s.amount != mp.annual_price) OR
        (s.is_annual = FALSE AND s.amount != mp.monthly_price)
    ) as fail_count,
    COUNT(*) as total,
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

-- ============================================================================
-- TEST 2: DATA INTEGRITY - Contacts
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 2: Contact Data Integrity'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- 2.1: Contacts with active subscriptions must have membership_level
SELECT
    '2.1' as test_id,
    'Active subscribers have membership_level populated' as test_name,
    COUNT(*) FILTER (WHERE c.membership_level IS NOT NULL AND c.membership_level != '') as pass_count,
    COUNT(*) FILTER (WHERE c.membership_level IS NULL OR c.membership_level = '') as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE c.membership_level IS NULL OR c.membership_level = '') = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM contacts c
WHERE c.has_active_subscription = TRUE;

-- 2.2: membership_level must match active subscription product
SELECT
    '2.2' as test_id,
    'Contact membership_level matches subscription product' as test_name,
    COUNT(*) FILTER (WHERE c.membership_level = mp.membership_level) as pass_count,
    COUNT(*) FILTER (WHERE c.membership_level != mp.membership_level OR c.membership_level IS NULL) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE c.membership_level != mp.membership_level OR c.membership_level IS NULL) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM contacts c
JOIN subscriptions s ON c.id = s.contact_id
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active' AND c.has_active_subscription = TRUE;

-- 2.3: has_active_subscription flag accuracy
SELECT
    '2.3' as test_id,
    'has_active_subscription flag is accurate' as test_name,
    COUNT(*) FILTER (WHERE
        (c.has_active_subscription = TRUE AND EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        )) OR
        (c.has_active_subscription = FALSE AND NOT EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        ))
    ) as pass_count,
    COUNT(*) FILTER (WHERE
        (c.has_active_subscription = TRUE AND NOT EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        )) OR
        (c.has_active_subscription = FALSE AND EXISTS(
            SELECT 1 FROM subscriptions s2 WHERE s2.contact_id = c.id AND s2.status = 'active'
        ))
    ) as fail_count,
    COUNT(*) as total,
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

-- 2.4: Email format validation
SELECT
    '2.4' as test_id,
    'All contact emails are valid format' as test_name,
    COUNT(*) FILTER (WHERE email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$') as pass_count,
    COUNT(*) FILTER (WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$') as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$') = 0
        THEN '✅ PASS'
        ELSE '⚠️  WARNING'
    END as result
FROM contacts
WHERE email IS NOT NULL;

-- ============================================================================
-- TEST 3: REFERENTIAL INTEGRITY
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 3: Referential Integrity'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- 3.1: All subscriptions reference valid contacts
SELECT
    '3.1' as test_id,
    'All subscriptions reference valid contacts' as test_name,
    COUNT(*) FILTER (WHERE c.id IS NOT NULL) as pass_count,
    COUNT(*) FILTER (WHERE c.id IS NULL) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE c.id IS NULL) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions s
LEFT JOIN contacts c ON s.contact_id = c.id;

-- 3.2: All active subscriptions reference valid membership products
SELECT
    '3.2' as test_id,
    'Active subscriptions reference valid products' as test_name,
    COUNT(*) FILTER (WHERE mp.id IS NOT NULL) as pass_count,
    COUNT(*) FILTER (WHERE mp.id IS NULL) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE mp.id IS NULL) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions s
LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active';

-- ============================================================================
-- TEST 4: BUSINESS LOGIC
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 4: Business Logic Validation'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- 4.1: No contact should have multiple active subscriptions (data model constraint)
SELECT
    '4.1' as test_id,
    'Contacts with multiple active subscriptions' as test_name,
    COUNT(*) FILTER (WHERE sub_count = 1) as pass_count,
    COUNT(*) FILTER (WHERE sub_count > 1) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE sub_count > 1) = 0
        THEN '✅ PASS'
        ELSE '⚠️  WARNING (check if intentional)'
    END as result
FROM (
    SELECT contact_id, COUNT(*) as sub_count
    FROM subscriptions
    WHERE status = 'active'
    GROUP BY contact_id
) sub_counts;

-- 4.2: Subscription amounts must be positive
SELECT
    '4.2' as test_id,
    'All subscription amounts are positive' as test_name,
    COUNT(*) FILTER (WHERE amount > 0) as pass_count,
    COUNT(*) FILTER (WHERE amount <= 0) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE amount <= 0) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions
WHERE status = 'active';

-- 4.3: Start date should be before or equal to next billing date
SELECT
    '4.3' as test_id,
    'Start date <= next billing date' as test_name,
    COUNT(*) FILTER (WHERE start_date <= next_billing_date OR next_billing_date IS NULL) as pass_count,
    COUNT(*) FILTER (WHERE start_date > next_billing_date AND next_billing_date IS NOT NULL) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE start_date > next_billing_date AND next_billing_date IS NOT NULL) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions
WHERE status = 'active';

-- ============================================================================
-- TEST 5: PERFORMANCE CHECKS
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 5: Performance Validation'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

\echo 'Testing v_contact_list_optimized view performance...'
EXPLAIN ANALYZE
SELECT * FROM v_contact_list_optimized LIMIT 50;

\echo ''
\echo 'Testing v_contact_detail_enriched view performance...'
EXPLAIN ANALYZE
SELECT * FROM v_contact_detail_enriched
WHERE id = (SELECT id FROM contacts LIMIT 1);

\echo ''
\echo 'Testing search_contacts function performance...'
EXPLAIN ANALYZE
SELECT * FROM search_contacts('john', 50, 0);

-- ============================================================================
-- TEST 6: PAYPAL SUBSCRIPTION SPECIFIC TESTS
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 6: PayPal Subscription Data Quality'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- 6.1: All PayPal subscriptions have proper reference format
SELECT
    '6.1' as test_id,
    'PayPal references have correct format (I-XXXX)' as test_name,
    COUNT(*) FILTER (WHERE paypal_subscription_reference ~ '^I-[A-Z0-9]+$') as pass_count,
    COUNT(*) FILTER (WHERE paypal_subscription_reference !~ '^I-[A-Z0-9]+$') as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE paypal_subscription_reference !~ '^I-[A-Z0-9]+$') = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions
WHERE paypal_subscription_reference IS NOT NULL;

-- 6.2: All active PayPal subscriptions have membership product
SELECT
    '6.2' as test_id,
    'Active PayPal subs have membership_product_id' as test_name,
    COUNT(*) FILTER (WHERE membership_product_id IS NOT NULL) as pass_count,
    COUNT(*) FILTER (WHERE membership_product_id IS NULL) as fail_count,
    COUNT(*) as total,
    CASE
        WHEN COUNT(*) FILTER (WHERE membership_product_id IS NULL) = 0
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM subscriptions
WHERE status = 'active' AND paypal_subscription_reference IS NOT NULL;

-- ============================================================================
-- TEST 7: SPECIFIC ISSUE VERIFICATION
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'TEST 7: Verify Specific Fixes from Today'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

-- 7.1: Verify brieandbjorn@gmail.com has membership level
\echo '7.1: Verifying brieandbjorn@gmail.com (original issue)...'
SELECT
    '7.1' as test_id,
    'brieandbjorn@gmail.com has membership level' as test_name,
    email,
    membership_level,
    has_active_subscription,
    CASE
        WHEN membership_level = 'Antares' AND has_active_subscription = TRUE
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM contacts
WHERE email = 'brieandbjorn@gmail.com';

-- 7.2: Verify Scott Medina (missing PayPal subscription)
\echo '7.2: Verifying mysticcker@aol.com (missing PayPal subscription)...'
SELECT
    '7.2' as test_id,
    'mysticcker@aol.com has Astral Partner subscription' as test_name,
    c.email,
    c.membership_level,
    s.paypal_subscription_reference,
    s.amount,
    CASE
        WHEN s.paypal_subscription_reference = 'I-62RBW0RK1J8L'
         AND c.membership_level = 'Astral Partner'
         AND s.amount = 1089.00
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as result
FROM contacts c
JOIN subscriptions s ON c.id = s.contact_id
WHERE c.email = 'mysticcker@aol.com' AND s.status = 'active';

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================
\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'DATABASE SUMMARY STATISTICS'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

SELECT
    'Total Contacts' as metric,
    COUNT(*)::text as value
FROM contacts
UNION ALL
SELECT
    'Contacts with Active Subscriptions',
    COUNT(*)::text
FROM contacts
WHERE has_active_subscription = TRUE
UNION ALL
SELECT
    'Total Subscriptions',
    COUNT(*)::text
FROM subscriptions
UNION ALL
SELECT
    'Active Subscriptions',
    COUNT(*)::text
FROM subscriptions
WHERE status = 'active'
UNION ALL
SELECT
    'PayPal Subscription References',
    COUNT(DISTINCT paypal_subscription_reference)::text
FROM subscriptions
WHERE paypal_subscription_reference IS NOT NULL
UNION ALL
SELECT
    'Membership Products',
    COUNT(*)::text
FROM membership_products;

\echo ''
\echo '╔══════════════════════════════════════════════════════════════════════════╗'
\echo '║                    VERIFICATION COMPLETE                                 ║'
\echo '╚══════════════════════════════════════════════════════════════════════════╝'
\echo ''

\timing off
