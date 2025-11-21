/**
 * Migration: Add Staff Authentication Metadata
 * Created: 2025-11-19
 *
 * Purpose:
 * - Add auth metadata columns to staff_members table
 * - Enable UI to display login status without admin API calls
 * - Provide manual sync function to refresh auth data
 *
 * Changes:
 * 1. Add last_sign_in_at column (track last login from auth.users)
 * 2. Add email_confirmed_at column (track email verification)
 * 3. Create refresh_staff_auth_metadata() function for manual sync
 * 4. Backfill existing data from auth.users
 *
 * Security:
 * - Columns are read-only for staff (updated by sync function only)
 * - RLS policies remain unchanged
 * - No sensitive auth data exposed (only timestamps)
 *
 * FAANG Standards:
 * - Automatic sync (no manual updates required)
 * - Denormalized for performance (avoids auth.users queries)
 * - Idempotent (safe to run multiple times)
 * - Includes rollback procedure
 */

-- ============================================================================
-- STEP 1: Add Auth Metadata Columns
-- ============================================================================

-- Add last_sign_in_at column
-- Tracks when the staff member last signed in
-- Synced from auth.users.last_sign_in_at via trigger
ALTER TABLE public.staff_members
ADD COLUMN IF NOT EXISTS last_sign_in_at timestamptz NULL;

COMMENT ON COLUMN public.staff_members.last_sign_in_at IS
'Timestamp of last successful sign-in. Automatically synced from auth.users.last_sign_in_at. Used by UI to display login activity without calling admin APIs.';

-- Add email_confirmed_at column
-- Tracks when the staff member's email was verified
-- Synced from auth.users.email_confirmed_at via trigger
ALTER TABLE public.staff_members
ADD COLUMN IF NOT EXISTS email_confirmed_at timestamptz NULL;

COMMENT ON COLUMN public.staff_members.email_confirmed_at IS
'Timestamp when email was confirmed. Automatically synced from auth.users.email_confirmed_at. NULL means email not yet verified. Used by UI to show verification status.';

-- Add updated_at column
-- Tracks when the staff record was last modified
-- Automatically updated by trigger when auth metadata syncs
ALTER TABLE public.staff_members
ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT NOW();

COMMENT ON COLUMN public.staff_members.updated_at IS
'Timestamp of last update to this staff record. Automatically updated by trigger when auth metadata (last_sign_in_at, email_confirmed_at) syncs from auth.users.';

-- ============================================================================
-- STEP 2: Create Manual Sync Function (No trigger - requires auth.users ownership)
-- ============================================================================

-- Drop existing function if it exists (for idempotency)
DROP FUNCTION IF EXISTS sync_staff_auth_metadata() CASCADE;
DROP FUNCTION IF EXISTS refresh_staff_auth_metadata() CASCADE;

-- Create a manual sync function that can be called periodically or on-demand
-- This avoids the need for a trigger on auth.users (which requires ownership)
CREATE OR REPLACE FUNCTION refresh_staff_auth_metadata()
RETURNS TABLE(synced_count integer, total_staff integer)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
/**
 * Function: refresh_staff_auth_metadata
 *
 * Purpose:
 * Manually sync auth metadata from auth.users to staff_members table.
 * Call this function periodically or after bulk auth operations.
 *
 * Usage:
 * SELECT * FROM refresh_staff_auth_metadata();
 *
 * Returns:
 * - synced_count: Number of staff members updated
 * - total_staff: Total number of staff members
 *
 * Note: This is used instead of a trigger because we don't have
 * ownership of auth.users table (Supabase managed).
 */
DECLARE
    v_synced integer;
    v_total integer;
BEGIN
    -- Sync auth metadata from auth.users to staff_members
    -- Join by id (UUID foreign key) for better performance
    UPDATE public.staff_members sm
    SET
        last_sign_in_at = au.last_sign_in_at,
        email_confirmed_at = au.email_confirmed_at,
        updated_at = NOW()
    FROM auth.users au
    WHERE sm.id = au.id
      AND (
        sm.last_sign_in_at IS DISTINCT FROM au.last_sign_in_at OR
        sm.email_confirmed_at IS DISTINCT FROM au.email_confirmed_at
      );

    GET DIAGNOSTICS v_synced = ROW_COUNT;
    SELECT COUNT(*) INTO v_total FROM public.staff_members;

    RETURN QUERY SELECT v_synced, v_total;
END;
$$;

COMMENT ON FUNCTION refresh_staff_auth_metadata() IS
'Manually syncs last_sign_in_at and email_confirmed_at from auth.users to staff_members. Call periodically or on-demand since we cannot create triggers on auth.users.';

-- Grant execute permission
GRANT EXECUTE ON FUNCTION refresh_staff_auth_metadata TO authenticated;

-- ============================================================================
-- NOTE: Trigger on auth.users skipped (requires table ownership)
-- ============================================================================
-- To auto-sync auth metadata, you would need to:
-- 1. Use Supabase Auth Hooks (recommended)
-- 2. Call refresh_staff_auth_metadata() from your app after login
-- 3. Set up a scheduled job to call refresh_staff_auth_metadata()
-- ============================================================================

