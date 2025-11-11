-- Migration 004: Merge Phone Duplicate Contacts
-- Created: 2025-11-09
-- Purpose: Merge 9 contacts with duplicate phone numbers identified in data quality audit
--
-- IMPORTANT: Review each merge carefully before running!
-- These merges preserve all data by moving transactions, subscriptions, and
-- enriching the primary contact with data from the secondary.

BEGIN;

-- Create backup table
CREATE TABLE IF NOT EXISTS backup_phone_duplicate_merge_20251109 AS
SELECT * FROM contacts WHERE 1=0;

-- ============================================================================
-- CRITICAL PRIORITY: Laura Brown (Both have active subscriptions!)
-- ============================================================================

DO $$
DECLARE
    primary_id uuid := '931895ab-f451-4e14-9201-3cc5de36e472'; -- laura@thestarhouse.org
    secondary_id uuid := '7ed08b26-3856-4bc2-a9a7-0e4b32edcedc'; -- divinereadingsbylaura@gmail.com
    primary_rec record;
    secondary_rec record;
BEGIN
    -- Backup both records
    INSERT INTO backup_phone_duplicate_merge_20251109
    SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    -- Get both records
    SELECT * INTO primary_rec FROM contacts WHERE id = primary_id;
    SELECT * INTO secondary_rec FROM contacts WHERE id = secondary_id;

    RAISE NOTICE '=== MERGING: Laura Brown ===';
    RAISE NOTICE 'Primary:   % (%) - Spent: $%, Active: %',
        primary_rec.first_name || ' ' || COALESCE(primary_rec.last_name, ''),
        primary_rec.email,
        primary_rec.total_spent,
        primary_rec.has_active_subscription;
    RAISE NOTICE 'Secondary: % (%) - Spent: $%, Active: %',
        secondary_rec.first_name || ' ' || COALESCE(secondary_rec.last_name, ''),
        secondary_rec.email,
        secondary_rec.total_spent,
        secondary_rec.has_active_subscription;

    -- Move all transactions from secondary to primary
    UPDATE transactions
    SET contact_id = primary_id
    WHERE contact_id = secondary_id;

    RAISE NOTICE 'Moved % transactions', (SELECT COUNT(*) FROM transactions WHERE contact_id = primary_id);

    -- Move all subscriptions from secondary to primary
    UPDATE subscriptions
    SET contact_id = primary_id
    WHERE contact_id = secondary_id;

    RAISE NOTICE 'Moved % subscriptions (CRITICAL: verify both subs active)',
        (SELECT COUNT(*) FROM subscriptions WHERE contact_id = primary_id);

    -- Move contact_tags
    INSERT INTO contact_tags (contact_id, tag_id, created_at)
    SELECT primary_id, tag_id, created_at
    FROM contact_tags
    WHERE contact_id = secondary_id
    ON CONFLICT (contact_id, tag_id) DO NOTHING;

    -- Move contact_products
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source)
    SELECT primary_id, product_id, purchased_at, source
    FROM contact_products
    WHERE contact_id = secondary_id
    ON CONFLICT (contact_id, product_id) DO NOTHING;

    -- Enrich primary with secondary data (use first_name from secondary if primary is blank)
    UPDATE contacts
    SET
        first_name = COALESCE(NULLIF(first_name, ''), secondary_rec.first_name),
        last_name = COALESCE(NULLIF(last_name, ''), secondary_rec.last_name),
        additional_email = CASE
            WHEN additional_email IS NULL THEN secondary_rec.email
            WHEN additional_email NOT LIKE '%' || secondary_rec.email || '%'
            THEN additional_email || '; ' || secondary_rec.email
            ELSE additional_email
        END,
        phone = COALESCE(phone, secondary_rec.phone),
        address_line_1 = COALESCE(address_line_1, secondary_rec.address_line_1),
        city = COALESCE(city, secondary_rec.city),
        state = COALESCE(state, secondary_rec.state),
        postal_code = COALESCE(postal_code, secondary_rec.postal_code)
    WHERE id = primary_id;

    -- Delete secondary contact
    DELETE FROM contacts WHERE id = secondary_id;

    RAISE NOTICE '✅ Merge complete for Laura Brown';
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- HIGH PRIORITY #1: Virginia Anderson ($1,672 customer, active subscription)
-- ============================================================================

DO $$
DECLARE
    primary_id uuid := '770d3340-4426-4a12-83d4-42ec8a60b9c0'; -- vlanderson@ecentral.com (has $1672 and active sub)
    secondary_id uuid := '2807e667-64f5-4e3d-a667-77b51aba09e2'; -- tenaciousv.43f@gmail.com
    primary_rec record;
    secondary_rec record;
