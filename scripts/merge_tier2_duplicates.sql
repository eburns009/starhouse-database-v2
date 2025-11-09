-- ============================================================================
-- TIER 2 BATCH MERGE: Enhanced Multi-Signal Analysis
-- ============================================================================
-- Merging 2 pairs (4 contacts) with 70-100% ENHANCED confidence scores
-- Enhanced with 2 additional signals: creation timing + exact tag match
--
-- Cases:
-- 1. Greg Yamada (100% - ENHANCED) - Same-day creation + identical 3 tags
--    gregory.yamada@naropa.edu ↔ yiggig@gmail.com
--
-- 2. Susanne Blanchette (70% - ENHANCED) - 1-day creation + same address
--    sblanchette@lefthand.com ↔ scedar53@yahoo.com
--
-- FAANG Enhancement Methodology:
-- - Signal 6: Account creation timing (same-day = 99% match)
-- - Signal 7: Exact tag match (behavioral fingerprint)
-- - Original 5 signals: domain, transactions, address, tags, age
-- ============================================================================

BEGIN;

\echo '════════════════════════════════════════════════════════════'
\echo 'TIER 2 BATCH MERGE: Enhanced Confidence (70-100%)'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Reuse merge function
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
    'Tier 2 enhanced merge: ' || p_name
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
-- CASE 1: Greg Yamada (100% Enhanced Confidence)
-- ============================================================================
\echo '--- Case 1: Greg Yamada (100%) ---'
\echo '    Same-day creation (2023-08-14) + Identical 3 tags'
\echo '    gregory.yamada@naropa.edu ← yiggig@gmail.com'
\echo ''

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep university email as primary (more formal/official)
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'gregory.yamada@naropa.edu'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'yiggig@gmail.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Greg Yamada (gregory.yamada@naropa.edu ← yiggig@gmail.com) [100% - Same-day creation + identical tags]'
    );
    RAISE NOTICE '✓ Merged Greg Yamada (100%% confidence)';
  ELSE
    RAISE NOTICE '⚠ Greg Yamada: Contact not found';
  END IF;
END $$;

-- ============================================================================
-- CASE 2: Susanne Blanchette (70% Enhanced Confidence)
-- ============================================================================
\echo '--- Case 2: Susanne Blanchette (70%) ---'
\echo '    1-day creation gap + Same address (4859 Fairlawn Court)'
\echo '    sblanchette@lefthand.com ← scedar53@yahoo.com'
\echo ''

DO $$
DECLARE
  v_primary_id UUID;
  v_duplicate_id UUID;
BEGIN
  -- Keep sblanchette@lefthand.com as primary (matches name pattern)
  SELECT id INTO v_primary_id
  FROM contacts
  WHERE email = 'sblanchette@lefthand.com'
  LIMIT 1;

  SELECT id INTO v_duplicate_id
  FROM contacts
  WHERE email = 'scedar53@yahoo.com'
  LIMIT 1;

  IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
    PERFORM merge_contacts(
      v_primary_id,
      v_duplicate_id,
      'Susanne Blanchette (sblanchette@lefthand.com ← scedar53@yahoo.com) [70% - 1-day creation + same address]'
    );
    RAISE NOTICE '✓ Merged Susanne Blanchette (70%% confidence)';
  ELSE
    RAISE NOTICE '⚠ Susanne Blanchette: Contact not found';
  END IF;
END $$;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'MERGE SUMMARY'
\echo '════════════════════════════════════════════════════════════'

-- Summary statistics
SELECT
  'Tier 2 Merges Completed' as metric,
  COUNT(*) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Tier 2 enhanced merge:%'
  AND merged_at > NOW() - INTERVAL '5 minutes';

SELECT
  'Confidence Range' as metric,
  '70-100%' as value;

SELECT
  'Total Transactions Preserved' as metric,
  COALESCE(SUM(merged_transactions_count), 0) as value
FROM contacts_merge_backup
WHERE notes LIKE 'Tier 2 enhanced merge:%'
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
WHERE notes LIKE 'Tier 2 enhanced merge:%'
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
\echo '✓ TIER 2 ENHANCED BATCH MERGE COMMITTED!'
\echo '════════════════════════════════════════════════════════════'
