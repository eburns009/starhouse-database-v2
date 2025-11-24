-- ============================================================================
-- BATCH MERGE: November 24, 2025 - 25 Phone-Matched Duplicates
-- ============================================================================
-- High-confidence merges: Same name + matching phone number (normalized)
-- Rule: Keep contact with more transaction history, merge duplicate's email
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'BATCH MERGE: Processing 25 phone-matched duplicates'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- MERGE FUNCTION
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
    'Phone-matched merge Nov 24: ' || p_reason
  FROM contacts c
  WHERE c.id = p_merge_id;

  -- 2. Add duplicate's email to contact_emails
  INSERT INTO contact_emails (contact_id, email, email_type, is_primary, source)
  VALUES (p_keep_id, v_merge_email, 'personal', false, 'merged_duplicate')
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
-- EXECUTE MERGES (25 pairs)
-- ============================================================================

\echo 'Processing merges...'
\echo ''

-- 1. Harwood Ferguson - KEEP id2 (18697.00 vs 799.00)
SELECT merge_contact_pair(
  '3d7cd345-5551-4a94-bb25-b4a4768fa514'::uuid,  -- keep: harwood.ferguson+paypal@gmail.com
  '13961a53-c715-40da-a6b6-4341a17d5b99'::uuid,  -- merge: harwood.ferguson@gmail.com
  'Harwood Ferguson'
);

-- 2. Sharon Montes - KEEP id1 (3196.00 vs 1308.55)
SELECT merge_contact_pair(
  '1445d037-0ba6-406f-b2b0-7ff6be416294'::uuid,  -- keep: drsharon@livingwellwholehealth.com
  '468d6e89-c674-4928-9841-fbb1c88c521a'::uuid,  -- merge: drsharonmontes@gmail.com
  'Sharon Montes'
);

-- 3. Ellen Friedlander - KEEP id1 (2524.00 vs 968.00)
SELECT merge_contact_pair(
  '6c70bfc5-502c-4d85-a034-36777efb0224'::uuid,  -- keep: elliebelle17@mac.com
  '8790070d-98ed-4f1f-b76c-e4eac0991779'::uuid,  -- merge: efriedlander17@yahoo.com
  'Ellen Friedlander'
);

-- 4. Taylor Bratches - KEEP id2 (2395.00 vs 561.00)
SELECT merge_contact_pair(
  'f439becf-fad6-4a26-8f3b-c6ff69e12a6f'::uuid,  -- keep: tk.bratches@gmail.com
  'd5891ea5-b6dc-4061-a815-ca9d79dc8ab0'::uuid,  -- merge: taylor.bratches@gmail.com
  'Taylor Bratches'
);

-- 5. Iain Gillespie - KEEP id1 (2206.00 vs 966.00)
SELECT merge_contact_pair(
  '99e0b8b7-e99b-4dd0-9cb0-f032430dbe57'::uuid,  -- keep: iaingill.law@gmail.com
  'fbd60971-0ec5-4193-aefc-06daf0e59e74'::uuid,  -- merge: iain@sangha.one
  'Iain Gillespie'
);

-- 6. Juliet Haines - KEEP id1 (1000.00 vs 0)
SELECT merge_contact_pair(
  '77ee715e-3535-425f-a073-33dcb2e69f46'::uuid,  -- keep: juliet@depthsoffeminine.earth
  '9548930b-e9e8-403d-8ec9-ac6904f94df8'::uuid,  -- merge: juliet@juliethaines.com
  'Juliet Haines'
);

-- 7. Amrita Rose - KEEP id2 (753.00 vs 20.00)
SELECT merge_contact_pair(
  'cd0800e0-7e23-4c60-aafa-3ed819236d44'::uuid,  -- keep: hello@anunstoppablelife.com
  '63422e81-e47a-4c04-ab78-c4cf50268c24'::uuid,  -- merge: hello@amrita-rose.com
  'Amrita Rose'
);

