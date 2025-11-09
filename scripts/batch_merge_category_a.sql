-- Phase 1b: Category A High-Confidence Phone Duplicate Merges
-- FAANG Standards: Atomic transactions, comprehensive backups, validation
-- Date: 2025-11-09
-- Expected: 17 merges (34 contacts → 17 contacts)

BEGIN;

-- Validation: Ensure contacts_merge_backup table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_merge_backup') THEN
        RAISE EXCEPTION 'contacts_merge_backup table does not exist';
    END IF;
END $$;

-- ============================================================================
-- CATEGORY A: HIGH-CONFIDENCE MERGES (Same/Similar Names)
-- ============================================================================

-- 1. Sharona Fein (1 203-702-3697)
-- Primary: sharonaf@gmx.com (3 txns)
-- Duplicate: pollin8@gmx.com (1 txn)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'sharonaf@gmx.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'pollin8@gmx.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Sharona Fein / Sharona Hana Fein (1 203-702-3697)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'pollin8@gmx.com',
            first_name = 'Sharona',
            last_name = 'Fein',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Sharona Fein';
    END IF;
END $$;

-- 2. Mary Rhoades (1 214-208-4827)
-- Primary: rhoadesfamily87@hotmail.com (3 txns)
-- Duplicate: maryrhoades34@hotmail.com (2 txns)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'rhoadesfamily87@hotmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'maryrhoades34@hotmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Mary Rhoades (1 214-208-4827)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'maryrhoades34@hotmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Mary Rhoades';
    END IF;
END $$;

-- 3. Lora Olowczuk (1 301-221-0546)
-- Primary: lola8732@gmail.com (2 txns) - Olowczuk spelling
-- Duplicate: lora@priorityretreats.com (1 txn) - Polowczuk spelling
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'lola8732@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'lora@priorityretreats.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Lora Olowczuk / Lora Polowczuk (1 301-221-0546)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'lora@priorityretreats.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Lora Olowczuk';
    END IF;
END $$;

-- 4. Shannon Kelly (1 303-472-0399)
-- Primary: skelly@geoforest.org (3 txns) - Shan Kelly
-- Duplicate: biz@geoforest.org (2 txns) - Shannon Kelly
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'skelly@geoforest.org';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'biz@geoforest.org';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Shan Kelly / Shannon Kelly (1 303-472-0399)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'biz@geoforest.org',
            first_name = 'Shannon',
            last_name = 'Kelly',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Shannon Kelly';
    END IF;
END $$;

-- 5. Kelly Sikora (1 317-503-4781)
-- Primary: empowertherapistco@gmail.com (2 txns)
-- Duplicate: kellyenright5@gmail.com (2 txns)
-- Choose empowertherapistco (business email, likely primary)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'empowertherapistco@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'kellyenright5@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Kelly Sikora (1 317-503-4781)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'kellyenright5@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Kelly Sikora';
    END IF;
END $$;

-- 6. Frances Harjeet (1 434-466-6936)
-- Primary: francesharjeet@gmail.com (1 txn)
-- Duplicate: francespgrace@gmail.com (1 txn) - Frances Grace
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'francesharjeet@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'francespgrace@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Frances Harjeet / Frances Grace (1 434-466-6936)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'francespgrace@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Frances Harjeet';
    END IF;
END $$;

-- 7. Kala Anderson (1 512-774-8383)
-- Primary: blessed_light@ymail.com (6 txns) - Kala Anderson
-- Duplicate: kalarose1991@gmail.com (3 txns) - Kala Rose
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'blessed_light@ymail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'kalarose1991@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Kala Anderson / Kala Rose (1 512-774-8383)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'kalarose1991@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Kala Anderson';
    END IF;
END $$;

-- 8. Laura Gabelsberg (1 520-222-2377)
-- Primary: laura@gabelsberg.com (1 txn)
-- Duplicate: lauralee@eagleeyeastrology.com (1 txn) - Laura L Gabelsberg
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'laura@gabelsberg.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'lauralee@eagleeyeastrology.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Laura Gabelsberg / Laura L Gabelsberg (1 520-222-2377)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'lauralee@eagleeyeastrology.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Laura Gabelsberg';
    END IF;
END $$;

-- 9. Kolea Kelly (1 720-534-7507)
-- Primary: koleavlw369@gmail.com (5 txns) - Kolea Kelly
-- Duplicate: k7aloha@gmail.com (2 txns) - Kolea Dinneen
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'koleavlw369@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'k7aloha@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Kolea Kelly / Kolea Dinneen (1 720-534-7507)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'k7aloha@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Kolea Kelly';
    END IF;
END $$;

-- 10. Shannon O'Kane (2628443332)
-- Primary: shannon.okane@gmail.com (18 txns)
-- Duplicate: shannon@thestarhouse.org (0 txns) - Staff email
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'shannon.okane@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'shannon@thestarhouse.org';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Shannon OKane / Shannon O''Kane (2628443332)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'shannon@thestarhouse.org',
            first_name = 'Shannon',
            last_name = 'O''Kane',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Shannon O''Kane';
    END IF;
