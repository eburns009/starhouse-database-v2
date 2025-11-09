-- Phase 2: Batch Merge Exact Name Duplicates
-- FAANG Standards: Dynamic merge of all exact name matches
-- Date: 2025-11-09
-- Expected: ~118 groups → ~236 contacts merged

BEGIN;

-- Validation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contacts_merge_backup') THEN
        RAISE EXCEPTION 'contacts_merge_backup table does not exist';
    END IF;
END $$;

-- ============================================================================
-- SPECIAL CASE 1: Correct Genevieve Ayala (wrong name in database)
-- ============================================================================
-- genevieve@anemeraldearth.com is incorrectly named "Jeremy Colbert"
-- Raw_source shows "Genevieve Ayala"
DO $$
DECLARE
    v_genevieve_id UUID := (SELECT id FROM contacts WHERE email = 'genevieve@anemeraldearth.com');
BEGIN
    IF v_genevieve_id IS NOT NULL THEN
        -- Backup before correction
        INSERT INTO contacts_merge_backup (primary_contact_id, duplicate_contact_id, duplicate_contact_data, notes)
        SELECT v_genevieve_id, v_genevieve_id, row_to_json(c.*)::jsonb,
               'Phase 2: Name correction - was Jeremy Colbert, corrected to Genevieve Ayala based on raw_source'
        FROM contacts c WHERE c.id = v_genevieve_id;

        -- Correct the name
        UPDATE contacts SET
            first_name = 'Genevieve',
            last_name = 'Ayala',
            updated_at = NOW()
        WHERE id = v_genevieve_id;

        RAISE NOTICE 'Corrected: genevieve@anemeraldearth.com - Jeremy Colbert → Genevieve Ayala';
    END IF;
END $$;

-- ============================================================================
-- DYNAMIC EXACT NAME MERGE
-- ============================================================================
-- Merge all exact name duplicates (same first_name + last_name, different emails)
-- Strategy: Keep contact with most transactions as primary

DO $$
DECLARE
    v_name_group RECORD;
    v_primary RECORD;
    v_duplicate RECORD;
    v_merge_count INT := 0;
    v_error_count INT := 0;
    v_existing_additional_email TEXT;
