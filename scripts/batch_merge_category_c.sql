-- Phase 1b: Category C Special Cases Phone Duplicate Merges
-- FAANG Standards: Transaction data verified, business accounts handled
-- Date: 2025-11-09
-- Expected: 5 merges (10 contacts → 5 contacts)
-- Note: Ed vs Debbie Burns (All Chalice) kept separate - different people

BEGIN;

-- Validation: Ensure contacts_merge_backup table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_merge_backup') THEN
        RAISE EXCEPTION 'contacts_merge_backup table does not exist';
    END IF;
END $$;

-- ============================================================================
-- CATEGORY C: SPECIAL CASES (Business Accounts, Multiple Identities)
-- ============================================================================

-- 1. Steve Dedrick (3035883538)
-- Primary: stevededrick@gmail.com (2 txns) - Steve Dedrick
-- Duplicate: steve@cocreator.us (1 txn) - Steve
-- Verification: Transaction shows "Steven Dedrick"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'stevededrick@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'steve@cocreator.us';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category C: Steve Dedrick (3035883538) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'steve@cocreator.us',
            first_name = 'Steve',
            last_name = 'Dedrick',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Steve Dedrick';
    END IF;
END $$;

-- 2. Shaun's Cello Studio (5093930343)
-- Primary: payments@shaunpaul.com (2 txns, 1 sub) - Business payments
-- Duplicate: info@shaunpaul.com (0 txns, 1 sub) - Shaun Diaz
-- Verification: Both business emails, same entity
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'payments@shaunpaul.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'info@shaunpaul.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category C: Shaun''s Cello Studio (5093930343) - Business account'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'info@shaunpaul.com',
            first_name = 'Shaun',
            last_name = 'Diaz',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Shaun''s Cello Studio';
    END IF;
END $$;

-- 3. Katherine Hassler / Karta Allred (7202972267)
-- CRITICAL: Katherine Kripke's multiple identities!
-- Primary: dralafly@gmail.com (18 txns, 1 sub) - Katherine Hassler
-- Duplicate: kartaelise@gmail.com (2 txns, 1 sub) - Karta Allred
-- Verification: Transaction shows "Katherine Hassler" for BOTH emails
-- Note: This is part of Katherine Kripke's 4-identity system (see handoff doc)
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'dralafly@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'kartaelise@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category C: Katherine Hassler / Karta Allred (7202972267) - Katherine Kripke identities - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'kartaelise@gmail.com',
            first_name = 'Katherine',
            last_name = 'Hassler',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Katherine Hassler / Karta Allred (Katherine Kripke)';
    END IF;
END $$;

-- 4. Amanda Klenner (7203233385)
-- Primary: artemisiaandrose@gmail.com (8 txns, 2 subs) - Amanda Klenner
-- Duplicate: mkamandak@gmail.com (5 txns, 1 sub) - Natural Living Mamma
-- Verification: Transaction shows "Amanda Rose Klenner"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'artemisiaandrose@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'mkamandak@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category C: Amanda Klenner / Natural Living Mamma (7203233385) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'mkamandak@gmail.com',
            first_name = 'Amanda',
            last_name = 'Klenner',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Amanda Klenner';
    END IF;
END $$;

-- 5. Bjorn Brie / Temple of the Golden Light (7602015642)
-- Primary: bjornleonards@gmail.com (24 txns, 1 sub) - Temple Of The Golden Light
-- Duplicate: brieandbjorn@gmail.com (0 txns, 1 sub) - Bjorn Brie
-- Verification: Transaction shows "Temple of the Golden Light"
DO $$
DECLARE
    v_primary_id UUID;
    v_duplicate_id UUID;
BEGIN
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'bjornleonards@gmail.com';
    SELECT id INTO v_duplicate_id FROM contacts WHERE email = 'brieandbjorn@gmail.com';

    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Category C: Bjorn Brie / Temple of the Golden Light (7602015642) - Business account'
        FROM contacts c WHERE c.id = v_duplicate_id;

        UPDATE contacts SET
            additional_email = 'brieandbjorn@gmail.com',
            first_name = 'Bjorn',
            last_name = 'Brie',
            updated_at = NOW()
        WHERE id = v_primary_id;

        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Bjorn Brie / Temple of the Golden Light';
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
    RAISE NOTICE 'Category C Batch Merge Complete';
    RAISE NOTICE 'Final contact count: %', v_contact_count;
    RAISE NOTICE 'Orphaned transactions: %', v_orphaned_transactions;
    RAISE NOTICE 'Orphaned subscriptions: %', v_orphaned_subscriptions;
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Note: Ed vs Debbie Burns (All Chalice) kept separate - different people sharing org phone';
    RAISE NOTICE 'Note: Katherine Kripke still has 2 more identities to merge in Phase 2 (name-based)';
END $$;

COMMIT;
