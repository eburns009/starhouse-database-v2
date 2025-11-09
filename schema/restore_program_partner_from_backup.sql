-- ============================================================================
-- RESTORE PLAN: Program Partner Module from Backup
-- ============================================================================
-- Purpose: Restore program partner functionality if rollback needs to be undone
-- Prerequisites: Backup tables must exist from rollback process
--
-- IMPORTANT: Only run this if you need to restore the program partner data
-- after running the rollback script.
--
-- Created: 2025-11-08
-- ============================================================================

-- ============================================================================
-- STEP 0: VERIFY BACKUPS EXIST
-- ============================================================================

DO $$
DECLARE
  v_backup_contacts INTEGER;
  v_backup_audit INTEGER;
  v_backup_corrections INTEGER;
BEGIN
  RAISE NOTICE '=== VERIFYING BACKUPS ===';

  -- Check if backup tables exist
  IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'backup_program_partner_contacts') THEN
    RAISE EXCEPTION 'Backup table backup_program_partner_contacts does not exist!';
  END IF;

  IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'backup_program_partner_audit_log') THEN
    RAISE EXCEPTION 'Backup table backup_program_partner_audit_log does not exist!';
  END IF;

  IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'backup_legacy_program_partner_corrections') THEN
    RAISE EXCEPTION 'Backup table backup_legacy_program_partner_corrections does not exist!';
  END IF;

  -- Count backup records
  SELECT COUNT(*) INTO v_backup_contacts FROM backup_program_partner_contacts;
  SELECT COUNT(*) INTO v_backup_audit FROM backup_program_partner_audit_log;
  SELECT COUNT(*) INTO v_backup_corrections FROM backup_legacy_program_partner_corrections;

  RAISE NOTICE 'Backup contacts: %', v_backup_contacts;
  RAISE NOTICE 'Backup audit log: %', v_backup_audit;
  RAISE NOTICE 'Backup corrections: %', v_backup_corrections;

  IF v_backup_contacts = 0 AND v_backup_audit = 0 AND v_backup_corrections = 0 THEN
    RAISE WARNING 'All backup tables are empty. Nothing to restore.';
  END IF;
END $$;

-- ============================================================================
-- STEP 1: RECREATE TABLES
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 1: RECREATING TABLES ===';
END $$;

-- Recreate program_partner_audit_log
CREATE TABLE IF NOT EXISTS program_partner_audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
  action TEXT NOT NULL CHECK (action IN ('status_removed', 'status_added', 'payment_method_updated')),
  previous_value JSONB,
  new_value JSONB,
  reason TEXT,
  notes TEXT,
  changed_by TEXT,
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ip_address INET,
  user_agent TEXT,
  metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_partner_audit_contact_id ON program_partner_audit_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_partner_audit_action ON program_partner_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_partner_audit_changed_at ON program_partner_audit_log(changed_at DESC);

-- Recreate legacy_program_partner_corrections
CREATE TABLE IF NOT EXISTS legacy_program_partner_corrections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID REFERENCES contacts(id),
  contact_email TEXT NOT NULL,
  current_group TEXT NOT NULL,
  correct_group TEXT NOT NULL,
  correct_level TEXT,
  notes TEXT,
  corrected BOOLEAN DEFAULT FALSE,
  corrected_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT legacy_corrections_groups_check CHECK (
    current_group IN ('Individual', 'Program Partner') AND
    correct_group IN ('Individual', 'Program Partner')
  )
);

CREATE INDEX IF NOT EXISTS idx_legacy_corrections_contact ON legacy_program_partner_corrections(contact_id);
CREATE INDEX IF NOT EXISTS idx_legacy_corrections_uncorrected ON legacy_program_partner_corrections(corrected) WHERE corrected = false;

-- ============================================================================
-- STEP 2: RECREATE COLUMNS
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 2: RECREATING COLUMNS ===';
END $$;

-- Add columns back to contacts
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS is_expected_program_partner BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS payment_method TEXT CHECK (payment_method IN ('credit_card', 'paypal', 'check', 'cash', 'wire_transfer', 'other')),
ADD COLUMN IF NOT EXISTS payment_method_notes TEXT,
ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS partner_status_notes TEXT;

-- Add columns back to subscriptions
ALTER TABLE subscriptions
ADD COLUMN IF NOT EXISTS payment_method TEXT CHECK (payment_method IN ('credit_card', 'paypal', 'check', 'cash', 'wire_transfer', 'other')),
ADD COLUMN IF NOT EXISTS payment_notes TEXT;

-- Recreate index
CREATE INDEX IF NOT EXISTS idx_contacts_expected_partner
ON contacts(is_expected_program_partner)
WHERE is_expected_program_partner = true;

-- ============================================================================
-- STEP 3: RESTORE DATA
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 3: RESTORING DATA ===';
END $$;

-- Restore contacts data
UPDATE contacts c
SET
  is_expected_program_partner = b.is_expected_program_partner,
  payment_method = b.payment_method,
  payment_method_notes = b.payment_method_notes,
  last_payment_date = b.last_payment_date,
  partner_status_notes = b.partner_status_notes
FROM backup_program_partner_contacts b
WHERE c.id = b.id;

-- Restore audit log
INSERT INTO program_partner_audit_log (
  id, contact_id, action, previous_value, new_value,
  reason, notes, changed_by, changed_at, ip_address, user_agent, metadata
)
SELECT
  id, contact_id, action, previous_value, new_value,
  reason, notes, changed_by, changed_at, ip_address, user_agent, metadata
FROM backup_program_partner_audit_log
ON CONFLICT (id) DO NOTHING;

-- Restore legacy corrections
INSERT INTO legacy_program_partner_corrections (
  id, contact_id, contact_email, current_group, correct_group,
  correct_level, notes, corrected, corrected_at, created_at
)
SELECT
  id, contact_id, contact_email, current_group, correct_group,
  correct_level, notes, corrected, corrected_at, created_at
FROM backup_legacy_program_partner_corrections
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- STEP 4: RECREATE FUNCTIONS AND VIEWS
-- ============================================================================
-- Note: You'll need to run the original schema/program_partner_management.sql
-- to recreate all functions and views

DO $$
BEGIN
  RAISE NOTICE '=== STEP 4: FUNCTIONS AND VIEWS ===';
  RAISE NOTICE 'Run schema/program_partner_management.sql to recreate functions and views';
END $$;

-- ============================================================================
-- STEP 5: VERIFICATION
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '=== STEP 5: VERIFICATION ===';
END $$;

SELECT
  'Restored program partners' as metric,
  COUNT(*) FILTER (WHERE is_expected_program_partner = true) as count
FROM contacts

UNION ALL

SELECT
  'Restored audit log entries' as metric,
  COUNT(*) as count
FROM program_partner_audit_log

UNION ALL

SELECT
  'Restored legacy corrections' as metric,
  COUNT(*) as count
FROM legacy_program_partner_corrections;

SELECT '✓ Program Partner data restored from backup' as status;
