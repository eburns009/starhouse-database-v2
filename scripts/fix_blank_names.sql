-- ============================================================================
-- FIX BLANK NAMES: Extract from Email Addresses
-- ============================================================================
-- Strategy: Parse email usernames and extract probable first/last names
-- Safe extraction with backup
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'FIX BLANK NAMES: Extract from Email Addresses (11 contacts)'
\echo '============================================================================'
\echo ''

-- Create backup and apply fixes
INSERT INTO contacts_cleanup_backup (contact_id, old_data, cleanup_type, notes)
SELECT
  id,
  jsonb_build_object(
    'first_name', first_name,
    'last_name', last_name,
    'email', email
  ),
  'blank_name_extraction',
  'Extracted name from email: ' || email
FROM contacts
WHERE TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) = '';

-- Apply smart name extraction
UPDATE contacts
SET
  first_name = CASE
    WHEN email LIKE 'abigailfking%' THEN 'Abigail'
    WHEN email LIKE 'stacylambatos%' THEN 'Stacy'
    WHEN email LIKE 'kimberlycherry%' THEN 'Kimberly'
    WHEN email LIKE 'kellylawyer%' THEN 'Kelly'
    WHEN email LIKE 'katieontherun%' THEN 'Katie'
    WHEN email LIKE 'robin%' THEN 'Robin'
    WHEN email LIKE 'nellie%' THEN 'Nellie'
    WHEN email LIKE 'mirradawn%' THEN 'Mirra'
    WHEN email LIKE 'strangejill%' THEN 'Jill'
    WHEN email LIKE 'windwhisper%' THEN 'Windwhisper'
    WHEN email LIKE 'cneckes%' THEN 'C'
    ELSE INITCAP(SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 1))
  END,
  last_name = CASE
    WHEN email LIKE 'abigailfking%' THEN 'King'
    WHEN email LIKE 'stacylambatos%' THEN 'Lambatos'
    WHEN email LIKE 'kimberlycherry%' THEN 'Cherry'
    WHEN email LIKE 'kellylawyer%' THEN 'Lawyer'
    WHEN email LIKE 'mirradawn%' THEN 'Dawn'
    WHEN email LIKE 'cneckes%' THEN 'Neckes'
    ELSE NULL  -- Leave blank if uncertain
  END,
  updated_at = NOW()
WHERE TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) = '';

\echo ''
\echo '============================================================================'
\echo 'RESULTS'
\echo '============================================================================'

-- Show what we fixed
SELECT
  'Names extracted from email' as status,
  COUNT(*) as count
FROM contacts_cleanup_backup
WHERE cleanup_type = 'blank_name_extraction'
  AND cleaned_at > NOW() - INTERVAL '1 minute';

-- Show the results
SELECT
  first_name,
  last_name,
  email,
  'Extracted' as source
FROM contacts
WHERE id IN (
  SELECT contact_id
  FROM contacts_cleanup_backup
  WHERE cleanup_type = 'blank_name_extraction'
    AND cleaned_at > NOW() - INTERVAL '1 minute'
)
ORDER BY email;

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'

SELECT
  'Contacts still with blank names' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '⚠ SOME REMAIN' END as status
FROM contacts
WHERE TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) = '';

\echo ''
\echo '============================================================================'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '============================================================================'

-- COMMIT the fixes
COMMIT;

\echo ''
\echo '============================================================================'
\echo '✓ BLANK NAMES FIXED!'
\echo '============================================================================'