BEGIN
    -- Backup both records
    INSERT INTO backup_phone_duplicate_merge_20251109
    SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    SELECT * INTO primary_rec FROM contacts WHERE id = primary_id;
    SELECT * INTO secondary_rec FROM contacts WHERE id = secondary_id;

    RAISE NOTICE '=== MERGING: Virginia Anderson ===';
    RAISE NOTICE 'Primary:   % (%) - Spent: $%, Active: %',
        primary_rec.first_name || ' ' || COALESCE(primary_rec.last_name, ''),
        primary_rec.email,
        primary_rec.total_spent,
        primary_rec.has_active_subscription;
    RAISE NOTICE 'Secondary: % (%) - Spent: $%, Active: %',
        secondary_rec.first_name || ' ' || COALESCE(secondary_rec.last_name, ''),
        secondary_rec.email,
        secondary_rec.total_spent,
        secondary_rec.has_active_subscription;

    -- Move transactions
    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;

    -- Move subscriptions
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;

    -- Move tags
    INSERT INTO contact_tags (contact_id, tag_id, created_at)
    SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id
    ON CONFLICT (contact_id, tag_id) DO NOTHING;

    -- Move products
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source)
    SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id
    ON CONFLICT (contact_id, product_id) DO NOTHING;

    -- Enrich primary
    UPDATE contacts
    SET
        additional_email = CASE
            WHEN additional_email IS NULL THEN secondary_rec.email
            ELSE additional_email || '; ' || secondary_rec.email
        END,
        additional_name = CASE
            WHEN additional_name IS NULL THEN secondary_rec.first_name || ' ' || secondary_rec.last_name
            ELSE additional_name || '; ' || secondary_rec.first_name || ' ' || secondary_rec.last_name
        END
    WHERE id = primary_id;

    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete for Virginia Anderson';
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- HIGH PRIORITY #2: Rita Fox (active subscription)
-- ============================================================================

DO $$
DECLARE
    primary_id uuid := '14687585-758c-4b0d-9834-d79e15cf67a8'; -- rita@ritariverafox.com
    secondary_id uuid := '56bcd62c-736c-48cc-938d-59819aeb41b9'; -- ritariverafox@gmail.com (has $66 and active)
    primary_rec record;
    secondary_rec record;
BEGIN
    INSERT INTO backup_phone_duplicate_merge_20251109
    SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    SELECT * INTO primary_rec FROM contacts WHERE id = primary_id;
    SELECT * INTO secondary_rec FROM contacts WHERE id = secondary_id;

    RAISE NOTICE '=== MERGING: Rita Fox ===';
    RAISE NOTICE 'Primary:   % - Spent: $%', primary_rec.email, primary_rec.total_spent;
    RAISE NOTICE 'Secondary: % - Spent: $%', secondary_rec.email, secondary_rec.total_spent;

    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;

    INSERT INTO contact_tags (contact_id, tag_id, created_at)
    SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id
    ON CONFLICT (contact_id, tag_id) DO NOTHING;

    INSERT INTO contact_products (contact_id, product_id, purchased_at, source)
    SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id
    ON CONFLICT (contact_id, product_id) DO NOTHING;

    UPDATE contacts
    SET
        additional_email = CASE
            WHEN additional_email IS NULL THEN secondary_rec.email
            ELSE additional_email || '; ' || secondary_rec.email
        END
    WHERE id = primary_id;

    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete for Rita Fox';
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- MEDIUM PRIORITY: Remaining 5 duplicates
-- ============================================================================

-- Annie Heywood ($242 customer)
DO $$
DECLARE
    primary_id uuid := '82ae34ff-75d2-4b0d-955d-b687ec065e3b'; -- sunshineanniem@hotmail.com (has $242)
    secondary_id uuid := '22e7b350-ef51-4b60-b0ce-eb05ad43798e'; -- annemariheywood@yahoo.com
BEGIN
    INSERT INTO backup_phone_duplicate_merge_20251109 SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    RAISE NOTICE '=== MERGING: Annie Heywood ===';
    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;
    INSERT INTO contact_tags (contact_id, tag_id, created_at) SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source) SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;

    UPDATE contacts SET
        additional_email = (SELECT email FROM contacts WHERE id = secondary_id),
        first_name = COALESCE(first_name, (SELECT first_name FROM contacts WHERE id = secondary_id))
    WHERE id = primary_id;

    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete';
END $$;

