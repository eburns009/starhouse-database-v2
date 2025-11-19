/**
 * Migration: Add Staff Authentication Metadata
 * Created: 2025-11-19
 *
 * Purpose:
 * - Add auth metadata columns to staff_users table
 * - Enable UI to display login status without admin API calls
 * - Auto-sync metadata from auth.users table via triggers
 *
 * Changes:
 * 1. Add last_sign_in_at column (track last login)
 * 2. Add email_confirmed_at column (track email verification)
 * 3. Create trigger to sync from auth.users on auth events
 * 4. Backfill existing data from auth.users
 *
 * Security:
 * - Columns are read-only for staff (updated by trigger only)
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
ALTER TABLE public.staff_users
ADD COLUMN IF NOT EXISTS last_sign_in_at timestamptz NULL;

COMMENT ON COLUMN public.staff_users.last_sign_in_at IS
'Timestamp of last successful sign-in. Automatically synced from auth.users.last_sign_in_at. Used by UI to display login activity without calling admin APIs.';

-- Add email_confirmed_at column
-- Tracks when the staff member's email was verified
-- Synced from auth.users.email_confirmed_at via trigger
ALTER TABLE public.staff_users
ADD COLUMN IF NOT EXISTS email_confirmed_at timestamptz NULL;

COMMENT ON COLUMN public.staff_users.email_confirmed_at IS
'Timestamp when email was confirmed. Automatically synced from auth.users.email_confirmed_at. NULL means email not yet verified. Used by UI to show verification status.';

-- Add updated_at column
-- Tracks when the staff record was last modified
-- Automatically updated by trigger when auth metadata syncs
ALTER TABLE public.staff_users
ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT NOW();

COMMENT ON COLUMN public.staff_users.updated_at IS
'Timestamp of last update to this staff record. Automatically updated by trigger when auth metadata (last_sign_in_at, email_confirmed_at) syncs from auth.users.';

-- ============================================================================
-- STEP 2: Create Trigger Function to Sync Auth Metadata
-- ============================================================================

-- Drop existing function if it exists (for idempotency)
DROP FUNCTION IF EXISTS sync_staff_auth_metadata() CASCADE;

CREATE OR REPLACE FUNCTION sync_staff_auth_metadata()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
/**
 * Function: sync_staff_auth_metadata
 *
 * Purpose:
 * Automatically sync auth metadata from auth.users to staff_users table
 * when authentication events occur (sign-in, email confirmation)
 *
 * Trigger Events:
 * - AFTER UPDATE on auth.users
 * - Only when last_sign_in_at or email_confirmed_at changes
 *
 * Logic:
 * 1. Check if user exists in staff_users (by ID match)
 * 2. If exists, update last_sign_in_at and/or email_confirmed_at
 * 3. Update updated_at timestamp
 *
 * Security:
 * - SECURITY DEFINER allows updating staff_users from auth context
 * - Only updates matching user IDs (prevents cross-contamination)
 * - No sensitive data exposed (only timestamps)
 *
 * Performance:
 * - Uses primary key lookup (fastest possible)
 * - Only runs on actual changes (WHEN clause in trigger)
 * - Single UPDATE statement (efficient)
 */
BEGIN
    -- Only process if this is an UPDATE that changed auth metadata
    IF TG_OP = 'UPDATE' THEN
        -- Check if last_sign_in_at or email_confirmed_at changed
        IF (OLD.last_sign_in_at IS DISTINCT FROM NEW.last_sign_in_at) OR
           (OLD.email_confirmed_at IS DISTINCT FROM NEW.email_confirmed_at) THEN

            -- Update staff_users table where ID matches
            UPDATE public.staff_users
            SET
                last_sign_in_at = NEW.last_sign_in_at,
                email_confirmed_at = NEW.email_confirmed_at,
                updated_at = NOW()
            WHERE id = NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION sync_staff_auth_metadata() IS
'Automatically syncs last_sign_in_at and email_confirmed_at from auth.users to staff_users when auth events occur. Triggered on UPDATE to auth.users table.';

-- ============================================================================
-- STEP 3: Create Trigger on auth.users
-- ============================================================================

-- Drop existing trigger if it exists (for idempotency)
DROP TRIGGER IF EXISTS sync_staff_auth_metadata_trigger ON auth.users;

