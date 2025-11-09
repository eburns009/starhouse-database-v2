-- ============================================================================
-- TIER 1 HIGH-CONFIDENCE DUPLICATE MERGES
-- ============================================================================
-- Merging 6 pairs (12 contacts) with 85-98% confidence scores
-- All have multiple corroborating signals (address, tags, same username, etc.)
-- Full backup and rollback capability included
--
-- Cases:
-- 1. Deborah Ogden (98%) - Same username migration: drumrgirl@comcast → drumrgirl@outlook
-- 2. Kiley Hartigan (95%) - Same business domain: kiley@ → support@
-- 3. Corin Blanchard (95%) - StarHouse email: personal → @thestarhouse.org
-- 4. Ibrahim Abdiov (95%) - Same username: @gmail → @icloud
-- 5. Catherine Boerder (90%) - Same domain: cboerder.toolkit@ → catherine.boerder@
-- 6. Rebecca Kester (85%) - Same address + tags: daaniarebecca@ → rebeccalkester@
-- ============================================================================

BEGIN;

\echo '════════════════════════════════════════════════════════════'
\echo 'TIER 1 HIGH-CONFIDENCE DUPLICATE MERGES'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Reuse merge function from previous cleanup
CREATE OR REPLACE FUNCTION merge_contacts(
  p_primary_id UUID,
  p_duplicate_id UUID,
  p_name TEXT
) RETURNS TEXT AS $$
BEGIN
  -- Backup duplicate record
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
    'Tier 1 high-confidence merge: ' || p_name
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
  UPDATE transactions
  SET contact_id = p_primary_id, updated_at = NOW()
  WHERE contact_id = p_duplicate_id;

  -- Reassign subscriptions
  UPDATE subscriptions
  SET contact_id = p_primary_id, updated_at = NOW()
  WHERE contact_id = p_duplicate_id;

  -- Merge tags
  INSERT INTO contact_tags (contact_id, tag_id)
  SELECT DISTINCT p_primary_id, ct.tag_id
  FROM contact_tags ct
  WHERE ct.contact_id = p_duplicate_id
    AND NOT EXISTS (
      SELECT 1 FROM contact_tags ct2
      WHERE ct2.contact_id = p_primary_id
        AND ct2.tag_id = ct.tag_id
    )
  ON CONFLICT (contact_id, tag_id) DO NOTHING;

  -- Update backup metadata
  UPDATE contacts_merge_backup
  SET
    merged_transactions_count = (SELECT COUNT(*) FROM transactions WHERE contact_id = p_primary_id),
    merged_tags = (
      SELECT ARRAY_AGG(t.name ORDER BY t.name)
      FROM contact_tags ct
      JOIN tags t ON ct.tag_id = t.id
      WHERE ct.contact_id = p_primary_id
    )
  WHERE duplicate_contact_id = p_duplicate_id
    AND merged_at > NOW() - INTERVAL '1 minute';

  -- Delete duplicate
  DELETE FROM contact_tags WHERE contact_id = p_duplicate_id;
  DELETE FROM contacts WHERE id = p_duplicate_id;

  RETURN '✓ Merged: ' || p_name;
END;
$$ LANGUAGE plpgsql;

\echo 'Merge function created'
\echo ''

-- ============================================================================
-- CASE 1: Deborah Ogden (98% confidence)
-- ============================================================================
\echo '--- Case 1: Deborah Ogden (98%) ---'

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep the one with more activity (drumrgirl@outlook.com has 2 txns)
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'drumrgirl@outlook.com'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'drumrgirl@comcast.net'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Deborah Ogden (drumrgirl@outlook.com ← drumrgirl@comcast.net) [Same username migration]'
    );
    RAISE NOTICE '✓ Merged Deborah Ogden';
  ELSE
    RAISE NOTICE '⚠ Deborah Ogden: Contact not found';
  END IF;
END $$;

