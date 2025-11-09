-- ============================================================================
-- QUICK FIX: Phone Formatting Duplicates
-- ============================================================================
-- Merges 5 groups with identical normalized phone numbers
-- Examples: "1 303-555-1212" vs "3035551212" (same number, different format)
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'QUICK FIX: Phone Formatting Duplicates (5 groups)'
\echo '============================================================================'
\echo ''

-- Reuse merge function
CREATE OR REPLACE FUNCTION merge_contacts(
  p_primary_id UUID,
  p_duplicate_id UUID,
  p_name TEXT
) RETURNS TEXT AS $$
BEGIN
  INSERT INTO contacts_merge_backup (
    primary_contact_id,
    duplicate_contact_id,
    duplicate_contact_data,
    notes
  )
  SELECT p_primary_id, p_duplicate_id, row_to_json(c.*)::jsonb, 'Phone formatting fix: ' || p_name
  FROM contacts c WHERE c.id = p_duplicate_id;

  UPDATE contacts
  SET
    additional_email = CASE
      WHEN additional_email IS NULL THEN (SELECT email FROM contacts WHERE id = p_duplicate_id)
      WHEN additional_email NOT LIKE '%' || (SELECT email FROM contacts WHERE id = p_duplicate_id) || '%'
        THEN additional_email || ', ' || (SELECT email FROM contacts WHERE id = p_duplicate_id)
      ELSE additional_email
    END,
    created_at = LEAST(created_at, (SELECT created_at FROM contacts WHERE id = p_duplicate_id)),
    updated_at = NOW()
  WHERE id = p_primary_id;

  UPDATE transactions SET contact_id = p_primary_id, updated_at = NOW()
  WHERE contact_id = p_duplicate_id;

  UPDATE subscriptions SET contact_id = p_primary_id, updated_at = NOW()
  WHERE contact_id = p_duplicate_id;

  INSERT INTO contact_tags (contact_id, tag_id)
  SELECT DISTINCT p_primary_id, ct.tag_id
  FROM contact_tags ct
  WHERE ct.contact_id = p_duplicate_id
    AND NOT EXISTS (SELECT 1 FROM contact_tags ct2 WHERE ct2.contact_id = p_primary_id AND ct2.tag_id = ct.tag_id)
  ON CONFLICT (contact_id, tag_id) DO NOTHING;

  UPDATE contacts_merge_backup
  SET
    merged_transactions_count = (SELECT COUNT(*) FROM transactions WHERE contact_id = p_primary_id),
    merged_tags = (SELECT ARRAY_AGG(t.name ORDER BY t.name) FROM contact_tags ct JOIN tags t ON ct.tag_id = t.id WHERE ct.contact_id = p_primary_id)
  WHERE duplicate_contact_id = p_duplicate_id AND merged_at > NOW() - INTERVAL '1 minute';

  DELETE FROM contact_tags WHERE contact_id = p_duplicate_id;
  DELETE FROM contacts WHERE id = p_duplicate_id;

  RETURN '✓ Fixed: ' || p_name;
END;
$$ LANGUAGE plpgsql;

\echo 'Created merge function'
\echo ''

-- Merge phone formatting duplicates
DO $$
DECLARE
  v_group RECORD;
  v_dup_id UUID;
  v_dup_email TEXT;
  v_merge_count INTEGER := 0;
BEGIN
  FOR v_group IN (
    WITH phone_groups AS (
      SELECT
        LOWER(TRIM(first_name || ' ' || last_name)) as full_name,
        REGEXP_REPLACE(phone, '[^0-9]', '', 'g') as normalized_phone,
        ARRAY_AGG(id ORDER BY
          (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) DESC,
          LENGTH(phone) DESC  -- Prefer formatted phone numbers
        ) as contact_ids,
        ARRAY_AGG(email ORDER BY
          (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) DESC,
          LENGTH(phone) DESC
        ) as emails,
        ARRAY_AGG(phone ORDER BY
          (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) DESC,
          LENGTH(phone) DESC
        ) as phones
      FROM contacts
      WHERE phone IS NOT NULL
        AND phone != ''
        AND TRIM(first_name || ' ' || last_name) != ''
      GROUP BY
        LOWER(TRIM(first_name || ' ' || last_name)),
        REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
      HAVING COUNT(*) > 1
    )
    SELECT
      full_name,
      contact_ids[1] as primary_id,
      emails[1] as primary_email,
      phones[1] as primary_phone,
      normalized_phone,
      contact_ids[2:] as duplicate_ids,
      emails[2:] as duplicate_emails,
      phones[2:] as duplicate_phones
    FROM phone_groups
    ORDER BY full_name
  )
  LOOP
    FOR i IN 1..COALESCE(ARRAY_LENGTH(v_group.duplicate_ids, 1), 0)
    LOOP
      v_dup_id := v_group.duplicate_ids[i];
      v_dup_email := v_group.duplicate_emails[i];

      PERFORM merge_contacts(
        v_group.primary_id,
        v_dup_id,
        v_group.full_name || ' (Phone: ' || v_group.primary_phone || ' ← ' || v_group.duplicate_phones[i] || ')'
      );

      v_merge_count := v_merge_count + 1;
    END LOOP;
  END LOOP;

  RAISE NOTICE 'Total phone formatting fixes: %', v_merge_count;
END $$;

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'

SELECT
  'Phone Formatting Fixes' as metric,
  COUNT(*) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Phone formatting fix:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

SELECT
  'Orphaned Transactions' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM transactions t
LEFT JOIN contacts c ON t.contact_id = c.id
WHERE c.id IS NULL;

SELECT
  'Orphaned Subscriptions' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM subscriptions s
LEFT JOIN contacts c ON s.contact_id = c.id
WHERE c.id IS NULL;

-- Check remaining phone formatting issues
SELECT
  'Remaining Phone Format Issues' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '⚠ Some Remain' END as status
FROM (
  SELECT
    LOWER(TRIM(first_name || ' ' || last_name)),
    REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
  FROM contacts
  WHERE phone IS NOT NULL
    AND phone != ''
    AND TRIM(first_name || ' ' || last_name) != ''
  GROUP BY
    LOWER(TRIM(first_name || ' ' || last_name)),
    REGEXP_REPLACE(phone, '[^0-9]', '', 'g')
  HAVING COUNT(*) > 1
) subq;

\echo ''
\echo '============================================================================'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '============================================================================'

DROP FUNCTION merge_contacts(UUID, UUID, TEXT);

-- COMMIT the quick fix
COMMIT;

\echo ''
\echo '============================================================================'
\echo '✓ PHONE FORMATTING QUICK FIX COMMITTED!'
\echo '============================================================================'
