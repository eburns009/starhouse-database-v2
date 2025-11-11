-- ============================================================================
-- BATCH MERGE: November 10, 2025 - 6 High-Confidence Duplicates
-- ============================================================================
-- Found using cross-reference logic (email matching, phone matching, same address)
-- Similar to Lynn Ryan / Amber Ryan duplicate pattern
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'BATCH MERGE: Processing 6 high-confidence duplicates found Nov 10'
\echo '============================================================================'
\echo ''

-- Create merge function for reusability
CREATE OR REPLACE FUNCTION merge_contacts_nov10(
  p_primary_id UUID,
  p_duplicate_id UUID,
  p_name TEXT
) RETURNS TEXT AS $$
DECLARE
  v_dup_email TEXT;
  v_dup_phone TEXT;
  v_dup_name TEXT;
  v_dup_additional_email TEXT;
  v_dup_additional_phone TEXT;
  v_dup_additional_name TEXT;
BEGIN
  -- Get duplicate contact info
  SELECT
    email,
    phone,
    first_name || ' ' || COALESCE(last_name, ''),
    additional_email,
    additional_phone,
    additional_name
  INTO
    v_dup_email,
    v_dup_phone,
    v_dup_name,
    v_dup_additional_email,
    v_dup_additional_phone,
    v_dup_additional_name
  FROM contacts
  WHERE id = p_duplicate_id;

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
    'Batch merge Nov 10: ' || p_name
  FROM contacts c
  WHERE c.id = p_duplicate_id;

  -- Update primary with data from duplicate
  UPDATE contacts
  SET
    -- Add duplicate's primary email as additional email if not already set
    additional_email = CASE
      WHEN additional_email IS NULL THEN v_dup_email
      WHEN additional_email != v_dup_email THEN additional_email
      ELSE additional_email
    END,
    -- Add duplicate's additional email to additional_email_source tracking
    additional_email_source = CASE
      WHEN v_dup_additional_email IS NOT NULL AND additional_email IS NULL
        THEN COALESCE(additional_email_source, '') || ' duplicate_merge'
      ELSE additional_email_source
    END,
    -- Add duplicate's phone as additional phone if not already set
    additional_phone = CASE
      WHEN additional_phone IS NULL AND v_dup_phone IS NOT NULL THEN v_dup_phone
      ELSE additional_phone
    END,
    -- Add duplicate's name as additional name if not already set
    additional_name = CASE
      WHEN additional_name IS NULL AND v_dup_name IS NOT NULL THEN v_dup_name
      WHEN additional_name IS NULL AND v_dup_additional_name IS NOT NULL THEN v_dup_additional_name
      ELSE additional_name
    END,
    -- Take earliest created date
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

  -- Merge contact_emails (preserve all email variations)
  INSERT INTO contact_emails (contact_id, email, source, is_primary)
  SELECT
    p_primary_id,
    ce.email,
    ce.source,
    false  -- Don't override primary
  FROM contact_emails ce
  WHERE ce.contact_id = p_duplicate_id
    AND NOT EXISTS (
      SELECT 1 FROM contact_emails ce2
      WHERE ce2.contact_id = p_primary_id AND ce2.email = ce.email
    )
  ON CONFLICT (contact_id, email) DO NOTHING;

  -- Merge contact_names (preserve all name variations)
  INSERT INTO contact_names (contact_id, name_text, name_type, source, is_primary)
  SELECT
    p_primary_id,
    cn.name_text,
    cn.name_type,
    cn.source,
    false  -- Don't override primary
  FROM contact_names cn
  WHERE cn.contact_id = p_duplicate_id
    AND NOT EXISTS (
      SELECT 1 FROM contact_names cn2
      WHERE cn2.contact_id = p_primary_id AND cn2.name_text = cn.name_text
    )
  ON CONFLICT (contact_id, name_text) DO NOTHING;

  -- Update backup metadata
  UPDATE contacts_merge_backup
  SET
    merged_transactions_count = (SELECT COUNT(*) FROM transactions WHERE contact_id = p_primary_id),
    merged_tags = (SELECT ARRAY_AGG(t.name ORDER BY t.name) FROM contact_tags ct JOIN tags t ON ct.tag_id = t.id WHERE ct.contact_id = p_primary_id)
  WHERE duplicate_contact_id = p_duplicate_id AND merged_at > NOW() - INTERVAL '1 minute';

  -- Delete duplicate from junction tables
  DELETE FROM contact_tags WHERE contact_id = p_duplicate_id;
  DELETE FROM contact_emails WHERE contact_id = p_duplicate_id;
  DELETE FROM contact_names WHERE contact_id = p_duplicate_id;

  -- Delete duplicate contact
  DELETE FROM contacts WHERE id = p_duplicate_id;

  RETURN '✓ Merged: ' || p_name;
END;
$$ LANGUAGE plpgsql;

\echo 'Created merge function'
\echo ''

-- ============================================================================
-- MERGE #1: Brooke LeClaire - Email cross-match + same phone
-- ============================================================================
-- Primary: Brooke LeClaire (elegant_caterer0g@icloud.com) - has brookeleclaire@gmail.com as additional
-- Duplicate: Brookeleclairehealing (brookeleclaire@gmail.com) - inactive
-- Same phone: 970-420-8952
SELECT merge_contacts_nov10(
  'c29399ea-27cc-4f77-8f16-b40791643265'::uuid,
  '1b9f3d2b-27f2-4554-9f72-c4efe540d2f4'::uuid,
  'Brooke LeClaire (elegant_caterer0g@icloud.com ← brookeleclaire@gmail.com)'
);