-- 8. Kate Heartsong - KEEP id1 (711.00 vs 0)
SELECT merge_contact_pair(
  '62147f79-0f61-4493-aaa7-bda71ab12696'::uuid,  -- keep: katesanks22@protonmail.com
  '965c6077-0559-4c89-a554-6f8b81d59ca9'::uuid,  -- merge: joyfulradiance@gmail.com
  'Kate Heartsong'
);

-- 9. Courtney Cosgriff - KEEP id1 (590.00 vs 35.00)
SELECT merge_contact_pair(
  '7bce00e6-b305-453d-957e-1b1a1b3975ef'::uuid,  -- keep: courtney@honeybeeherbals.co
  'f39a33bf-52bc-44a3-b18e-be404eae6eaf'::uuid,  -- merge: courtney@honeybeeherbs.co
  'Courtney Cosgriff'
);

-- 10. Jack Swift - KEEP id1 (370.00 vs 0)
SELECT merge_contact_pair(
  '421b1060-b2c0-4640-ac23-b19f51d670a8'::uuid,  -- keep: jack@jackcswift.com
  'f3be30b1-08ae-48c6-9a3b-e6db393a5051'::uuid,  -- merge: jackcswift@gmail.com
  'Jack Swift'
);

-- 11. Eleanor Rome - KEEP id1 (275.00 vs 55.00)
SELECT merge_contact_pair(
  '07441593-55a5-4cf7-8536-b0ad911a03ac'::uuid,  -- keep: erome91@gmail.com
  '8cb38031-467b-4e9c-8370-a86a47b04c01'::uuid,  -- merge: ellie@mindfulbellie.com
  'Eleanor Rome'
);

-- 12. Miranda Clendening - KEEP id1 (204.00 vs 60.00)
SELECT merge_contact_pair(
  '9222d476-a325-4667-89c2-1a4509825892'::uuid,  -- keep: miranda@boulderriverside.com
  'b5c4fa4a-fd0b-4c1b-9982-6c50e5d8759f'::uuid,  -- merge: miranda8280@gmail.com
  'Miranda Clendening'
);

-- 13. Stephanie Volk - KEEP id1 (200.00 vs 60.00)
SELECT merge_contact_pair(
  '3c1fba86-d991-4db7-9f04-2f8a992d0140'::uuid,  -- keep: elphanzo@hotmail.com
  'b2f913d9-1deb-4432-950e-d9622489ea29'::uuid,  -- merge: inspirebt@icloud.com
  'Stephanie Volk'
);

-- 14. Tam Barthel - KEEP id1 (186.00 vs 0)
SELECT merge_contact_pair(
  '04dff20c-7e87-489a-9023-37cb0976a63b'::uuid,  -- keep: tam.a.barthel@gmail.com
  'fadea80e-59f5-4bce-9699-6f65455aeb3b'::uuid,  -- merge: tambarthel@aol.com
  'Tam Barthel'
);

-- 15. Jeremy Colbert - KEEP id2 (175.00 vs 121.00)
SELECT merge_contact_pair(
  'd6c4e359-ab6f-4f63-aed8-996215e6bbe9'::uuid,  -- keep: taragape@gmail.com
  'a01c1346-219e-4887-9b11-5f88bea4884b'::uuid,  -- merge: colbert.jeremy@gmail.com
  'Jeremy Colbert'
);

-- 16. Brie Doyle - KEEP id2 (112.00 vs 0)
SELECT merge_contact_pair(
  'c7bae645-a579-459c-ab0d-357055c75383'::uuid,  -- keep: brie@briedoyle.com
  'b1e93bad-e284-4b68-ba65-3594c416c89b'::uuid,  -- merge: doylebrie@gmail.com
  'Brie Doyle'
);

-- 17. Wendy Nelson - KEEP id1 (99.00 vs 0)
SELECT merge_contact_pair(
  '6e4f6995-fb5e-4e3a-8adb-59f8826afaa5'::uuid,  -- keep: wendynelsonlpc@gmail.com
  '6eeeb2b7-56f5-4172-9185-d023d185bf3e'::uuid,  -- merge: wendalion9@gmail.com
  'Wendy Nelson'
);

