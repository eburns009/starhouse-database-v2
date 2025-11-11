-- ============================================================================
-- RESTORE LOST OPT-INS FROM MERGE OPERATIONS
-- ============================================================================
-- Purpose: Restore email_subscribed = TRUE for contacts who lost opt-in status during merges
-- Author: Claude Code
-- Date: 2025-11-11
--
-- Context: During recent merge operations (last 30 days), 50 contacts lost their
--          email_subscribed = TRUE status when a subscribed duplicate was merged
--          into an unsubscribed primary contact.
--
-- Safety: This script has full audit trail, dry-run mode, and rollback capability
-- ============================================================================

-- Configuration
\set DRY_RUN true  -- Change to false to execute

BEGIN;

-- 1. Create restoration audit table
-- ============================================================================
CREATE TABLE IF NOT EXISTS subscription_restoration_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID REFERENCES contacts(id),
  email TEXT NOT NULL,

  -- State before restoration
  old_subscribed BOOLEAN NOT NULL,
  old_source_system TEXT,

  -- Why we're restoring
  merge_backup_id INTEGER,
  duplicate_was_subscribed BOOLEAN NOT NULL,
  duplicate_source_system TEXT,
  merged_at TIMESTAMP WITH TIME ZONE,

  -- State after restoration
  new_subscribed BOOLEAN NOT NULL,
  restoration_reason TEXT NOT NULL,

  -- Metadata
  restored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  restored_by TEXT DEFAULT 'system',

  -- Verification
  verified BOOLEAN DEFAULT FALSE,
  verified_at TIMESTAMP WITH TIME ZONE,
  verified_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_subscription_restoration_contact
  ON subscription_restoration_audit(contact_id);

COMMENT ON TABLE subscription_restoration_audit IS
  'Audit trail for subscription status restorations from merge operations.';

-- 2. Identify contacts to restore
-- ============================================================================
CREATE TEMP TABLE contacts_to_restore AS
SELECT
  c.id as contact_id,
  c.email,
  c.first_name,
  c.last_name,
  c.source_system,
  c.email_subscribed as current_subscribed,
  c.subscription_protected as current_protected,

  cmb.backup_id as merge_backup_id,
  cmb.merged_at,
  (cmb.duplicate_contact_data->>'email_subscribed')::boolean as duplicate_was_subscribed,
  (cmb.duplicate_contact_data->>'source_system') as duplicate_source,
  (cmb.duplicate_contact_data->>'email') as duplicate_email,

  -- Restoration decision
  CASE
    WHEN (cmb.duplicate_contact_data->>'source_system') IN ('kajabi', 'ticket_tailor') THEN 'Authoritative opt-in source'
    WHEN (cmb.duplicate_contact_data->>'source_system') = 'manual' THEN 'Manual opt-in (trusted)'
    WHEN (cmb.duplicate_contact_data->>'source_system') = 'zoho' THEN 'Zoho opt-in (CRM)'
    ELSE 'Merge conflict - duplicate was subscribed'
  END as restoration_reason
FROM contacts c
JOIN contacts_merge_backup cmb ON c.id = cmb.primary_contact_id
WHERE
  cmb.merged_at > NOW() - INTERVAL '30 days'
  AND (cmb.duplicate_contact_data->>'email_subscribed')::boolean = true
  AND c.email_subscribed = false
  AND c.deleted_at IS NULL
ORDER BY cmb.merged_at DESC;

-- 3. Display restoration plan
-- ============================================================================
\echo ''
\echo '================================================================================'
\echo '  SUBSCRIPTION RESTORATION PLAN'
\echo '================================================================================'
\echo ''

SELECT
  'Total contacts to restore' as metric,
  COUNT(*) as count
FROM contacts_to_restore

UNION ALL

SELECT
  'From Kajabi merges' as metric,
  COUNT(*) as count
FROM contacts_to_restore
WHERE duplicate_source = 'kajabi'

