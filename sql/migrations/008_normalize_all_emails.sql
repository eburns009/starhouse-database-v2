-- ============================================
-- NORMALIZE ALL EMAILS TO contact_emails TABLE
-- ============================================
-- Purpose: Fix email system to show and search ALL emails
-- Date: 2025-11-10
-- Issues Fixed:
--   1. 955 contacts missing primary email in contact_emails
--   2. 373 contacts with additional_email not in contact_emails
--   3. Search doesn't work for additional emails
--   4. UI can't display all emails per contact
-- ============================================

\echo '================================'
\echo 'EMAIL NORMALIZATION MIGRATION'
\echo 'Starting at:' :current_timestamp
\echo '================================'

BEGIN;

-- ============================================
-- STEP 1: PRE-MIGRATION DIAGNOSTICS
-- ============================================

\echo ''
\echo 'STEP 1: Running diagnostics...'

DO $$
DECLARE
    v_total_contacts INTEGER;
    v_contacts_with_primary INTEGER;
    v_contacts_missing_primary INTEGER;
    v_contacts_with_additional INTEGER;
    v_total_additional_emails INTEGER;
    v_contacts_with_multiple_primaries INTEGER;
BEGIN
    -- Total contacts
    SELECT COUNT(*) INTO v_total_contacts
    FROM contacts WHERE deleted_at IS NULL;

    RAISE NOTICE 'Total active contacts: %', v_total_contacts;

    -- Contacts with primary email in contact_emails
    SELECT COUNT(DISTINCT contact_id) INTO v_contacts_with_primary
    FROM contact_emails WHERE is_primary = true;

    RAISE NOTICE 'Contacts with primary in contact_emails: %', v_contacts_with_primary;

    -- Contacts missing primary
    SELECT COUNT(*) INTO v_contacts_missing_primary
    FROM contacts c
    WHERE c.deleted_at IS NULL
      AND c.email IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM contact_emails ce
        WHERE ce.contact_id = c.id AND ce.is_primary = true
      );

    RAISE NOTICE 'Contacts MISSING primary: %', v_contacts_missing_primary;

    -- Contacts with additional_email field
    SELECT COUNT(*) INTO v_contacts_with_additional
    FROM contacts
    WHERE additional_email IS NOT NULL
      AND additional_email <> ''
      AND deleted_at IS NULL;

    RAISE NOTICE 'Contacts with additional_email field: %', v_contacts_with_additional;

    -- Total additional emails (split by comma)
    SELECT SUM(array_length(string_to_array(additional_email, ','), 1))
    INTO v_total_additional_emails
    FROM contacts
    WHERE additional_email IS NOT NULL
      AND additional_email <> ''
      AND deleted_at IS NULL;

    RAISE NOTICE 'Total additional emails to migrate: %', v_total_additional_emails;

    -- Check for multiple primaries (should be 0)
    SELECT COUNT(*) INTO v_contacts_with_multiple_primaries
    FROM (
      SELECT contact_id, COUNT(*)
      FROM contact_emails
      WHERE is_primary = true
      GROUP BY contact_id
      HAVING COUNT(*) > 1
    ) x;

    IF v_contacts_with_multiple_primaries > 0 THEN
        RAISE EXCEPTION 'CRITICAL: % contacts have multiple primary emails!', v_contacts_with_multiple_primaries;
    END IF;

    RAISE NOTICE 'Validation: No duplicate primaries ✓';
    RAISE NOTICE '================================';
END $$;

-- ============================================
-- STEP 2: CREATE BACKUP
-- ============================================

\echo ''
\echo 'STEP 2: Creating backup...'

DROP TABLE IF EXISTS contact_emails_backup_20251110;
CREATE TABLE contact_emails_backup_20251110 AS
SELECT * FROM contact_emails;

DO $$
DECLARE
    v_backup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_backup_count FROM contact_emails_backup_20251110;
    RAISE NOTICE 'Backed up % contact_emails records ✓', v_backup_count;
END $$;

-- ============================================
-- STEP 3: BACKFILL MISSING PRIMARY EMAILS
-- ============================================

\echo ''
\echo 'STEP 3: Backfilling missing primary emails...'

INSERT INTO contact_emails (
  contact_id,
  email,
  email_type,
  is_primary,
  is_outreach,
  source,
  verified,
  created_at
)
SELECT
  c.id,
  c.email,
  'personal'::TEXT,
  true,  -- Is primary
  true,  -- Also set as outreach for backward compatibility
  c.source_system,
  true,  -- Assume verified (from trusted sources)
  c.created_at
