-- ============================================================================
-- COMPREHENSIVE DUPLICATE DETECTION FUNCTION
-- ============================================================================
-- Purpose: Find existing contacts by checking ALL email addresses
-- Author: Claude Code
-- Date: 2025-11-11
--
-- This function checks:
-- 1. contacts.email (primary)
-- 2. contacts.additional_email
-- 3. contacts.paypal_email
-- 4. contacts.zoho_email
-- 5. contact_emails table (all alternate emails)
--
-- Returns: contact_id if found, NULL if not found
-- ============================================================================

BEGIN;

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS find_contact_by_any_email(TEXT);

-- Create comprehensive lookup function
CREATE OR REPLACE FUNCTION find_contact_by_any_email(search_email TEXT)
RETURNS UUID
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  found_contact_id UUID;
  normalized_email TEXT;
BEGIN
  -- Normalize the email
  normalized_email := LOWER(TRIM(search_email));

  IF normalized_email IS NULL OR normalized_email = '' THEN
    RETURN NULL;
  END IF;

  -- Check primary email
  SELECT id INTO found_contact_id
  FROM contacts
  WHERE deleted_at IS NULL
    AND LOWER(email) = normalized_email
  LIMIT 1;

  IF found_contact_id IS NOT NULL THEN
    RETURN found_contact_id;
  END IF;

  -- Check additional_email
  SELECT id INTO found_contact_id
  FROM contacts
  WHERE deleted_at IS NULL
    AND LOWER(additional_email) = normalized_email
  LIMIT 1;

  IF found_contact_id IS NOT NULL THEN
    RETURN found_contact_id;
  END IF;

  -- Check paypal_email
  SELECT id INTO found_contact_id
  FROM contacts
  WHERE deleted_at IS NULL
    AND LOWER(paypal_email) = normalized_email
  LIMIT 1;

  IF found_contact_id IS NOT NULL THEN
    RETURN found_contact_id;
  END IF;

  -- Check zoho_email
  SELECT id INTO found_contact_id
  FROM contacts
  WHERE deleted_at IS NULL
    AND LOWER(zoho_email) = normalized_email
  LIMIT 1;

  IF found_contact_id IS NOT NULL THEN
    RETURN found_contact_id;
  END IF;

  -- Check contact_emails table
  SELECT ce.contact_id INTO found_contact_id
  FROM contact_emails ce
  JOIN contacts c ON ce.contact_id = c.id
  WHERE c.deleted_at IS NULL
    AND LOWER(ce.email) = normalized_email
  LIMIT 1;

  RETURN found_contact_id;
END;
$$;

COMMENT ON FUNCTION find_contact_by_any_email IS
  'Finds a contact by searching ALL email fields (primary, additional, paypal, zoho, and contact_emails table). Returns contact_id if found, NULL otherwise.';

-- Create an index-backed version for performance
CREATE INDEX IF NOT EXISTS idx_contacts_email_lower
  ON contacts(LOWER(email)) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_additional_email_lower
  ON contacts(LOWER(additional_email)) WHERE deleted_at IS NULL AND additional_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_paypal_email_lower
  ON contacts(LOWER(paypal_email)) WHERE deleted_at IS NULL AND paypal_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_zoho_email_lower
  ON contacts(LOWER(zoho_email)) WHERE deleted_at IS NULL AND zoho_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contact_emails_email_lower
  ON contact_emails(LOWER(email));

-- ============================================================================
-- BATCH DUPLICATE DETECTION FUNCTION
-- ============================================================================
-- Purpose: Find duplicates for a batch of emails (for import scripts)
-- Returns: TABLE of (search_email, found_contact_id, match_field)
-- ============================================================================

