-- ============================================================================
-- FAANG-LEVEL DUPLICATE ANALYSIS WITH CONFIDENCE SCORING
-- ============================================================================
-- Multi-signal approach to identify remaining duplicates without phone data
-- Scoring model: 100 points max
--   - Email domain similarity: 30 points
--   - Transaction patterns: 20 points
--   - Address overlap: 25 points
--   - Tag overlap: 15 points
--   - Account age proximity: 10 points
-- ============================================================================

\echo '════════════════════════════════════════════════════════════'
\echo 'FAANG DUPLICATE ANALYSIS: Multi-Signal Confidence Scoring'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Step 1: Identify duplicate groups (same name, no phone OR missing phone)
DROP TABLE IF EXISTS temp_dup_groups;
CREATE TEMP TABLE temp_dup_groups AS
SELECT
  LOWER(TRIM(first_name || ' ' || last_name)) as full_name,
  id as contact_id,
  email,
  phone,
  created_at,
  (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) as txn_count,
  address_line_1,
  shipping_address_line_1
FROM contacts
WHERE TRIM(first_name || ' ' || last_name) <> ''
  AND LOWER(TRIM(first_name || ' ' || last_name)) IN (
    SELECT LOWER(TRIM(first_name || ' ' || last_name))
    FROM contacts
    WHERE TRIM(first_name || ' ' || last_name) <> ''
    GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
    HAVING COUNT(*) > 1
      AND (COUNT(DISTINCT phone) FILTER (WHERE phone IS NOT NULL AND phone <> '') <> 1
           OR COUNT(*) FILTER (WHERE phone IS NULL OR phone = '') > 0)
  );

\echo 'Step 1: Identified duplicate groups'
\echo ''

-- Step 2: Build pairwise comparison with scoring
DROP TABLE IF EXISTS temp_dup_pairs;
CREATE TEMP TABLE temp_dup_pairs AS
SELECT
  t1.full_name,
  t1.contact_id as contact_1_id,
  t2.contact_id as contact_2_id,
  t1.email as email_1,
  t2.email as email_2,

  -- SIGNAL 1: Email domain (30 points)
  CASE
    WHEN SUBSTRING(t1.email FROM '@(.*)$') = SUBSTRING(t2.email FROM '@(.*)$')
    THEN 30
    ELSE 0
  END as email_domain_score,

  -- SIGNAL 2: Transaction patterns (20 points)
  CASE
    WHEN t1.txn_count = 0 AND t2.txn_count = 0 THEN 20  -- Both inactive
    WHEN t1.txn_count > 0 AND t2.txn_count = 0 THEN 10  -- One active
    WHEN t1.txn_count = 0 AND t2.txn_count > 0 THEN 10  -- One active
    WHEN ABS(t1.txn_count - t2.txn_count) <= 2 THEN 15  -- Similar activity
    ELSE 5  -- Different activity levels
  END as transaction_score,

  -- SIGNAL 3: Address overlap (25 points)
  CASE
    WHEN t1.address_line_1 IS NOT NULL
     AND t2.address_line_1 IS NOT NULL
     AND t1.address_line_1 = t2.address_line_1
    THEN 25  -- Same billing address
    WHEN t1.shipping_address_line_1 IS NOT NULL
     AND t2.shipping_address_line_1 IS NOT NULL
     AND t1.shipping_address_line_1 = t2.shipping_address_line_1
    THEN 25  -- Same shipping address
    WHEN (t1.address_line_1 IS NULL OR t1.address_line_1 = '')
     AND (t2.address_line_1 IS NULL OR t2.address_line_1 = '')
    THEN 10  -- Both have no address
    ELSE 0
  END as address_score,

  -- SIGNAL 4: Tag overlap (15 points)
  (SELECT
    CASE
      WHEN COUNT(*) > 0 THEN 15
      ELSE 0
    END
   FROM contact_tags ct1
   INNER JOIN contact_tags ct2 ON ct1.tag_id = ct2.tag_id
   WHERE ct1.contact_id = t1.contact_id
     AND ct2.contact_id = t2.contact_id
  ) as tag_score,

  -- SIGNAL 5: Account age proximity (10 points)
  CASE
    WHEN ABS(EXTRACT(EPOCH FROM (t1.created_at - t2.created_at))) < 30 * 24 * 3600 THEN 10  -- Within 30 days
    WHEN ABS(EXTRACT(EPOCH FROM (t1.created_at - t2.created_at))) < 90 * 24 * 3600 THEN 5   -- Within 90 days
    ELSE 0
  END as age_proximity_score,

  -- Metadata
  t1.txn_count as txn_count_1,
  t2.txn_count as txn_count_2,
  t1.created_at as created_1,
  t2.created_at as created_2

FROM temp_dup_groups t1
INNER JOIN temp_dup_groups t2
  ON t1.full_name = t2.full_name
  AND t1.contact_id < t2.contact_id;  -- Avoid duplicate pairs

-- Add total confidence score
ALTER TABLE temp_dup_pairs ADD COLUMN confidence_score INTEGER;

UPDATE temp_dup_pairs
SET confidence_score = email_domain_score + transaction_score + address_score + tag_score + age_proximity_score;

\echo 'Step 2: Calculated confidence scores for all pairs'
\echo ''

-- Step 3: Show results
\echo '════════════════════════════════════════════════════════════'
\echo 'CONFIDENCE SCORE DISTRIBUTION'
\echo '════════════════════════════════════════════════════════════'

SELECT
  CASE
    WHEN confidence_score >= 90 THEN '🟢 Very High (90-100) - AUTO MERGE'
    WHEN confidence_score >= 70 THEN '🟡 High (70-89) - REVIEW & MERGE'
    WHEN confidence_score >= 50 THEN '🟠 Medium (50-69) - MANUAL REVIEW'
    ELSE '🔴 Low (<50) - SKIP OR DEEP REVIEW'
  END as confidence_level,
  COUNT(*) as pairs,
  COUNT(*) * 2 as contacts_affected,
  MIN(confidence_score) || '-' || MAX(confidence_score) as score_range
FROM temp_dup_pairs
GROUP BY
  CASE
    WHEN confidence_score >= 90 THEN '🟢 Very High (90-100) - AUTO MERGE'
    WHEN confidence_score >= 70 THEN '🟡 High (70-89) - REVIEW & MERGE'
    WHEN confidence_score >= 50 THEN '🟠 Medium (50-69) - MANUAL REVIEW'
    ELSE '🔴 Low (<50) - SKIP OR DEEP REVIEW'
  END
ORDER BY MIN(confidence_score) DESC;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'TOP 15 HIGHEST CONFIDENCE MATCHES'
\echo '════════════════════════════════════════════════════════════'

SELECT
  full_name,
  confidence_score as score,
  email_1,
  email_2,
  'D:' || email_domain_score || ' T:' || transaction_score || ' A:' || address_score ||
  ' Tag:' || tag_score || ' Age:' || age_proximity_score as breakdown
FROM temp_dup_pairs
ORDER BY confidence_score DESC, full_name
LIMIT 15;

\echo ''
\echo '════════════════════════════════════════════════════════════'
