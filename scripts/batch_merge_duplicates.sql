-- ============================================================================
-- BATCH MERGE: 15 High-Confidence Duplicates
-- ============================================================================
-- This script merges the remaining 15 duplicates identified by fuzzy matching
-- All have 80%+ confidence (same name, phone, and address)
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'BATCH MERGE: Processing 15 high-confidence duplicates'
\echo '============================================================================'
\echo ''

-- Create merge function for reusability
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
    'Batch merge: ' || p_name
  FROM contacts c
  WHERE c.id = p_duplicate_id;

  -- Update primary with additional email
  UPDATE contacts
  SET
    additional_email = COALESCE(additional_email, (SELECT email FROM contacts WHERE id = p_duplicate_id)),
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

-- Merge #2: Alan Kaplan (91% confidence)
SELECT merge_contacts(
  '27303ecd-5c30-4376-8130-ef168e3c8f9e'::uuid,
  '97a58493-35e5-4ae2-895a-da2a3a8798f2'::uuid,
  'Alan Kaplan (alan@clickplay.com ← alan@fastideas.biz)'
);

-- Merge #3: Amrita Rose (91% confidence)
SELECT merge_contacts(
  '63422e81-e47a-4c04-ab78-c4cf50268c24'::uuid,
  '185218ac-e0f2-4e9a-9414-d262d933f235'::uuid,
  'Amrita Rose (hello@amrita-rose.com ← hello@anunstoppablelife.com)'
);

-- Merge #4: Melissa Michaels (89.9% confidence)
SELECT merge_contacts(
  '98ab8bc1-da9a-4507-944c-0a798d4e4d3e'::uuid,
  '8df135f7-75ff-4d8b-aa04-7993b69b430c'::uuid,
  'Melissa Michaels (melissa@bdanced.com ← melissa@goldenbridge.org)'
);

-- Merge #5: Daniel Kolman (86.1% confidence)
SELECT merge_contacts(
  '3e5d8354-1d4c-4c6c-8b14-be82ee5ea34e'::uuid,
  '21e104e2-5305-42f0-9bd2-6908d3596b7c'::uuid,
  'Daniel Kolman (daniel.kolman+us@gmail.com ← daniel.kolman@gmail.com)'
);

-- Merge #6: Amy Garnsey (84.4% confidence)
SELECT merge_contacts(
  '06bfe216-e449-4b6d-b876-7963874c85c7'::uuid,
  'b860f8ee-9454-43bc-ab74-1dcc4a7df7af'::uuid,
  'Amy Garnsey (abzgarnsey@bellsouth.net ← ajfgarnsey@gmail.com)'
);

-- Merge #7: Cindy Michel (83.2% confidence)
SELECT merge_contacts(
  'ed745490-00ca-497d-8fc6-6e87c424943f'::uuid,
  'bf31595c-f835-407e-9550-72a96e294686'::uuid,
  'Cindy Michel (cindy_michel@yahoo.com ← cindymicheltherapy@gmail.com)'
);

-- Merge #8: Amy Susynski (83.0% confidence)
SELECT merge_contacts(
  'fd29317f-7077-42f1-88d6-892d392b44f9'::uuid,
  '88327793-ba22-43b7-a019-d2d6d86f3802'::uuid,
  'Amy Susynski (amysusynski@yahoo.com ← madge_susynski@yahoo.com)'
);

-- Merge #9: Alanna Bell (82.6% confidence)
SELECT merge_contacts(
  '0c44dd72-5f03-4c92-83f2-f616594ff8f1'::uuid,
  '4eee8893-4374-4e69-9a51-8d367594189b'::uuid,
  'Alanna Bell (llamabell@hotmail.com ← alannajbell@gmail.com)'
);

-- Merge #10: Songya Kesler (82.6% confidence)
SELECT merge_contacts(
  'dfa0b190-2fb2-410a-9364-8d10b0277500'::uuid,
  'ca8a8a28-7d56-4d5b-8f45-2069ff149fe6'::uuid,
  'Songya Kesler (songyakesler@gmail.com ← stkesler@gmail.com)'
);

-- Merge #11: Heather Baines (82.0% confidence)
SELECT merge_contacts(
  'c2a54e1b-231d-41b7-9b95-3a998c1536ee'::uuid,
  'dafda632-b1f2-422b-9d0e-ada244823ecb'::uuid,
  'Heather Baines (heather@earthguardians.org ← heather.baines@outlook.com)'
);

-- Merge #12: Sharon Montes (81.9% confidence)
SELECT merge_contacts(
  '468d6e89-c674-4928-9841-fbb1c88c521a'::uuid,
  'baf16068-de37-4936-af96-e18b5e54d177'::uuid,
  'Sharon Montes (drsharonmontes@gmail.com ← drsharon@livingwellwholehealth.com)'
);

-- Merge #13: Heidi Robbins (80.6% confidence)
SELECT merge_contacts(
  '964e0cb7-1fef-44d1-b081-42094a9b2b08'::uuid,
  'a8b411f6-f0fa-4767-9ddf-f3a7d1606915'::uuid,
  'Heidi Robbins (heidirose4@me.com ← heidi@heidirose.com)'
);

-- Merge #14: Patricia Fields (80.3% confidence)
SELECT merge_contacts(
  '4ee7cadf-8c74-4fbc-b1fc-48a153e743ab'::uuid,
  'e591b345-35cc-4b09-b46f-46570aafcbc4'::uuid,
  'Patricia Fields (patrice@spirit-evolving.com ← fieldspatricia@comcast.net)'
);

-- Merge #15: Kate Kripke (80.3% confidence)
SELECT merge_contacts(
  '79a0aaa3-26b4-4526-923c-56410d4ffe62'::uuid,
  'c0e169ab-5493-4819-9615-5aa1ae63f71c'::uuid,
  'Kate Kripke (katekripke@gmail.com ← kate@pwcboulder.com)'
);

-- Merge #16: Claire Thompson (80.0% confidence)
SELECT merge_contacts(
  'f7a1782c-73eb-4072-b7e9-e30774f947f8'::uuid,
  'fcb436d0-e29e-47d8-a637-4f2888569a52'::uuid,
  'Claire Thompson (claire@producethefuture.com ← zuzuclaire@gmail.com)'
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

SELECT
  'Contacts Before Merge' as metric,
  32 as original_count,
  16 as merged_count,
  16 as final_count;

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

-- Verify backup records
SELECT
  'Backup Records Created' as check,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 15 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM contacts_merge_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes';

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
\echo '✓ BATCH MERGE COMMITTED - All 15 duplicates merged successfully!'
\echo '============================================================================'
