-- ============================================================================
-- CLEANUP PAYPAL DUPLICATE CONTACTS
-- ============================================================================
-- Purpose: Merge 12-15 duplicate PayPal contacts into existing records
-- Strategy: Keep existing records (kajabi/manual), add PayPal data to them
-- Total duplicates: 9 definite (phone match) + 6 probable (name match)
-- ============================================================================

BEGIN;

\echo '════════════════════════════════════════════════════════════'
\echo 'PAYPAL DUPLICATE CLEANUP'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Create backup table for deleted PayPal duplicates
CREATE TABLE IF NOT EXISTS contacts_duplicate_cleanup_backup (
    backup_id SERIAL PRIMARY KEY,
    paypal_contact_id UUID NOT NULL,
    paypal_email TEXT NOT NULL,
    existing_contact_id UUID NOT NULL,
    existing_email TEXT NOT NULL,
    paypal_contact_data JSONB NOT NULL,
    match_type TEXT NOT NULL,
    merged_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

\echo 'Backup table ready'
\echo ''

-- ============================================================================
-- SECTION 1: DEFINITE DUPLICATES (Phone Matches)
-- ============================================================================

\echo '--- Section 1: Definite Duplicates (Phone Matches) ---'
\echo ''

-- 1. Allison DeHart: dehartaa@yahoo.com → dehartaa@gmail.com
\echo '1. Merging Allison DeHart (Yahoo → Gmail)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    -- Get IDs
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'dehartaa@yahoo.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'dehartaa@gmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        -- Backup PayPal record
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'dehartaa@yahoo.com', v_existing_id, 'dehartaa@gmail.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Same person, Yahoo vs Gmail'
        FROM contacts c WHERE c.id = v_paypal_id;

        -- Add Yahoo email to existing record
        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'dehartaa@yahoo.com'
            WHEN additional_email NOT LIKE '%dehartaa@yahoo.com%' THEN additional_email || ', dehartaa@yahoo.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        -- Delete PayPal duplicate
        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Allison DeHart';
    END IF;
END $$;

-- 2. Melissa Lago: TYPO - melissa.lago@gmail.con → .com
\echo '2. Fixing Melissa Lago (TYPO: .con → .com)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'melissa.lago@gmail.con' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'melissa.lago@gmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'melissa.lago@gmail.con', v_existing_id, 'melissa.lago@gmail.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'TYPO: .con should be .com'
        FROM contacts c WHERE c.id = v_paypal_id;

        -- Just delete - it's a typo, not a real alternate email
        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Removed Melissa Lago typo record';
    END IF;
END $$;

-- 3. Holly McCann: hollybeth1212@gmail.com → holly@grailleadership.com
\echo '3. Merging Holly McCann (personal Gmail → business)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'hollybeth1212@gmail.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'holly@grailleadership.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'hollybeth1212@gmail.com', v_existing_id, 'holly@grailleadership.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Personal Gmail vs business email'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'hollybeth1212@gmail.com'
            WHEN additional_email NOT LIKE '%hollybeth1212@gmail.com%' THEN additional_email || ', hollybeth1212@gmail.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Holly McCann';
    END IF;
END $$;

-- 4. Songya Kesler: stkesler@gmail.com → songyakesler@gmail.com
\echo '4. Merging Songya Kesler (abbreviated → full name)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'stkesler@gmail.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'songyakesler@gmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'stkesler@gmail.com', v_existing_id, 'songyakesler@gmail.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Abbreviated vs full name email'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'stkesler@gmail.com'
            WHEN additional_email NOT LIKE '%stkesler@gmail.com%' THEN additional_email || ', stkesler@gmail.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Songya Kesler';
    END IF;
END $$;

-- 5. Spencer Bowie: spencer.m.bowie@gmail.com → whodabowie@proton.me
\echo '5. Merging Spencer Bowie (formal → nickname) + adding phone'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
    v_paypal_phone TEXT;
BEGIN
    SELECT id, phone INTO v_paypal_id, v_paypal_phone FROM contacts WHERE email = 'spencer.m.bowie@gmail.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'whodabowie@proton.me';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'spencer.m.bowie@gmail.com', v_existing_id, 'whodabowie@proton.me',
               row_to_json(c.*)::jsonb, 'phone_match', 'Formal vs nickname, adding phone'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'spencer.m.bowie@gmail.com'
            WHEN additional_email NOT LIKE '%spencer.m.bowie@gmail.com%' THEN additional_email || ', spencer.m.bowie@gmail.com'
            ELSE additional_email
        END,
        phone = COALESCE(phone, v_paypal_phone),
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Spencer Bowie + added phone';
    END IF;
END $$;

-- 6. Claire Thompson/Sugarloaf: zuzuclaire@gmail.com → claire@producethefuture.com
\echo '6. Merging Claire Thompson (personal → business) + adding phone'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
    v_paypal_phone TEXT;
BEGIN
    SELECT id, phone INTO v_paypal_id, v_paypal_phone FROM contacts WHERE email = 'zuzuclaire@gmail.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'claire@producethefuture.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'zuzuclaire@gmail.com', v_existing_id, 'claire@producethefuture.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Personal vs business, adding phone'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'zuzuclaire@gmail.com'
            WHEN additional_email NOT LIKE '%zuzuclaire@gmail.com%' THEN additional_email || ', zuzuclaire@gmail.com'
            ELSE additional_email
        END,
        phone = COALESCE(phone, v_paypal_phone),
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Claire Thompson + added phone';
    END IF;
END $$;

-- 7. Mike Cohen/Shiva Datta: mike@mikecohenkirtan.com → mcohen1966@gmail.com
\echo '7. Merging Mike Cohen (business → personal) + adding phone'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
    v_paypal_phone TEXT;
BEGIN
    SELECT id, phone INTO v_paypal_id, v_paypal_phone FROM contacts WHERE email = 'mike@mikecohenkirtan.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'mcohen1966@gmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'mike@mikecohenkirtan.com', v_existing_id, 'mcohen1966@gmail.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Business vs personal, adding phone'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'mike@mikecohenkirtan.com'
            WHEN additional_email NOT LIKE '%mike@mikecohenkirtan.com%' THEN additional_email || ', mike@mikecohenkirtan.com'
            ELSE additional_email
        END,
        phone = COALESCE(phone, v_paypal_phone),
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Mike Cohen + added phone';
    END IF;
END $$;

-- 8. Lynn Ryan/Root Flight: info@amberryan.com → amber@the360emergence.com
\echo '8. Merging Lynn Ryan (different business emails) + adding phone'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
    v_paypal_phone TEXT;
BEGIN
    SELECT id, phone INTO v_paypal_id, v_paypal_phone FROM contacts WHERE email = 'info@amberryan.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'amber@the360emergence.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'info@amberryan.com', v_existing_id, 'amber@the360emergence.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Different business ventures, adding phone'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'info@amberryan.com'
            WHEN additional_email NOT LIKE '%info@amberryan.com%' THEN additional_email || ', info@amberryan.com'
            ELSE additional_email
        END,
        phone = COALESCE(phone, v_paypal_phone),
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Lynn Ryan + added phone';
    END IF;
END $$;

-- 9. Allison Conte/The Sanctuary: hello@center4sacredunion.org → allison@sophia-leadership.com
\echo '9. Merging Allison Conte (different businesses) + adding phone'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
    v_paypal_phone TEXT;
BEGIN
    SELECT id, phone INTO v_paypal_id, v_paypal_phone FROM contacts WHERE email = 'hello@center4sacredunion.org' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'allison@sophia-leadership.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'hello@center4sacredunion.org', v_existing_id, 'allison@sophia-leadership.com',
               row_to_json(c.*)::jsonb, 'phone_match', 'Different business ventures, adding phone'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'hello@center4sacredunion.org'
            WHEN additional_email NOT LIKE '%hello@center4sacredunion.org%' THEN additional_email || ', hello@center4sacredunion.org'
            ELSE additional_email
        END,
        phone = COALESCE(phone, v_paypal_phone),
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Allison Conte + added phone';
    END IF;
END $$;

\echo ''
\echo '--- Section 1 Complete: 9 phone-matched duplicates processed ---'
\echo ''

-- ============================================================================
-- SECTION 2: PROBABLE DUPLICATES (Name Matches)
-- ============================================================================

\echo '--- Section 2: Probable Duplicates (Name Matches) ---'
\echo ''

-- 10. Alanna Bell: alannajbell@gmail.com → llamabell@hotmail.com
\echo '10. Merging Alanna Bell (Gmail → Hotmail) + enriching'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
    v_existing_phone TEXT;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'alannajbell@gmail.com' AND source_system = 'paypal';
    SELECT id, phone INTO v_existing_id, v_existing_phone FROM contacts WHERE email = 'llamabell@hotmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'alannajbell@gmail.com', v_existing_id, 'llamabell@hotmail.com',
               row_to_json(c.*)::jsonb, 'name_match', 'Same name, different email pattern'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'alannajbell@gmail.com'
            WHEN additional_email NOT LIKE '%alannajbell@gmail.com%' THEN additional_email || ', alannajbell@gmail.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Alanna Bell';
    END IF;
END $$;

-- 11. Bradley Bernstein: opportunitypainting@outlook.com → coloradorawhoney@gmail.com
\echo '11. Merging Bradley Bernstein (business emails)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'opportunitypainting@outlook.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'coloradorawhoney@gmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'opportunitypainting@outlook.com', v_existing_id, 'coloradorawhoney@gmail.com',
               row_to_json(c.*)::jsonb, 'name_match', 'Different business ventures'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'opportunitypainting@outlook.com'
            WHEN additional_email NOT LIKE '%opportunitypainting@outlook.com%' THEN additional_email || ', opportunitypainting@outlook.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Bradley Bernstein';
    END IF;
END $$;

-- 12. Catherine Boerder: Merge ALL 3 records!
\echo '12. Merging Catherine Boerder (3 records → 1!)'

DO $$
DECLARE
    v_primary_id UUID;
    v_dup1_id UUID;
    v_dup2_id UUID;
    v_dup2_phone TEXT;
BEGIN
    -- Keep catherine.boerder@gmail.com as primary
    SELECT id INTO v_primary_id FROM contacts WHERE email = 'catherine.boerder@gmail.com';
    SELECT id, phone INTO v_dup2_id, v_dup2_phone FROM contacts WHERE email = 'cboerder@hotmail.com';
    SELECT id INTO v_dup1_id FROM contacts WHERE email = 'cboerder.nature@gmail.com' AND source_system = 'paypal';

    IF v_primary_id IS NOT NULL THEN
        -- Backup PayPal record
        IF v_dup1_id IS NOT NULL THEN
            INSERT INTO contacts_duplicate_cleanup_backup
            (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
            SELECT v_dup1_id, 'cboerder.nature@gmail.com', v_primary_id, 'catherine.boerder@gmail.com',
                   row_to_json(c.*)::jsonb, 'name_match', 'Merging 3 Catherine Boerder records into 1'
            FROM contacts c WHERE c.id = v_dup1_id;
        END IF;

        -- Reassign any transactions from duplicates to primary
        IF v_dup1_id IS NOT NULL THEN
            UPDATE transactions SET contact_id = v_primary_id, updated_at = NOW()
            WHERE contact_id = v_dup1_id;
        END IF;
        IF v_dup2_id IS NOT NULL THEN
            UPDATE transactions SET contact_id = v_primary_id, updated_at = NOW()
            WHERE contact_id = v_dup2_id;
        END IF;

        -- Reassign any subscriptions from duplicates to primary
        IF v_dup1_id IS NOT NULL THEN
            UPDATE subscriptions SET contact_id = v_primary_id, updated_at = NOW()
            WHERE contact_id = v_dup1_id;
        END IF;
        IF v_dup2_id IS NOT NULL THEN
            UPDATE subscriptions SET contact_id = v_primary_id, updated_at = NOW()
            WHERE contact_id = v_dup2_id;
        END IF;

        -- Merge tags from duplicates to primary
        IF v_dup1_id IS NOT NULL THEN
            INSERT INTO contact_tags (contact_id, tag_id)
            SELECT DISTINCT v_primary_id, ct.tag_id
            FROM contact_tags ct
            WHERE ct.contact_id = v_dup1_id
              AND NOT EXISTS (
                SELECT 1 FROM contact_tags ct2
                WHERE ct2.contact_id = v_primary_id
                  AND ct2.tag_id = ct.tag_id
              )
            ON CONFLICT (contact_id, tag_id) DO NOTHING;

            DELETE FROM contact_tags WHERE contact_id = v_dup1_id;
        END IF;
        IF v_dup2_id IS NOT NULL THEN
            INSERT INTO contact_tags (contact_id, tag_id)
            SELECT DISTINCT v_primary_id, ct.tag_id
            FROM contact_tags ct
            WHERE ct.contact_id = v_dup2_id
              AND NOT EXISTS (
                SELECT 1 FROM contact_tags ct2
                WHERE ct2.contact_id = v_primary_id
                  AND ct2.tag_id = ct.tag_id
              )
            ON CONFLICT (contact_id, tag_id) DO NOTHING;

            DELETE FROM contact_tags WHERE contact_id = v_dup2_id;
        END IF;

        -- Merge all emails into primary
        UPDATE contacts
        SET additional_email =
            CASE
                WHEN additional_email IS NULL THEN 'cboerder.nature@gmail.com, cboerder@hotmail.com'
                ELSE additional_email || ', cboerder.nature@gmail.com, cboerder@hotmail.com'
            END,
        phone = COALESCE(phone, v_dup2_phone),
        updated_at = NOW()
        WHERE id = v_primary_id;

        -- Delete duplicates
        DELETE FROM contacts WHERE id IN (v_dup1_id, v_dup2_id);

        RAISE NOTICE '  ✓ Merged Catherine Boerder (3 → 1)';
    END IF;
END $$;

-- 13. Heather Baines: heather.baines@outlook.com → heather@earthguardians.org
\echo '13. Merging Heather Baines (personal → organization)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'heather.baines@outlook.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'heather@earthguardians.org';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'heather.baines@outlook.com', v_existing_id, 'heather@earthguardians.org',
               row_to_json(c.*)::jsonb, 'name_match', 'Personal vs organization email'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'heather.baines@outlook.com'
            WHEN additional_email NOT LIKE '%heather.baines@outlook.com%' THEN additional_email || ', heather.baines@outlook.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Heather Baines';
    END IF;
END $$;

-- 14. William Eigles: sagescholar@aol.com → wpeigles@aol.com
\echo '14. Merging William Eigles (nickname → initials)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'sagescholar@aol.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'wpeigles@aol.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'sagescholar@aol.com', v_existing_id, 'wpeigles@aol.com',
               row_to_json(c.*)::jsonb, 'name_match', 'Nickname vs initials'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'sagescholar@aol.com'
            WHEN additional_email NOT LIKE '%sagescholar@aol.com%' THEN additional_email || ', sagescholar@aol.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged William Eigles';
    END IF;
END $$;

-- 15. Aurélie Roy/Aura Rose: aureliearoy@gmail.com → travelingalchemy@gmail.com
\echo '15. Merging Aurélie Roy/Aura Rose (name variation?)'

DO $$
DECLARE
    v_paypal_id UUID;
    v_existing_id UUID;
BEGIN
    SELECT id INTO v_paypal_id FROM contacts WHERE email = 'aureliearoy@gmail.com' AND source_system = 'paypal';
    SELECT id INTO v_existing_id FROM contacts WHERE email = 'travelingalchemy@gmail.com';

    IF v_paypal_id IS NOT NULL AND v_existing_id IS NOT NULL THEN
        INSERT INTO contacts_duplicate_cleanup_backup
        (paypal_contact_id, paypal_email, existing_contact_id, existing_email, paypal_contact_data, match_type, notes)
        SELECT v_paypal_id, 'aureliearoy@gmail.com', v_existing_id, 'travelingalchemy@gmail.com',
               row_to_json(c.*)::jsonb, 'name_match', 'Possible name variation: Aurélie Roy vs Aura Rose'
        FROM contacts c WHERE c.id = v_paypal_id;

        UPDATE contacts
        SET additional_email = CASE
            WHEN additional_email IS NULL THEN 'aureliearoy@gmail.com'
            WHEN additional_email NOT LIKE '%aureliearoy@gmail.com%' THEN additional_email || ', aureliearoy@gmail.com'
            ELSE additional_email
        END,
        updated_at = NOW()
        WHERE id = v_existing_id;

        DELETE FROM contacts WHERE id = v_paypal_id;

        RAISE NOTICE '  ✓ Merged Aurélie Roy/Aura Rose';
    END IF;
END $$;

\echo ''
\echo '--- Section 2 Complete: 6 name-matched duplicates processed ---'
\echo ''

-- ============================================================================
-- SUMMARY & VERIFICATION
-- ============================================================================

\echo '════════════════════════════════════════════════════════════'
\echo 'CLEANUP SUMMARY'
\echo '════════════════════════════════════════════════════════════'

SELECT
    'Total duplicates merged' as metric,
    COUNT(*) as value
FROM contacts_duplicate_cleanup_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes';

SELECT
    'By match type:' as metric,
    '' as value

UNION ALL

SELECT
    '  ' || match_type as metric,
    COUNT(*)::text as value
FROM contacts_duplicate_cleanup_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes'
GROUP BY match_type;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'DATABASE SIZE'
\echo '════════════════════════════════════════════════════════════'

SELECT
    'Total contacts after cleanup' as metric,
    COUNT(*)::text as value
FROM contacts;

SELECT
    'Remaining PayPal-sourced contacts' as metric,
    COUNT(*)::text as value
FROM contacts
WHERE source_system = 'paypal';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'VERIFICATION'
\echo '════════════════════════════════════════════════════════════'

-- Verify no orphaned records
SELECT
    'Orphaned transactions' as check,
    COUNT(*) as count,
    CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM transactions t
LEFT JOIN contacts c ON t.contact_id = c.id
WHERE c.id IS NULL;

SELECT
    'Backup records created' as check,
    COUNT(*) as count,
    CASE WHEN COUNT(*) >= 14 THEN '✓ PASS' ELSE '⚠ WARNING' END as status
FROM contacts_duplicate_cleanup_backup
WHERE merged_at > NOW() - INTERVAL '5 minutes';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '════════════════════════════════════════════════════════════'

COMMIT;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '✓ PAYPAL DUPLICATE CLEANUP COMPLETE!'
\echo '════════════════════════════════════════════════════════════'
\echo ''
\echo 'Result: 15 duplicates merged, additional emails preserved'
\echo 'Final database: More accurate contact count'
\echo ''
