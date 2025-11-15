-- ============================================================================
-- TEST SUITE: Validation-First Scoring Algorithm
-- ============================================================================
-- Purpose: Comprehensive testing before and after migration
-- Run this BEFORE migration to capture baseline
-- Run this AFTER migration to verify changes
-- ============================================================================

\echo '===================================================================================='
\echo 'TEST SUITE: Validation-First Scoring Algorithm'
\echo 'Run Time:' `date`
\echo '===================================================================================='
\echo ''

-- ============================================================================
-- BASELINE METRICS (Before Migration)
-- ============================================================================

\echo '------------------------------------------------------------------------------------'
\echo 'TEST 1: Overall Distribution (Baseline)'
\echo '------------------------------------------------------------------------------------'

SELECT
  confidence,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage,
  ROUND(AVG(GREATEST(billing_score, shipping_score)), 1) as avg_score
FROM mailing_list_priority
GROUP BY confidence
ORDER BY
  CASE confidence
    WHEN 'very_high' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
    WHEN 'very_low' THEN 5
  END;

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 2: Validated Contacts (DPV=Y, No NCOA Move) by Confidence'
\echo 'Expected AFTER: All should be high or very_high'
\echo '------------------------------------------------------------------------------------'

SELECT
  mlp.confidence,
  COUNT(*) as count,
  MIN(GREATEST(mlp.billing_score, mlp.shipping_score)) as min_score,
  MAX(GREATEST(mlp.billing_score, mlp.shipping_score)) as max_score,
  ROUND(AVG(GREATEST(mlp.billing_score, mlp.shipping_score)), 1) as avg_score
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE mlp.billing_usps_dpv_match_code = 'Y'
  AND c.ncoa_move_date IS NULL
GROUP BY mlp.confidence
ORDER BY
  CASE mlp.confidence
    WHEN 'very_high' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
    WHEN 'very_low' THEN 5
  END;

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 3: NCOA Moves - Should All Score 0 After Migration'
\echo '------------------------------------------------------------------------------------'

SELECT
  mlp.confidence,
  COUNT(*) as count,
  MIN(GREATEST(mlp.billing_score, mlp.shipping_score)) as min_score,
  MAX(GREATEST(mlp.billing_score, mlp.shipping_score)) as max_score,
  ROUND(AVG(GREATEST(mlp.billing_score, mlp.shipping_score)), 1) as avg_score
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE c.ncoa_move_date IS NOT NULL
GROUP BY mlp.confidence
ORDER BY
  CASE mlp.confidence
    WHEN 'very_high' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
    WHEN 'very_low' THEN 5
  END;

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 4: Specific Test Cases'
\echo '------------------------------------------------------------------------------------'

-- Case 1: Deborah Frazier - Should move from low (30) to high (60)
\echo 'Case 1: Deborah Frazier (beautyschool911@gmail.com)'
\echo 'BEFORE: confidence=low, billing_score=30'
\echo 'AFTER: confidence=high, billing_score=60'

SELECT
  c.first_name,
  c.last_name,
  c.email,
  mlp.confidence,
  mlp.billing_score,
  mlp.billing_usps_dpv_match_code,
  c.ncoa_move_date,
  c.last_transaction_date,
  c.billing_address_updated_at
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE c.email = 'beautyschool911@gmail.com';

\echo ''

-- Case 2: Sharon Montes - Should move to very_low (0) due to NCOA move
\echo 'Case 2: Sharon Montes (drsharonmontes@gmail.com)'
\echo 'BEFORE: confidence=low, billing_score=30'
\echo 'AFTER: confidence=very_low, billing_score=0 (NCOA move detected)'

SELECT
  c.first_name,
  c.last_name,
  c.email,
  mlp.confidence,
  mlp.billing_score,
  mlp.billing_usps_dpv_match_code,
  c.ncoa_move_date,
  c.last_transaction_date,
  c.billing_address_updated_at
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE c.email = 'drsharonmontes@gmail.com';

\echo ''

-- Case 3: Random very_high contact - Should stay very_high
\echo 'Case 3: Random very_high contact (should stay very_high)'

SELECT
  c.first_name,
  c.last_name,
  c.email,
  mlp.confidence,
  mlp.billing_score,
  mlp.billing_usps_dpv_match_code,
  c.ncoa_move_date,
  c.last_transaction_date
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE mlp.confidence = 'very_high'
  AND mlp.billing_usps_dpv_match_code = 'Y'
  AND c.ncoa_move_date IS NULL
ORDER BY RANDOM()
LIMIT 1;

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 5: Validation Age Distribution'
\echo '------------------------------------------------------------------------------------'

SELECT
  CASE
    WHEN mlp.billing_usps_validated_at > NOW() - INTERVAL '90 days' THEN '<90 days (score: 70)'
    WHEN mlp.billing_usps_validated_at > NOW() - INTERVAL '365 days' THEN '90-365 days (score: 65)'
    WHEN mlp.billing_usps_validated_at IS NOT NULL THEN '>365 days (score: 60)'
    ELSE 'Not validated (score: 0)'
  END as validation_age,
  COUNT(*) as count,
  COUNT(CASE WHEN mlp.billing_usps_dpv_match_code = 'Y' AND c.ncoa_move_date IS NULL THEN 1 END) as dpv_y_no_move
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
GROUP BY validation_age
ORDER BY MIN(mlp.billing_usps_validated_at) DESC NULLS LAST;

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 6: Problem Contacts - Validated but Low Scored'
\echo 'BEFORE: Should show ~483 contacts'
\echo 'AFTER: Should show 0 contacts'
\echo '------------------------------------------------------------------------------------'

SELECT
  COUNT(*) as problem_count,
  ROUND(AVG(GREATEST(mlp.billing_score, mlp.shipping_score)), 1) as avg_current_score
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE mlp.billing_usps_dpv_match_code = 'Y'
  AND c.ncoa_move_date IS NULL
  AND mlp.confidence IN ('low', 'very_low');

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 7: NCOA Moves Incorrectly Scored High'
\echo 'BEFORE: Should show contacts with score > 0'
\echo 'AFTER: Should show 0 contacts (all NCOA moves score 0)'
\echo '------------------------------------------------------------------------------------'

SELECT
  COUNT(*) as ncoa_moves_scored_high,
  MIN(GREATEST(mlp.billing_score, mlp.shipping_score)) as min_score,
  MAX(GREATEST(mlp.billing_score, mlp.shipping_score)) as max_score
FROM mailing_list_priority mlp
JOIN contacts c ON mlp.id = c.id
WHERE c.ncoa_move_date IS NOT NULL
  AND GREATEST(mlp.billing_score, mlp.shipping_score) > 0;

\echo ''
\echo '------------------------------------------------------------------------------------'
\echo 'TEST 8: Mailing List Size (High + Very High)'
\echo 'BEFORE: ~832 contacts'
\echo 'AFTER: ~1,315 contacts'
\echo '------------------------------------------------------------------------------------'

SELECT
  COUNT(*) as mailable_contacts,
  COUNT(CASE WHEN confidence = 'very_high' THEN 1 END) as very_high_count,
  COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_count
FROM mailing_list_priority
WHERE confidence IN ('very_high', 'high');

\echo ''
\echo '===================================================================================='
\echo 'TEST SUITE COMPLETE'
\echo '===================================================================================='
\echo ''