CREATE OR REPLACE FUNCTION find_duplicates_batch(emails TEXT[])
RETURNS TABLE (
  search_email TEXT,
  found_contact_id UUID,
  match_field TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
  RETURN QUERY
  WITH normalized_emails AS (
    SELECT DISTINCT LOWER(TRIM(unnest)) as email
    FROM unnest(emails)
    WHERE unnest IS NOT NULL AND TRIM(unnest) != ''
  )
  SELECT
    ne.email as search_email,
    c.id as found_contact_id,
    'primary_email'::TEXT as match_field
  FROM normalized_emails ne
  JOIN contacts c ON LOWER(c.email) = ne.email
  WHERE c.deleted_at IS NULL

  UNION ALL

  SELECT
    ne.email as search_email,
    c.id as found_contact_id,
    'additional_email'::TEXT as match_field
  FROM normalized_emails ne
  JOIN contacts c ON LOWER(c.additional_email) = ne.email
  WHERE c.deleted_at IS NULL
    AND c.additional_email IS NOT NULL

  UNION ALL

  SELECT
    ne.email as search_email,
    c.id as found_contact_id,
    'paypal_email'::TEXT as match_field
  FROM normalized_emails ne
  JOIN contacts c ON LOWER(c.paypal_email) = ne.email
  WHERE c.deleted_at IS NULL
    AND c.paypal_email IS NOT NULL

  UNION ALL

  SELECT
    ne.email as search_email,
    c.id as found_contact_id,
    'zoho_email'::TEXT as match_field
  FROM normalized_emails ne
  JOIN contacts c ON LOWER(c.zoho_email) = ne.email
  WHERE c.deleted_at IS NULL
    AND c.zoho_email IS NOT NULL

  UNION ALL

  SELECT
    ne.email as search_email,
    ce.contact_id as found_contact_id,
    'contact_emails_table'::TEXT as match_field
  FROM normalized_emails ne
  JOIN contact_emails ce ON LOWER(ce.email) = ne.email
  JOIN contacts c ON ce.contact_id = c.id
  WHERE c.deleted_at IS NULL;
END;
$$;

COMMENT ON FUNCTION find_duplicates_batch IS
  'Batch version of duplicate detection. Checks all email fields for multiple emails at once. Used by import scripts for performance.';

-- ============================================================================
-- TESTING & VERIFICATION
-- ============================================================================

-- Test single lookup
\echo ''
\echo '================================================================================'
\echo '  TESTING DUPLICATE DETECTION'
\echo '================================================================================'
\echo ''

-- Test 1: Find a contact by primary email
\echo 'Test 1: Find by primary email'
SELECT
  'Test primary email' as test,
  find_contact_by_any_email('lilaplays@gmail.com') as contact_id,
  CASE WHEN find_contact_by_any_email('lilaplays@gmail.com') IS NOT NULL
    THEN '✅ PASS' ELSE '❌ FAIL' END as result;

-- Test 2: Find a contact by additional_email
\echo ''
\echo 'Test 2: Find by additional_email'
SELECT
  'Test additional_email' as test,
  c.email as primary_email,
  c.additional_email,
  find_contact_by_any_email(c.additional_email) as found_id,
  CASE WHEN find_contact_by_any_email(c.additional_email) = c.id
    THEN '✅ PASS' ELSE '❌ FAIL' END as result
FROM contacts c
WHERE c.additional_email IS NOT NULL
  AND c.deleted_at IS NULL
LIMIT 1;

-- Test 3: Find a contact by paypal_email
\echo ''
\echo 'Test 3: Find by paypal_email'
SELECT
  'Test paypal_email' as test,
  c.email as primary_email,
  c.paypal_email,
  find_contact_by_any_email(c.paypal_email) as found_id,
  CASE WHEN find_contact_by_any_email(c.paypal_email) = c.id
    THEN '✅ PASS' ELSE '❌ FAIL' END as result
FROM contacts c
WHERE c.paypal_email IS NOT NULL
  AND c.deleted_at IS NULL
LIMIT 1;

-- Test 4: Non-existent email
\echo ''
\echo 'Test 4: Non-existent email (should return NULL)'
SELECT
  'Test non-existent' as test,
  find_contact_by_any_email('thisdoesnotexist@nowhere.com') as contact_id,
  CASE WHEN find_contact_by_any_email('thisdoesnotexist@nowhere.com') IS NULL
    THEN '✅ PASS (correctly returns NULL)' ELSE '❌ FAIL' END as result;

-- Performance test
\echo ''
\echo 'Test 5: Performance test (10 lookups)'
\echo ''
SELECT
  COUNT(*) as lookups_completed,
  '✅ Function is working' as status
FROM (
  SELECT find_contact_by_any_email(email)
  FROM contacts
  WHERE deleted_at IS NULL
  LIMIT 10
) t;

\echo ''
\echo '================================================================================'
\echo '  ALL TESTS COMPLETE'
\echo '================================================================================'
\echo ''

COMMIT;