-- ============================================================================
-- MERGE #2: Melissa Michaels - Email cross-match + same phone
-- ============================================================================
-- Primary: Melissa Michaels (melissa@bdanced.com) - has melissa@goldenbridge.org as additional
-- Duplicate: Melissa Michaels (melissa@goldenbridge.org) - inactive
-- Same phone: 303-875-1178
SELECT merge_contacts_nov10(
  '98ab8bc1-da9a-4507-944c-0a798d4e4d3e'::uuid,
  '35b6cc8b-df1c-451e-b68d-896b82aad45f'::uuid,
  'Melissa Michaels (melissa@bdanced.com ← melissa@goldenbridge.org)'
);

-- ============================================================================
-- MERGE #3: Sharon Montes / Living Well Whole Health LLC - Business vs Personal
-- ============================================================================
-- Primary: Sharon Montes (drsharonmontes@gmail.com) - ACTIVE, 2 trans, $214
-- Duplicate: Living Well Whole Health Llc (drsharon@livingwellwholehealth.com) - business entity
-- Email cross-match confirmed
SELECT merge_contacts_nov10(
  '468d6e89-c674-4928-9841-fbb1c88c521a'::uuid,
  '33f9a393-da95-4da2-af9a-92ecfdf4540a'::uuid,
  'Sharon Montes (drsharonmontes@gmail.com ← drsharon@livingwellwholehealth.com [business])'
);

-- ============================================================================
-- MERGE #4: Daniela Papi / Systems-Led Leadership LLC - Business vs Personal
-- ============================================================================
-- Primary: Daniela Papi (danielapapi@gmail.com) - ACTIVE, 6 trans, $425
-- Duplicate: Systems-Led Leadership LLC (daniela@systems-ledleadership.com) - business entity
-- Same address + same phone (different format)
SELECT merge_contacts_nov10(
  '921562ea-2a47-4782-baa7-a07ef7df0989'::uuid,
  'f34bfe5c-76b8-4d4d-bbf3-3f4534ba2d03'::uuid,
  'Daniela Papi (danielapapi@gmail.com ← daniela@systems-ledleadership.com [business])'
);

-- ============================================================================
-- MERGE #5: Roberta Mylan / Roberta Scaer - Maiden/Married name
-- ============================================================================
-- Primary: Roberta Mylan (agoodbirth@yahoo.com) - ACTIVE, 3 trans, $277
-- Duplicate: Roberta Scaer (mercedesmom@att.net) - inactive
-- Same address: 710 Grape Ave, Boulder 80304
SELECT merge_contacts_nov10(
  '1f333ef5-d508-411b-8e08-e9651667268d'::uuid,
  '96cf545d-b798-41c7-84fc-6d6b12c39cf0'::uuid,
  'Roberta Mylan/Scaer (agoodbirth@yahoo.com ← mercedesmom@att.net [maiden/married name])'
);

-- ============================================================================
-- MERGE #6: Lynn Ryan / Amber Ryan - Original duplicate identified
-- ============================================================================
-- Primary: Lynn Ryan (amber@the360emergence.com) - ACTIVE, 22 trans, $1,012
-- Duplicate: Amber Ryan (sacredartsspace@gmail.com) - inactive, created earlier
-- Different Kajabi IDs but same person with name variation
SELECT merge_contacts_nov10(
  '8109792b-9bcb-4cef-87e4-0fb658fe372e'::uuid,
  'fdf2ff15-81bf-426f-80e3-fe00a883dfb8'::uuid,
  'Lynn Ryan/Amber Ryan (amber@the360emergence.com ← sacredartsspace@gmail.com [name variation])'
);

\echo ''
\echo '============================================================================'
\echo 'BATCH MERGE SUMMARY'
\echo '============================================================================'

-- Summary statistics
SELECT
  'Total Merges' as metric,
  COUNT(*) as value
FROM contacts_merge_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes';

SELECT
  'Total Transactions Preserved' as metric,
  SUM(merged_transactions_count) as value
FROM contacts_merge_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes';

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
  CASE WHEN COUNT(*) = 6 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM contacts_merge_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes';

-- Show merged contacts details
\echo ''
\echo 'Merged Contacts Details:'
SELECT
  cmb.notes,
  cmb.merged_transactions_count as trans_count,
  cmb.merged_at::timestamp(0)
FROM contacts_merge_backup cmb
WHERE cmb.merged_at > NOW() - INTERVAL '5 minutes'
ORDER BY cmb.merged_at;

\echo ''
\echo '============================================================================'
\echo 'Ready to COMMIT or ROLLBACK'
\echo 'Review the output above. If everything looks correct, the transaction'
\echo 'will commit. Otherwise, you can manually ROLLBACK.'
\echo '============================================================================'

-- Clean up function
DROP FUNCTION merge_contacts_nov10(UUID, UUID, TEXT);

-- COMMIT the batch merge
COMMIT;

\echo ''
\echo '============================================================================'
\echo '✓ BATCH MERGE COMMITTED - All 6 duplicates merged successfully!'
\echo '============================================================================'
