-- Phase 2: Katherine Kripke Complete Identity Merge
-- FAANG Standards: Merging 3 remaining identities into 1 contact
-- Date: 2025-11-09
-- Expected: 3 contacts → 1 contact (2 merges)

BEGIN;

-- Validation: Ensure contacts_merge_backup table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_merge_backup') THEN
        RAISE EXCEPTION 'contacts_merge_backup table does not exist';
    END IF;
END $$;

-- ============================================================================
-- KATHERINE KRIPKE - 4 IDENTITY COMPLETE MERGE
-- ============================================================================
-- Identity 1 + 2 (Phase 1): dralafly@gmail.com (Katherine Hassler + Karta Allred merged)
-- Identity 3: kate@katekripke.com (Kate Kripke) - PRIMARY (most transactions)
-- Identity 4: katekripke@gmail.com (Katherine Kripke) - No transactions
--
-- Transaction verification:
-- - kate@katekripke.com raw_source: "Katherine Kripke"
-- - dralafly@gmail.com raw_source: "Katherine Hassler"
--
-- Strategy: Merge all into kate@katekripke.com (most transactions)
-- ============================================================================

-- Merge 1: dralafly@gmail.com (Katherine Hassler) → kate@katekripke.com
DO $$
DECLARE
    v_primary_id UUID := '8928c333-b108-49e9-bf88-3ded50096616'::UUID;  -- kate@katekripke.com
    v_duplicate_id UUID := '97b383fc-9aa5-477e-8102-3db0c4f6b47a'::UUID; -- dralafly@gmail.com
    v_existing_additional_email TEXT;
BEGIN
    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        -- Backup
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Phase 2: Katherine Kripke identity merge 1/2 - dralafly@gmail.com (Katherine Hassler) - Transaction verified'
        FROM contacts c WHERE c.id = v_duplicate_id;

        -- Get existing additional_email from duplicate (it has kartaelise@gmail.com from Phase 1)
        SELECT additional_email INTO v_existing_additional_email
        FROM contacts WHERE id = v_duplicate_id;

        -- Update primary with both emails
        UPDATE contacts SET
            additional_email = CASE
                WHEN v_existing_additional_email IS NOT NULL THEN
                    'dralafly@gmail.com, ' || v_existing_additional_email
                ELSE
                    'dralafly@gmail.com'
            END,
            phone = '7202972267',  -- Add phone from duplicate
            updated_at = NOW()
        WHERE id = v_primary_id;

        -- Reassign data
        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        -- Merge tags
        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Katherine Hassler (dralafly@gmail.com) → Kate Kripke (kate@katekripke.com)';
    END IF;
END $$;

-- Merge 2: katekripke@gmail.com (Katherine Kripke, no txns) → kate@katekripke.com
DO $$
DECLARE
    v_primary_id UUID := '8928c333-b108-49e9-bf88-3ded50096616'::UUID;  -- kate@katekripke.com
    v_duplicate_id UUID := 'fda0441a-a0ae-4000-bb1c-0540d0bf6846'::UUID; -- katekripke@gmail.com
    v_existing_additional_email TEXT;
BEGIN
    IF v_primary_id IS NOT NULL AND v_duplicate_id IS NOT NULL THEN
        -- Backup
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_primary_id, v_duplicate_id, row_to_json(c.*)::jsonb,
               'Phase 2: Katherine Kripke identity merge 2/2 - katekripke@gmail.com (Katherine Kripke) - Name match'
        FROM contacts c WHERE c.id = v_duplicate_id;

        -- Get existing additional_email from primary
        SELECT additional_email INTO v_existing_additional_email
        FROM contacts WHERE id = v_primary_id;

        -- Update primary with all emails
        UPDATE contacts SET
            additional_email = CASE
                WHEN v_existing_additional_email IS NOT NULL THEN
                    v_existing_additional_email || ', katekripke@gmail.com'
                ELSE
                    'katekripke@gmail.com'
            END,
            first_name = 'Katherine',  -- Use full name
            last_name = 'Kripke',
            updated_at = NOW()
        WHERE id = v_primary_id;

        -- Reassign data (should be none, but for safety)
        UPDATE transactions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;
        UPDATE subscriptions SET contact_id = v_primary_id WHERE contact_id = v_duplicate_id;

        -- Merge tags
        INSERT INTO contact_tags (contact_id, tag_id)
        SELECT DISTINCT v_primary_id, ct.tag_id FROM contact_tags ct WHERE ct.contact_id = v_duplicate_id
        ON CONFLICT (contact_id, tag_id) DO NOTHING;

        DELETE FROM contact_tags WHERE contact_id = v_duplicate_id;
        DELETE FROM contacts WHERE id = v_duplicate_id;

        RAISE NOTICE 'Merged: Katherine Kripke (katekripke@gmail.com) → Katherine Kripke (kate@katekripke.com)';
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
    v_kripke_txns INT;
    v_kripke_subs INT;
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

    -- Get Katherine Kripke final counts
    SELECT
        (SELECT COUNT(*) FROM transactions WHERE contact_id = '8928c333-b108-49e9-bf88-3ded50096616'::UUID),
        (SELECT COUNT(*) FROM subscriptions WHERE contact_id = '8928c333-b108-49e9-bf88-3ded50096616'::UUID)
    INTO v_kripke_txns, v_kripke_subs;

    IF v_orphaned_transactions > 0 THEN
        RAISE EXCEPTION 'Validation failed: % orphaned transactions found', v_orphaned_transactions;
    END IF;

    IF v_orphaned_subscriptions > 0 THEN
        RAISE EXCEPTION 'Validation failed: % orphaned subscriptions found', v_orphaned_subscriptions;
    END IF;

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Katherine Kripke Complete Identity Merge Success';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Final contact count: %', v_contact_count;
    RAISE NOTICE 'Katherine Kripke final stats:';
    RAISE NOTICE '  - Email: kate@katekripke.com';
    RAISE NOTICE '  - Transactions: %', v_kripke_txns;
    RAISE NOTICE '  - Subscriptions: %', v_kripke_subs;
    RAISE NOTICE '  - Total identities merged: 4 (Phase 1: 2, Phase 2: 2)';
    RAISE NOTICE '  - All emails: kate@katekripke.com + 3 additional';
    RAISE NOTICE 'Orphaned transactions: %', v_orphaned_transactions;
    RAISE NOTICE 'Orphaned subscriptions: %', v_orphaned_subscriptions;
    RAISE NOTICE '==============================================';
END $$;

COMMIT;
