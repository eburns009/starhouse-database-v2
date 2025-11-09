-- ============================================================================
-- FAANG DATA ENHANCEMENT AUDIT
-- ============================================================================
-- Comprehensive analysis of data quality and enhancement opportunities
-- ============================================================================

\echo '════════════════════════════════════════════════════════════'
\echo 'FAANG DATA ENHANCEMENT AUDIT'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Current database size
SELECT
  'Total Contacts' as metric,
  COUNT(*) as value
FROM contacts;

\echo ''
\echo '┌────────────────────────────────────────────────────────────┐'
\echo '│ SECTION 1: DATA COMPLETENESS SCORECARD                    │'
\echo '└────────────────────────────────────────────────────────────┘'
\echo ''

SELECT
  field,
  total,
  populated,
  missing,
  completeness,
  CASE
    WHEN completeness_pct >= 95 THEN '🟢 Excellent'
    WHEN completeness_pct >= 70 THEN '🟡 Good'
    WHEN completeness_pct >= 40 THEN '🟠 Fair'
    ELSE '🔴 Poor'
  END as grade
FROM (
  SELECT
    'Email (required)' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE email IS NOT NULL AND email <> '') as populated,
    COUNT(*) FILTER (WHERE email IS NULL OR email = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NOT NULL AND email <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NOT NULL AND email <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'First Name' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE first_name IS NOT NULL AND first_name <> '') as populated,
    COUNT(*) FILTER (WHERE first_name IS NULL OR first_name = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE first_name IS NOT NULL AND first_name <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE first_name IS NOT NULL AND first_name <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'Last Name' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE last_name IS NOT NULL AND last_name <> '') as populated,
    COUNT(*) FILTER (WHERE last_name IS NULL OR last_name = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE last_name IS NOT NULL AND last_name <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE last_name IS NOT NULL AND last_name <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'Phone Number' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone <> '') as populated,
    COUNT(*) FILTER (WHERE phone IS NULL OR phone = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE phone IS NOT NULL AND phone <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'Billing Address' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL AND address_line_1 <> '') as populated,
    COUNT(*) FILTER (WHERE address_line_1 IS NULL OR address_line_1 = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL AND address_line_1 <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE address_line_1 IS NOT NULL AND address_line_1 <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'Shipping Address' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 <> '') as populated,
    COUNT(*) FILTER (WHERE shipping_address_line_1 IS NULL OR shipping_address_line_1 = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'City' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE city IS NOT NULL AND city <> '') as populated,
    COUNT(*) FILTER (WHERE city IS NULL OR city = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE city IS NOT NULL AND city <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE city IS NOT NULL AND city <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'State' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE state IS NOT NULL AND state <> '') as populated,
    COUNT(*) FILTER (WHERE state IS NULL OR state = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE state IS NOT NULL AND state <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE state IS NOT NULL AND state <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'Zip Code' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE zipcode IS NOT NULL AND zipcode <> '') as populated,
    COUNT(*) FILTER (WHERE zipcode IS NULL OR zipcode = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE zipcode IS NOT NULL AND zipcode <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE zipcode IS NOT NULL AND zipcode <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts

  UNION ALL

  SELECT
    'Country' as field,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE country IS NOT NULL AND country <> '') as populated,
    COUNT(*) FILTER (WHERE country IS NULL OR country = '') as missing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE country IS NOT NULL AND country <> '') / COUNT(*), 1) as completeness_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE country IS NOT NULL AND country <> '') / COUNT(*), 1)::text || '%' as completeness
  FROM contacts
) subq
ORDER BY completeness_pct DESC;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo ''
\echo '┌────────────────────────────────────────────────────────────┐'
\echo '│ SECTION 2: ADDRESS VALIDATION OPPORTUNITIES               │'
\echo '└────────────────────────────────────────────────────────────┘'
\echo ''

SELECT
  'Contacts with billing address' as category,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM contacts), 1)::text || '%' as percentage
FROM contacts
WHERE address_line_1 IS NOT NULL AND address_line_1 <> ''

UNION ALL

SELECT
  '  → Verified' as category,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM contacts WHERE address_line_1 IS NOT NULL), 0), 1)::text || '%' as percentage
