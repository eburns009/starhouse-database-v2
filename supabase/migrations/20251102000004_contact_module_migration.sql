-- ============================================
-- CONTACT MODULE - DATA MIGRATION
-- StarHouse CRM Database
-- ============================================
-- Purpose: Migrate existing contact data to new schema
-- Critical: This migration MUST succeed for all 5,912 contacts
-- Created: 2025-11-02
-- Migration: 20251102000004
-- ============================================

-- ============================================
-- PRE-MIGRATION CHECKS
-- ============================================

DO $$
DECLARE
    v_contact_count INTEGER;
    v_contacts_without_email INTEGER;
BEGIN
    -- Count total contacts
    SELECT count(*) INTO v_contact_count FROM contacts;
    RAISE NOTICE 'Total contacts to migrate: %', v_contact_count;

    -- Check for contacts without email
    SELECT count(*) INTO v_contacts_without_email FROM contacts WHERE email IS NULL;
    IF v_contacts_without_email > 0 THEN
        RAISE EXCEPTION 'Found % contacts without email. All contacts must have an email before migration.', v_contacts_without_email;
    END IF;

    RAISE NOTICE 'Pre-migration checks passed!';
END $$;

-- ============================================
-- STEP 1: Migrate contacts.email → contact_emails (PRIMARY)
-- ============================================

RAISE NOTICE 'Step 1: Migrating primary emails...';

INSERT INTO contact_emails (
    contact_id,
    email,
    email_type,
    is_primary,
    is_outreach,
    source,
    verified,
    verified_at,
    created_by,
    created_at
)
SELECT
    c.id AS contact_id,
    c.email,
    'personal'::TEXT AS email_type,
    true AS is_primary,
    true AS is_outreach,  -- By default, primary is also outreach
    c.source_system AS source,
    true AS verified,  -- Assume existing emails are verified
    c.created_at AS verified_at,
    '00000000-0000-0000-0000-000000000000'::uuid AS created_by,  -- System migration
    c.created_at
FROM contacts c
WHERE c.email IS NOT NULL
ON CONFLICT (contact_id, email) DO NOTHING;  -- Skip if somehow already exists

-- Verify step 1
DO $$
DECLARE
    v_migrated_count INTEGER;
    v_contact_count INTEGER;
BEGIN
    SELECT count(*) INTO v_migrated_count FROM contact_emails WHERE is_primary = true;
    SELECT count(*) INTO v_contact_count FROM contacts;

    RAISE NOTICE 'Step 1 complete: % primary emails migrated (expected: %)', v_migrated_count, v_contact_count;

    IF v_migrated_count != v_contact_count THEN
        RAISE WARNING 'Email migration count mismatch! Got %, expected %', v_migrated_count, v_contact_count;
    END IF;
END $$;

-- ============================================
-- STEP 2: Migrate contacts.paypal_email → contact_emails
-- ============================================

RAISE NOTICE 'Step 2: Migrating PayPal emails...';

-- Insert PayPal emails that are different from primary email
INSERT INTO contact_emails (
    contact_id,
    email,
    email_type,
    is_primary,
    is_outreach,
    source,
    verified,
    verified_at,
    created_by,
    created_at
)
SELECT
    c.id AS contact_id,
    c.paypal_email,
    'personal'::TEXT AS email_type,
    false AS is_primary,  -- PayPal email is NOT primary (unless same as primary)
    false AS is_outreach,  -- Primary email is outreach by default
    'paypal'::TEXT AS source,
    true AS verified,  -- PayPal emails are verified
    COALESCE(c.first_transaction_date, c.created_at) AS verified_at,
    '00000000-0000-0000-0000-000000000000'::uuid AS created_by,
    COALESCE(c.first_transaction_date, c.created_at) AS created_at
FROM contacts c
WHERE c.paypal_email IS NOT NULL
  AND c.paypal_email != c.email  -- Only if different from primary
ON CONFLICT (contact_id, email) DO NOTHING;

-- Verify step 2
DO $$
DECLARE
    v_paypal_email_count INTEGER;
    v_different_paypal_count INTEGER;
BEGIN
    SELECT count(*) INTO v_paypal_email_count
    FROM contact_emails WHERE source = 'paypal';

    SELECT count(*) INTO v_different_paypal_count
    FROM contacts WHERE paypal_email IS NOT NULL AND paypal_email != email;

    RAISE NOTICE 'Step 2 complete: % PayPal emails migrated (expected: %)', v_paypal_email_count, v_different_paypal_count;
END $$;

-- ============================================
-- STEP 3: Migrate external IDs → external_identities
-- ============================================

