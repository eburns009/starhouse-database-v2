-- ============================================================================
-- Trigger Functionality Test Script
-- Tests that auth metadata syncs correctly from auth.users to staff_users
-- ============================================================================

-- BEFORE TEST: Capture current state
SELECT
    'BEFORE TEST - Current staff user state' as test_stage,
    id,
    email,
    last_sign_in_at,
    email_confirmed_at,
    updated_at
FROM public.staff_users
WHERE email = 'YOUR_TEST_EMAIL_HERE'  -- Replace with actual test email
LIMIT 1;

-- Note: At this point, sign in via the UI or Supabase Auth
-- Then wait 5 seconds and run the AFTER TEST query below

-- AFTER TEST: Check if data synced
SELECT
    'AFTER TEST - Updated staff user state' as test_stage,
    id,
    email,
    last_sign_in_at,
    email_confirmed_at,
    updated_at,
    -- Calculate time since last update
    EXTRACT(EPOCH FROM (NOW() - updated_at)) as seconds_since_update
FROM public.staff_users
WHERE email = 'YOUR_TEST_EMAIL_HERE'  -- Replace with actual test email
LIMIT 1;

-- DETAILED COMPARISON: Show auth.users vs staff_users
SELECT
    'DETAILED COMPARISON - auth.users vs staff_users' as test_stage,
    au.id,
    au.email,
    au.last_sign_in_at as auth_last_sign_in,
    su.last_sign_in_at as staff_last_sign_in,
    au.email_confirmed_at as auth_email_confirmed,
    su.email_confirmed_at as staff_email_confirmed,
    -- Check if they match
    CASE
        WHEN au.last_sign_in_at = su.last_sign_in_at THEN '✅ MATCH'
        WHEN au.last_sign_in_at IS NULL AND su.last_sign_in_at IS NULL THEN '✅ BOTH NULL'
        ELSE '❌ MISMATCH'
    END as last_sign_in_match,
    CASE
        WHEN au.email_confirmed_at = su.email_confirmed_at THEN '✅ MATCH'
        WHEN au.email_confirmed_at IS NULL AND su.email_confirmed_at IS NULL THEN '✅ BOTH NULL'
        ELSE '❌ MISMATCH'
    END as email_confirmed_match
FROM auth.users au
JOIN public.staff_users su ON au.id = su.id
WHERE au.email = 'YOUR_TEST_EMAIL_HERE'  -- Replace with actual test email
LIMIT 1;

-- TRIGGER DIAGNOSTICS: Check if trigger exists and is enabled
SELECT
    'TRIGGER DIAGNOSTICS' as test_stage,
    trigger_name,
    event_manipulation,
    event_object_table,
    action_timing,
    action_statement,
    tgenabled::text as trigger_enabled
FROM information_schema.triggers
WHERE trigger_schema = 'auth'
  AND event_object_table = 'users'
  AND trigger_name = 'sync_staff_auth_metadata_trigger';

-- FUNCTION DIAGNOSTICS: Check if function exists
SELECT
    'FUNCTION DIAGNOSTICS' as test_stage,
    routine_name,
    routine_type,
    security_type,
    routine_definition
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'sync_staff_auth_metadata';