-- 18. Michelle Kaye - KEEP id2 (66.00 vs 33.00)
SELECT merge_contact_pair(
  'fb4f6bad-8733-4908-bd29-2186f7dc9168'::uuid,  -- keep: michelle.kaye.lpc@gmail.com
  'f6e80e40-e72d-4869-a5b8-3c03bea6444f'::uuid,  -- merge: kaye.michelle@gmail.com
  'Michelle Kaye'
);

-- 19. Elizabeth Morris - KEEP id2 (58.00 vs 0)
SELECT merge_contact_pair(
  'fb595433-efd1-4e0f-a72c-32a03b035841'::uuid,  -- keep: morr.liz@gmail.com
  '1b5535df-d040-4641-a3d2-e6f1638d0cc1'::uuid,  -- merge: radicallyembracingyou@gmail.com
  'Elizabeth Morris'
);

-- 20. Christine McGroarty - KEEP id1 (50.00 vs 0)
SELECT merge_contact_pair(
  '73ce6293-b15c-4cb5-b769-dc26cb5afc15'::uuid,  -- keep: cmcg216@gmail.com
  'f22b4021-2ce1-48f7-af12-75daaeb03380'::uuid,  -- merge: c.mcgroarty@att.net
  'Christine McGroarty'
);

-- 21. Thomas Bufano - KEEP id2 (37.00 vs 0)
SELECT merge_contact_pair(
  '8041fd4d-6cda-44aa-89b7-38ca03893cd5'::uuid,  -- keep: tombufano@gmail.com
  '723411b3-c057-413f-9eac-2ddd41856a34'::uuid,  -- merge: info@tombufanocounseling.com
  'Thomas Bufano'
);

-- 22. Anja Shine - KEEP id1 (20.00 vs 0)
SELECT merge_contact_pair(
  '33f2612e-d815-4787-951d-4e6b56b7fb11'::uuid,  -- keep: connectnow22@icloud.com
  '8f35e26b-b76c-4e1d-95dd-c1ab4c17e575'::uuid,  -- merge: anjashine11@yahoo.com
  'Anja Shine'
);

-- 23. Jeremy Roske - KEEP id1 (equal at 0, use older)
SELECT merge_contact_pair(
  '117023ef-e479-45d4-83c2-f659a301969a'::uuid,  -- keep: jroske1111@gmail.com
  '81af2b0b-b034-4bb4-9d7b-b27065811e60'::uuid,  -- merge: jeremy@jeremyroske.com
  'Jeremy Roske'
);

-- 24. Christa Ray - KEEP id1 (equal at 0, use older)
SELECT merge_contact_pair(
  'd4a2997a-68c4-4eb2-8e39-1552b61066ce'::uuid,  -- keep: christavoice@outlook.com
  'e1e8cab1-d18b-4e4f-9aab-74a3fd465103'::uuid,  -- merge: christavoice@yahoo.com
  'Christa Ray'
);

-- 25. Anita Rodriguez-McCaffrey - KEEP id2 (0.00 vs 0, use one with txn)
SELECT merge_contact_pair(
  'a8f33d90-a306-4cda-a635-571a869dc893'::uuid,  -- keep: anitarodriguez@suncoastwaldorf.org (has 1 txn)
  '14f285a4-0bb2-440e-9e12-85abef0b6172'::uuid,  -- merge: rodanita41@gmail.com
  'Anita Rodriguez-McCaffrey'
);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'
\echo ''

-- Check remaining duplicates
SELECT COUNT(*) as remaining_duplicate_sets
FROM (
  SELECT LOWER(TRIM(first_name || ' ' || last_name)) as full_name
  FROM contacts
  WHERE deleted_at IS NULL
  GROUP BY LOWER(TRIM(first_name || ' ' || last_name))
  HAVING COUNT(*) > 1
) dups;

-- Show backup count
SELECT COUNT(*) as merge_backup_records
FROM contacts_merge_backup
WHERE notes LIKE '%Nov 24%';

\echo ''
\echo '============================================================================'
\echo 'MERGE COMPLETE - Review above results'
\echo '============================================================================'

COMMIT;
