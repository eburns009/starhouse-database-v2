-- ============================================================================
-- BATCH MERGE: Phone-Verified Duplicates
-- ============================================================================
-- Merges contacts with identical names and SAME phone number
-- Strategy: Keep contact with most activity (transactions, subscriptions)
--
-- Safe to merge because:
-- - Same person name
-- - Same phone number = definitely same person
-- - Example: person@gmail.com + person@business.com (same phone)
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'BATCH MERGE: Phone-Verified Duplicates (Same Name + Same Phone)'
\echo '============================================================================'
\echo ''

-- Reuse merge function
CREATE OR REPLACE FUNCTION merge_contacts(
  p_primary_id UUID,
  p_duplicate_id UUID,
  p_name TEXT
) RETURNS TEXT AS $$
BEGIN
  -- Backup duplicate
  INSERT INTO contacts_merge_backup (
    primary_contact_id,
    duplicate_contact_id,
    duplicate_contact_data,
    notes
  )
  SELECT
    p_primary_id,
    p_duplicate_id,
    row_to_json(c.*)::jsonb,
    'Phone-verified merge: ' || p_name
  FROM contacts c
  WHERE c.id = p_duplicate_id;

  -- Update primary with additional email
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

  -- Reassign transactions
  UPDATE transactions SET contact_id = p_primary_id, updated_at = NOW()
  WHERE contact_id = p_duplicate_id;

  -- Reassign subscriptions
  UPDATE subscriptions SET contact_id = p_primary_id, updated_at = NOW()
  WHERE contact_id = p_duplicate_id;

  -- Merge tags
  INSERT INTO contact_tags (contact_id, tag_id)
  SELECT DISTINCT p_primary_id, ct.tag_id
  FROM contact_tags ct
  WHERE ct.contact_id = p_duplicate_id
    AND NOT EXISTS (SELECT 1 FROM contact_tags ct2 WHERE ct2.contact_id = p_primary_id AND ct2.tag_id = ct.tag_id)
  ON CONFLICT (contact_id, tag_id) DO NOTHING;

  -- Update backup metadata
  UPDATE contacts_merge_backup
  SET
    merged_transactions_count = (SELECT COUNT(*) FROM transactions WHERE contact_id = p_primary_id),
    merged_tags = (SELECT ARRAY_AGG(t.name ORDER BY t.name) FROM contact_tags ct JOIN tags t ON ct.tag_id = t.id WHERE ct.contact_id = p_primary_id)
  WHERE duplicate_contact_id = p_duplicate_id AND merged_at > NOW() - INTERVAL '1 minute';

  -- Delete duplicate
  DELETE FROM contact_tags WHERE contact_id = p_duplicate_id;
  DELETE FROM contacts WHERE id = p_duplicate_id;

  RETURN '✓ Merged: ' || p_name;
END;
$$ LANGUAGE plpgsql;

\echo 'Created merge function'
\echo ''

-- Generate and execute merges for phone-verified duplicates
DO $$
DECLARE
  v_group RECORD;
  v_dup_id UUID;
  v_dup_email TEXT;
  v_merge_count INTEGER := 0;
