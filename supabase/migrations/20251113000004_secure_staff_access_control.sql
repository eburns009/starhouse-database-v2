-- ============================================
-- SECURE STAFF ACCESS CONTROL
-- StarHouse CRM Database
-- ============================================
-- Purpose: Implement proper staff verification with role-based access
-- Model: Explicit allowlist + Role system (admin/staff)
-- Security: Defense in depth - verify users even with invite-only auth
-- Created: 2025-11-13
-- Migration: 20251113000004
-- ============================================

-- ============================================
-- STEP 1: CREATE STAFF ALLOWLIST TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS staff_members (
    -- Primary identification
    email TEXT PRIMARY KEY,

    -- Role system (future: admins can assign other admins)
    role TEXT NOT NULL DEFAULT 'staff'
        CHECK (role IN ('admin', 'staff')),

    -- Audit trail
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by TEXT,  -- Email of person who added them
    notes TEXT,     -- Why they were added, expiration date, etc.

    -- Status tracking
    active BOOLEAN NOT NULL DEFAULT true,
    deactivated_at TIMESTAMPTZ,
    deactivated_by TEXT
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_staff_members_role ON staff_members(role) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_staff_members_active ON staff_members(active);

COMMENT ON TABLE staff_members IS
'Explicit allowlist of authorized staff. Only emails in this table can access contacts.
Supports admin/staff roles for future permission differentiation.';

COMMENT ON COLUMN staff_members.role IS
'admin: Can manage staff_members, assign other admins
staff: Can view/edit contacts only';

-- ============================================
-- STEP 2: ADD INITIAL ADMIN (YOU)
-- ============================================
-- IMPORTANT: Replace 'your.email@thestarhouse.org' with your actual email
-- This is critical - you need at least one admin to bootstrap the system

INSERT INTO staff_members (email, role, added_by, notes)
VALUES (
    'support@thestarhouse.com',  -- Ed Burns - Initial Admin
    'admin',
    'system',
    'Initial admin - created during migration'
)
ON CONFLICT (email) DO UPDATE
SET role = 'admin',  -- Ensure you're admin even if you exist
    notes = 'Initial admin - created during migration';

-- ============================================
-- STEP 3: DROP INSECURE POLICIES
-- ============================================
-- Remove the dangerous USING (true) policies

DROP POLICY IF EXISTS "staff_select_all_contacts" ON contacts;
DROP POLICY IF EXISTS "staff_update_all_contacts" ON contacts;
DROP POLICY IF EXISTS "staff_insert_contacts" ON contacts;
DROP POLICY IF EXISTS "staff_delete_contacts" ON contacts;

-- ============================================
-- STEP 4: CREATE SECURE RLS POLICIES FOR CONTACTS
-- ============================================

-- Helper function: Check if user is verified staff
CREATE OR REPLACE FUNCTION is_verified_staff()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM staff_members
        WHERE email = auth.jwt()->>'email'
        AND active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION is_verified_staff IS
'Returns true if authenticated user is in staff_members allowlist and active.
Used by RLS policies to verify staff access.';

-- Policy: Verified staff can view all contacts
CREATE POLICY "verified_staff_select_contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (is_verified_staff());

COMMENT ON POLICY "verified_staff_select_contacts" ON contacts IS
'Only users in staff_members allowlist can view contacts. Checked via is_verified_staff().';

-- Policy: Verified staff can update all contacts
CREATE POLICY "verified_staff_update_contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (is_verified_staff())
    WITH CHECK (is_verified_staff());

COMMENT ON POLICY "verified_staff_update_contacts" ON contacts IS
'Only verified staff can update contacts. Audit trail tracked via updated_by trigger.';

-- Policy: Verified staff can insert contacts
CREATE POLICY "verified_staff_insert_contacts"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (is_verified_staff());

COMMENT ON POLICY "verified_staff_insert_contacts" ON contacts IS
'Only verified staff can create new contacts.';

-- Policy: Only admins can delete contacts (soft delete recommended)
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
'Only admins can delete contacts. Consider implementing soft deletes instead (deleted_at column).';

-- ============================================
-- STEP 5: RLS POLICIES FOR STAFF_MEMBERS TABLE
-- ============================================

ALTER TABLE staff_members ENABLE ROW LEVEL SECURITY;

-- All verified staff can view staff list (know who else is staff)
CREATE POLICY "staff_view_staff_list"
    ON staff_members FOR SELECT
    TO authenticated
    USING (is_verified_staff());

COMMENT ON POLICY "staff_view_staff_list" ON staff_members IS
'All verified staff can see the staff list. Transparency about who has access.';

-- Only admins can add new staff members
CREATE POLICY "admin_add_staff"
    ON staff_members FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );

COMMENT ON POLICY "admin_add_staff" ON staff_members IS
'Only admins can add new staff members to the allowlist.';

-- Only admins can modify staff members (change role, deactivate)
CREATE POLICY "admin_update_staff"
    ON staff_members FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );

COMMENT ON POLICY "admin_update_staff" ON staff_members IS
'Only admins can update staff members (promote to admin, deactivate, etc.).';