FROM contacts c
WHERE c.deleted_at IS NULL
  AND c.email IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM contact_emails ce
    WHERE ce.contact_id = c.id AND ce.is_primary = true
  )
ON CONFLICT (contact_id, email) DO NOTHING;

-- Verify
DO $$
DECLARE
    v_inserted_count INTEGER;
    v_expected_count INTEGER;
BEGIN
    -- Count newly inserted primaries (created in last minute)
    SELECT COUNT(*) INTO v_inserted_count
    FROM contact_emails
    WHERE is_primary = true
      AND created_at >= NOW() - INTERVAL '1 minute';

    -- Expected count (contacts missing primary)
    SELECT COUNT(*) INTO v_expected_count
    FROM contacts c
    WHERE c.deleted_at IS NULL
      AND c.email IS NOT NULL
      AND created_at < NOW() - INTERVAL '1 minute'  -- Old contacts
      AND NOT EXISTS (
        SELECT 1 FROM contact_emails ce
        WHERE ce.contact_id = c.id
          AND ce.is_primary = true
          AND ce.created_at < NOW() - INTERVAL '1 minute'
      );

    RAISE NOTICE 'Backfilled % missing primary emails ✓', v_inserted_count;

    IF v_inserted_count < v_expected_count THEN
        RAISE WARNING 'Expected to insert ~%, only inserted %', v_expected_count, v_inserted_count;
    END IF;
END $$;

-- ============================================
-- STEP 4: MIGRATE ADDITIONAL EMAILS
-- ============================================

\echo ''
\echo 'STEP 4: Migrating additional emails from contacts.additional_email...'

INSERT INTO contact_emails (
  contact_id,
  email,
  email_type,
  is_primary,
  is_outreach,
  source,
  verified,
  created_at
)
SELECT
  c.id,
  TRIM(email_part)::TEXT as email,
  'personal'::TEXT as email_type,
  false as is_primary,  -- Never primary
  false as is_outreach,  -- Not for outreach by default
  -- Map additional_email_source to valid source values
  CASE
    WHEN c.additional_email_source LIKE 'paypal%' THEN 'paypal'
    WHEN c.additional_email_source IN ('kajabi', 'zoho', 'ticket_tailor', 'quickbooks', 'mailchimp') THEN c.additional_email_source
    ELSE 'manual'
  END::TEXT as source,
  false as verified,  -- Not verified
  c.created_at
FROM contacts c
CROSS JOIN LATERAL unnest(string_to_array(c.additional_email, ',')) as email_part
WHERE c.additional_email IS NOT NULL
  AND c.additional_email <> ''
  AND c.deleted_at IS NULL
  AND TRIM(email_part) ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'  -- Valid email format
ON CONFLICT (contact_id, email) DO NOTHING;

-- Verify
DO $$
DECLARE
    v_inserted_count INTEGER;
    v_expected_min INTEGER := 400;  -- Expect ~404
BEGIN
    SELECT COUNT(*) INTO v_inserted_count
    FROM contact_emails
    WHERE source IN ('manual', 'import')
      AND is_primary = false
      AND created_at >= NOW() - INTERVAL '1 minute';

    RAISE NOTICE 'Migrated % additional emails ✓', v_inserted_count;

    IF v_inserted_count < v_expected_min THEN
        RAISE WARNING 'Expected ~404 additional emails, only inserted %', v_inserted_count;
    END IF;
END $$;

-- ============================================
-- STEP 5: UPDATE SEARCH FUNCTION
-- ============================================

\echo ''
\echo 'STEP 5: Updating search function to search ALL emails...'