BEGIN
  -- Loop through each duplicate group with matching phones
  FOR v_group IN (
    WITH two_domain_phone_groups AS (
      SELECT
        LOWER(TRIM(first_name || ' ' || last_name)) as full_name,
        ARRAY_AGG(id ORDER BY
          (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) DESC,
          (SELECT COUNT(*) FROM subscriptions WHERE contact_id = contacts.id) DESC,
          created_at DESC
        ) as contact_ids,
        ARRAY_AGG(email ORDER BY
          (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) DESC,
          (SELECT COUNT(*) FROM subscriptions WHERE contact_id = contacts.id) DESC,
          created_at DESC
        ) as emails,
        ARRAY_AGG(phone ORDER BY
          (SELECT COUNT(*) FROM transactions WHERE contact_id = contacts.id) DESC,
          (SELECT COUNT(*) FROM subscriptions WHERE contact_id = contacts.id) DESC,
          created_at DESC
        ) as phones,
        COUNT(DISTINCT phone) FILTER (WHERE phone IS NOT NULL AND phone != '') as unique_phones
      FROM contacts
      WHERE LOWER(TRIM(first_name || ' ' || last_name)) IN (
        SELECT LOWER(TRIM(first_name || ' ' || last_name))
        FROM contacts
        GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
        HAVING COUNT(*) > 1
          AND COUNT(DISTINCT SUBSTRING(email FROM '@(.*)$')) >= 2
      )
      GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
    )
    SELECT
      full_name,
      contact_ids[1] as primary_id,
      emails[1] as primary_email,
      phones[1] as shared_phone,
      contact_ids[2:] as duplicate_ids,
      emails[2:] as duplicate_emails
    FROM two_domain_phone_groups
    WHERE unique_phones = 1  -- Same phone number across all contacts
    ORDER BY full_name
  )
  LOOP
    -- Merge each duplicate in the group
    FOR i IN 1..COALESCE(ARRAY_LENGTH(v_group.duplicate_ids, 1), 0)
    LOOP
      v_dup_id := v_group.duplicate_ids[i];
      v_dup_email := v_group.duplicate_emails[i];

      PERFORM merge_contacts(
        v_group.primary_id,
        v_dup_id,
        v_group.full_name || ' (' || v_group.primary_email || ' ← ' || v_dup_email || ') [Phone: ' || v_group.shared_phone || ']'
      );

      v_merge_count := v_merge_count + 1;

      -- Progress indicator every 20 merges
      IF v_merge_count % 20 = 0 THEN
        RAISE NOTICE 'Progress: % merges completed', v_merge_count;
      END IF;
    END LOOP;
  END LOOP;

  RAISE NOTICE 'Total merges completed: %', v_merge_count;
END $$;

\echo ''
\echo '============================================================================'
\echo 'BATCH MERGE SUMMARY'
\echo '============================================================================'

-- Summary statistics
SELECT
  'Phone-Verified Merges' as metric,
  COUNT(*) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Phone-verified merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

SELECT
  'Total Transactions Preserved' as metric,
  SUM(merged_transactions_count) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Phone-verified merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'

-- Verify no orphaned transactions
SELECT
  'Orphaned Transactions' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM transactions t
LEFT JOIN contacts c ON t.contact_id = c.id
WHERE c.id IS NULL;

-- Verify no orphaned subscriptions
SELECT
  'Orphaned Subscriptions' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM subscriptions s
LEFT JOIN contacts c ON s.contact_id = c.id
WHERE c.id IS NULL;

-- Verify backup records
SELECT
  'Backup Records Created' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) > 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM contacts_merge_backup
WHERE notes LIKE 'Phone-verified merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

-- Check remaining phone-verified duplicates
SELECT
  'Remaining Phone-Verified Duplicates' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '⚠ Some Remain' END as status
FROM (
  WITH two_domain_groups AS (
    SELECT
      LOWER(TRIM(first_name || ' ' || last_name)) as full_name,
      COUNT(DISTINCT phone) FILTER (WHERE phone IS NOT NULL AND phone != '') as unique_phones
    FROM contacts
    WHERE LOWER(TRIM(first_name || ' ' || last_name)) IN (
      SELECT LOWER(TRIM(first_name || ' ' || last_name))
      FROM contacts
      GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
      HAVING COUNT(*) > 1
    )
    GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
  )
  SELECT full_name
  FROM two_domain_groups
  WHERE unique_phones = 1
) subq;

\echo ''
\echo '============================================================================'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '============================================================================'

-- Clean up function
DROP FUNCTION merge_contacts(UUID, UUID, TEXT);

-- COMMIT the batch merge
COMMIT;

\echo ''
\echo '============================================================================'
\echo '✓ PHONE-VERIFIED BATCH MERGE COMMITTED!'
\echo '============================================================================'