FROM contacts
WHERE address_line_1 IS NOT NULL
  AND billing_address_verified = true

UNION ALL

SELECT
  '  → NOT Verified (OPPORTUNITY)' as category,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM contacts WHERE address_line_1 IS NOT NULL), 0), 1)::text || '%' as percentage
FROM contacts
WHERE address_line_1 IS NOT NULL
  AND (billing_address_verified = false OR billing_address_verified IS NULL)

UNION ALL

SELECT
  'Contacts with shipping address' as category,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM contacts), 1)::text || '%' as percentage
FROM contacts
WHERE shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 <> ''

UNION ALL

SELECT
  '  → NOT Verified (OPPORTUNITY)' as category,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM contacts WHERE shipping_address_line_1 IS NOT NULL), 0), 1)::text || '%' as percentage
FROM contacts
WHERE shipping_address_line_1 IS NOT NULL
  AND (shipping_address_verified = false OR shipping_address_verified IS NULL);

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo ''
\echo '┌────────────────────────────────────────────────────────────┐'
\echo '│ SECTION 3: PHONE NUMBER ENRICHMENT OPPORTUNITIES          │'
\echo '└────────────────────────────────────────────────────────────┘'
\echo ''

SELECT
  'Contacts WITHOUT phone' as category,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM contacts), 1)::text || '%' as pct_of_total
FROM contacts
WHERE phone IS NULL OR phone = ''

UNION ALL

SELECT
  '  → Have transactions (could enrich from Kajabi/PayPal)' as category,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM contacts WHERE phone IS NULL OR phone = ''), 0), 1)::text || '%' as pct_of_no_phone
FROM contacts
WHERE (phone IS NULL OR phone = '')
  AND EXISTS (SELECT 1 FROM transactions WHERE contact_id = contacts.id)

UNION ALL

SELECT
  '  → Have subscriptions (could enrich from PayPal)' as category,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM contacts WHERE phone IS NULL OR phone = ''), 0), 1)::text || '%' as pct_of_no_phone
FROM contacts
WHERE (phone IS NULL OR phone = '')
  AND EXISTS (SELECT 1 FROM subscriptions WHERE contact_id = contacts.id);

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo ''
\echo '┌────────────────────────────────────────────────────────────┐'
\echo '│ SECTION 4: ACTIVITY-BASED SEGMENTATION                    │'
\echo '└────────────────────────────────────────────────────────────┘'
\echo ''

SELECT
  activity_level,
  count,
  ROUND(100.0 * count / (SELECT COUNT(*) FROM contacts), 1)::text || '%' as percentage,
  CASE
    WHEN activity_level LIKE '%Never%' THEN '🔴 Consider archiving or re-engagement'
    WHEN activity_level LIKE '%Low%' THEN '🟠 Re-engagement opportunity'
    WHEN activity_level LIKE '%Medium%' THEN '🟡 Active, enrich for retention'
    ELSE '🟢 High-value, prioritize data quality'
  END as recommendation
FROM (
  SELECT
    CASE
      WHEN txn_count = 0 AND sub_count = 0 THEN 'Never Transacted'
      WHEN txn_count = 1 THEN 'Low Activity (1 txn)'
      WHEN txn_count BETWEEN 2 AND 5 THEN 'Medium Activity (2-5 txns)'
      WHEN txn_count BETWEEN 6 AND 20 THEN 'High Activity (6-20 txns)'
      ELSE 'Very High Activity (20+ txns)'
    END as activity_level,
    COUNT(*) as count
  FROM (
    SELECT
      c.id,
      (SELECT COUNT(*) FROM transactions WHERE contact_id = c.id) as txn_count,
      (SELECT COUNT(*) FROM subscriptions WHERE contact_id = c.id) as sub_count
    FROM contacts c
  ) activity
  GROUP BY activity_level
) subq
ORDER BY
  CASE activity_level
    WHEN 'Very High Activity (20+ txns)' THEN 1
    WHEN 'High Activity (6-20 txns)' THEN 2
    WHEN 'Medium Activity (2-5 txns)' THEN 3
    WHEN 'Low Activity (1 txn)' THEN 4
    ELSE 5
  END;

\echo ''
\echo '════════════════════════════════════════════════════════════'