-- All Chalice ($77 customer)
DO $$
DECLARE
    primary_id uuid := '12021f64-925f-4c41-a51a-34cedb51e9cd'; -- ascpr@thestarhouse.org (has $77)
    secondary_id uuid := 'd2619732-3f12-4959-8c68-dc8a9a13897e'; -- asc@thestarhouse.org
BEGIN
    INSERT INTO backup_phone_duplicate_merge_20251109 SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    RAISE NOTICE '=== MERGING: All Chalice ===';
    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;
    INSERT INTO contact_tags (contact_id, tag_id, created_at) SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source) SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;

    UPDATE contacts SET additional_email = (SELECT email FROM contacts WHERE id = secondary_id) WHERE id = primary_id;
    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete';
END $$;

-- Kate Heartsong / Joyful Radiance ($75 customer)
DO $$
DECLARE
    primary_id uuid := '62147f79-0f61-4493-aaa7-bda71ab12696'; -- katesanks22@protonmail.com (has $75)
    secondary_id uuid := '8568d803-58d5-475f-95b9-1e7bc66c8e53'; -- joyfulradiance@gmail.com
BEGIN
    INSERT INTO backup_phone_duplicate_merge_20251109 SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    RAISE NOTICE '=== MERGING: Kate Heartsong ===';
    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;
    INSERT INTO contact_tags (contact_id, tag_id, created_at) SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source) SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;

    UPDATE contacts SET
        additional_email = (SELECT email FROM contacts WHERE id = secondary_id),
        additional_name = (SELECT first_name || ' ' || last_name FROM contacts WHERE id = secondary_id)
    WHERE id = primary_id;
    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete';
END $$;

-- Anastacia Nutt / Tending The Sacred ($260 customer)
DO $$
DECLARE
    primary_id uuid := 'f00bb0b9-ced3-4774-95ad-36d572c13da0'; -- anastacianutt@gmail.com (has $260)
    secondary_id uuid := '8740854d-f1f2-4290-8350-157f0b94065b'; -- tendingthesacred@proton.me
BEGIN
    INSERT INTO backup_phone_duplicate_merge_20251109 SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    RAISE NOTICE '=== MERGING: Anastacia Nutt ===';
    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;
    INSERT INTO contact_tags (contact_id, tag_id, created_at) SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source) SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;

    UPDATE contacts SET
        additional_email = (SELECT email FROM contacts WHERE id = secondary_id),
        additional_name = (SELECT first_name FROM contacts WHERE id = secondary_id) -- Business name
    WHERE id = primary_id;
    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete';
END $$;

-- ============================================================================
-- LOW PRIORITY: Bob Wing / Ru Wing (no activity)
-- ============================================================================

DO $$
DECLARE
    primary_id uuid := '88183e45-c434-4ee1-a38f-81bd2e94c80b'; -- rcwing@me.com (Bob Wing)
    secondary_id uuid := 'b8db8701-47b1-4c5a-a399-040407d98cd7'; -- ruwing@me.com (Ru Wing)
BEGIN
    INSERT INTO backup_phone_duplicate_merge_20251109 SELECT * FROM contacts WHERE id IN (primary_id, secondary_id);

    RAISE NOTICE '=== MERGING: Bob Wing / Ru Wing ===';
    UPDATE transactions SET contact_id = primary_id WHERE contact_id = secondary_id;
    UPDATE subscriptions SET contact_id = primary_id WHERE contact_id = secondary_id;
    INSERT INTO contact_tags (contact_id, tag_id, created_at) SELECT primary_id, tag_id, created_at FROM contact_tags WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;
    INSERT INTO contact_products (contact_id, product_id, purchased_at, source) SELECT primary_id, product_id, purchased_at, source FROM contact_products WHERE contact_id = secondary_id ON CONFLICT DO NOTHING;

    UPDATE contacts SET
        additional_email = (SELECT email FROM contacts WHERE id = secondary_id),
        additional_name = (SELECT first_name || ' ' || last_name FROM contacts WHERE id = secondary_id)
    WHERE id = primary_id;
    DELETE FROM contacts WHERE id = secondary_id;
    RAISE NOTICE '✅ Merge complete';
END $$;

-- ============================================================================
-- MANUAL REVIEW REQUIRED: Emily Bamford / Marianne Shiple
-- ============================================================================

RAISE NOTICE '⚠️  SKIPPED: Emily Bamford / Marianne Shiple - Requires manual review';
RAISE NOTICE '   Same phone (786-877-9344) but very different names';
RAISE NOTICE '   Could be: roommates, name change, or data error';
RAISE NOTICE '   IDs: 171275b8-f5fc-47a7-b728-fcdd39a324a8, d2566fc0-8953-4ee8-b768-94ed8cbe5ba4';

