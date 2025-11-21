/**
 * Migration: Refactor staff_members to use UUID Primary Key
 * Created: 2025-11-20
 *
 * Purpose:
 * - Change primary key from email (TEXT) to id (UUID)
 * - Link staff_members to auth.users via foreign key
 * - Follow FAANG standards (immutable PK, referential integrity)
 *
 * Why This Change:
 * - Email is a mutable field (users can change email)
 * - UUID provides stable identity across email changes
 * - Enables proper foreign key to auth.users
 * - Better performance for joins (UUID vs TEXT comparison)
 *
 * Changes:
 * 1. Add id UUID column
 * 2. Populate id from auth.users where email matches
 * 3. Make id the PRIMARY KEY
 * 4. Keep email as UNIQUE NOT NULL
 * 5. Add foreign key to auth.users(id)
 * 6. Update indexes
 *
 * Security:
 * - RLS policies continue to work (they check email via auth.jwt())
 * - Foreign key ensures data integrity
 * - CASCADE delete keeps data consistent
 *
 * FAANG Standards:
 * - Immutable primary key (UUID)
 * - Referential integrity (FK to auth.users)
 * - Idempotent (safe to run multiple times)
 * - Zero data loss
 * - Includes rollback procedure
 */

-- ============================================================================
-- PRE-FLIGHT CHECKS
-- ============================================================================

-- Check if migration already completed (idempotency)
DO $$
BEGIN
    -- Check if id column already exists and is primary key
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'staff_members'
        AND column_name = 'id'
        AND data_type = 'uuid'
    ) AND EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'staff_members'::regclass
        AND contype = 'p'
        AND conname = 'staff_members_pkey'
        AND pg_get_constraintdef(oid) LIKE '%id%'
    ) THEN
        RAISE NOTICE '✅ Migration already completed - staff_members.id is already PRIMARY KEY';
        -- We'll still run through to ensure all constraints are correct
    ELSE
        RAISE NOTICE '🔄 Starting migration: Refactoring staff_members to UUID primary key';
    END IF;
END $$;

-- ============================================================================
-- STEP 1: Add id UUID Column (if not exists)
-- ============================================================================

-- Add id column as nullable initially
ALTER TABLE public.staff_members
ADD COLUMN IF NOT EXISTS id UUID NULL;

COMMENT ON COLUMN public.staff_members.id IS
'Primary key linking to auth.users.id. Provides stable identity even if email changes.';

DO $$ BEGIN RAISE NOTICE 'Step 1: Added id UUID column (nullable)'; END $$;

-- ============================================================================
-- STEP 2: Populate id from auth.users
-- ============================================================================

-- Update staff_members.id from auth.users where email matches
UPDATE public.staff_members sm
SET id = au.id
FROM auth.users au
WHERE sm.email = au.email
  AND sm.id IS NULL;  -- Only update if not already set

-- Verify all staff members got an id
DO $$
DECLARE
    v_null_count integer;
    v_total_count integer;
    v_orphan_emails text;
BEGIN
    -- Count staff without id
    SELECT COUNT(*) INTO v_null_count
    FROM public.staff_members
    WHERE id IS NULL;

    -- Get total count
    SELECT COUNT(*) INTO v_total_count
    FROM public.staff_members;

    IF v_null_count > 0 THEN
        -- Get list of orphaned emails
        SELECT string_agg(email, ', ') INTO v_orphan_emails
        FROM public.staff_members
        WHERE id IS NULL;

        RAISE EXCEPTION 'MIGRATION FAILED: % of % staff members have no matching auth.users entry. Orphaned emails: %',
            v_null_count, v_total_count, v_orphan_emails;
    END IF;

    RAISE NOTICE 'Step 2: Populated id for all % staff members from auth.users', v_total_count;
END $$;

-- ============================================================================
-- STEP 3: Make id NOT NULL
-- ============================================================================

ALTER TABLE public.staff_members
ALTER COLUMN id SET NOT NULL;

DO $$ BEGIN RAISE NOTICE 'Step 3: Made id column NOT NULL'; END $$;

-- ============================================================================
-- STEP 4: Drop old PRIMARY KEY on email
-- ============================================================================

-- Drop the old primary key constraint
-- First, find and drop it (handles different constraint names)
DO $$
DECLARE
    v_constraint_name text;
BEGIN
    -- Find the primary key constraint name
    SELECT conname INTO v_constraint_name
    FROM pg_constraint
    WHERE conrelid = 'staff_members'::regclass
    AND contype = 'p';

    IF v_constraint_name IS NOT NULL THEN
        -- Check if it's on email (old) or id (new)
        IF EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
            WHERE c.conrelid = 'staff_members'::regclass
            AND c.contype = 'p'
            AND a.attname = 'email'
        ) THEN
            EXECUTE 'ALTER TABLE public.staff_members DROP CONSTRAINT ' || v_constraint_name;
            RAISE NOTICE 'Step 4: Dropped old PRIMARY KEY on email (constraint: %)', v_constraint_name;
        ELSE
            RAISE NOTICE 'Step 4: PRIMARY KEY already on id, skipping drop';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- STEP 5: Add new PRIMARY KEY on id
-- ============================================================================

-- Add primary key on id (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'staff_members'::regclass
        AND contype = 'p'
    ) THEN
        ALTER TABLE public.staff_members
        ADD CONSTRAINT staff_members_pkey PRIMARY KEY (id);
        RAISE NOTICE 'Step 5: Added PRIMARY KEY on id';
    ELSE
        RAISE NOTICE 'Step 5: PRIMARY KEY already exists, skipping';
    END IF;
END $$;

-- ============================================================================
-- STEP 6: Add UNIQUE constraint on email
-- ============================================================================