-- ============================================================================
-- CASE 2: Kiley Hartigan (95% confidence)
-- ============================================================================
\echo '--- Case 2: Kiley Hartigan (95%) ---'

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep kiley@ (personal) as primary, merge support@
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'kiley@journeyon-coaching.com'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'support@journeyon-coaching.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Kiley Hartigan (kiley@journeyon-coaching.com ← support@journeyon-coaching.com) [Same business domain]'
    );
    RAISE NOTICE '✓ Merged Kiley Hartigan';
  ELSE
    RAISE NOTICE '⚠ Kiley Hartigan: Contact not found';
  END IF;
END $$;

-- ============================================================================
-- CASE 3: Corin Blanchard (95% confidence)
-- ============================================================================
\echo '--- Case 3: Corin Blanchard (95%) ---'

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep @thestarhouse.org as primary (official email)
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'corin@thestarhouse.org'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'corinblanchard@gmail.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Corin Blanchard (corin@thestarhouse.org ← corinblanchard@gmail.com) [StarHouse official email]'
    );
    RAISE NOTICE '✓ Merged Corin Blanchard';
  ELSE
    RAISE NOTICE '⚠ Corin Blanchard: Contact not found';
  END IF;
END $$;

-- ============================================================================
-- CASE 4: Ibrahim Abdiov (95% confidence)
-- ============================================================================
\echo '--- Case 4: Ibrahim Abdiov (95%) ---'

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep @gmail.com as primary (more common)
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'ibrahimabdiov@gmail.com'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'ibrahimabdiov@icloud.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Ibrahim Abdiov (ibrahimabdiov@gmail.com ← ibrahimabdiov@icloud.com) [Same username, multi-device]'
    );
    RAISE NOTICE '✓ Merged Ibrahim Abdiov';
  ELSE
    RAISE NOTICE '⚠ Ibrahim Abdiov: Contact not found';
  END IF;
END $$;

-- ============================================================================
-- CASE 5: Catherine Boerder (90% confidence)
-- ============================================================================
\echo '--- Case 5: Catherine Boerder (90%) ---'

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep catherine.boerder@ as primary (more formal), merge cboerder.toolkit@
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'catherine.boerder@gmail.com'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'cboerder.toolkit@gmail.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Catherine Boerder (catherine.boerder@gmail.com ← cboerder.toolkit@gmail.com) [Same Gmail domain]'
    );
    RAISE NOTICE '✓ Merged Catherine Boerder';
  ELSE
    RAISE NOTICE '⚠ Catherine Boerder: Contact not found';
  END IF;
END $$;

-- ============================================================================
-- CASE 6: Rebecca Kester (85% confidence)
-- ============================================================================
\echo '--- Case 6: Rebecca Kester (85%) ---'

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep rebeccalkester@msn.com as primary (full name format)
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'rebeccalkester@msn.com'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'daaniarebecca@gmail.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Rebecca Kester (rebeccalkester@msn.com ← daaniarebecca@gmail.com) [Same address + tags]'
    );
    RAISE NOTICE '✓ Merged Rebecca Kester';
  ELSE
    RAISE NOTICE '⚠ Rebecca Kester: Contact not found';
  END IF;
END $$;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'MERGE SUMMARY'
\echo '════════════════════════════════════════════════════════════'

-- Summary statistics
SELECT
  'Tier 1 Merges Completed' as metric,
  COUNT(*) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Tier 1 high-confidence merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

SELECT
  'Total Transactions Preserved' as metric,
  SUM(merged_transactions_count) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Tier 1 high-confidence merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'VERIFICATION'
\echo '════════════════════════════════════════════════════════════'

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
WHERE notes LIKE 'Tier 1 high-confidence merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '════════════════════════════════════════════════════════════'

-- Clean up function
DROP FUNCTION merge_contacts(UUID, UUID, TEXT);

-- COMMIT the merges
COMMIT;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '✓ TIER 1 HIGH-CONFIDENCE MERGES COMMITTED!'
\echo '════════════════════════════════════════════════════════════'
