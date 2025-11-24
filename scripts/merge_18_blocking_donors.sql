-- ============================================================================
-- MERGE: 18 Blocking Donor Imports - November 24, 2025
-- ============================================================================
-- These 18 duplicates are blocking QuickBooks donor imports.
-- Priority: Resolve these to unblock import of 18 donor records.
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'MERGE: 18 Blocking Donor Imports'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- MERGE FUNCTION (reuse from previous scripts)
-- ============================================================================

CREATE OR REPLACE FUNCTION merge_contact_pair(
  p_keep_id UUID,
  p_merge_id UUID,
  p_reason TEXT
) RETURNS TEXT AS $$
DECLARE
  v_merge_email TEXT;
  v_merge_phone TEXT;
  v_txn_count INT;
  v_sub_count INT;
  v_donor_count INT;
BEGIN
  -- Get duplicate's email
  SELECT email, phone INTO v_merge_email, v_merge_phone
  FROM contacts WHERE id = p_merge_id;

  -- 1. Backup the duplicate contact
  INSERT INTO contacts_merge_backup (
    primary_contact_id,
    duplicate_contact_id,
    duplicate_contact_data,
    notes
  )
  SELECT
    p_keep_id,
    p_merge_id,
    row_to_json(c.*)::jsonb,
    'Blocking donor merge Nov 24: ' || p_reason
  FROM contacts c
  WHERE c.id = p_merge_id;

  -- 2. Add duplicate's email to contact_emails
  INSERT INTO contact_emails (contact_id, email, email_type, is_primary, source)
  VALUES (p_keep_id, v_merge_email, 'personal', false, 'import')
  ON CONFLICT (contact_id, email) DO NOTHING;

  -- 3. Update keeper with earliest created_at
  UPDATE contacts
  SET
    created_at = LEAST(created_at, (SELECT created_at FROM contacts WHERE id = p_merge_id)),
    updated_at = NOW()
  WHERE id = p_keep_id;

  -- 4. Reassign transactions
  UPDATE transactions
  SET contact_id = p_keep_id, updated_at = NOW()
  WHERE contact_id = p_merge_id;
  GET DIAGNOSTICS v_txn_count = ROW_COUNT;

  -- 5. Reassign subscriptions
  UPDATE subscriptions
  SET contact_id = p_keep_id, updated_at = NOW()
  WHERE contact_id = p_merge_id;
  GET DIAGNOSTICS v_sub_count = ROW_COUNT;

  -- 6. Reassign donors
  UPDATE donors
  SET contact_id = p_keep_id, updated_at = NOW()
  WHERE contact_id = p_merge_id;
  GET DIAGNOSTICS v_donor_count = ROW_COUNT;

  -- 7. Soft-delete the duplicate
  UPDATE contacts
  SET
    deleted_at = NOW(),
    updated_at = NOW()
  WHERE id = p_merge_id;

  RETURN format('Merged %s -> %s: %s txns, %s subs, %s donors',
    LEFT(p_merge_id::text, 8), LEFT(p_keep_id::text, 8),
    v_txn_count, v_sub_count, v_donor_count);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- EXECUTE 18 MERGES
-- ============================================================================

\echo 'Processing 18 blocking donor merges...'
\echo ''

-- ============================================================================
-- PHONE-MATCHED (HIGH CONFIDENCE) - 10 pairs
-- ============================================================================

\echo '=== Phone-Matched Merges (High Confidence) ==='

-- 1. Christa Ray - Same phone (303-887-0202)
-- KEEP older (christavoice@outlook.com) - equal spending at $0
SELECT merge_contact_pair(
  'd4a2997a-68c4-4eb2-8e39-1552b61066ce'::uuid,  -- keep: christavoice@outlook.com
  'e1e8cab1-d18b-4e4f-9aab-74a3fd465103'::uuid,  -- merge: christavoice@yahoo.com
  'Christa Ray - same phone'
);

-- 2. Christine McGroarty - Same phone (303-888-7118)
-- KEEP id1 with $50 spending
SELECT merge_contact_pair(
  '73ce6293-b15c-4cb5-b769-dc26cb5afc15'::uuid,  -- keep: cmcg216@gmail.com ($50)
  'f22b4021-2ce1-48f7-af12-75daaeb03380'::uuid,  -- merge: c.mcgroarty@att.net
  'Christine McGroarty - same phone'
);

-- 3. Dawn Nocera - Same phone (614-679-1021)
-- KEEP id1 with $30 spending
SELECT merge_contact_pair(
  '0030bc05-be1a-4980-943e-cf4a1f988889'::uuid,  -- keep: dawn@grailleadership.com ($30)
  '0a4f1e93-9dd6-44ec-bb5c-9273b6d2dc05'::uuid,  -- merge: dawnrnocera@gmail.com
  'Dawn Nocera - same phone'
);

