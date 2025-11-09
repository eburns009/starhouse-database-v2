-- Phase 2: Email Username Duplicate Merges
-- FAANG Standards: Merge contacts with same email username (different domains)
-- Date: 2025-11-09
-- Expected: 4 merge groups (8 contacts → 4 contacts)

BEGIN;

-- Validation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_merge_backup') THEN
        RAISE EXCEPTION 'contacts_merge_backup table does not exist';
    END IF;
END $$;

-- ============================================================================
-- EMAIL USERNAME DUPLICATES - HIGH CONFIDENCE CASES
-- ============================================================================

-- 1. Heidi Robbins (heidirose4@me.com / heidirose4@aol.com)
-- Primary: heidirose4@me.com (15 txns)
-- Duplicate: heidirose4@aol.com (9 txns)
-- Verification: Raw_source shows "Heidi Rose Robbins"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'heidirose4@me.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'heidirose4@aol.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Phase 2: Email username duplicate - Heidi Robbins (heidirose4)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'heidirose4@aol.com',
            first_name = 'Heidi',
            last_name = 'Robbins',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Heidi Robbins (heidirose4@me.com + heidirose4@aol.com)';
    END IF;
END $$;

-- 2. Gitama Fortier (harmonyzafu@gmail.com / harmonyzafu@gmai.com [TYPO])
-- Primary: harmonyzafu@gmail.com (14 txns)
-- Duplicate: harmonyzafu@gmai.com (3 txns) - TYPO: gmai.com should be gmail.com
-- Verification: Raw_source shows "Gitama Gini Fortier"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'harmonyzafu@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'harmonyzafu@gmai.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Phase 2: Email username duplicate - Gitama Fortier (harmonyzafu) - duplicate had typo @gmai.com'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'harmonyzafu@gmai.com (typo - should be gmail.com)',
            first_name = 'Gitama',
            last_name = 'Fortier',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Gitama Fortier (harmonyzafu@gmail.com + harmonyzafu@gmai.com [typo])';
    END IF;
END $$;

-- 3. Lila Tressemer / Laura Cannon (lilaplays@gmail.com / lilaplays@icloud.com)
-- Primary: lilaplays@gmail.com (7 txns) - Lila Tressemer
-- Duplicate: lilaplays@icloud.com (3 txns) - Lila (no last name)
-- Verification: Same phone (1 720-320-5988 / 7203205988), Raw_source shows "Lila Tresemer" and "Laura Cannon"
-- Note: Person uses both names "Lila Tressemer" and "Laura Cannon" in transactions
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'lilaplays@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'lilaplays@icloud.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Phase 2: Email username duplicate - Lila Tressemer (lilaplays) - Also uses name Laura Cannon'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'lilaplays@icloud.com',
            first_name = 'Lila',
            last_name = 'Tressemer',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Lila Tressemer (lilaplays@gmail.com + lilaplays@icloud.com)';
    END IF;
END $$;

-- 4. Sophia Bobier (sophia@bobier.net / sophia@sophiafoundation.org)
-- Primary: sophia@bobier.net (6 txns) - Sophia Bobier (personal)
-- Duplicate: sophia@sophiafoundation.org (1 txn) - Sophia Foundation
-- Verification: Raw_source confirms both
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'sophia@bobier.net';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'sophia@sophiafoundation.org';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Phase 2: Email username duplicate - Sophia Bobier (personal) + Sophia Foundation'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'sophia@sophiafoundation.org',
            first_name = 'Sophia',
            last_name = 'Bobier',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Sophia Bobier (sophia@bobier.net + sophia@sophiafoundation.org)';
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
    -- Check for orphaned records
    SELECT COUNT(*) INTO v_orphaned_transactions
    FROM transactions t
    WHERE NOT EXISTS (SELECT 1 FROM contacts c WHERE c.id = t.contact_id);

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
    RAISE NOTICE 'Email Username Duplicates Merge Complete';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Final contact count: %', v_contact_count;
    RAISE NOTICE 'Merges completed: 4 (8 contacts → 4 contacts)';
    RAISE NOTICE 'Orphaned transactions: %', v_orphaned_transactions;
    RAISE NOTICE 'Orphaned subscriptions: %', v_orphaned_subscriptions;
    RAISE NOTICE '==============================================';
END $$;

COMMIT;