END $$;

-- 11. Kristina Papin (3144944318)
-- Primary: kmpapin@gmail.com (23 txns, 1 sub)
-- Duplicate: bodymindfreq@gmail.com (0 txns, 1 sub)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'kmpapin@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'bodymindfreq@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Kristina Papin (3144944318)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'bodymindfreq@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Kristina Papin';
    END IF;
END $$;

-- 12. Drew Davis (6467012433)
-- Primary: drewgdavis@gmail.com (6 txns, 1 sub)
-- Duplicate: brotherhoodoftheroots@gmail.com (1 txn, 0 subs)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'drewgdavis@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'brotherhoodoftheroots@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Drew Davis (6467012433)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'brotherhoodoftheroots@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Drew Davis';
    END IF;
END $$;

-- 13. Dalila Orozco (7193200034)
-- Primary: methiasgold@gmail.com (10 txns, 1 sub) - Dalila Orozco
-- Duplicate: dalilageorgette@gmail.com (1 txn, 1 sub) - Dalila Georgette
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'methiasgold@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'dalilageorgette@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Dalila Orozco / Dalila Georgette (7193200034)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'dalilageorgette@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Dalila Orozco';
    END IF;
END $$;

-- 14. Andrea Pettit (7202535260)
-- Primary: andreap@rightfromtheheart.com (3 txns, 1 sub) - Andrea Pettit
-- Duplicate: apettit14@gmail.com (1 txn, 1 sub) - Andrea Undefined
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'andreap@rightfromtheheart.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'apettit14@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Andrea Pettit / Andrea Undefined (7202535260)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'apettit14@gmail.com',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Andrea Pettit';
    END IF;
END $$;

-- 15. Garry Caudill (7206354514)
-- Primary: aquilanegra48@yahoo.com (11 txns, 4 subs) - Garry Caudill (personal)
-- Duplicate: garry.caudill48@gmail.com (13 txns, 1 sub) - Caudill & Associates LLC
-- Choose personal email as primary (more subscriptions indicate ongoing engagement)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'aquilanegra48@yahoo.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'garry.caudill48@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Garry Caudill / Caudill & Associates LLC (7206354514)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'garry.caudill48@gmail.com',
            first_name = 'Garry',
            last_name = 'Caudill',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Garry Caudill';
    END IF;
END $$;

-- 16. Kimberley Wukitsch (7816904550)
-- Primary: wukitka@gmail.com (6 txns, 1 sub) - Kimberley
-- Duplicate: kimberalisse@gmail.com (0 txns, 1 sub) - Kimber
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'wukitka@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'kimberalisse@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Kimberley Wukitsch / Kimber Wukitsch (7816904550)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'kimberalisse@gmail.com',
            first_name = 'Kimberley',
            last_name = 'Wukitsch',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Kimberley Wukitsch';
    END IF;
END $$;

-- 17. Cristina Sajovich (9703069126)
-- Primary: cristina@sajovich.com (20 txns, 1 sub) - Cristina
-- Duplicate: ina@ishometeam.com (1 txn, 1 sub) - Ina (typo)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'cristina@sajovich.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'ina@ishometeam.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb, 'Category A: Cristina Sajovich / Ina Sajovich (9703069126)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'ina@ishometeam.com',
            first_name = 'Cristina',
            last_name = 'Sajovich',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Cristina Sajovich';
    END IF;
END $$;

-- ============================================================================
-- FINAL VALIDATION
-- ============================================================================

DO $$
DECLARE
    v_orphaned_transactions INT;
    v_orphaned_subscriptions INT;
    v_contact_count INT;
BEGIN
    -- Check for orphaned transactions
    SELECT COUNT(*) INTO v_orphaned_transactions
    FROM transactions t
    WHERE NOT EXISTS (SELECT 1 FROM contacts c WHERE c.id = t.contact_id);

    -- Check for orphaned subscriptions
    SELECT COUNT(*) INTO v_orphaned_subscriptions
    FROM subscriptions s
    WHERE NOT EXISTS (SELECT 1 FROM contacts c WHERE c.id = s.contact_id);

    -- Get final contact count
    SELECT COUNT(*) INTO v_contact_count FROM contacts;

    IF v_orphaned_transactions > 0 THEN
        RAISE EXCEPTION 'Validation failed: % orphaned transactions found', v_orphaned_transactions;
    END IF;

    IF v_orphaned_subscriptions > 0 THEN
        RAISE EXCEPTION 'Validation failed: % orphaned subscriptions found', v_orphaned_subscriptions;
    END IF;

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Category A Batch Merge Complete';
    RAISE NOTICE 'Final contact count: %', v_contact_count;
    RAISE NOTICE 'Orphaned transactions: %', v_orphaned_transactions;
    RAISE NOTICE 'Orphaned subscriptions: %', v_orphaned_subscriptions;
    RAISE NOTICE '==============================================';
END $$;

COMMIT;