-- 4. Elizabeth de Lorimier - KEEP id1 with phone
-- KEEP id1 which has phone number
SELECT merge_contact_pair(
  '74540bf1-e0bc-4f18-b394-65f43825a1b9'::uuid,  -- keep: pinkmanzanita1@gmail.com (has phone)
  '3f9646df-d821-43d5-b880-9478cecf1a1d'::uuid,  -- merge: e_delorimier@protonmail.com
  'Elizabeth de Lorimier - keep one with phone'
);

-- 5. Iain Gillespie - Same phone (267-423-3458)
-- KEEP id1 with $2206 spending
SELECT merge_contact_pair(
  '99e0b8b7-e99b-4dd0-9cb0-f032430dbe57'::uuid,  -- keep: iaingill.law@gmail.com ($2206)
  'fbd60971-0ec5-4193-aefc-06daf0e59e74'::uuid,  -- merge: iain@sangha.one
  'Iain Gillespie - same phone'
);

-- 6. Jeremy Colbert - Same phone (814-322-6558)
-- KEEP id2 with $175 spending
SELECT merge_contact_pair(
  'd6c4e359-ab6f-4f63-aed8-996215e6bbe9'::uuid,  -- keep: taragape@gmail.com ($175)
  'a01c1346-219e-4887-9b11-5f88bea4884b'::uuid,  -- merge: colbert.jeremy@gmail.com
  'Jeremy Colbert - same phone'
);

-- 7. Margo King / Steiner Foundation - Same phone (303-912-8300)
-- KEEP Margo King (personal name) over Steiner Foundation
SELECT merge_contact_pair(
  'bb927f7b-8589-43c1-a3ef-dd71c2c4cea3'::uuid,  -- keep: steiner_king@earthlink.net (Margo King)
  '0da19862-f2d5-4331-8e92-cd9474a6f082'::uuid,  -- merge: steinerking33@gmail.com (Steiner Foundation)
  'Margo King / Steiner Foundation - same phone'
);

-- 8. Melissa Michaels - Same phone (303-875-1178)
-- KEEP newer with $95 spending
SELECT merge_contact_pair(
  '698641ef-8a8b-41c7-ad9f-0a7ae0227ae4'::uuid,  -- keep: melissa@goldenbridge.org ($95)
  '98ab8bc1-da9a-4507-944c-0a798d4e4d3e'::uuid,  -- merge: melissa@bdanced.com
  'Melissa Michaels - same phone'
);

-- 9. Thomas Bufano - Same phone (828-329-4805)
-- KEEP id1 with $37 spending
SELECT merge_contact_pair(
  '8041fd4d-6cda-44aa-89b7-38ca03893cd5'::uuid,  -- keep: tombufano@gmail.com ($37)
  '723411b3-c057-413f-9eac-2ddd41856a34'::uuid,  -- merge: info@tombufanocounseling.com
  'Thomas Bufano - same phone'
);

-- 10. Wendy Nelson - Same phone (303-919-3650)
-- KEEP id1 with $99 spending
SELECT merge_contact_pair(
  '6e4f6995-fb5e-4e3a-8adb-59f8826afaa5'::uuid,  -- keep: wendynelsonlpc@gmail.com ($99)
  '6eeeb2b7-56f5-4172-9185-d023d185bf3e'::uuid,  -- merge: wendalion9@gmail.com
  'Wendy Nelson - same phone'
);

-- ============================================================================
-- NO PHONE MATCH (MEDIUM CONFIDENCE) - 7 pairs
-- Decision: Keep contact with most data/spending, or oldest
-- ============================================================================

\echo ''
\echo '=== No Phone Match (Based on Name + Email Pattern) ==='

-- 11. Annette Welch - Different phones
-- KEEP id1 with $15 spending (older, has transaction)
SELECT merge_contact_pair(
  '742b1433-53c1-4a6a-bc3d-5696ed58de4f'::uuid,  -- keep: mayamaya339@comcast.net ($15)
  'cd1f773a-8c51-428d-af70-652498b13009'::uuid,  -- merge: mayamaya8@comcast.net
  'Annette Welch - keep older with spending'
);

-- 12. Christine Harvey - No phones, same email pattern
-- KEEP id1 (older, same domain pattern)
SELECT merge_contact_pair(
  '5dba095b-3d57-49d5-a2ce-2a581dae13bc'::uuid,  -- keep: charvey@outofthebox-co.com (older)
  '0428933b-1a42-4f42-89d2-aa2151062fe3'::uuid,  -- merge: charvey@outofthebox.com
  'Christine Harvey - keep older, same email pattern'
);

-- 13. Deborah Ogden - Different phones
-- KEEP id1 with $408 spending
SELECT merge_contact_pair(
  'fe08cc7b-7bcd-438f-9901-dbb7cf04f51a'::uuid,  -- keep: drumrgirl@outlook.com ($408)
  'bf178549-8374-4a04-91f7-dbff498bddc4'::uuid,  -- merge: drumrgirl@comcast.net
  'Deborah Ogden - keep one with spending'
);

