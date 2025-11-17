-- ============================================================================
-- TEST SCRIPT: Three-Tier Staff Roles Migration
-- ============================================================================
-- Purpose: Verify migration 20251117000001 works correctly
-- Run this AFTER applying the migration
-- ============================================================================

-- Test 1: Verify new columns exist
SELECT 'Test 1: New columns' AS test;
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'staff_members'
AND column_name IN ('display_name', 'last_login_at')
ORDER BY column_name;
-- Expected: Both columns present, nullable

-- Test 2: Verify role constraint updated
SELECT 'Test 2: Role constraint' AS test;
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname = 'staff_members_role_check';
-- Expected: CHECK includes 'admin', 'staff', 'full_user', 'read_only'

-- Test 3: Verify no 'staff' roles remain (all migrated to 'full_user')
SELECT 'Test 3: Role migration' AS test;
SELECT role, COUNT(*) as count
FROM staff_members
GROUP BY role
ORDER BY role;
-- Expected: No 'staff' role, 'full_user' present

-- Test 4: Verify helper functions exist
SELECT 'Test 4: Helper functions' AS test;
SELECT
    routine_name,
    routine_type,
    data_type AS return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN ('is_admin', 'can_edit', 'get_user_role', 'change_staff_role')
ORDER BY routine_name;
-- Expected: All 4 functions present

-- Test 5: Verify RLS policies updated
SELECT 'Test 5: RLS policies on contacts' AS test;
SELECT
    tablename,
    policyname,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'contacts'
ORDER BY policyname;
-- Expected: staff_read_contacts, staff_update_contacts, staff_insert_contacts, admin_delete_contacts

-- Test 6: Verify RLS policies on all tables
SELECT 'Test 6: RLS policy count by table' AS test;
SELECT
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('contacts', 'tags', 'products', 'transactions', 'subscriptions', 'staff_members')
GROUP BY tablename
ORDER BY tablename;
-- Expected: Each table has appropriate policies

-- Test 7: Verify index created
SELECT 'Test 7: Performance indexes' AS test;
SELECT
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname = 'idx_staff_members_last_login';
-- Expected: Index on last_login_at DESC WHERE active = true

-- ============================================================================
-- FUNCTIONAL TESTS (Run as authenticated user)
-- ============================================================================

-- Test 8: Test is_admin() function
SELECT 'Test 8: is_admin()' AS test;
SELECT is_admin() AS result;
-- Expected: true if you're admin, false otherwise

-- Test 9: Test can_edit() function
SELECT 'Test 9: can_edit()' AS test;
SELECT can_edit() AS result;
-- Expected: true if admin or full_user, false if read_only

-- Test 10: Test get_user_role() function
SELECT 'Test 10: get_user_role()' AS test;
SELECT get_user_role() AS result;
-- Expected: 'admin', 'full_user', 'read_only', or 'none'

-- ============================================================================
-- SUMMARY
-- ============================================================================
SELECT 'Migration test complete!' AS summary;
SELECT
    'staff_members' AS table_name,
    (SELECT COUNT(*) FROM staff_members) AS total_staff,
    (SELECT COUNT(*) FROM staff_members WHERE role = 'admin') AS admins,
    (SELECT COUNT(*) FROM staff_members WHERE role = 'full_user') AS full_users,
    (SELECT COUNT(*) FROM staff_members WHERE role = 'read_only') AS read_only_users,
    (SELECT COUNT(*) FROM staff_members WHERE active = true) AS active_staff;
