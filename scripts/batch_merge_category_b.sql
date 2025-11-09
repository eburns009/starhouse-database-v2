-- Phase 1b: Category B Medium-Confidence Phone Duplicate Merges
-- FAANG Standards: Transaction data verified via raw_source
-- Date: 2025-11-09
-- Expected: 6 merges (12 contacts → 6 contacts)
-- Note: 2 cases excluded (Bob & Ru Wing are a couple, Marianne & Emily are different people)

BEGIN;

-- Validation: Ensure contacts_merge_backup table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_merge_backup') THEN
        RAISE EXCEPTION 'contacts_merge_backup table does not exist';
    END IF;
END $$;

-- ============================================================================
-- CATEGORY B: MEDIUM-CONFIDENCE MERGES (Different Names, Transaction Verified)
-- ============================================================================

-- 1. Hazel Archer-Ginsberg (1 773-344-1150)
-- Primary: hazel@reverseritual.com (6 txns) - Hazel Archer-Ginsberg
-- Duplicate: hag@rschicago.org (1 txn) - Hazel, Ultra-Violet Archer & Chuck Ginsberg
-- Verification: Transactions show "Hazel Archer-Ginsberg" | "Hazel Lucchesi-Ginsberg"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'hazel@reverseritual.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'hag@rschicago.org';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category B: Hazel Archer-Ginsberg (1 773-344-1150) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'hag@rschicago.org',
            first_name = 'Hazel',
            last_name = 'Archer-Ginsberg',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Hazel Archer-Ginsberg';
    END IF;
END $$;

-- 2. Lisa Hunter (303-842-4321)
-- Primary: lisa@freeyourmenopause.com (1 txn, 1 sub) - Lisa Undefined
-- Duplicate: lisa@realbeautymenopause.com (0 txns, 1 sub) - Lisa Hunter
-- Verification: Transaction shows "Lisa Hunter"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'lisa@freeyourmenopause.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'lisa@realbeautymenopause.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category B: Lisa Hunter (303-842-4321) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'lisa@realbeautymenopause.com',
            first_name = 'Lisa',
            last_name = 'Hunter',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Lisa Hunter';
    END IF;
END $$;

-- 3. Ali Katz (3103514173)
-- Primary: ali@newlawbusinessmodel.com (13 txns, 1 sub) - Business
-- Duplicate: lexcoach@gmail.com (0 txns, 1 sub) - Ali Katz
-- Verification: Transaction shows "Family Wealth Planning Institute, LLC"
-- Note: Keeping business email as primary (more transactions)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'ali@newlawbusinessmodel.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'lexcoach@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category B: Ali Katz / Llc Family Wealth Planning Institute (3103514173) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'lexcoach@gmail.com',
            first_name = 'Ali',
            last_name = 'Katz',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Ali Katz';
    END IF;
END $$;

-- 4. Glenda Thuener (4012073921)
-- Primary: glethu@yahoo.com (15 txns, 1 sub) - Glenda Thuener
-- Duplicate: glendaluck@gmail.com (0 txns, 1 sub) - Glenda Luck
-- Verification: Transaction shows "Glenda Thuener" (married name)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'glethu@yahoo.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'glendaluck@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category B: Glenda Thuener / Glenda Luck (4012073921) - Transaction verified (married name)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'glendaluck@gmail.com',
            first_name = 'Glenda',
            last_name = 'Thuener',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Glenda Thuener';
    END IF;
END $$;

-- 5. Regina Stribling (7205453041)
-- Primary: regina@transpersonalguidance.com (1 txn) - Transpersonal Guidance (business)
-- Duplicate: karunacuna@gmail.com (0 txns) - Regina Stribling (personal)
-- Verification: Transaction shows "Transpersonal Guidance"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'regina@transpersonalguidance.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'karunacuna@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category B: Regina Stribling / Transpersonal Guidance (7205453041) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'karunacuna@gmail.com',
            first_name = 'Regina',
            last_name = 'Stribling',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Regina Stribling';
    END IF;
END $$;

-- 6. Ixeeya Lin Beacher (7208831540)
-- Primary: womenstentix@gmail.com (7 txns) - Ixeeya Lin
-- Duplicate: billingixeeya@gmail.com (1 txn) - Stephanie Beacher
-- Verification: Transaction shows "Ixeeya lin beacher" | "Ixeeya Lin Beacher"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'womenstentix@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'billingixeeya@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category B: Ixeeya Lin Beacher (7208831540) - Transaction verified (full name)'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'billingixeeya@gmail.com',
            first_name = 'Ixeeya',
            last_name = 'Lin Beacher',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Ixeeya Lin Beacher';
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
    RAISE NOTICE 'Category B Batch Merge Complete';
    RAISE NOTICE 'Final contact count: %', v_contact_count;
    RAISE NOTICE 'Orphaned transactions: %', v_orphaned_transactions;
    RAISE NOTICE 'Orphaned subscriptions: %', v_orphaned_subscriptions;
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Note: Bob & Ru Wing kept separate (couple)';
    RAISE NOTICE 'Note: Marianne Shiple & Emily Bamford kept separate (different people)';
END $$;

COMMIT;
