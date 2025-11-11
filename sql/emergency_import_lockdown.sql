-- ============================================================================
-- EMERGENCY IMPORT LOCKDOWN
-- ============================================================================
-- Purpose: Prevent any import from overwriting enriched or manually-edited data
-- Author: Claude Code
-- Date: 2025-11-11
--
-- This adds a safety flag to protect contacts that have been:
-- - Manually edited by staff
-- - Enriched from multiple sources
-- - Merged from duplicates
-- - Have protected subscription status
-- ============================================================================

BEGIN;

-- 1. Add import_locked column
-- ============================================================================
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  import_locked BOOLEAN DEFAULT FALSE;

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  import_locked_reason TEXT;

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  import_locked_at TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN contacts.import_locked IS
  'Prevents automated imports from overwriting this contact. Manual review required for updates.';

-- 2. Add subscription_protected column (for Phase 1 compliance)
-- ============================================================================
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  subscription_protected BOOLEAN DEFAULT FALSE;

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  subscription_protected_reason TEXT;

COMMENT ON COLUMN contacts.subscription_protected IS
  'Protects email_subscribed field from being overwritten. Used for Ticket Tailor opt-ins.';

-- 3. Lock ALL enriched contacts
-- ============================================================================
-- Lock contacts with enriched data from other sources
UPDATE contacts
SET
  import_locked = TRUE,
  import_locked_reason = 'Has enriched data from multiple sources',
  import_locked_at = NOW()
WHERE
  deleted_at IS NULL
  AND (
    -- Has data from multiple sources
    additional_email IS NOT NULL OR
    paypal_email IS NOT NULL OR
    paypal_subscription_reference IS NOT NULL OR
    zoho_id IS NOT NULL OR

    -- From non-Kajabi sources (preserve provenance)
    source_system IN ('ticket_tailor', 'manual', 'zoho', 'paypal') OR

    -- Has been manually edited (updated after creation)
    updated_at > created_at + INTERVAL '1 day' OR

    -- Has subscription protection already
    subscription_protected = TRUE
  )
  AND import_locked = FALSE;  -- Don't overwrite existing locks

-- 4. Protect Ticket Tailor opt-ins specifically
-- ============================================================================
UPDATE contacts
SET
  subscription_protected = TRUE,
  subscription_protected_reason = 'Ticket Tailor opt-in - legal protection'
WHERE
  deleted_at IS NULL
  AND source_system = 'ticket_tailor'
  AND email_subscribed = TRUE
  AND subscription_protected = FALSE;

-- 5. Protect manual opt-outs (staff-initiated unsubscribes)
-- ============================================================================
UPDATE contacts
SET
  subscription_protected = TRUE,
  subscription_protected_reason = 'Manual unsubscribe - do not re-subscribe'
WHERE
  deleted_at IS NULL
  AND source_system = 'manual'
  AND email_subscribed = FALSE
  AND subscription_protected = FALSE;

-- 6. Create audit log table for import operations
-- ============================================================================
CREATE TABLE IF NOT EXISTS import_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID REFERENCES contacts(id),
  operation TEXT NOT NULL,  -- 'create', 'update', 'skip', 'conflict'
  import_source TEXT NOT NULL,  -- 'kajabi', 'ticket_tailor', 'paypal'
  import_batch_id UUID NOT NULL,

  -- What changed
  fields_updated TEXT[],
  old_values JSONB,
  new_values JSONB,

  -- Conflict detection
  had_conflict BOOLEAN DEFAULT FALSE,
  conflict_reason TEXT,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_import_audit_contact
  ON import_audit_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_import_audit_batch
  ON import_audit_log(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_import_audit_created
  ON import_audit_log(created_at);

COMMENT ON TABLE import_audit_log IS
  'Audit trail for all import operations. Used for rollback and compliance tracking.';

-- 7. Create import conflicts table
-- ============================================================================
CREATE TABLE IF NOT EXISTS import_conflicts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID REFERENCES contacts(id),
  import_batch_id UUID NOT NULL,
  import_source TEXT NOT NULL,

  -- The conflict
  field_name TEXT NOT NULL,
  db_value TEXT,
  import_value TEXT,
  conflict_type TEXT NOT NULL,  -- 'subscription', 'source_system', 'enriched_data'

  -- Resolution
  resolved BOOLEAN DEFAULT FALSE,
  resolution TEXT,  -- 'keep_db', 'use_import', 'merge', 'manual_review'
  resolved_at TIMESTAMP WITH TIME ZONE,
  resolved_by TEXT,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_conflicts_contact
  ON import_conflicts(contact_id);
CREATE INDEX IF NOT EXISTS idx_import_conflicts_resolved
  ON import_conflicts(resolved);

COMMENT ON TABLE import_conflicts IS
  'Tracks conflicts detected during imports. Requires manual resolution before applying changes.';

-- 8. Verification queries
-- ============================================================================

-- Count locked contacts
SELECT
  'Total locked contacts' as metric,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM contacts WHERE deleted_at IS NULL), 2) as pct
FROM contacts
WHERE deleted_at IS NULL AND import_locked = TRUE

UNION ALL

SELECT
  'Subscription protected' as metric,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM contacts WHERE deleted_at IS NULL), 2) as pct
FROM contacts
WHERE deleted_at IS NULL AND subscription_protected = TRUE

UNION ALL

SELECT
  'Unlocked (safe to update)' as metric,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM contacts WHERE deleted_at IS NULL), 2) as pct
FROM contacts
WHERE deleted_at IS NULL AND import_locked = FALSE;

-- Breakdown by source system
SELECT
  source_system,
  COUNT(*) as total_contacts,
  SUM(CASE WHEN import_locked THEN 1 ELSE 0 END) as locked,
  SUM(CASE WHEN subscription_protected THEN 1 ELSE 0 END) as sub_protected
FROM contacts
WHERE deleted_at IS NULL
GROUP BY source_system
ORDER BY total_contacts DESC;

-- Verification: No unlocked enriched contacts
SELECT
  id,
  email,
  source_system,
  import_locked,
  CASE
    WHEN additional_email IS NOT NULL THEN 'Has additional_email'
    WHEN paypal_email IS NOT NULL THEN 'Has paypal_email'
    WHEN zoho_id IS NOT NULL THEN 'Has zoho_id'
    ELSE 'Manual edit'
  END as enriched_reason
FROM contacts
WHERE deleted_at IS NULL
  AND import_locked = FALSE
  AND (
    additional_email IS NOT NULL OR
    paypal_email IS NOT NULL OR
    zoho_id IS NOT NULL OR
    source_system IN ('ticket_tailor', 'manual', 'zoho', 'paypal')
  )
LIMIT 10;

-- This should return 0 rows. If it doesn't, those contacts need locking.

COMMIT;

-- ============================================================================
-- ROLLBACK PROCEDURE (if needed)
-- ============================================================================
/*
BEGIN;

-- Remove lockdown
UPDATE contacts SET
  import_locked = FALSE,
  import_locked_reason = NULL,
  import_locked_at = NULL,
  subscription_protected = FALSE,
  subscription_protected_reason = NULL;

-- Drop audit tables (optional - you may want to keep for history)
-- DROP TABLE import_conflicts;
-- DROP TABLE import_audit_log;

COMMIT;
*/