RAISE NOTICE 'Step 3: Migrating external identities...';

-- Migrate Kajabi IDs
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'kajabi'::TEXT,
    c.kajabi_id,
    true,
    c.created_at,
    c.created_at
FROM contacts c
WHERE c.kajabi_id IS NOT NULL AND c.kajabi_id != ''
ON CONFLICT (system, external_id) DO NOTHING;

-- Migrate Kajabi Member IDs (if different from kajabi_id)
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'kajabi_member'::TEXT,
    c.kajabi_member_id,
    true,
    c.created_at,
    c.created_at
FROM contacts c
WHERE c.kajabi_member_id IS NOT NULL
  AND c.kajabi_member_id != ''
  AND c.kajabi_member_id != c.kajabi_id  -- Only if different
ON CONFLICT (system, external_id) DO NOTHING;

-- Migrate PayPal Payer IDs
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'paypal'::TEXT,
    c.paypal_payer_id,
    true,
    COALESCE(c.first_transaction_date, c.created_at),
    COALESCE(c.first_transaction_date, c.created_at)
FROM contacts c
WHERE c.paypal_payer_id IS NOT NULL AND c.paypal_payer_id != ''
ON CONFLICT (system, external_id) DO NOTHING;

-- Migrate Ticket Tailor IDs
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'ticket_tailor'::TEXT,
    c.ticket_tailor_id,
    true,
    c.created_at,
    c.created_at
FROM contacts c
WHERE c.ticket_tailor_id IS NOT NULL AND c.ticket_tailor_id != ''
ON CONFLICT (system, external_id) DO NOTHING;

-- Migrate Zoho IDs
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'zoho'::TEXT,
    c.zoho_id,
    true,
    c.created_at,
    c.created_at
FROM contacts c
WHERE c.zoho_id IS NOT NULL AND c.zoho_id != ''
ON CONFLICT (system, external_id) DO NOTHING;

-- Migrate QuickBooks IDs
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'quickbooks'::TEXT,
    c.quickbooks_id,
    true,
    c.created_at,
    c.created_at
FROM contacts c
WHERE c.quickbooks_id IS NOT NULL AND c.quickbooks_id != ''
ON CONFLICT (system, external_id) DO NOTHING;

-- Migrate Mailchimp IDs
INSERT INTO external_identities (contact_id, system, external_id, verified, verified_at, created_at)
SELECT
    c.id,
    'mailchimp'::TEXT,
    c.mailchimp_id,
    true,
    c.created_at,
    c.created_at
FROM contacts c
WHERE c.mailchimp_id IS NOT NULL AND c.mailchimp_id != ''
ON CONFLICT (system, external_id) DO NOTHING;

-- Verify step 3
DO $$
DECLARE
    v_external_ids_count INTEGER;
BEGIN
    SELECT count(*) INTO v_external_ids_count FROM external_identities;
    RAISE NOTICE 'Step 3 complete: % external identities migrated', v_external_ids_count;
END $$;

-- ============================================
-- STEP 4: Create initial contact_roles based on existing data
-- ============================================

RAISE NOTICE 'Step 4: Creating initial contact roles...';

-- Create 'member' role for contacts with active subscriptions
INSERT INTO contact_roles (contact_id, role, status, started_at, source, created_at)
SELECT DISTINCT
    c.id,
    'member'::TEXT,
    CASE
        WHEN c.has_active_subscription = true THEN 'active'::TEXT
        ELSE 'inactive'::TEXT
    END,
    COALESCE(
        (SELECT min(s.start_date) FROM subscriptions s WHERE s.contact_id = c.id),
        c.created_at
    ) AS started_at,
    'subscription'::TEXT AS source,
    c.created_at
FROM contacts c
WHERE c.membership_level IS NOT NULL
   OR c.membership_tier IS NOT NULL
   OR c.has_active_subscription = true
   OR EXISTS (SELECT 1 FROM subscriptions s WHERE s.contact_id = c.id)
ON CONFLICT (contact_id, role) WHERE status = 'active' DO NOTHING;

-- Create 'donor' role for contacts who have made transactions
INSERT INTO contact_roles (contact_id, role, status, started_at, source, metadata, created_at)
SELECT DISTINCT
    c.id,
    'donor'::TEXT,
    CASE
        WHEN c.last_transaction_date > NOW() - INTERVAL '1 year' THEN 'active'::TEXT
        ELSE 'inactive'::TEXT
    END,
    COALESCE(c.first_transaction_date, c.created_at),
    'donation'::TEXT AS source,
    jsonb_build_object(
        'total_spent', c.total_spent,
        'transaction_count', c.transaction_count
    ),
    c.created_at
