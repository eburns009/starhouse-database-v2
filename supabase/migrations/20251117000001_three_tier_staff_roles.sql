-- ============================================================================
-- MIGRATION: Three-Tier Staff Role System (FAANG Standards)
-- ============================================================================
-- Purpose: Upgrade from 2-tier (admin/staff) to 3-tier (admin/full_user/read_only)
-- Standard: Zero-downtime migration with rollback capability
-- Author: Staff Management Team
-- Date: 2025-11-17
-- Migration: 20251117000001
-- ============================================================================

-- ============================================================================
-- STEP 1: ADD NEW COLUMNS (Non-breaking changes)
-- ============================================================================

-- Add display_name for friendly UI display
ALTER TABLE staff_members
ADD COLUMN IF NOT EXISTS display_name TEXT;

COMMENT ON COLUMN staff_members.display_name IS
'Friendly display name for UI (e.g., "John Smith"). Falls back to email if null.';

-- Add last_login tracking for audit/security
ALTER TABLE staff_members
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

COMMENT ON COLUMN staff_members.last_login_at IS
'Timestamp of most recent successful login. Updated by frontend on each session start.';

-- Create index for performance on active staff with recent logins
CREATE INDEX IF NOT EXISTS idx_staff_members_last_login
ON staff_members(last_login_at DESC)
WHERE active = true;

-- ============================================================================
-- STEP 2: UPDATE ROLE CONSTRAINT (Add 'read_only', keep backward compat)
-- ============================================================================

-- Drop old constraint
ALTER TABLE staff_members
DROP CONSTRAINT IF EXISTS staff_members_role_check;

-- Add new constraint with all 3 roles + backward compatibility
ALTER TABLE staff_members
ADD CONSTRAINT staff_members_role_check
CHECK (role IN ('admin', 'staff', 'full_user', 'read_only'));

COMMENT ON CONSTRAINT staff_members_role_check ON staff_members IS
'Role validation: admin (full access + user mgmt), full_user (view/edit data), read_only (view only), staff (legacy - migrated to full_user)';

-- ============================================================================
-- STEP 3: MIGRATE EXISTING 'staff' ROLE TO 'full_user'
-- ============================================================================

-- Update all existing 'staff' users to 'full_user' (backward compatible)
UPDATE staff_members
SET role = 'full_user'
WHERE role = 'staff';

-- Log migration results
DO $$
DECLARE
    v_migrated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_migrated_count
    FROM staff_members
    WHERE role = 'full_user';

    RAISE NOTICE 'Migrated % staff members from "staff" to "full_user" role', v_migrated_count;
END $$;

-- ============================================================================
-- STEP 4: UPDATE RLS POLICIES FOR THREE-TIER ACCESS
-- ============================================================================

-- Drop old policies (we'll recreate with better names and 3-tier logic)
DROP POLICY IF EXISTS "verified_staff_select_contacts" ON contacts;
DROP POLICY IF EXISTS "verified_staff_update_contacts" ON contacts;
DROP POLICY IF EXISTS "verified_staff_insert_contacts" ON contacts;
DROP POLICY IF EXISTS "admin_delete_contacts" ON contacts;

-- -------------------------
-- READ ACCESS (All 3 roles)
-- -------------------------
CREATE POLICY "staff_read_contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role IN ('admin', 'full_user', 'read_only')
            AND active = true
        )
    );

COMMENT ON POLICY "staff_read_contacts" ON contacts IS
'All active staff (admin, full_user, read_only) can view contacts. Read-only users stop here.';

-- -------------------------
-- UPDATE ACCESS (Admin + Full User)
-- -------------------------
CREATE POLICY "staff_update_contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role IN ('admin', 'full_user')
            AND active = true
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role IN ('admin', 'full_user')
            AND active = true
        )
    );

COMMENT ON POLICY "staff_update_contacts" ON contacts IS
'Admin and full_user can update contacts. Read-only users cannot.';

-- -------------------------
-- INSERT ACCESS (Admin + Full User)
-- -------------------------
CREATE POLICY "staff_insert_contacts"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role IN ('admin', 'full_user')
            AND active = true
        )
    );

COMMENT ON POLICY "staff_insert_contacts" ON contacts IS
'Admin and full_user can create new contacts. Read-only users cannot.';

-- -------------------------
-- DELETE ACCESS (Admin only)
-- -------------------------
CREATE POLICY "admin_delete_contacts"
    ON contacts FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );

COMMENT ON POLICY "admin_delete_contacts" ON contacts IS
'Only admins can delete contacts. Soft delete (deleted_at) is recommended instead.';

-- ============================================================================
-- STEP 5: UPDATE HELPER FUNCTIONS
-- ============================================================================

-- Function: Check if current user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM staff_members
        WHERE email = auth.jwt()->>'email'
        AND role = 'admin'
        AND active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION is_admin IS
