-- ============================================================================
-- TIERED LOCK STRATEGY
-- ============================================================================
-- Purpose: Replace binary lock with tiered protection levels
-- Author: Claude Code
-- Date: 2025-11-11
--
-- Lock Levels:
--   FULL_LOCK: No import updates allowed (manual, ticket_tailor, multi-source)
--   PARTIAL_LOCK: Allow source-of-truth updates, preserve enrichment
--   UNLOCKED: Allow full updates from source of truth
-- ============================================================================

BEGIN;

-- 1. Add lock_level column
-- ============================================================================
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS lock_level TEXT;

COMMENT ON COLUMN contacts.lock_level IS
  'Import protection level: FULL_LOCK (no updates), PARTIAL_LOCK (selective updates), UNLOCKED (full updates allowed)';

-- 2. FULL_LOCK: Critical contacts (never update via import)
-- ============================================================================
UPDATE contacts
SET
  lock_level = 'FULL_LOCK',
  import_locked = TRUE,
  import_locked_reason = CASE
    WHEN source_system = 'manual' THEN 'Staff-entered data - manual review required'
    WHEN source_system = 'ticket_tailor' THEN 'Ticket Tailor source - preserve event data'
    WHEN source_system = 'zoho' THEN 'Zoho CRM source - preserve relationship data'
    WHEN (paypal_email IS NOT NULL AND zoho_id IS NOT NULL) THEN 'Multi-source enrichment - high value data'
    WHEN (additional_email IS NOT NULL AND paypal_email IS NOT NULL) THEN 'Multi-source enrichment - high value data'
    WHEN updated_at > created_at + INTERVAL '30 days' THEN 'Heavily edited - preserve manual work'
    ELSE 'Full lock'
  END
WHERE
  deleted_at IS NULL
  AND (
    -- Non-Kajabi sources (preserve provenance)
    source_system IN ('manual', 'ticket_tailor', 'zoho') OR

    -- Multi-source enrichment (2+ sources)
    (paypal_email IS NOT NULL AND zoho_id IS NOT NULL) OR
    (additional_email IS NOT NULL AND paypal_email IS NOT NULL) OR
    (additional_email IS NOT NULL AND zoho_id IS NOT NULL) OR

    -- Heavily edited (30+ days of updates)
    updated_at > created_at + INTERVAL '30 days'
  );

-- 3. PARTIAL_LOCK: Kajabi contacts with enrichment
-- ============================================================================
-- Allow Kajabi to update subscription status, but preserve enriched data
UPDATE contacts
SET
  lock_level = 'PARTIAL_LOCK',
  import_locked = FALSE,  -- Allow import (but controlled)
  import_locked_reason = 'Kajabi contact with enrichment - selective updates only'
WHERE
  deleted_at IS NULL
  AND source_system = 'kajabi'
  AND lock_level IS NULL  -- Not already locked
  AND (
    -- Has enrichment from other sources
    additional_email IS NOT NULL OR
    paypal_email IS NOT NULL OR
    paypal_first_name IS NOT NULL OR
    zoho_id IS NOT NULL OR
    zoho_email IS NOT NULL
  );

-- 4. UNLOCKED: Pure Kajabi contacts (allow full updates)
-- ============================================================================
-- These are pure Kajabi contacts with no enrichment - safe to fully update
UPDATE contacts
SET
  lock_level = 'UNLOCKED',
  import_locked = FALSE,
  import_locked_reason = NULL
WHERE
  deleted_at IS NULL
  AND source_system = 'kajabi'
  AND lock_level IS NULL  -- Not already locked
  AND additional_email IS NULL
  AND paypal_email IS NULL
  AND zoho_id IS NULL;

-- 5. UNLOCKED: PayPal-only contacts (no Kajabi ID)
-- ============================================================================
-- PayPal contacts without Kajabi ID - likely not in Kajabi system
-- But should be PARTIAL if they have other enrichment
UPDATE contacts
SET
  lock_level = CASE
    WHEN additional_email IS NOT NULL OR zoho_id IS NOT NULL THEN 'PARTIAL_LOCK'
    ELSE 'UNLOCKED'
  END,
  import_locked = CASE
    WHEN additional_email IS NOT NULL OR zoho_id IS NOT NULL THEN TRUE
    ELSE FALSE
  END,
  import_locked_reason = CASE
    WHEN additional_email IS NOT NULL OR zoho_id IS NOT NULL THEN 'PayPal with enrichment'
    ELSE NULL
  END
WHERE
  deleted_at IS NULL
  AND source_system = 'paypal'
  AND lock_level IS NULL;

-- 6. Verification & Distribution
-- ============================================================================
\echo ''
\echo '================================================================================'
\echo '  TIERED LOCK DISTRIBUTION'
\echo '================================================================================'
\echo ''

SELECT
  lock_level,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct,
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
\echo 'Breakdown by source_system:'
\echo ''

SELECT
  source_system,
  lock_level,
  COUNT(*) as contacts,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY source_system), 2) as pct_of_source
FROM contacts
WHERE deleted_at IS NULL
GROUP BY source_system, lock_level
ORDER BY source_system,
  CASE lock_level
    WHEN 'FULL_LOCK' THEN 1
    WHEN 'PARTIAL_LOCK' THEN 2
    WHEN 'UNLOCKED' THEN 3
    ELSE 4
  END;

\echo ''
\echo 'Import Update Permissions:'
\echo ''

SELECT
  lock_level,
  import_locked,
  subscription_protected,
  COUNT(*) as contacts
FROM contacts
WHERE deleted_at IS NULL
GROUP BY lock_level, import_locked, subscription_protected
ORDER BY lock_level, import_locked DESC, subscription_protected DESC;

\echo ''
\echo '================================================================================'
\echo ''

-- 7. Create update rules reference table
-- ============================================================================
CREATE TABLE IF NOT EXISTS import_lock_rules (
  lock_level TEXT PRIMARY KEY,
  allows_subscription_update BOOLEAN NOT NULL,
  allows_name_update BOOLEAN NOT NULL,
  allows_address_update BOOLEAN NOT NULL,
  allows_source_system_update BOOLEAN NOT NULL,
  allows_enriched_data_update BOOLEAN NOT NULL,
  description TEXT NOT NULL
);

TRUNCATE import_lock_rules;

INSERT INTO import_lock_rules VALUES
  ('FULL_LOCK', false, false, false, false, false,
   'No updates allowed. Requires manual review for any changes.'),
  ('PARTIAL_LOCK', true, false, false, false, false,
   'Allow subscription updates from source of truth. Preserve all other data.'),
  ('UNLOCKED', true, true, true, false, false,
   'Allow full updates from source of truth. Never change source_system.');

COMMENT ON TABLE import_lock_rules IS
  'Defines what fields can be updated for each lock level during imports.';

\echo 'Import lock rules defined:'
\echo ''

SELECT * FROM import_lock_rules;

\echo ''
\echo '✅ Tiered lock strategy implemented'
\echo ''

COMMIT;