FROM contacts c
WHERE c.total_spent > 0
   OR c.transaction_count > 0
ON CONFLICT (contact_id, role) WHERE status = 'active' DO NOTHING;

-- Create 'subscriber' role for email subscribers
INSERT INTO contact_roles (contact_id, role, status, started_at, source, created_at)
SELECT
    c.id,
    'subscriber'::TEXT,
    'active'::TEXT,
    c.created_at,
    'email'::TEXT AS source,
    c.created_at
FROM contacts c
WHERE c.email_subscribed = true
ON CONFLICT (contact_id, role) WHERE status = 'active' DO NOTHING;

-- Verify step 4
DO $$
DECLARE
    v_member_count INTEGER;
    v_donor_count INTEGER;
    v_subscriber_count INTEGER;
BEGIN
    SELECT count(*) INTO v_member_count FROM contact_roles WHERE role = 'member';
    SELECT count(*) INTO v_donor_count FROM contact_roles WHERE role = 'donor';
    SELECT count(*) INTO v_subscriber_count FROM contact_roles WHERE role = 'subscriber';

    RAISE NOTICE 'Step 4 complete: % members, % donors, % subscribers', v_member_count, v_donor_count, v_subscriber_count;
END $$;

-- ============================================
-- STEP 5: Migrate contacts.notes → contact_notes
-- ============================================

RAISE NOTICE 'Step 5: Migrating contact notes...';

INSERT INTO contact_notes (
    contact_id,
    note_type,
    subject,
    content,
    author_user_id,
    author_name,
    created_at
)
SELECT
    c.id,
    'general'::TEXT,
    'Legacy Note (Migrated)'::TEXT,
    c.notes,
    '00000000-0000-0000-0000-000000000000'::uuid,
    'System Migration'::TEXT,
    c.created_at
FROM contacts c
WHERE c.notes IS NOT NULL
  AND trim(c.notes) != '';

-- Verify step 5
DO $$
DECLARE
    v_notes_count INTEGER;
    v_contacts_with_notes INTEGER;
BEGIN
    SELECT count(*) INTO v_notes_count FROM contact_notes WHERE note_type = 'general';
    SELECT count(*) INTO v_contacts_with_notes FROM contacts WHERE notes IS NOT NULL AND trim(notes) != '';

    RAISE NOTICE 'Step 5 complete: % notes migrated (expected: %)', v_notes_count, v_contacts_with_notes;
END $$;

-- ============================================
-- POST-MIGRATION VERIFICATION
-- ============================================

RAISE NOTICE 'Running post-migration verification...';

DO $$
DECLARE
    v_contact_count INTEGER;
    v_primary_email_count INTEGER;
    v_outreach_email_count INTEGER;
    v_contacts_without_primary INTEGER;
    v_contacts_without_outreach INTEGER;
    v_null_outreach_count INTEGER;
    v_external_id_count INTEGER;
BEGIN
    -- Count contacts
    SELECT count(*) INTO v_contact_count FROM contacts;
    RAISE NOTICE 'Total contacts: %', v_contact_count;

    -- Verify every contact has primary email
    SELECT count(*) INTO v_primary_email_count
    FROM contact_emails WHERE is_primary = true;
    RAISE NOTICE 'Contacts with primary email: %', v_primary_email_count;

    SELECT count(*) INTO v_contacts_without_primary
    FROM contacts c
    WHERE NOT EXISTS (
        SELECT 1 FROM contact_emails ce
        WHERE ce.contact_id = c.id AND ce.is_primary = true
    );

    IF v_contacts_without_primary > 0 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: % contacts without primary email!', v_contacts_without_primary;
    END IF;

    -- Verify every contact has outreach email
    SELECT count(*) INTO v_outreach_email_count
    FROM contact_emails WHERE is_outreach = true;
    RAISE NOTICE 'Contacts with outreach email: %', v_outreach_email_count;

    SELECT count(*) INTO v_contacts_without_outreach
    FROM contacts c
    WHERE NOT EXISTS (
        SELECT 1 FROM contact_emails ce
        WHERE ce.contact_id = c.id AND ce.is_outreach = true
    );

    IF v_contacts_without_outreach > 0 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: % contacts without outreach email!', v_contacts_without_outreach;
    END IF;

    -- Verify v_contact_outreach_email never returns NULL
    SELECT count(*) INTO v_null_outreach_count
    FROM v_contact_outreach_email
    WHERE outreach_email IS NULL;

    IF v_null_outreach_count > 0 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: v_contact_outreach_email returned NULL for % contacts!', v_null_outreach_count;
    END IF;

    -- Count external identities
    SELECT count(*) INTO v_external_id_count FROM external_identities;
    RAISE NOTICE 'Total external identities migrated: %', v_external_id_count;

    RAISE NOTICE '✅ POST-MIGRATION VERIFICATION PASSED!';
    RAISE NOTICE '================================';
    RAISE NOTICE 'Migration Summary:';
    RAISE NOTICE '  - Contacts: %', v_contact_count;
    RAISE NOTICE '  - Primary Emails: %', v_primary_email_count;
    RAISE NOTICE '  - Outreach Emails: %', v_outreach_email_count;
    RAISE NOTICE '  - External IDs: %', v_external_id_count;
    RAISE NOTICE '================================';