-- Only admins can delete staff members
CREATE POLICY "admin_delete_staff"
    ON staff_members FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );

COMMENT ON POLICY "admin_delete_staff" ON staff_members IS
'Only admins can permanently delete staff members. Soft delete (active=false) is recommended.';

-- ============================================
-- STEP 6: ADD AUDIT TRAIL TO CONTACTS TABLE
-- ============================================

-- Add audit columns if they don't exist
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS created_by TEXT,
ADD COLUMN IF NOT EXISTS updated_by TEXT,
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by TEXT;

-- Create audit trigger for updates
CREATE OR REPLACE FUNCTION contacts_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_by = auth.jwt()->>'email';
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS contacts_audit_update ON contacts;

CREATE TRIGGER contacts_audit_update
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION contacts_audit_trigger();

-- Create audit trigger for inserts
CREATE OR REPLACE FUNCTION contacts_audit_insert()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_by = auth.jwt()->>'email';
    NEW.updated_by = auth.jwt()->>'email';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS contacts_audit_insert ON contacts;

CREATE TRIGGER contacts_audit_insert
    BEFORE INSERT ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION contacts_audit_insert();

COMMENT ON COLUMN contacts.created_by IS 'Email of staff member who created this contact';
COMMENT ON COLUMN contacts.updated_by IS 'Email of staff member who last updated this contact';
COMMENT ON COLUMN contacts.deleted_at IS 'Timestamp when contact was soft-deleted (NULL = active)';
COMMENT ON COLUMN contacts.deleted_by IS 'Email of staff member who deleted this contact';

-- ============================================
-- STEP 7: ADMIN HELPER FUNCTIONS
-- ============================================

-- Function: Add staff member (admins only)
CREATE OR REPLACE FUNCTION add_staff_member(
    p_email TEXT,
    p_role TEXT DEFAULT 'staff',
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
    IF p_role NOT IN ('admin', 'staff') THEN
        RAISE EXCEPTION 'Role must be either admin or staff';
    END IF;

    -- Add staff member
    INSERT INTO staff_members (email, role, added_by, notes)
    VALUES (p_email, p_role, v_admin_email, p_notes);

    RETURN jsonb_build_object(
        'success', true,
        'email', p_email,
        'role', p_role,
        'added_by', v_admin_email
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION add_staff_member IS
'Adds a new staff member to the allowlist. Only callable by admins.
Usage: SELECT add_staff_member(''newstaff@example.com'', ''staff'', ''Marketing team'');';

-- Function: Deactivate staff member (soft delete)
CREATE OR REPLACE FUNCTION deactivate_staff_member(
    p_email TEXT
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
        RAISE EXCEPTION 'Only admins can deactivate staff members';
    END IF;

    -- Prevent self-deactivation
    IF p_email = v_admin_email THEN
        RAISE EXCEPTION 'Cannot deactivate yourself';
    END IF;

    -- Deactivate
    UPDATE staff_members
    SET active = false,
        deactivated_at = NOW(),
        deactivated_by = v_admin_email
    WHERE email = p_email;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Staff member not found: %', p_email;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'email', p_email,
        'deactivated_by', v_admin_email
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION deactivate_staff_member IS
'Deactivates a staff member (soft delete). Immediate access revocation.
Usage: SELECT deactivate_staff_member(''exstaff@example.com'');';

-- Function: Promote staff to admin
CREATE OR REPLACE FUNCTION promote_to_admin(
    p_email TEXT
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
        RAISE EXCEPTION 'Only admins can promote to admin';
    END IF;

    -- Promote
    UPDATE staff_members
    SET role = 'admin'
    WHERE email = p_email
    AND active = true;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Staff member not found or inactive: %', p_email;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'email', p_email,
        'role', 'admin',
        'promoted_by', v_admin_email
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION promote_to_admin IS
'Promotes a staff member to admin role. Only callable by existing admins.
Usage: SELECT promote_to_admin(''trusted@thestarhouse.org'');';

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION is_verified_staff TO authenticated;
GRANT EXECUTE ON FUNCTION add_staff_member TO authenticated;
GRANT EXECUTE ON FUNCTION deactivate_staff_member TO authenticated;
GRANT EXECUTE ON FUNCTION promote_to_admin TO authenticated;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these after migration to verify setup:

-- 1. Check your admin account exists:
--    SELECT * FROM staff_members WHERE role = 'admin';
--    Expected: Your email with role='admin'

-- 2. Test staff verification function:
--    SET ROLE authenticated;
--    SELECT is_verified_staff();
--    Expected: Returns true if your email is in staff_members

-- 3. Check RLS policies:
--    SELECT * FROM pg_policies WHERE tablename = 'contacts';
--    Expected: 4 policies with is_verified_staff() checks

-- 4. Test as staff:
--    SET ROLE authenticated;
--    SELECT COUNT(*) FROM contacts;  -- Should work
--    SELECT * FROM staff_members;    -- Should work
--    SELECT add_staff_member('test@example.com', 'staff');  -- Should fail if not admin
--    RESET ROLE;