-- Ensure email remains unique
-- Using DO block to handle gracefully (idempotent)
DO $$
BEGIN
    BEGIN
        ALTER TABLE public.staff_members
        ADD CONSTRAINT staff_members_email_key UNIQUE (email);
        RAISE NOTICE 'Step 6: Added UNIQUE constraint on email';
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Step 6: UNIQUE constraint on email already exists, skipping';
    END;
END $$;

-- ============================================================================
-- STEP 7: Add Foreign Key to auth.users
-- ============================================================================

-- Add foreign key with CASCADE delete
-- This ensures staff_members are deleted when auth user is deleted
DO $$
BEGIN
    BEGIN
        ALTER TABLE public.staff_members
        ADD CONSTRAINT staff_members_id_fkey
        FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
        RAISE NOTICE 'Step 7: Added FOREIGN KEY to auth.users(id) with CASCADE delete';
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Step 7: FOREIGN KEY to auth.users already exists, skipping';
    END;
END $$;

COMMENT ON CONSTRAINT staff_members_id_fkey ON public.staff_members IS
'Links staff member to Supabase auth user. CASCADE delete removes staff when auth user is deleted.';

-- ============================================================================
-- STEP 8: Update Indexes
-- ============================================================================

-- Create index on email for fast lookups (RLS policies use email)
CREATE INDEX IF NOT EXISTS idx_staff_members_email
ON public.staff_members (email);

COMMENT ON INDEX idx_staff_members_email IS
'Performance index for RLS policy lookups by email. Critical for auth.jwt()->>"email" checks.';

-- Note: id is already indexed as PRIMARY KEY

DO $$ BEGIN RAISE NOTICE 'Step 8: Created index on email for RLS policy performance'; END $$;

-- ============================================================================
-- STEP 9: Update refresh_staff_auth_metadata function
-- ============================================================================

-- Update the function to use id instead of email for the join
-- This is more efficient and correct now that we have the FK relationship
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
 * Now uses id join (more efficient than email).
 *
 * Usage:
 * SELECT * FROM refresh_staff_auth_metadata();
 */
DECLARE
    v_synced integer;
    v_total integer;
BEGIN
    -- Sync auth metadata from auth.users to staff_members
    -- Join by id (foreign key) for better performance
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
'Syncs last_sign_in_at and email_confirmed_at from auth.users to staff_members. Uses id join for performance.';

DO $$ BEGIN RAISE NOTICE 'Step 9: Updated refresh_staff_auth_metadata() to use id join'; END $$;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these to verify migration success:

-- 1. Check new table structure
-- \d staff_members

-- 2. Verify primary key is on id
-- SELECT conname, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'staff_members'::regclass
-- AND contype = 'p';

-- 3. Verify foreign key to auth.users
-- SELECT conname, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'staff_members'::regclass
-- AND contype = 'f';

-- 4. Verify all staff have valid ids
-- SELECT sm.email, sm.id, au.id as auth_id
-- FROM staff_members sm
-- JOIN auth.users au ON sm.id = au.id;

-- 5. Check constraints
-- SELECT conname, contype, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'staff_members'::regclass
-- ORDER BY contype;

-- ============================================================================
-- ROLLBACK PROCEDURE (if needed)
-- ============================================================================

/**
 * To rollback this migration (DESTRUCTIVE - use with caution):
 *
 * -- Step 1: Drop foreign key
 * ALTER TABLE public.staff_members DROP CONSTRAINT IF EXISTS staff_members_id_fkey;
 *
 * -- Step 2: Drop primary key on id
 * ALTER TABLE public.staff_members DROP CONSTRAINT IF EXISTS staff_members_pkey;
 *
 * -- Step 3: Add primary key back on email
 * ALTER TABLE public.staff_members ADD PRIMARY KEY (email);
 *
 * -- Step 4: Drop unique constraint on email (now it's PK)
 * ALTER TABLE public.staff_members DROP CONSTRAINT IF EXISTS staff_members_email_key;
 *
 * -- Step 5: Drop id column
 * ALTER TABLE public.staff_members DROP COLUMN IF EXISTS id;
 *
 * -- Step 6: Drop email index (PK handles it)
 * DROP INDEX IF EXISTS idx_staff_members_email;
 *
 * -- Step 7: Revert refresh_staff_auth_metadata to use email join
 * -- (copy from previous version)
 *
 * WARNING: This rollback will:
 * - Remove the auth.users relationship
 * - Lose the UUID identifiers
 * - Require updating any code that uses staff_members.id
 */

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
DECLARE
    v_staff_count integer;
BEGIN
    SELECT COUNT(*) INTO v_staff_count FROM public.staff_members;

    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '✅ Migration 20251120000001 completed successfully!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Summary:';
    RAISE NOTICE '   - Refactored % staff members to UUID primary key', v_staff_count;
    RAISE NOTICE '   - Added foreign key to auth.users(id)';
    RAISE NOTICE '   - Email remains UNIQUE NOT NULL';
    RAISE NOTICE '   - RLS policies continue to work (use email from JWT)';
    RAISE NOTICE '   - Updated refresh_staff_auth_metadata() to use id join';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 FAANG Standards Achieved:';
    RAISE NOTICE '   - Immutable primary key (UUID)';
    RAISE NOTICE '   - Referential integrity (FK to auth.users)';
    RAISE NOTICE '   - CASCADE delete (staff removed when auth user deleted)';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Next Steps:';
    RAISE NOTICE '   1. Update application code to use id instead of email for lookups';
    RAISE NOTICE '   2. Update any APIs that return staff_members to include id';
    RAISE NOTICE '   3. Consider updating RLS policies to use id (optional - email still works)';
    RAISE NOTICE '';
END $$;
