-- ===========================================================================
-- RLS Implementation for Backend-Only System
-- ===========================================================================
-- Migration: 002_enable_rls_backend_only.sql
-- Date: 2025-11-09
-- Priority: P0 - HIGH PRIORITY SECURITY FIX
--
-- Use case: Import scripts and webhooks need full access
--           No direct user access to database
--           Prevents accidental data exposure from anon/authenticated roles
-- ===========================================================================

BEGIN;

-- ===========================================================================
-- STEP 1: Enable RLS on all core tables
-- ===========================================================================

ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE membership_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_nonces ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_check_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE dlq_events ENABLE ROW LEVEL SECURITY;

-- ===========================================================================
-- STEP 2: Create service_role policies (full access for backend services)
-- ===========================================================================

-- Contacts table
CREATE POLICY "service_role_all_contacts" ON contacts
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Transactions table
CREATE POLICY "service_role_all_transactions" ON transactions
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Subscriptions table
CREATE POLICY "service_role_all_subscriptions" ON subscriptions
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Products table
CREATE POLICY "service_role_all_products" ON products
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Tags table
CREATE POLICY "service_role_all_tags" ON tags
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Contact_tags junction table
CREATE POLICY "service_role_all_contact_tags" ON contact_tags
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Contact_products junction table
CREATE POLICY "service_role_all_contact_products" ON contact_products
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Membership_products table
CREATE POLICY "service_role_all_membership_products" ON membership_products
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Webhook_nonces table
CREATE POLICY "service_role_all_webhook_nonces" ON webhook_nonces
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Webhook_rate_limits table
CREATE POLICY "service_role_all_webhook_rate_limits" ON webhook_rate_limits
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Health_check_log table
CREATE POLICY "service_role_all_health_check_log" ON health_check_log
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- DLQ_events table
CREATE POLICY "service_role_all_dlq_events" ON dlq_events
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ===========================================================================
-- STEP 3: Revoke access from other roles (prevent accidental exposure)
-- ===========================================================================

-- Revoke from authenticated and anon roles
REVOKE ALL ON contacts FROM authenticated, anon;
REVOKE ALL ON transactions FROM authenticated, anon;
REVOKE ALL ON subscriptions FROM authenticated, anon;
REVOKE ALL ON products FROM authenticated, anon;
REVOKE ALL ON tags FROM authenticated, anon;
REVOKE ALL ON contact_tags FROM authenticated, anon;
REVOKE ALL ON contact_products FROM authenticated, anon;
REVOKE ALL ON membership_products FROM authenticated, anon;
REVOKE ALL ON webhook_nonces FROM authenticated, anon;
REVOKE ALL ON webhook_rate_limits FROM authenticated, anon;
REVOKE ALL ON health_check_log FROM authenticated, anon;
REVOKE ALL ON dlq_events FROM authenticated, anon;

-- ===========================================================================
-- STEP 4: Grant explicit permissions to service_role
-- ===========================================================================

GRANT ALL ON contacts TO service_role;
GRANT ALL ON transactions TO service_role;
GRANT ALL ON subscriptions TO service_role;
GRANT ALL ON products TO service_role;
GRANT ALL ON tags TO service_role;
GRANT ALL ON contact_tags TO service_role;
GRANT ALL ON contact_products TO service_role;
GRANT ALL ON membership_products TO service_role;
GRANT ALL ON webhook_nonces TO service_role;
GRANT ALL ON webhook_rate_limits TO service_role;
GRANT ALL ON health_check_log TO service_role;
GRANT ALL ON dlq_events TO service_role;

-- Also grant on sequences if they exist
DO $$
DECLARE
    seq RECORD;
BEGIN
    FOR seq IN
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE format('GRANT ALL ON SEQUENCE %I TO service_role', seq.sequence_name);
    END LOOP;
END $$;

COMMIT;

-- ===========================================================================
-- Verification queries (run these manually after migration)
-- ===========================================================================

-- Check RLS is enabled on all tables
-- SELECT
--   schemaname,
--   tablename,
--   rowsecurity as rls_enabled
-- FROM pg_tables
-- WHERE schemaname = 'public'
--   AND tablename IN (
--     'contacts', 'transactions', 'subscriptions', 'products', 'tags',
--     'contact_tags', 'contact_products', 'membership_products',
--     'webhook_nonces', 'webhook_rate_limits', 'health_check_log', 'dlq_events'
--   )
-- ORDER BY tablename;

-- Check policies exist
-- SELECT
--   schemaname,
--   tablename,
--   policyname,
--   roles,
--   cmd
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- ORDER BY tablename, policyname;

-- ===========================================================================
-- Security Model Documentation
-- ===========================================================================

/*
SECURITY MODEL: StarHouse Database V2

Current State (Backend-Only):
------------------------------
Access Pattern:
- Import scripts: service_role (full access via DATABASE_URL)
- Webhooks: service_role (full access via DATABASE_URL)
- Direct user access: NONE

RLS Configuration:
- Enabled on all core tables
- Service role has full access via policies
- Authenticated/anon roles have NO access
- Prevents accidental data exposure if credentials leak

Authentication Method:
- Service account with DATABASE_URL environment variable
- No user authentication required (backend-only system)

Future Considerations:
----------------------
If building user-facing API:
1. Implement Supabase Auth
2. Add user_id/organization_id columns to tables
3. Update RLS policies for per-user/per-org access
4. Create proper role hierarchy (admin, member, viewer)
5. Implement JWT-based authentication

References:
-----------
- docs/CRITICAL_SECURITY_FIXES_CORRECTED.md
- docs/FAANG_CODE_REVIEW_ACTION_PLAN.md
*/