UNION ALL

SELECT
  'From Ticket Tailor merges' as metric,
  COUNT(*) as count
FROM contacts_to_restore
WHERE duplicate_source = 'ticket_tailor'

UNION ALL

SELECT
  'From Manual merges' as metric,
  COUNT(*) as count
FROM contacts_to_restore
WHERE duplicate_source = 'manual'

UNION ALL

SELECT
  'From Zoho merges' as metric,
  COUNT(*) as count
FROM contacts_to_restore
WHERE duplicate_source = 'zoho';

\echo ''
\echo 'Sample contacts to be restored:'
\echo ''

SELECT
  email,
  first_name || ' ' || last_name as name,
  source_system,
  duplicate_source,
  restoration_reason
FROM contacts_to_restore
LIMIT 10;

\echo ''
\echo '================================================================================'

-- 4. Create audit entries (always run, even in dry-run)
-- ============================================================================
INSERT INTO subscription_restoration_audit (
  contact_id,
  email,
  old_subscribed,
  old_source_system,
  merge_backup_id,
  duplicate_was_subscribed,
  duplicate_source_system,
  merged_at,
  new_subscribed,
  restoration_reason
)
SELECT
  contact_id,
  email,
  current_subscribed as old_subscribed,
  source_system as old_source_system,
  merge_backup_id,
  duplicate_was_subscribed,
  duplicate_source as duplicate_source_system,
  merged_at,
  true as new_subscribed,  -- Will be set to true
  restoration_reason
FROM contacts_to_restore;

-- 5. Execute restoration (conditional on DRY_RUN setting)
-- ============================================================================
\if :DRY_RUN
  \echo ''
  \echo '⚠️  DRY RUN MODE - No changes will be committed'
  \echo ''
  \echo 'To execute restoration, edit script and set DRY_RUN to false'
  \echo ''
  ROLLBACK;
\else
  \echo ''
  \echo '🔴 EXECUTING RESTORATION...'
  \echo ''

  -- Update contacts
  UPDATE contacts c
  SET
    email_subscribed = true,
    subscription_protected = true,
    subscription_protected_reason = 'Restored from merge - ' || ctr.restoration_reason,
    updated_at = NOW()
  FROM contacts_to_restore ctr
  WHERE c.id = ctr.contact_id;

  -- Verify restoration
  \echo ''
  \echo 'Verification:'
  \echo ''

  SELECT
    'Contacts restored' as metric,
    COUNT(*) as count
  FROM contacts c
  JOIN contacts_to_restore ctr ON c.id = ctr.contact_id
  WHERE c.email_subscribed = true;

  -- Check for failures (should be 0)
  SELECT
    'Failed restorations' as metric,
    COUNT(*) as count
  FROM contacts c
  JOIN contacts_to_restore ctr ON c.id = ctr.contact_id
  WHERE c.email_subscribed = false;

  \echo ''
  \echo '✅ Restoration complete'
  \echo ''
  \echo 'To verify later, run:'
  \echo '  SELECT * FROM subscription_restoration_audit;'
  \echo ''

  COMMIT;
\endif

-- ============================================================================
-- ROLLBACK PROCEDURE (if needed)
-- ============================================================================
/*
If you need to rollback the restoration:

BEGIN;

-- Restore original subscription states
UPDATE contacts c
SET
  email_subscribed = sra.old_subscribed,
  subscription_protected = false,
  subscription_protected_reason = NULL,
  updated_at = NOW()
FROM subscription_restoration_audit sra
WHERE c.id = sra.contact_id
  AND sra.restored_at > NOW() - INTERVAL '1 hour';  -- Safety: only recent restorations

-- Mark as rolled back
UPDATE subscription_restoration_audit
SET
  verified = false,
  verified_at = NOW(),
  verified_by = 'rollback'
WHERE restored_at > NOW() - INTERVAL '1 hour';

COMMIT;
*/