CREATE OR REPLACE FUNCTION search_contacts(
  p_query TEXT,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  contact_id UUID,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  total_spent NUMERIC,
  is_member BOOLEAN,
  is_donor BOOLEAN,
  match_score REAL,
  match_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ON (c.id)
    c.id,
    CONCAT_WS(' ', c.first_name, c.last_name) as full_name,
    c.email::TEXT,  -- Cast citext to TEXT
    c.phone,
    COALESCE(c.total_spent, 0) as total_spent,
    COALESCE(c.has_active_subscription, false) as is_member,
    (COALESCE(c.total_spent, 0) > 0) as is_donor,
    1.0::REAL as match_score,
    CASE
      WHEN c.first_name ILIKE '%' || p_query || '%' OR c.last_name ILIKE '%' || p_query || '%' THEN 'name'
      WHEN c.email ILIKE '%' || p_query || '%' THEN 'primary_email'
      WHEN ce.email ILIKE '%' || p_query || '%' THEN 'additional_email'
      WHEN c.phone ILIKE '%' || p_query || '%' THEN 'phone'
      ELSE 'other'
    END::TEXT as match_type
  FROM contacts c
  LEFT JOIN contact_emails ce ON c.id = ce.contact_id
  WHERE c.deleted_at IS NULL
    AND (
      c.first_name ILIKE '%' || p_query || '%'
      OR c.last_name ILIKE '%' || p_query || '%'
      OR c.phone ILIKE '%' || p_query || '%'
      OR c.email ILIKE '%' || p_query || '%'
      OR ce.email ILIKE '%' || p_query || '%'  -- ✅ SEARCH ALL EMAILS
    )
  ORDER BY c.id, c.created_at DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

DO $$ BEGIN
  RAISE NOTICE 'Updated search_contacts() function ✓';
END $$;

-- ============================================
-- STEP 6: CREATE EMAIL MANAGEMENT FUNCTIONS
-- ============================================

\echo ''
\echo 'STEP 6: Creating email management functions...'

-- Function to change primary email
CREATE OR REPLACE FUNCTION set_primary_email(
  p_contact_id UUID,
  p_new_primary_email TEXT
)
RETURNS TABLE(
  success BOOLEAN,
  message TEXT,
  old_primary_email TEXT,
  new_primary_email TEXT
) AS $$
DECLARE
  v_old_primary_email TEXT;
  v_email_exists BOOLEAN;
BEGIN
  -- Validate: Check if email exists for this contact
  SELECT EXISTS(
    SELECT 1 FROM contact_emails
    WHERE contact_id = p_contact_id
      AND email = p_new_primary_email
  ) INTO v_email_exists;

  IF NOT v_email_exists THEN
    RETURN QUERY SELECT
      false,
      'Email not found for this contact'::TEXT,
      NULL::TEXT,
      NULL::TEXT;
    RETURN;
  END IF;

  -- Get current primary email
  SELECT email INTO v_old_primary_email
  FROM contact_emails
  WHERE contact_id = p_contact_id
    AND is_primary = true;

  -- Check if already primary
  IF v_old_primary_email = p_new_primary_email THEN
    RETURN QUERY SELECT
      true,
      'Email is already primary'::TEXT,
      v_old_primary_email,
      p_new_primary_email;
    RETURN;
  END IF;

  -- ATOMIC OPERATION: Change primary email
  -- Step 1: Unset old primary
  UPDATE contact_emails
  SET is_primary = false
  WHERE contact_id = p_contact_id
    AND is_primary = true;

  -- Step 2: Set new primary
  UPDATE contact_emails
  SET is_primary = true
  WHERE contact_id = p_contact_id
    AND email = p_new_primary_email;

  -- Step 3: Update contacts.email for backward compatibility
  UPDATE contacts
  SET email = p_new_primary_email,
      updated_at = NOW()
  WHERE id = p_contact_id;

  -- Return success
  RETURN QUERY SELECT
    true,
    'Primary email changed successfully'::TEXT,
    v_old_primary_email,
    p_new_primary_email;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
  RAISE NOTICE 'Created set_primary_email() function ✓';
END $$;

-- ============================================
-- STEP 7: CREATE MONITORING VIEW
-- ============================================

\echo ''
\echo 'STEP 7: Creating email health monitoring view...'

CREATE OR REPLACE VIEW email_sync_health AS
SELECT
  'Total contacts' as metric,
  COUNT(*)::TEXT as count
FROM contacts
WHERE deleted_at IS NULL
UNION ALL
SELECT
  'Contacts with email field',
  COUNT(*)::TEXT
FROM contacts
WHERE deleted_at IS NULL AND email IS NOT NULL
UNION ALL
SELECT
  'Contacts with primary in contact_emails',
  COUNT(DISTINCT contact_id)::TEXT
FROM contact_emails
WHERE is_primary = true
UNION ALL
SELECT
  'MISSING primary emails',
  COUNT(*)::TEXT
FROM contacts c
WHERE c.deleted_at IS NULL
  AND c.email IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM contact_emails ce
    WHERE ce.contact_id = c.id AND ce.is_primary = true
  )
UNION ALL
SELECT
  'Contacts with 1 email',
  COUNT(*)::TEXT
FROM (
  SELECT contact_id
  FROM contact_emails
  GROUP BY contact_id
  HAVING COUNT(*) = 1
) x
UNION ALL
SELECT
  'Contacts with 2 emails',
  COUNT(*)::TEXT
FROM (
  SELECT contact_id
  FROM contact_emails
  GROUP BY contact_id
  HAVING COUNT(*) = 2
) x
UNION ALL
SELECT
  'Contacts with 3+ emails',
  COUNT(*)::TEXT