BEGIN
    -- Loop through all name duplicate groups
    FOR v_name_group IN (
        SELECT
            LOWER(TRIM(first_name)) as fname,
            LOWER(TRIM(last_name)) as lname,
            COUNT(*) as cnt
        FROM contacts
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
          AND first_name <> '' AND last_name <> ''
        GROUP BY LOWER(TRIM(first_name)), LOWER(TRIM(last_name))
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    )
    LOOP
        BEGIN
            -- Get primary contact (most transactions, earliest created if tie)
            SELECT
                c.id,
                c.email,
                c.first_name,
                c.last_name,
                c.phone,
                c.additional_email,
                (SELECT COUNT(*) FROM transactions WHERE contact_id = c.id) as txn_count
            INTO v_primary
            FROM contacts c
            WHERE LOWER(TRIM(c.first_name)) = v_name_group.fname
              AND LOWER(TRIM(c.last_name)) = v_name_group.lname
            ORDER BY (SELECT COUNT(*) FROM transactions WHERE contact_id = c.id) DESC,
                     c.created_at ASC
            LIMIT 1;

            -- Loop through duplicates and merge into primary
            FOR v_duplicate IN (
                SELECT
                    c.id,
                    c.email,
                    c.phone,
                    c.additional_email
                FROM contacts c
                WHERE LOWER(TRIM(c.first_name)) = v_name_group.fname
                  AND LOWER(TRIM(c.last_name)) = v_name_group.lname
                  AND c.id <> v_primary.id
                ORDER BY (SELECT COUNT(*) FROM transactions WHERE contact_id = c.id) DESC
            )
            LOOP
                -- Backup
                INSERT INTO contacts_merge_backup (
                    primary_contact_id,
                    duplicate_contact_id,
                    duplicate_contact_data,
                    notes
                )
                SELECT
                    v_primary.id,
                    v_duplicate.id,
                    row_to_json(c.*)::jsonb,
                    'Phase 2: Exact name match - ' || v_primary.first_name || ' ' || v_primary.last_name
                FROM contacts c WHERE c.id = v_duplicate.id;

                -- Get current additional_email from primary
                SELECT additional_email INTO v_existing_additional_email
                FROM contacts WHERE id = v_primary.id;

                -- Build new additional_email list
                DECLARE
                    v_new_additional_email TEXT;
                    v_emails_to_add TEXT;
                BEGIN
                    -- Start with duplicate's primary email
                    v_emails_to_add := v_duplicate.email;

                    -- Add duplicate's additional_email if exists
                    IF v_duplicate.additional_email IS NOT NULL AND v_duplicate.additional_email <> '' THEN
                        v_emails_to_add := v_emails_to_add || ', ' || v_duplicate.additional_email;
                    END IF;

                    -- Combine with existing additional_email
                    IF v_existing_additional_email IS NOT NULL AND v_existing_additional_email <> '' THEN
                        v_new_additional_email := v_existing_additional_email || ', ' || v_emails_to_add;
                    ELSE
                        v_new_additional_email := v_emails_to_add;
                    END IF;

                    -- Update primary with new email list and phone if missing
                    UPDATE contacts SET
                        additional_email = v_new_additional_email,
                        phone = COALESCE(phone, v_duplicate.phone),  -- Use duplicate phone if primary has none
                        updated_at = NOW()
                    WHERE id = v_primary.id;
                END;

                -- Reassign transactions
                UPDATE transactions SET contact_id = v_primary.id WHERE contact_id = v_duplicate.id;

                -- Reassign subscriptions
                UPDATE subscriptions SET contact_id = v_primary.id WHERE contact_id = v_duplicate.id;

                -- Merge tags
                INSERT INTO contact_tags (contact_id, tag_id)
                SELECT DISTINCT v_primary.id, ct.tag_id
                FROM contact_tags ct
                WHERE ct.contact_id = v_duplicate.id
                ON CONFLICT (contact_id, tag_id) DO NOTHING;

                -- Delete duplicate tags
                DELETE FROM contact_tags WHERE contact_id = v_duplicate.id;

                -- Delete duplicate contact
                DELETE FROM contacts WHERE id = v_duplicate.id;

                v_merge_count := v_merge_count + 1;

                -- Progress logging every 10 merges
                IF v_merge_count % 10 = 0 THEN
                    RAISE NOTICE 'Progress: % merges completed', v_merge_count;
                END IF;
            END LOOP;

        EXCEPTION
            WHEN OTHERS THEN
                v_error_count := v_error_count + 1;
                RAISE NOTICE 'Error merging group % %: %', v_name_group.fname, v_name_group.lname, SQLERRM;
        END;
    END LOOP;

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Exact Name Merge Complete';
    RAISE NOTICE 'Total merges: %', v_merge_count;
    RAISE NOTICE 'Errors: %', v_error_count;
    RAISE NOTICE '==============================================';
END $$;

-- ============================================================================
-- FINAL VALIDATION
-- ============================================================================

DO $$
DECLARE
    v_orphaned_transactions INT;
    v_orphaned_subscriptions INT;
    v_contact_count INT;
    v_remaining_name_dupes INT;
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

    -- Check remaining exact name duplicates
    WITH name_dupes AS (
        SELECT
            LOWER(TRIM(first_name)) as fname,
            LOWER(TRIM(last_name)) as lname
        FROM contacts
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
          AND first_name <> '' AND last_name <> ''
        GROUP BY LOWER(TRIM(first_name)), LOWER(TRIM(last_name))
        HAVING COUNT(*) > 1
    )
    SELECT COUNT(*) INTO v_remaining_name_dupes FROM name_dupes;

    IF v_orphaned_transactions > 0 THEN
        RAISE EXCEPTION 'Validation failed: % orphaned transactions found', v_orphaned_transactions;
    END IF;

    IF v_orphaned_subscriptions > 0 THEN
        RAISE EXCEPTION 'Validation failed: % orphaned subscriptions found', v_orphaned_subscriptions;
    END IF;

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'FINAL VALIDATION';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Final contact count: %', v_contact_count;
    RAISE NOTICE 'Remaining exact name duplicates: %', v_remaining_name_dupes;
    RAISE NOTICE 'Orphaned transactions: %', v_orphaned_transactions;
    RAISE NOTICE 'Orphaned subscriptions: %', v_orphaned_subscriptions;
    RAISE NOTICE '==============================================';
END $$;

COMMIT;
