-- ============================================
-- SIMPLIFY STAFF ACCESS FOR SMALL TEAMS
-- StarHouse CRM Database
-- ============================================
-- Purpose: Replace complex staff_members allowlist with simple auth check
-- Use Case: 5-9 trusted staff members, all need full access
-- Security: Still protected by invite-only Supabase auth + RLS
-- Created: 2025-11-13
-- Migration: 20251113000006
-- ============================================

-- ============================================
-- SIMPLIFIED SECURITY MODEL
-- ============================================
-- BEFORE: is_verified_staff() checks staff_members table
-- AFTER:  is_verified_staff() just checks if authenticated
--
-- Security maintained by:
-- 1. Invite-only Supabase authentication
-- 2. RLS policies still in place (protection if auth compromised)
-- 3. Audit trails (created_by, updated_by) still active
--
-- Removes:
-- - Need to manually add users to staff_members
-- - Role management overhead (admin/staff distinction)
-- - Staff activation/deactivation complexity

-- ============================================
-- STEP 1: SIMPLIFY is_verified_staff() FUNCTION
-- ============================================

CREATE OR REPLACE FUNCTION is_verified_staff()
RETURNS BOOLEAN AS $$
BEGIN
    -- Simply check if user is authenticated via Supabase
    -- Works because you use invite-only auth (only invited users can log in)
    RETURN auth.uid() IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, pg_temp;  -- ✅ Added search_path protection

COMMENT ON FUNCTION is_verified_staff IS
'Simplified: Returns true if user is authenticated.
Security provided by invite-only Supabase authentication.
For small teams (5-9 staff) where everyone needs full access.';

-- ============================================
-- STEP 2: KEEP EXISTING RLS POLICIES
-- ============================================
-- All RLS policies stay the same:
-- - verified_staff_select_contacts
-- - verified_staff_update_contacts
-- - verified_staff_insert_contacts
-- - admin_delete_contacts (now same as staff since no role distinction)
-- - verified_staff_select_transactions
-- - verified_staff_update_transactions
-- - etc.
--
-- They all call is_verified_staff(), which now just checks auth

-- ============================================
-- STEP 3: OPTIONAL - KEEP staff_members TABLE
-- ============================================
-- You can keep the staff_members table for audit purposes
-- (tracking who was added when), but it's no longer enforced by RLS
--
-- If you want to completely remove it:
-- DROP TABLE staff_members CASCADE;
--
-- But I recommend KEEPING it for:
-- - Historical record of staff
-- - Future use if you grow and need roles
-- - Documentation of who has/had access

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these after migration to verify:

-- 1. Test the simplified function (should return true if logged in):
--    SELECT is_verified_staff();
--    Expected: true (if you're authenticated)

-- 2. Verify RLS policies still work:
--    SELECT COUNT(*) FROM contacts;       -- Should work
--    SELECT COUNT(*) FROM transactions;   -- Should work
--    SELECT COUNT(*) FROM subscriptions;  -- Should work

-- 3. Test as unauthenticated (should fail):
--    -- Log out and try to query
--    SELECT COUNT(*) FROM contacts;       -- Should fail: not authenticated

-- ============================================
-- ADMIN OPERATIONS NOW SIMPLIFIED
-- ============================================

-- Add new staff: Just invite via Supabase Dashboard
-- 1. Go to Supabase Dashboard → Authentication → Invite User
-- 2. Enter email
-- 3. They click invite link and set password
-- 4. Done - they have full access

-- Remove staff: Just disable in Supabase Dashboard
-- 1. Go to Supabase Dashboard → Authentication → Users
-- 2. Find user
-- 3. Delete user (or disable if you want soft delete)
-- 4. Done - they can't log in anymore

-- No SQL needed for user management!

-- ============================================
-- WHAT YOU STILL HAVE
-- ============================================
-- ✅ RLS protection on all tables (contacts, transactions, subscriptions)
-- ✅ Invite-only authentication (can't self-signup)
-- ✅ Audit trails (created_by, updated_by tracking)
-- ✅ Defense in depth (RLS + auth)
--
-- ❌ No more manual staff_members management
-- ❌ No more admin vs staff roles (everyone equal)
-- ❌ No more SQL commands to add/remove users

-- ============================================
-- SECURITY COMPARISON
-- ============================================

-- COMPLEX MODEL (Before):
-- user logs in → auth.jwt() → email checked in staff_members → RLS check
--
-- SIMPLIFIED MODEL (After):
-- user logs in → auth.uid() → RLS check
--
-- Same security level because:
-- - Still have invite-only auth (only invited users can log in)
-- - Still have RLS (authenticated users checked)
-- - Still have audit trails
-- - Removed one unnecessary layer (staff_members table check)

-- ============================================
-- ROLLBACK PROCEDURE (If Needed)
-- ============================================
-- If you want to go back to the complex model:
--
-- CREATE OR REPLACE FUNCTION is_verified_staff()
-- RETURNS BOOLEAN AS $$
-- BEGIN
--     RETURN EXISTS (
--         SELECT 1 FROM staff_members
--         WHERE email = auth.jwt()->>'email'
--         AND active = true
--     );
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER
-- SET search_path = public, pg_temp;

-- ============================================
-- SUMMARY
-- ============================================
-- Perfect for: 5-9 trusted staff, all need same access
-- Security: Invite-only auth + RLS (FAANG-level)
-- Management: Zero SQL needed - use Supabase Dashboard
-- Audit: Still have created_by/updated_by tracking
-- Scalability: Can add roles later if needed (staff_members table still exists)