FROM (
  SELECT contact_id
  FROM contact_emails
  GROUP BY contact_id
  HAVING COUNT(*) >= 3
) x
UNION ALL
SELECT
  'Total emails in contact_emails',
  COUNT(*)::TEXT
FROM contact_emails;

DO $$ BEGIN
  RAISE NOTICE 'Created email_sync_health view ✓';
END $$;

-- ============================================
-- STEP 8: DEPRECATE is_outreach FIELD
-- ============================================

\echo ''
\echo 'STEP 8: Deprecating is_outreach terminology...'

COMMENT ON COLUMN contact_emails.is_outreach IS
'⚠️ DEPRECATED (2025-11-10): No longer used. Use is_primary to identify main email.
All non-primary emails are "additional emails".';

DO $$ BEGIN
  RAISE NOTICE 'Deprecated is_outreach field ✓';
END $$;

-- ============================================
-- POST-MIGRATION VERIFICATION
-- ============================================

\echo ''
\echo '================================'
\echo 'POST-MIGRATION VERIFICATION'
\echo '================================'

DO $$
DECLARE
    v_total_contacts INTEGER;
    v_contacts_with_primary INTEGER;
    v_contacts_missing_primary INTEGER;
    v_total_emails INTEGER;
    v_contacts_with_multiple_emails INTEGER;
BEGIN
    -- Total contacts
    SELECT COUNT(*) INTO v_total_contacts
    FROM contacts WHERE deleted_at IS NULL;

    -- Contacts with primary
    SELECT COUNT(DISTINCT contact_id) INTO v_contacts_with_primary
    FROM contact_emails WHERE is_primary = true;

    -- Contacts still missing primary
    SELECT COUNT(*) INTO v_contacts_missing_primary
    FROM contacts c
    WHERE c.deleted_at IS NULL
      AND c.email IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM contact_emails ce
        WHERE ce.contact_id = c.id AND ce.is_primary = true
      );

    -- Total emails
    SELECT COUNT(*) INTO v_total_emails FROM contact_emails;

    -- Contacts with multiple emails
    SELECT COUNT(*) INTO v_contacts_with_multiple_emails
    FROM (
      SELECT contact_id
      FROM contact_emails
      GROUP BY contact_id
      HAVING COUNT(*) > 1
    ) x;

    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'MIGRATION SUMMARY:';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'Total contacts: %', v_total_contacts;
    RAISE NOTICE 'Contacts with primary email: %', v_contacts_with_primary;
    RAISE NOTICE 'Contacts MISSING primary: %', v_contacts_missing_primary;
    RAISE NOTICE 'Total emails in system: %', v_total_emails;
    RAISE NOTICE 'Contacts with 2+ emails: %', v_contacts_with_multiple_emails;
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';

    IF v_contacts_missing_primary > 0 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: % contacts still missing primary email!', v_contacts_missing_primary;
    END IF;

    IF v_contacts_with_primary != v_total_contacts THEN
        RAISE EXCEPTION 'MIGRATION FAILED: Primary count (%) != Total contacts (%)', v_contacts_with_primary, v_total_contacts;
    END IF;

    RAISE NOTICE '✅ ALL VERIFICATION CHECKS PASSED!';
END $$;

COMMIT;

\echo ''
\echo '================================'
\echo 'MIGRATION COMPLETED SUCCESSFULLY!'
\echo 'Completed at:' :current_timestamp
\echo '================================'
\echo ''
\echo 'Next steps:'
\echo '1. Run: SELECT * FROM email_sync_health;'
\echo '2. Test search: SELECT * FROM search_contacts(''gmail'', 10);'
\echo '3. Test with UI: Search for additional emails'
\echo ''

-- ============================================
-- EXAMPLE QUERIES FOR TESTING
-- ============================================

-- View email health
-- SELECT * FROM email_sync_health;

-- Find contacts with multiple emails
-- SELECT
--   c.first_name,
--   c.last_name,
--   COUNT(ce.email) as email_count,
--   string_agg(ce.email, ', ' ORDER BY ce.is_primary DESC) as all_emails
-- FROM contacts c
-- INNER JOIN contact_emails ce ON c.id = ce.contact_id
-- WHERE c.deleted_at IS NULL
-- GROUP BY c.id, c.first_name, c.last_name
-- HAVING COUNT(ce.email) >= 2
-- ORDER BY COUNT(ce.email) DESC
-- LIMIT 20;

-- Test search for additional email
-- SELECT * FROM search_contacts('dralafly@gmail.com', 10);

-- Test changing primary email
-- SELECT * FROM set_primary_email(
--   'contact-uuid-here',
--   'new-primary@example.com'
-- );