'Returns true if authenticated user is an active admin. Used for admin-only operations.';

-- Function: Check if current user can edit (admin or full_user)
CREATE OR REPLACE FUNCTION can_edit()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM staff_members
        WHERE email = auth.jwt()->>'email'
        AND role IN ('admin', 'full_user')
        AND active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION can_edit IS
'Returns true if authenticated user can edit data (admin or full_user).';

-- Function: Get current user role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
DECLARE
    v_role TEXT;
BEGIN
    SELECT role INTO v_role
    FROM staff_members
    WHERE email = auth.jwt()->>'email'
    AND active = true;

    RETURN COALESCE(v_role, 'none');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_role IS
'Returns current user role (admin/full_user/read_only) or "none" if not staff.';

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION is_admin TO authenticated;
GRANT EXECUTE ON FUNCTION can_edit TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_role TO authenticated;

-- ============================================================================
-- STEP 6: UPDATE STAFF MEMBER FUNCTIONS (Add display_name support)
-- ============================================================================

-- Drop existing function variants to avoid conflicts (idempotent migration)
DROP FUNCTION IF EXISTS add_staff_member(TEXT);
DROP FUNCTION IF EXISTS add_staff_member(TEXT, TEXT);
DROP FUNCTION IF EXISTS add_staff_member(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS add_staff_member(TEXT, TEXT, TEXT, TEXT);

-- Update add_staff_member function to support display_name
CREATE OR REPLACE FUNCTION add_staff_member(
    p_email TEXT,
    p_role TEXT DEFAULT 'full_user',
    p_display_name TEXT DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    v_admin_email TEXT;
BEGIN
    -- Verify caller is admin
    v_admin_email := auth.jwt()->>'email';

    IF NOT EXISTS (
        SELECT 1 FROM staff_members
        WHERE email = v_admin_email
        AND role = 'admin'
        AND active = true
    ) THEN
        RAISE EXCEPTION 'Only admins can add staff members';
    END IF;

    -- Validate role
    IF p_role NOT IN ('admin', 'full_user', 'read_only') THEN
        RAISE EXCEPTION 'Role must be: admin, full_user, or read_only';
    END IF;

    -- Validate email format
    IF p_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' THEN
        RAISE EXCEPTION 'Invalid email format';
    END IF;

    -- Add staff member
    INSERT INTO staff_members (email, role, display_name, added_by, notes)
    VALUES (p_email, p_role, p_display_name, v_admin_email, p_notes);

    RETURN jsonb_build_object(
        'success', true,
        'email', p_email,
        'role', p_role,
        'display_name', p_display_name,
        'added_by', v_admin_email
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION add_staff_member IS
'Adds new staff member with optional display name. Admin only.
Usage: SELECT add_staff_member(''user@example.com'', ''full_user'', ''John Smith'', ''Marketing team'');';

-- Update change_role function (new - for promoting/demoting users)
CREATE OR REPLACE FUNCTION change_staff_role(
    p_email TEXT,
    p_new_role TEXT
) RETURNS JSONB AS $$
DECLARE
    v_admin_email TEXT;
    v_old_role TEXT;
BEGIN
    -- Verify caller is admin
    v_admin_email := auth.jwt()->>'email';

    IF NOT EXISTS (
        SELECT 1 FROM staff_members
        WHERE email = v_admin_email
        AND role = 'admin'
        AND active = true
    ) THEN
        RAISE EXCEPTION 'Only admins can change roles';
    END IF;

    -- Validate new role
    IF p_new_role NOT IN ('admin', 'full_user', 'read_only') THEN
        RAISE EXCEPTION 'Role must be: admin, full_user, or read_only';
    END IF;

    -- Prevent self-demotion from admin
    IF p_email = v_admin_email AND p_new_role != 'admin' THEN
        RAISE EXCEPTION 'Cannot demote yourself from admin';
    END IF;

    -- Get old role and update
    SELECT role INTO v_old_role FROM staff_members WHERE email = p_email;

    UPDATE staff_members
    SET role = p_new_role
    WHERE email = p_email
    AND active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Staff member not found or inactive: %', p_email;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'email', p_email,
        'old_role', v_old_role,
        'new_role', p_new_role,
        'changed_by', v_admin_email
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION change_staff_role IS
'Changes staff member role. Prevents self-demotion. Admin only.
Usage: SELECT change_staff_role(''user@example.com'', ''read_only'');';

-- Grant execute permission
GRANT EXECUTE ON FUNCTION change_staff_role TO authenticated;

-- ============================================================================
-- STEP 7: APPLY SAME POLICIES TO OTHER TABLES
-- ============================================================================

-- Tags table policies
DROP POLICY IF EXISTS "staff_full_access" ON tags;
DROP POLICY IF EXISTS "staff_read_tags" ON tags;
DROP POLICY IF EXISTS "staff_modify_tags" ON tags;
DROP POLICY IF EXISTS "staff_update_tags" ON tags;
DROP POLICY IF EXISTS "admin_delete_tags" ON tags;

CREATE POLICY "staff_read_tags" ON tags FOR SELECT TO authenticated
    USING (is_verified_staff());

CREATE POLICY "staff_modify_tags" ON tags FOR INSERT TO authenticated
    WITH CHECK (can_edit());

CREATE POLICY "staff_update_tags" ON tags FOR UPDATE TO authenticated
    USING (can_edit()) WITH CHECK (can_edit());

CREATE POLICY "admin_delete_tags" ON tags FOR DELETE TO authenticated
    USING (is_admin());

-- Products table policies
DROP POLICY IF EXISTS "staff_full_access" ON products;
DROP POLICY IF EXISTS "staff_read_products" ON products;
DROP POLICY IF EXISTS "staff_modify_products" ON products;
DROP POLICY IF EXISTS "staff_update_products" ON products;
DROP POLICY IF EXISTS "admin_delete_products" ON products;

CREATE POLICY "staff_read_products" ON products FOR SELECT TO authenticated
    USING (is_verified_staff());

CREATE POLICY "staff_modify_products" ON products FOR INSERT TO authenticated
    WITH CHECK (can_edit());

CREATE POLICY "staff_update_products" ON products FOR UPDATE TO authenticated
    USING (can_edit()) WITH CHECK (can_edit());

CREATE POLICY "admin_delete_products" ON products FOR DELETE TO authenticated
    USING (is_admin());

-- Transactions table policies
DROP POLICY IF EXISTS "staff_full_access" ON transactions;
DROP POLICY IF EXISTS "staff_read_transactions" ON transactions;
DROP POLICY IF EXISTS "staff_modify_transactions" ON transactions;
DROP POLICY IF EXISTS "staff_update_transactions" ON transactions;
DROP POLICY IF EXISTS "admin_delete_transactions" ON transactions;

CREATE POLICY "staff_read_transactions" ON transactions FOR SELECT TO authenticated
    USING (is_verified_staff());

CREATE POLICY "staff_modify_transactions" ON transactions FOR INSERT TO authenticated
    WITH CHECK (can_edit());

CREATE POLICY "staff_update_transactions" ON transactions FOR UPDATE TO authenticated
    USING (can_edit()) WITH CHECK (can_edit());

CREATE POLICY "admin_delete_transactions" ON transactions FOR DELETE TO authenticated
    USING (is_admin());

-- Subscriptions table policies
DROP POLICY IF EXISTS "staff_full_access" ON subscriptions;
DROP POLICY IF EXISTS "staff_read_subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "staff_modify_subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "staff_update_subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "admin_delete_subscriptions" ON subscriptions;

CREATE POLICY "staff_read_subscriptions" ON subscriptions FOR SELECT TO authenticated
    USING (is_verified_staff());

CREATE POLICY "staff_modify_subscriptions" ON subscriptions FOR INSERT TO authenticated
    WITH CHECK (can_edit());

CREATE POLICY "staff_update_subscriptions" ON subscriptions FOR UPDATE TO authenticated
    USING (can_edit()) WITH CHECK (can_edit());

CREATE POLICY "admin_delete_subscriptions" ON subscriptions FOR DELETE TO authenticated
    USING (is_admin());

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after migration to verify:

-- 1. Check staff roles:
--    SELECT email, role, display_name, active, last_login_at FROM staff_members;
--    Expected: All 'staff' roles migrated to 'full_user'

-- 2. Test helper functions:
--    SELECT is_admin(), can_edit(), get_user_role();
--    Expected: Returns correct values for your user

-- 3. Check RLS policies:
--    SELECT tablename, policyname, cmd, roles FROM pg_policies
--    WHERE schemaname = 'public' AND tablename IN ('contacts', 'tags', 'products', 'transactions', 'subscriptions');
--    Expected: New 3-tier policies present

-- 4. Verify role constraint:
--    \d staff_members
--    Expected: role CHECK constraint includes 'read_only'

-- ============================================================================
-- ROLLBACK PLAN (if needed)
-- ============================================================================
-- If this migration causes issues, run:
--
-- ALTER TABLE staff_members DROP CONSTRAINT staff_members_role_check;
-- ALTER TABLE staff_members ADD CONSTRAINT staff_members_role_check
--   CHECK (role IN ('admin', 'staff'));
-- UPDATE staff_members SET role = 'staff' WHERE role IN ('full_user', 'read_only');
-- DROP FUNCTION IF EXISTS is_admin();
-- DROP FUNCTION IF EXISTS can_edit();
-- DROP FUNCTION IF EXISTS get_user_role();
-- DROP FUNCTION IF EXISTS change_staff_role(TEXT, TEXT);
--
-- Then restore old RLS policies from migration 20251113000004
-- ============================================================================
