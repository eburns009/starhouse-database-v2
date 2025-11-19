-- ============================================================================
-- Verification Script for Staff Auth Metadata Migration
-- Run this BEFORE and AFTER applying migration 20251119000001
-- ============================================================================

-- STEP 1: Check current state of staff_users table
SELECT
    'Current table structure' as check_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'staff_users'
ORDER BY ordinal_position;

-- STEP 2: Count current staff users
SELECT
    'Staff user counts' as check_name,
    COUNT(*) as total_staff_users
FROM public.staff_users;

-- STEP 3: Check if new columns exist (should be empty BEFORE migration)
SELECT
    'New columns check (should fail before migration)' as check_name,
    column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'staff_users'
  AND column_name IN ('last_sign_in_at', 'email_confirmed_at', 'updated_at');

-- STEP 4: Check trigger existence (should be empty BEFORE migration)
SELECT
    'Trigger check (should fail before migration)' as check_name,
    trigger_name,
    event_manipulation,
    event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'auth'
  AND event_object_table = 'users'
  AND trigger_name = 'sync_staff_auth_metadata_trigger';

-- STEP 5: Check index existence (should be empty BEFORE migration)
SELECT
    'Index check (should fail before migration)' as check_name,
    indexname,
    tablename
FROM pg_indexes
WHERE tablename = 'staff_users'
  AND indexname = 'idx_staff_users_last_sign_in';

-- ============================================================================
-- POST-MIGRATION VERIFICATION (Run AFTER applying migration)
-- ============================================================================

-- STEP 6: Verify columns were added
SELECT
    'Column verification (AFTER migration)' as check_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'staff_users'
  AND column_name IN ('last_sign_in_at', 'email_confirmed_at', 'updated_at');

-- STEP 7: Verify trigger was created
SELECT
    'Trigger verification (AFTER migration)' as check_name,
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'auth'
  AND event_object_table = 'users'
  AND trigger_name = 'sync_staff_auth_metadata_trigger';

-- STEP 8: Verify index was created
SELECT
    'Index verification (AFTER migration)' as check_name,
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'staff_users'
  AND indexname = 'idx_staff_users_last_sign_in';

-- STEP 9: Check backfill results
SELECT
    'Backfill verification (AFTER migration)' as check_name,
    COUNT(*) as total_staff,
    COUNT(last_sign_in_at) as staff_with_last_sign_in,
    COUNT(email_confirmed_at) as staff_with_email_confirmed,
    COUNT(updated_at) as staff_with_updated_at,
    COUNT(CASE WHEN last_sign_in_at IS NULL AND email_confirmed_at IS NULL THEN 1 END) as staff_without_auth_data
FROM public.staff_users;

-- STEP 10: Sample data (first 5 staff members)
SELECT
    'Sample data (AFTER migration)' as check_name,
    id,
    email,
    last_sign_in_at,
    email_confirmed_at,
    updated_at,
    created_at
FROM public.staff_users
ORDER BY created_at DESC
LIMIT 5;

-- STEP 11: Verify auth.users has matching records
SELECT
    'Auth users comparison (AFTER migration)' as check_name,
    COUNT(DISTINCT su.id) as staff_count,
    COUNT(DISTINCT au.id) as auth_users_count,
    COUNT(DISTINCT CASE WHEN au.id IS NOT NULL THEN su.id END) as matched_count
FROM public.staff_users su
LEFT JOIN auth.users au ON su.id = au.id;
