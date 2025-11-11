-- ============================================================================
-- REVISE LOCK STRATEGY - Fix Overly Aggressive Locking
-- ============================================================================
-- Purpose: Unlock Kajabi contacts that should be updatable by Kajabi imports
-- Author: Claude Code
-- Date: 2025-11-11
--
-- Problem: Current lock catches 99.94% of Kajabi contacts because they've
--          been updated by automated processes (lockdown, protection, merges)
--
-- Solution: Only lock if there's actual enrichment or manual work to preserve
-- ============================================================================

BEGIN;

-- 1. Reset Kajabi locks (will re-apply with better criteria)
-- ============================================================================
UPDATE contacts
SET
  lock_level = NULL,
  import_locked = FALSE,
  import_locked_reason = NULL
WHERE
  source_system = 'kajabi'
  AND deleted_at IS NULL;

-- 2. FULL_LOCK: Kajabi contacts with significant enrichment
-- ============================================================================
UPDATE contacts
SET
  lock_level = 'FULL_LOCK',
  import_locked = TRUE,
  import_locked_reason = CASE
    WHEN (paypal_email IS NOT NULL AND zoho_id IS NOT NULL) THEN 'Multi-source: PayPal + Zoho enrichment'
    WHEN (additional_email IS NOT NULL AND zoho_id IS NOT NULL) THEN 'Multi-source: Additional email + Zoho'
    WHEN (additional_email IS NOT NULL AND paypal_email IS NOT NULL) THEN 'Multi-source: Additional + PayPal'
    WHEN (paypal_email IS NOT NULL AND paypal_first_name IS NOT NULL AND zoho_id IS NOT NULL) THEN 'Heavy PayPal + Zoho enrichment'
    ELSE 'Multi-source enrichment'
  END
WHERE
  source_system = 'kajabi'
  AND deleted_at IS NULL
  AND (
    -- True multi-source enrichment (2+ external sources)
    (paypal_email IS NOT NULL AND zoho_id IS NOT NULL) OR
    (additional_email IS NOT NULL AND zoho_id IS NOT NULL) OR
    (additional_email IS NOT NULL AND paypal_email IS NOT NULL)
  );

-- 3. PARTIAL_LOCK: Kajabi contacts with single-source enrichment
-- ============================================================================
-- Allow Kajabi to update subscription, but preserve enriched data
UPDATE contacts
SET
  lock_level = 'PARTIAL_LOCK',
  import_locked = FALSE,
  import_locked_reason = CASE
    WHEN paypal_email IS NOT NULL THEN 'Has PayPal enrichment'
    WHEN zoho_id IS NOT NULL THEN 'Has Zoho enrichment'
    WHEN additional_email IS NOT NULL THEN 'Has additional email'
    ELSE 'Has enrichment data'
  END
WHERE
  source_system = 'kajabi'
  AND deleted_at IS NULL
  AND lock_level IS NULL  -- Not already locked
  AND (
    -- Single-source enrichment
    paypal_email IS NOT NULL OR
    zoho_id IS NOT NULL OR
    additional_email IS NOT NULL OR
    paypal_first_name IS NOT NULL OR
    zoho_email IS NOT NULL
  );

-- 4. UNLOCKED: Pure Kajabi contacts (no enrichment)
-- ============================================================================
-- Allow full Kajabi updates
UPDATE contacts
SET
  lock_level = 'UNLOCKED',
  import_locked = FALSE,
  import_locked_reason = NULL
WHERE
  source_system = 'kajabi'
  AND deleted_at IS NULL
  AND lock_level IS NULL;

-- 5. Keep other sources FULL_LOCK
-- ============================================================================
-- Don't change manual, ticket_tailor, zoho, paypal
-- (already set correctly in previous script)

-- 6. Verification
-- ============================================================================
\echo ''
\echo '================================================================================'
\echo '  REVISED LOCK DISTRIBUTION'
\echo '================================================================================'
\echo ''

SELECT
  lock_level,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct_total,
  STRING_AGG(DISTINCT source_system, ', ' ORDER BY source_system) as sources
FROM contacts
WHERE deleted_at IS NULL
GROUP BY lock_level
ORDER BY
  CASE lock_level
    WHEN 'FULL_LOCK' THEN 1
    WHEN 'PARTIAL_LOCK' THEN 2
    WHEN 'UNLOCKED' THEN 3
    ELSE 4
  END;

\echo ''
\echo 'Kajabi-specific breakdown:'
\echo ''

SELECT
  lock_level,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct_of_kajabi,
  CASE lock_level
    WHEN 'FULL_LOCK' THEN 'No updates'
    WHEN 'PARTIAL_LOCK' THEN 'Subscription + Kajabi fields only'
    WHEN 'UNLOCKED' THEN 'Full updates allowed'
  END as import_behavior
FROM contacts
WHERE source_system = 'kajabi'
  AND deleted_at IS NULL
GROUP BY lock_level
ORDER BY
  CASE lock_level
    WHEN 'FULL_LOCK' THEN 1
    WHEN 'PARTIAL_LOCK' THEN 2
    WHEN 'UNLOCKED' THEN 3
  END;

\echo ''
\echo 'Can be updated by Kajabi import:'
\echo ''

SELECT
  CASE
    WHEN lock_level IN ('PARTIAL_LOCK', 'UNLOCKED') THEN 'Can update'
    ELSE 'Cannot update'
  END as status,
  COUNT(*) as kajabi_contacts,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct
FROM contacts
WHERE source_system = 'kajabi'
  AND deleted_at IS NULL
GROUP BY status;

\echo ''
\echo '================================================================================'
\echo ''

COMMIT;