-- 14. Jamie Wheal - Different phones (personal vs business)
-- KEEP id1 with personal email
SELECT merge_contact_pair(
  '77cc418d-1dd6-49c0-9c43-b49709a5e448'::uuid,  -- keep: jamie.wheal@gmail.com (personal)
  '48efa0d1-62b7-43e1-ba06-4f881640b4df'::uuid,  -- merge: accounting@flowgenomeproject.com
  'Jamie Wheal - keep personal email'
);

-- 15. Marguerite McKenna - No phones
-- KEEP id1 (older)
SELECT merge_contact_pair(
  '44922cd0-9aaf-4321-85fd-156c30fc5dca'::uuid,  -- keep: marguerite.mckenna@hotmail.com (older)
  'd8a21ae7-58a9-44b2-a0f3-7db5d1a91246'::uuid,  -- merge: marguerite.808.mckenna@gmail.com
  'Marguerite McKenna - keep older'
);

-- 16. MJoy Silva - No phones
-- KEEP id1 (older)
SELECT merge_contact_pair(
  'be27f136-19f7-4a27-a2c5-1907e509c9ff'::uuid,  -- keep: hecreativelink@hushmail.com (older)
  'd2b742a7-b8df-4a03-b742-39d02348a26e'::uuid,  -- merge: allissacredceremonies@hushmail.com
  'MJoy Silva - keep older'
);

-- 17. Shiva Coffey - No phones
-- KEEP id1 (older)
SELECT merge_contact_pair(
  'de1c4e37-3af7-4c5a-b15b-368d22d4029c'::uuid,  -- keep: shiva.coffey@icloud.com (older)
  '0aac8111-ab51-4dd9-9532-d2be14b69986'::uuid,  -- merge: shivacoffey@comcast.net
  'Shiva Coffey - keep older'
);

-- ============================================================================
-- GLENDA SHETLER - 3-way merge (special case)
-- ============================================================================

\echo ''
\echo '=== Glenda Shetler (3-way merge) ==='

-- 18. Glenda Shetler - 3 contacts, different phones
-- KEEP id3 with $30 spending, merge other two
-- First: merge id1 into id3
SELECT merge_contact_pair(
  '5832e9e2-c6c1-4fff-a970-d5d1d22b22d9'::uuid,  -- keep: gshetler@sbcglobal.net ($30)
  '3f2e6622-5aa8-4753-8f4b-7ec172c7e1cb'::uuid,  -- merge: gfs@startmail.com ($19)
  'Glenda Shetler - merge 1 of 2'
);

-- Second: merge id2 into id3
SELECT merge_contact_pair(
  '5832e9e2-c6c1-4fff-a970-d5d1d22b22d9'::uuid,  -- keep: gshetler@sbcglobal.net
  'e1c32777-194a-45ad-badd-4c648987b8e2'::uuid,  -- merge: szctkriphs@use.startmail.com
  'Glenda Shetler - merge 2 of 2'
);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'
\echo ''

-- Check that all 18 names now have only 1 contact
SELECT
  LOWER(TRIM(first_name || ' ' || last_name)) as full_name,
  COUNT(*) as count
FROM contacts
WHERE deleted_at IS NULL
  AND LOWER(TRIM(first_name || ' ' || last_name)) IN (
    'annette welch', 'christa ray', 'christine harvey', 'christine mcgroarty',
    'deborah ogden', 'elizabeth de lorimier', 'glenda shetler',
    'iain gillespie', 'jamie wheal', 'jeremy colbert', 'margo king',
    'marguerite mckenna', 'mjoy silva', 'shiva coffey',
    'thomas bufano', 'wendy nelson'
  )
  OR (LOWER(first_name) = 'dawn' AND LOWER(last_name) LIKE 'nocera%')
  OR (LOWER(first_name) = 'melissa' AND LOWER(last_name) LIKE 'michaels%')
GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
HAVING COUNT(*) > 1;

\echo ''
\echo 'If no rows above, all 18 blocking donors have been resolved!'
\echo ''

-- Show backup count
SELECT COUNT(*) as merge_backup_records
FROM contacts_merge_backup
WHERE notes LIKE '%Blocking donor merge Nov 24%';

-- Check remaining total duplicates
SELECT COUNT(*) as remaining_duplicate_sets
FROM (
  SELECT LOWER(TRIM(first_name || ' ' || last_name)) as full_name
  FROM contacts
  WHERE deleted_at IS NULL
  GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
  HAVING COUNT(*) > 1
) dups;

\echo ''
\echo '============================================================================'
\echo 'MERGE COMPLETE - 18 blocking donors resolved'
\echo 'You can now re-run the QuickBooks donor import'
\echo '============================================================================'

COMMIT;
