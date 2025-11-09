-- ============================================================================
-- QUICK DATA CLEANUP: Email & Name Standardization
-- ============================================================================
-- Phase 1: Fix email capitalization (5 contacts)
-- Phase 2: Fix name capitalization - lowercase (218 contacts)
-- Phase 3: Fix name capitalization - ALL CAPS (36 contacts)
-- Total: 259 contacts (excluding blank names for now)
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'QUICK DATA CLEANUP: Email & Name Standardization'
\echo '============================================================================'
\echo ''

-- Create backup table if it doesn't exist
CREATE TABLE IF NOT EXISTS contacts_cleanup_backup (
  backup_id SERIAL PRIMARY KEY,
  contact_id UUID NOT NULL,
  old_data JSONB NOT NULL,
  new_data JSONB,
  cleanup_type TEXT NOT NULL,
  cleaned_at TIMESTAMP DEFAULT NOW(),
  notes TEXT
);

\echo 'Backup table ready'
\echo ''

-- ============================================================================
-- PHASE 1: Fix Email Capitalization (5 contacts)
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 1: Email Capitalization (5 contacts)'
\echo '============================================================================'

-- Backup and fix emails with uppercase
WITH emails_to_fix AS (
  SELECT
    id,
    email,
    LOWER(email) as fixed_email
  FROM contacts
  WHERE email != LOWER(email)
)
INSERT INTO contacts_cleanup_backup (contact_id, old_data, cleanup_type, notes)
SELECT
  id,
  jsonb_build_object('email', email),
  'email_case_fix',
  'Fixed email from "' || email || '" to "' || fixed_email || '"'
FROM emails_to_fix;

-- Apply fix
UPDATE contacts
SET
  email = LOWER(email),
  updated_at = NOW()
WHERE email != LOWER(email);

SELECT 'Fixed emails' as status, COUNT(*) as count
FROM contacts_cleanup_backup
WHERE cleanup_type = 'email_case_fix'
  AND cleaned_at > NOW() - INTERVAL '1 minute';

\echo ''

-- ============================================================================
-- PHASE 2: Fix Lowercase Names (218 contacts)
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 2: Lowercase Names to Title Case (218 contacts)'
\echo '============================================================================'

-- Backup and fix lowercase names
WITH names_to_fix AS (
  SELECT
    id,
    first_name,
    last_name,
    INITCAP(first_name) as fixed_first,
    INITCAP(last_name) as fixed_last
  FROM contacts
  WHERE (first_name = LOWER(first_name) AND first_name != '' AND first_name IS NOT NULL)
     OR (last_name = LOWER(last_name) AND last_name != '' AND last_name IS NOT NULL)
)
INSERT INTO contacts_cleanup_backup (contact_id, old_data, cleanup_type, notes)
SELECT
  id,
  jsonb_build_object('first_name', first_name, 'last_name', last_name),
  'lowercase_name_fix',
  'Fixed name from "' || COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') ||
  '" to "' || COALESCE(fixed_first, '') || ' ' || COALESCE(fixed_last, '') || '"'
FROM names_to_fix;

-- Apply fix
UPDATE contacts
SET
  first_name = INITCAP(first_name),
  last_name = INITCAP(last_name),
  updated_at = NOW()
WHERE (first_name = LOWER(first_name) AND first_name != '' AND first_name IS NOT NULL)
   OR (last_name = LOWER(last_name) AND last_name != '' AND last_name IS NOT NULL);

SELECT 'Fixed lowercase names' as status, COUNT(*) as count
FROM contacts_cleanup_backup
WHERE cleanup_type = 'lowercase_name_fix'
  AND cleaned_at > NOW() - INTERVAL '1 minute';

\echo ''

-- ============================================================================
-- PHASE 3: Fix ALL CAPS Names (36 contacts)
-- ============================================================================

\echo '============================================================================'
\echo 'PHASE 3: ALL CAPS Names to Title Case (36 contacts)'
\echo '============================================================================'