-- ============================================================================
-- Recalculate denormalized fields for all affected contacts
-- ============================================================================

DO $$
DECLARE
    affected_ids uuid[] := ARRAY[
        '931895ab-f451-4e14-9201-3cc5de36e472'::uuid, -- Laura Brown
        '770d3340-4426-4a12-83d4-42ec8a60b9c0'::uuid, -- Virginia Anderson
        '14687585-758c-4b0d-9834-d79e15cf67a8'::uuid, -- Rita Fox
        '82ae34ff-75d2-4b0d-955d-b687ec065e3b'::uuid, -- Annie Heywood
        '12021f64-925f-4c41-a51a-34cedb51e9cd'::uuid, -- All Chalice
        '62147f79-0f61-4493-aaa7-bda71ab12696'::uuid, -- Kate Heartsong
        'f00bb0b9-ced3-4774-95ad-36d572c13da0'::uuid, -- Anastacia Nutt
        '88183e45-c434-4ee1-a38f-81bd2e94c80b'::uuid  -- Bob Wing
    ];
    contact_id uuid;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Recalculating denormalized fields ===';

    FOREACH contact_id IN ARRAY affected_ids
    LOOP
        -- Recalculate total_spent
        UPDATE contacts c
        SET
            total_spent = (
                SELECT COALESCE(SUM(amount), 0)
                FROM transactions t
                WHERE t.contact_id = c.id
                  AND t.status = 'completed'
            ),
            transaction_count = (
                SELECT COUNT(*)
                FROM transactions t
                WHERE t.contact_id = c.id
            ),
            last_transaction_date = (
                SELECT MAX(transaction_date)
                FROM transactions t
                WHERE t.contact_id = c.id
            ),
            has_active_subscription = (
                SELECT EXISTS(
                    SELECT 1
                    FROM subscriptions s
                    WHERE s.contact_id = c.id
                      AND s.status = 'active'
                )
            )
        WHERE c.id = contact_id;
    END LOOP;

    RAISE NOTICE '✅ Recalculated denormalized fields for % contacts', array_length(affected_ids, 1);
END $$;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    backup_count int;
    remaining_dupes int;
BEGIN
    SELECT COUNT(*) INTO backup_count FROM backup_phone_duplicate_merge_20251109;

    SELECT COUNT(*) INTO remaining_dupes FROM (
        SELECT phone
        FROM contacts
        WHERE phone IS NOT NULL
        GROUP BY phone
        HAVING COUNT(*) > 1
    ) t;

    RAISE NOTICE '';
    RAISE NOTICE '=== MERGE SUMMARY ===';
    RAISE NOTICE 'Backed up: % contact records', backup_count;
    RAISE NOTICE 'Merged: 8 duplicate pairs (16 records → 8 records)';
    RAISE NOTICE 'Remaining phone duplicates: %', remaining_dupes;
    RAISE NOTICE '';

    IF remaining_dupes = 1 THEN
        RAISE NOTICE '✅ SUCCESS: Only Emily Bamford / Marianne Shiple remaining (manual review required)';
    ELSIF remaining_dupes = 0 THEN
        RAISE NOTICE '✅ PERFECT: All duplicates resolved!';
    ELSE
        RAISE WARNING '⚠️  WARNING: % duplicate phone numbers still exist', remaining_dupes;
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- Post-Merge Validation Queries
-- ============================================================================

-- Verify Laura Brown has 2 active subscriptions
SELECT
    'Laura Brown Verification' as check_name,
    email,
    total_spent,
    transaction_count,
    has_active_subscription,
    (SELECT COUNT(*) FROM subscriptions WHERE contact_id = c.id AND status = 'active') as active_sub_count
FROM contacts c
WHERE email = 'laura@thestarhouse.org';

-- Verify Virginia Anderson has $1,672
SELECT
    'Virginia Anderson Verification' as check_name,
    email,
    total_spent,
    has_active_subscription
FROM contacts
WHERE email = 'vlanderson@ecentral.com';

-- Verify Rita Fox has active subscription
SELECT
    'Rita Fox Verification' as check_name,
    email,
    total_spent,
    has_active_subscription
FROM contacts
WHERE email = 'rita@ritariverafox.com';

-- Check for remaining duplicates
SELECT
    'Remaining Duplicates' as check_name,
    COUNT(*) as duplicate_phone_count
FROM (
    SELECT phone
    FROM contacts
    WHERE phone IS NOT NULL
    GROUP BY phone
    HAVING COUNT(*) > 1
) t;
