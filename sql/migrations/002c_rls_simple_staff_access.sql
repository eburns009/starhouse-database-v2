-- ===========================================================================
-- RLS Implementation - Simple Staff Access Model
-- ===========================================================================
-- Migration: 002c_rls_simple_staff_access.sql
-- Date: 2025-11-09
-- Priority: P1 - Replaces incorrect backend-only RLS
--
-- CORRECTS: Migration 002_enable_rls_backend_only.sql
-- Previous migration only allowed service_role access, blocking staff UI
--
-- REQUIREMENTS (from user):
-- - 3-5 trusted staff need full access via UI
-- - All staff get same permissions (no role hierarchy)
-- - Will change in 6 months (don't over-engineer)
-- - Staff can view/edit everything
-- - Backend scripts must continue to work
--
-- SECURITY MODEL:
-- - authenticated users (staff logged into UI) = full access
-- - service_role (backend scripts/webhooks) = full access
-- - anon users (not logged in) = NO access
-- - postgres role (table owner) = bypasses RLS (import scripts)
-- ===========================================================================

BEGIN;

-- ===========================================================================
-- STEP 1: Drop old service_role-only policies
-- ===========================================================================

-- Drop the incorrect backend-only policies
DROP POLICY IF EXISTS "service_role_all_contacts" ON contacts;
DROP POLICY IF EXISTS "service_role_all_transactions" ON transactions;
DROP POLICY IF EXISTS "service_role_all_subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "service_role_all_products" ON products;
DROP POLICY IF EXISTS "service_role_all_tags" ON tags;
DROP POLICY IF EXISTS "service_role_all_contact_tags" ON contact_tags;
DROP POLICY IF EXISTS "service_role_all_contact_products" ON contact_products;
DROP POLICY IF EXISTS "service_role_all_membership_products" ON membership_products;
DROP POLICY IF EXISTS "service_role_all_webhook_nonces" ON webhook_nonces;
DROP POLICY IF EXISTS "service_role_all_webhook_rate_limits" ON webhook_rate_limits;
DROP POLICY IF EXISTS "service_role_all_health_check_log" ON health_check_log;
DROP POLICY IF EXISTS "service_role_all_dlq_events" ON dlq_events;

-- ===========================================================================
-- STEP 2: Create simple staff access policies
-- ===========================================================================

-- Contacts table: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON contacts
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Transactions table: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON transactions
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Subscriptions table: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON subscriptions
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Products table: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON products
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Tags table: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON tags
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Contact_tags junction: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON contact_tags
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Contact_products junction: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON contact_products
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Membership_products: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON membership_products
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Webhook_nonces: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON webhook_nonces
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Webhook_rate_limits: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON webhook_rate_limits
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Health_check_log: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON health_check_log
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- DLQ_events: Full access for authenticated staff
CREATE POLICY "staff_full_access" ON dlq_events
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- ===========================================================================
-- STEP 3: Add service_role policies (backend operations)
-- ===========================================================================

-- Service role also gets full access for backend operations
CREATE POLICY "service_role_full_access" ON contacts
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON transactions
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON subscriptions
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON products
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON tags
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON contact_tags
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON contact_products
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON membership_products
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON webhook_nonces
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON webhook_rate_limits
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON health_check_log
  FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON dlq_events
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ===========================================================================
-- STEP 4: Confirm anon users still have NO access
-- ===========================================================================

-- Anon users already have access revoked from migration 002
-- Verify it stays that way
DO $$
BEGIN
  -- These REVOKE statements are idempotent
  REVOKE ALL ON contacts FROM anon;
  REVOKE ALL ON transactions FROM anon;
  REVOKE ALL ON subscriptions FROM anon;
  REVOKE ALL ON products FROM anon;
  REVOKE ALL ON tags FROM anon;
  REVOKE ALL ON contact_tags FROM anon;
  REVOKE ALL ON contact_products FROM anon;
  REVOKE ALL ON membership_products FROM anon;
  REVOKE ALL ON webhook_nonces FROM anon;
  REVOKE ALL ON webhook_rate_limits FROM anon;
  REVOKE ALL ON health_check_log FROM anon;
  REVOKE ALL ON dlq_events FROM anon;

  RAISE NOTICE 'Anon access revoked (confirmed)';
END $$;

-- ===========================================================================
-- STEP 5: Grant table permissions to authenticated role
-- ===========================================================================

-- CRITICAL: RLS policies alone are not enough!
-- You must also GRANT permissions on the tables themselves

GRANT SELECT, INSERT, UPDATE, DELETE ON contacts TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON transactions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON subscriptions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON tags TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON contact_tags TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON contact_products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON membership_products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON webhook_nonces TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON webhook_rate_limits TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON health_check_log TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON dlq_events TO authenticated;

-- Verify grants were added
DO $$
DECLARE
  grant_count INTEGER;
BEGIN
  SELECT COUNT(DISTINCT table_name)
  INTO grant_count
  FROM information_schema.table_privileges
  WHERE grantee = 'authenticated'
    AND table_schema = 'public'
    AND table_name IN ('contacts', 'transactions', 'subscriptions', 'products',
                       'tags', 'contact_tags', 'contact_products', 'membership_products',
                       'webhook_nonces', 'webhook_rate_limits', 'health_check_log', 'dlq_events');

  IF grant_count != 12 THEN
    RAISE EXCEPTION 'GRANT verification failed: Expected 12 tables, found %', grant_count;
  END IF;

  RAISE NOTICE '✓ Authenticated role granted permissions on % tables', grant_count;
END $$;

COMMIT;

-- ===========================================================================
-- Verification
-- ===========================================================================

-- Check policies were created correctly
SELECT
  schemaname,
  tablename,
  policyname,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('contacts', 'transactions', 'subscriptions', 'products', 'tags')
ORDER BY tablename, policyname;

-- Expected: 2 policies per table
-- - staff_full_access (authenticated role)
-- - service_role_full_access (service_role)

-- ===========================================================================
-- Test Queries (run manually)
-- ===========================================================================

/*
-- Test 1: Verify authenticated users can access data
-- (This simulates what Supabase Auth users will see)

SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "test-user-123", "role": "authenticated"}';

SELECT COUNT(*) as should_be_6563 FROM contacts;
SELECT COUNT(*) as should_be_8077 FROM transactions;
SELECT COUNT(*) as should_be_410 FROM subscriptions;

RESET ROLE;

-- Test 2: Verify anon users CANNOT access data
SET ROLE anon;

SELECT COUNT(*) FROM contacts;  -- Should return: 0 rows or ERROR

RESET ROLE;

-- Test 3: Verify service_role can access data (backend operations)
SET ROLE service_role;

SELECT COUNT(*) FROM contacts;  -- Should return: 6563

RESET ROLE;
*/

-- ===========================================================================
-- Security Model Documentation
-- ===========================================================================

/*
SECURITY MODEL: Simple Staff Access (3-5 trusted users)

ACCESS LEVELS:
--------------
1. **Authenticated Users (Staff UI)**
   - Role: authenticated
   - Access: Full read/write on all tables
   - Authentication: Supabase Auth (email/password)
   - Users: 3-5 staff members
   - Permissions: Everyone gets same full access (no hierarchy)

2. **Service Role (Backend Operations)**
   - Role: service_role
   - Access: Full read/write on all tables
   - Authentication: Supabase service_role JWT key
   - Use cases: Webhooks, admin operations, Supabase dashboard

3. **Postgres Role (Import Scripts)**
   - Role: postgres (table owner)
   - Access: Full unrestricted access (BYPASSES RLS)
   - Authentication: DATABASE_URL password
   - Use cases: Import scripts, migrations, backups
   - Security: Relies on .env file protection

4. **Anonymous Users (Public)**
   - Role: anon
   - Access: NONE (all access revoked)
   - Use cases: Should never access database directly

FUTURE CONSIDERATIONS (6+ months):
-----------------------------------
When staff grows beyond 5 users or needs role hierarchy:

1. Add user_roles table:
   CREATE TABLE user_roles (
     user_id UUID REFERENCES auth.users(id),
     role TEXT CHECK (role IN ('admin', 'coordinator', 'volunteer')),
     created_at TIMESTAMPTZ DEFAULT now()
   );

2. Update policies to check role:
   CREATE POLICY "admins_full_access" ON contacts
     FOR ALL TO authenticated
     USING (
       EXISTS (
         SELECT 1 FROM user_roles
         WHERE user_id = auth.uid()
         AND role = 'admin'
       )
     );

3. Add granular permissions:
   - Admins: Full access
   - Coordinators: Read all, edit contacts/notes only
   - Volunteers: Read-only filtered by territory

But DON'T do this now - wait until requirements actually change.

KNOWN LIMITATIONS:
------------------
1. **Import scripts bypass RLS**
   - Connect as postgres (table owner)
   - RLS does not apply to table owners
   - This is expected and acceptable for backend-only scripts

2. **No row-level auditing**
   - All staff see same data
   - Can't track who viewed what
   - Add audit logging if needed later

3. **Financial data visible**
   - Staff can see transaction amounts
   - If need to hide, use database views or UI filtering
   - Option: Create subscriptions_limited view without amount field

STAFF ONBOARDING:
-----------------
To add a new staff member:

1. Go to Supabase Dashboard → Authentication → Users
2. Click "Invite User"
3. Email: [staff email]
4. Send invitation
5. Staff sets password and can immediately access UI

No additional configuration needed - authenticated users automatically
get full access per the "staff_full_access" policies.

REFERENCES:
-----------
- docs/CRITICAL_REVIEW_FINDINGS.md - Honest assessment of RLS approach
- docs/SESSION_2025_11_09_SECURITY_IMPLEMENTATION.md - Implementation session
*/

-- ===========================================================================
-- ROLLBACK PROCEDURE
-- ===========================================================================

/*
-- If you need to undo this migration completely:

BEGIN;

-- STEP 1: Drop all staff_full_access policies
DROP POLICY IF EXISTS "staff_full_access" ON contacts;
DROP POLICY IF EXISTS "staff_full_access" ON transactions;
DROP POLICY IF EXISTS "staff_full_access" ON subscriptions;
DROP POLICY IF EXISTS "staff_full_access" ON products;
DROP POLICY IF EXISTS "staff_full_access" ON tags;
DROP POLICY IF EXISTS "staff_full_access" ON contact_tags;
DROP POLICY IF EXISTS "staff_full_access" ON contact_products;
DROP POLICY IF EXISTS "staff_full_access" ON membership_products;
DROP POLICY IF EXISTS "staff_full_access" ON webhook_nonces;
DROP POLICY IF EXISTS "staff_full_access" ON webhook_rate_limits;
DROP POLICY IF EXISTS "staff_full_access" ON health_check_log;
DROP POLICY IF EXISTS "staff_full_access" ON dlq_events;

-- STEP 2: Drop all service_role_full_access policies
DROP POLICY IF EXISTS "service_role_full_access" ON contacts;
DROP POLICY IF EXISTS "service_role_full_access" ON transactions;
DROP POLICY IF EXISTS "service_role_full_access" ON subscriptions;
DROP POLICY IF EXISTS "service_role_full_access" ON products;
DROP POLICY IF EXISTS "service_role_full_access" ON tags;
DROP POLICY IF EXISTS "service_role_full_access" ON contact_tags;
DROP POLICY IF EXISTS "service_role_full_access" ON contact_products;
DROP POLICY IF EXISTS "service_role_full_access" ON membership_products;
DROP POLICY IF EXISTS "service_role_full_access" ON webhook_nonces;
DROP POLICY IF EXISTS "service_role_full_access" ON webhook_rate_limits;
DROP POLICY IF EXISTS "service_role_full_access" ON health_check_log;
DROP POLICY IF EXISTS "service_role_full_access" ON dlq_events;

-- STEP 3: Revoke authenticated role permissions
REVOKE ALL ON contacts FROM authenticated;
REVOKE ALL ON transactions FROM authenticated;
REVOKE ALL ON subscriptions FROM authenticated;
REVOKE ALL ON products FROM authenticated;
REVOKE ALL ON tags FROM authenticated;
REVOKE ALL ON contact_tags FROM authenticated;
REVOKE ALL ON contact_products FROM authenticated;
REVOKE ALL ON membership_products FROM authenticated;
REVOKE ALL ON webhook_nonces FROM authenticated;
REVOKE ALL ON webhook_rate_limits FROM authenticated;
REVOKE ALL ON health_check_log FROM authenticated;
REVOKE ALL ON dlq_events FROM authenticated;

-- STEP 4: Disable RLS (WARNING: This removes ALL security)
ALTER TABLE contacts DISABLE ROW LEVEL SECURITY;
ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions DISABLE ROW LEVEL SECURITY;
ALTER TABLE products DISABLE ROW LEVEL SECURITY;
ALTER TABLE tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE contact_tags DISABLE ROW LEVEL SECURITY;
ALTER TABLE contact_products DISABLE ROW LEVEL SECURITY;
ALTER TABLE membership_products DISABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_nonces DISABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_rate_limits DISABLE ROW LEVEL SECURITY;
ALTER TABLE health_check_log DISABLE ROW LEVEL SECURITY;
ALTER TABLE dlq_events DISABLE ROW LEVEL SECURITY;

-- STEP 5: Verify RLS disabled
SELECT tablename, rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('contacts', 'transactions', 'subscriptions')
ORDER BY tablename;
-- All should show rls_enabled = f

COMMIT;

-- WARNING: After rollback, ALL users (including anon) will have unrestricted access!
-- Only rollback if you're replacing with a different security model immediately.
*/