-- Backup and fix ALL CAPS names
-- Note: Only fix if length > 1 to avoid fixing single letters
WITH names_to_fix AS (
  SELECT
    id,
    first_name,
    last_name,
    CASE
      WHEN first_name = UPPER(first_name) AND LENGTH(first_name) > 1
      THEN INITCAP(first_name)
      ELSE first_name
    END as fixed_first,
    CASE
      WHEN last_name = UPPER(last_name) AND LENGTH(last_name) > 1
      THEN INITCAP(last_name)
      ELSE last_name
    END as fixed_last
  FROM contacts
  WHERE (first_name = UPPER(first_name) AND LENGTH(first_name) > 1)
     OR (last_name = UPPER(last_name) AND LENGTH(last_name) > 1)
)
INSERT INTO contacts_cleanup_backup (contact_id, old_data, cleanup_type, notes)
SELECT
  id,
  jsonb_build_object('first_name', first_name, 'last_name', last_name),
  'allcaps_name_fix',
  'Fixed name from "' || COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') ||
  '" to "' || COALESCE(fixed_first, '') || ' ' || COALESCE(fixed_last, '') || '"'
FROM names_to_fix;

-- Apply fix
UPDATE contacts
SET
  first_name = CASE
    WHEN first_name = UPPER(first_name) AND LENGTH(first_name) > 1
    THEN INITCAP(first_name)
    ELSE first_name
  END,
  last_name = CASE
    WHEN last_name = UPPER(last_name) AND LENGTH(last_name) > 1
    THEN INITCAP(last_name)
    ELSE last_name
  END,
  updated_at = NOW()
WHERE (first_name = UPPER(first_name) AND LENGTH(first_name) > 1)
   OR (last_name = UPPER(last_name) AND LENGTH(last_name) > 1);

SELECT 'Fixed ALL CAPS names' as status, COUNT(*) as count
FROM contacts_cleanup_backup
WHERE cleanup_type = 'allcaps_name_fix'
  AND cleaned_at > NOW() - INTERVAL '1 minute';

\echo ''

-- ============================================================================
-- SUMMARY & VERIFICATION
-- ============================================================================

\echo '============================================================================'
\echo 'CLEANUP SUMMARY'
\echo '============================================================================'

SELECT
  cleanup_type,
  COUNT(*) as contacts_cleaned,
  MIN(cleaned_at) as started_at,
  MAX(cleaned_at) as completed_at
FROM contacts_cleanup_backup
WHERE cleaned_at > NOW() - INTERVAL '2 minutes'
GROUP BY cleanup_type
ORDER BY MIN(cleaned_at);

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'

-- Verify no issues remain
SELECT
  'Emails still uppercase' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '⚠ ISSUES REMAIN' END as status
FROM contacts
WHERE email != LOWER(email);

SELECT
  'Names still lowercase' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '⚠ ISSUES REMAIN' END as status
FROM contacts
WHERE (first_name = LOWER(first_name) AND first_name != '' AND first_name IS NOT NULL)
   OR (last_name = LOWER(last_name) AND last_name != '' AND last_name IS NOT NULL);

SELECT
  'Names still ALL CAPS' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '⚠ ISSUES REMAIN' END as status
FROM contacts
WHERE (first_name = UPPER(first_name) AND LENGTH(first_name) > 1)
   OR (last_name = UPPER(last_name) AND LENGTH(last_name) > 1);

SELECT
  'Total contacts cleaned' as metric,
  COUNT(*) as value
FROM contacts_cleanup_backup
WHERE cleaned_at > NOW() - INTERVAL '2 minutes';

\echo ''
\echo '============================================================================'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '============================================================================'

-- COMMIT the cleanup
COMMIT;

\echo ''
\echo '============================================================================'
\echo '✓ QUICK DATA CLEANUP COMMITTED!'
\echo '============================================================================'