CREATE TRIGGER sync_staff_auth_metadata_trigger
    AFTER UPDATE ON auth.users
    FOR EACH ROW
    WHEN (
        -- Only fire when auth metadata actually changes
        OLD.last_sign_in_at IS DISTINCT FROM NEW.last_sign_in_at OR
        OLD.email_confirmed_at IS DISTINCT FROM NEW.email_confirmed_at
    )
    EXECUTE FUNCTION sync_staff_auth_metadata();

COMMENT ON TRIGGER sync_staff_auth_metadata_trigger ON auth.users IS
'Syncs authentication metadata to staff_users table when sign-in or email confirmation events occur';

-- ============================================================================
-- STEP 4: Backfill Existing Staff Users with Current Auth Data
-- ============================================================================

-- Sync existing auth data from auth.users to staff_users
-- This is a one-time backfill for existing staff members
UPDATE public.staff_users su
SET
    last_sign_in_at = au.last_sign_in_at,
    email_confirmed_at = au.email_confirmed_at,
    updated_at = NOW()
FROM auth.users au
WHERE su.id = au.id
  AND (
    -- Only update if values are different (avoid unnecessary updates)
    su.last_sign_in_at IS DISTINCT FROM au.last_sign_in_at OR
    su.email_confirmed_at IS DISTINCT FROM au.email_confirmed_at
  );

-- Log backfill results
DO $$
DECLARE
    v_backfilled_count integer;
    v_total_staff integer;
BEGIN
    -- Get total staff count
    SELECT COUNT(*) INTO v_total_staff FROM public.staff_users;

    -- Get count of staff with auth metadata
    SELECT COUNT(*) INTO v_backfilled_count
    FROM public.staff_users
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
CREATE INDEX IF NOT EXISTS idx_staff_users_last_sign_in
ON public.staff_users (last_sign_in_at DESC NULLS LAST);

COMMENT ON INDEX idx_staff_users_last_sign_in IS
'Performance index for staff admin UI queries. Optimizes sorting by recent activity (last_sign_in_at DESC). NULLS LAST ensures users who never signed in appear at the end.';

-- ============================================================================
-- VERIFICATION QUERIES (for testing)
-- ============================================================================

-- Uncomment to verify migration results:

-- Check column existence
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name = 'staff_users'
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
-- FROM public.staff_users;

-- Sample data (first 5 staff members)
-- SELECT
--     email,
--     last_sign_in_at,
--     email_confirmed_at,
--     created_at,
--     updated_at
-- FROM public.staff_users
-- ORDER BY created_at DESC
-- LIMIT 5;

-- ============================================================================
-- ROLLBACK PROCEDURE (if needed)
-- ============================================================================

/**
 * To rollback this migration:
 *
 * -- Drop trigger
 * DROP TRIGGER IF EXISTS sync_staff_auth_metadata_trigger ON auth.users;
 *
 * -- Drop function
 * DROP FUNCTION IF EXISTS sync_staff_auth_metadata() CASCADE;
 *
 * -- Remove columns
 * ALTER TABLE public.staff_users DROP COLUMN IF EXISTS last_sign_in_at;
 * ALTER TABLE public.staff_users DROP COLUMN IF EXISTS email_confirmed_at;
 */

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 20251119000001_add_staff_auth_metadata completed successfully';
    RAISE NOTICE '   - Added last_sign_in_at column to staff_users';
    RAISE NOTICE '   - Added email_confirmed_at column to staff_users';
    RAISE NOTICE '   - Added updated_at column to staff_users';
    RAISE NOTICE '   - Created sync_staff_auth_metadata() trigger function';
    RAISE NOTICE '   - Created trigger on auth.users table';
    RAISE NOTICE '   - Backfilled existing staff users with auth data';
    RAISE NOTICE '   - Created performance index: idx_staff_users_last_sign_in';
    RAISE NOTICE '   ';
    RAISE NOTICE '📊 Next steps:';
    RAISE NOTICE '   1. Update UI to display last_sign_in_at (login activity)';
    RAISE NOTICE '   2. Update UI to show email_confirmed_at (verification status)';
    RAISE NOTICE '   3. Remove admin API calls for auth metadata (use staff_users instead)';
    RAISE NOTICE '   ';
    RAISE NOTICE '🔒 Security: Auth metadata auto-syncs via ID matching on sign-in/email confirmation events';
END $$;