END $$;

-- ============================================
-- PERFORMANCE TEST QUERIES
-- ============================================

RAISE NOTICE 'Running performance tests...';

-- Test 1: Search contacts (should be <200ms)
\timing on
SELECT * FROM search_contacts('john', 10);
\timing off

-- Test 2: Get contact activity (should be <300ms)
-- Get a random contact_id first
DO $$
DECLARE
    v_test_contact_id UUID;
BEGIN
    SELECT id INTO v_test_contact_id FROM contacts LIMIT 1;
    RAISE NOTICE 'Testing get_contact_activity for contact: %', v_test_contact_id;
END $$;

\timing on
SELECT * FROM get_contact_activity((SELECT id FROM contacts LIMIT 1), 50, 0);
\timing off

-- Test 3: Contact list view (should be <250ms for 50 contacts)
\timing on
SELECT * FROM v_contact_list_optimized LIMIT 50;
\timing off

RAISE NOTICE 'Performance tests complete. Check timing above.';

-- ============================================
-- OPTIONAL: Add deprecation comments to old columns
-- ============================================

COMMENT ON COLUMN contacts.email IS
'⚠️ DEPRECATED: Use contact_emails table. This column maintained for backward compatibility during migration.';

COMMENT ON COLUMN contacts.paypal_email IS
'⚠️ DEPRECATED: Migrated to contact_emails table with source=paypal.';

COMMENT ON COLUMN contacts.kajabi_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=kajabi.';

COMMENT ON COLUMN contacts.kajabi_member_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=kajabi_member.';

COMMENT ON COLUMN contacts.ticket_tailor_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=ticket_tailor.';

COMMENT ON COLUMN contacts.zoho_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=zoho.';

COMMENT ON COLUMN contacts.quickbooks_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=quickbooks.';

COMMENT ON COLUMN contacts.mailchimp_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=mailchimp.';

COMMENT ON COLUMN contacts.paypal_payer_id IS
'⚠️ DEPRECATED: Migrated to external_identities table with system=paypal.';

COMMENT ON COLUMN contacts.notes IS
'⚠️ DEPRECATED: Migrated to contact_notes table. Use contact_notes for new entries.';

-- ============================================
-- NEXT STEPS (Manual)
-- ============================================

/*
After this migration succeeds, you should:

1. Test the application UI with new tables
2. Update API routes to use new tables:
   - Use v_contact_list_optimized for list views
   - Use v_contact_detail_enriched for detail views
   - Use search_contacts() function for search
   - Use get_contact_activity() for timelines

3. Monitor performance:
   - Check query times in Supabase dashboard
   - Add indexes if needed
   - Consider materialized views for heavy queries

4. Phase 2 (Week 3-4): Deprecate old columns
   - After confirming new system works
   - Update all queries to use new tables
   - Eventually: ALTER TABLE contacts DROP COLUMN email, paypal_email, etc.

5. Set up RLS policies for different user roles:
   - Viewer: Read-only access
   - Staff: Read + write notes
   - Admin: Full access

DO NOT DROP OLD COLUMNS YET! Keep for backward compatibility during transition.
*/

-- ============================================
-- ROLLBACK INSTRUCTIONS
-- ============================================
-- WARNING: This rollback will DELETE all migrated data!
-- Only use if migration fails during testing.

/*
-- Delete all migrated data
DELETE FROM contact_notes WHERE author_name = 'System Migration';
DELETE FROM contact_roles WHERE source IN ('subscription', 'donation', 'email');
DELETE FROM external_identities;
DELETE FROM contact_emails;

-- Verify rollback
SELECT 'contact_emails:', count(*) FROM contact_emails;
SELECT 'external_identities:', count(*) FROM external_identities;
SELECT 'contact_roles:', count(*) FROM contact_roles;
SELECT 'contact_notes:', count(*) FROM contact_notes;
*/