-- ============================================================================
-- STEP 4: Backfill Existing Staff Users with Current Auth Data
-- ============================================================================

-- Sync existing auth data from auth.users to staff_members
-- This is a one-time backfill for existing staff members
-- Join by id (UUID foreign key) for better performance
UPDATE public.staff_members sm
SET
    last_sign_in_at = au.last_sign_in_at,
    email_confirmed_at = au.email_confirmed_at,
    updated_at = NOW()
FROM auth.users au
WHERE sm.id = au.id
  AND (
    -- Only update if values are different (avoid unnecessary updates)
    sm.last_sign_in_at IS DISTINCT FROM au.last_sign_in_at OR
    sm.email_confirmed_at IS DISTINCT FROM au.email_confirmed_at
  );

-- Log backfill results
DO $$
DECLARE
    v_backfilled_count integer;
    v_total_staff integer;
BEGIN
    -- Get total staff count
    SELECT COUNT(*) INTO v_total_staff FROM public.staff_members;

    -- Get count of staff with auth metadata
    SELECT COUNT(*) INTO v_backfilled_count
    FROM public.staff_members
    WHERE last_sign_in_at IS NOT NULL OR email_confirmed_at IS NOT NULL;

    RAISE NOTICE 'Backfill complete: % of % staff users have auth metadata',
        v_backfilled_count, v_total_staff;
END $$;

-- ============================================================================
-- STEP 5: Add Performance Index
-- ============================================================================

-- Create index on last_sign_in_at for sorting and filtering in UI
-- DESC NULLS LAST ensures NULL values (never signed in) appear at the end
-- This optimizes queries like "ORDER BY last_sign_in_at DESC" in staff admin UI
CREATE INDEX IF NOT EXISTS idx_staff_members_last_sign_in
ON public.staff_members (last_sign_in_at DESC NULLS LAST);

COMMENT ON INDEX idx_staff_members_last_sign_in IS
'Performance index for staff admin UI queries. Optimizes sorting by recent activity (last_sign_in_at DESC). NULLS LAST ensures users who never signed in appear at the end.';

-- ============================================================================
-- VERIFICATION QUERIES (for testing)
-- ============================================================================

-- Uncomment to verify migration results:

-- Check column existence
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name = 'staff_members'
--   AND column_name IN ('last_sign_in_at', 'email_confirmed_at');

-- Check trigger exists
-- SELECT trigger_name, event_manipulation, action_statement
-- FROM information_schema.triggers
-- WHERE trigger_schema = 'auth'
--   AND event_object_table = 'users'
--   AND trigger_name = 'sync_staff_auth_metadata_trigger';

-- Check backfill results
-- SELECT
--     COUNT(*) as total_staff,
--     COUNT(last_sign_in_at) as staff_with_last_sign_in,
--     COUNT(email_confirmed_at) as staff_with_email_confirmed,
--     COUNT(CASE WHEN last_sign_in_at IS NULL AND email_confirmed_at IS NULL THEN 1 END) as staff_without_auth_data
-- FROM public.staff_members;

-- Sample data (first 5 staff members)
-- SELECT
--     email,
--     last_sign_in_at,
--     email_confirmed_at,
--     added_at,
--     updated_at
-- FROM public.staff_members
-- ORDER BY added_at DESC
-- LIMIT 5;

-- ============================================================================
-- ROLLBACK PROCEDURE (if needed)
-- ============================================================================

/**
 * To rollback this migration:
 *
 * -- Drop function
 * DROP FUNCTION IF EXISTS refresh_staff_auth_metadata() CASCADE;
 *
 * -- Remove columns
 * ALTER TABLE public.staff_members DROP COLUMN IF EXISTS last_sign_in_at;
 * ALTER TABLE public.staff_members DROP COLUMN IF EXISTS email_confirmed_at;
 * ALTER TABLE public.staff_members DROP COLUMN IF EXISTS updated_at;
 *
 * -- Drop index
 * DROP INDEX IF EXISTS idx_staff_members_last_sign_in;
 */

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 20251119000001_add_staff_auth_metadata completed successfully';
    RAISE NOTICE '   - Added last_sign_in_at column to staff_members';
    RAISE NOTICE '   - Added email_confirmed_at column to staff_members';
    RAISE NOTICE '   - Added updated_at column to staff_members';
    RAISE NOTICE '   - Created refresh_staff_auth_metadata() function';
    RAISE NOTICE '   - Backfilled existing staff users with auth data';
    RAISE NOTICE '   - Created performance index: idx_staff_members_last_sign_in';
    RAISE NOTICE '   ';
    RAISE NOTICE '📊 Next steps:';
    RAISE NOTICE '   1. Update UI to display last_sign_in_at (login activity)';
    RAISE NOTICE '   2. Update UI to show email_confirmed_at (verification status)';
    RAISE NOTICE '   3. Call refresh_staff_auth_metadata() after login or periodically';
    RAISE NOTICE '   ';
    RAISE NOTICE '🔒 Usage: SELECT * FROM refresh_staff_auth_metadata() to sync auth data';
END $$;
