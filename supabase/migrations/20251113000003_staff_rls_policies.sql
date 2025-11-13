-- ============================================
-- STAFF RLS POLICIES FOR CONTACTS
-- StarHouse CRM Database
-- ============================================
-- Purpose: Allow all authenticated staff to access all contacts
-- Model: Option 1 - Shared CRM (all staff are trusted)
-- Created: 2025-11-13
-- Migration: 20251113000003
-- ============================================
-- FAANG Standard: Use RLS instead of app-level permissions for defense in depth
-- ============================================

-- Drop old restrictive policy
-- This policy only allowed users to see contacts matching their own email
-- Not suitable for a staff CRM where everyone needs to see all contacts
DROP POLICY IF EXISTS "Users can view their own contact" ON contacts;

-- ============================================
-- STAFF ACCESS POLICIES
-- ============================================
-- All authenticated users are staff members who should have full access
-- User management is handled via Supabase Auth (invite-only)
-- ============================================

-- Policy: All staff can view all contacts
CREATE POLICY "staff_select_all_contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON POLICY "staff_select_all_contacts" ON contacts IS
'Allow all authenticated staff to view all contacts. Access control is via Supabase user management.';

-- Policy: All staff can update all contacts
CREATE POLICY "staff_update_all_contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (true)  -- Can update any contact
    WITH CHECK (true);  -- No restrictions on what can be updated

COMMENT ON POLICY "staff_update_all_contacts" ON contacts IS
'Allow all authenticated staff to update all contacts. Includes tag operations, notes, etc.';

-- Policy: All staff can insert new contacts
CREATE POLICY "staff_insert_contacts"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (true);  -- No restrictions on new contacts

COMMENT ON POLICY "staff_insert_contacts" ON contacts IS
'Allow all authenticated staff to create new contacts.';

-- Policy: All staff can delete contacts (soft delete recommended)
-- Note: Consider adding a deleted_at column instead of hard deletes
CREATE POLICY "staff_delete_contacts"
    ON contacts FOR DELETE
    TO authenticated
    USING (true);

COMMENT ON POLICY "staff_delete_contacts" ON contacts IS
'Allow all authenticated staff to delete contacts. Consider implementing soft deletes instead.';

-- ============================================
-- SERVICE ROLE POLICY (Keep for backend operations)
-- ============================================
-- The existing service_role policy should remain for webhook/import operations

-- Verify service role policy exists (already in schema, but defensive check)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'contacts'
        AND policyname = 'Service role has full access'
    ) THEN
        CREATE POLICY "Service role has full access"
            ON contacts FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify policies are working:
--
-- 1. Check all policies on contacts table:
--    SELECT * FROM pg_policies WHERE tablename = 'contacts';
--
-- 2. Test as authenticated user (in SQL editor with RLS):
--    SET ROLE authenticated;
--    SELECT COUNT(*) FROM contacts;  -- Should return all contacts
--    UPDATE contacts SET tags = ARRAY['test'] WHERE id = 'some-id';  -- Should work
--
-- 3. Reset role:
--    RESET ROLE;
-- ============================================
