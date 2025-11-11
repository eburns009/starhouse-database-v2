-- ============================================================================
-- MIGRATION 005: Row Level Security (RLS) Policies - SIMPLE STAFF MODEL
-- ============================================================================
-- Purpose: Secure data access with proper RLS policies
-- FAANG Standard: Database-level security, never trust application layer
-- Model: Simple staff access (all authenticated users = full access)
-- See: docs/FUTURE_RLS_MIGRATION.md for role-based model (when needed)
-- ============================================================================

-- Enable RLS on all core tables (if not already enabled)
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Enable RLS on new tables
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_views ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SERVICE ROLE: Full access for backend operations (import scripts, etc.)
-- ============================================================================

CREATE POLICY "service_role_full_access" ON contacts
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON tags
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON products
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON contact_tags
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON contact_products
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON subscriptions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON transactions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON audit_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON jobs
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_full_access" ON saved_views
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================================
-- AUTHENTICATED STAFF: Full access (simple model for trusted team)
-- ============================================================================
-- Rationale: Small trusted team (3-5 staff), everyone needs full access
-- When to change: See docs/FUTURE_RLS_MIGRATION.md (when team grows >5-7)
-- ============================================================================

-- Contacts: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON contacts
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Tags: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON tags
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Products: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON products
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Contact Tags: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON contact_tags
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Contact Products: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON contact_products
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Subscriptions: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON subscriptions
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Transactions: Staff have full CRUD access
CREATE POLICY "staff_full_access" ON transactions
    FOR ALL TO authenticated
    USING (true)
    WITH CHECK (true);

-- Audit Log: Read-only (append-only enforced by separate policy)
CREATE POLICY "staff_read_audit_log" ON audit_log
    FOR SELECT TO authenticated
    USING (true);

-- Jobs: Users manage their own jobs
CREATE POLICY "users_own_jobs" ON jobs
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Saved Views: Users manage their own views
CREATE POLICY "users_own_saved_views" ON saved_views
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ============================================================================
-- TESTING RLS
-- ============================================================================
-- CRITICAL: Test with real Supabase Auth, NOT SQL commands
-- See: docs/HOW_TO_TEST_RLS.md for complete testing guide
-- Quick test: Open test-rls.html and run all tests
-- ============================================================================

COMMENT ON POLICY "service_role_full_access" ON contacts IS
    'Backend scripts/imports use service_role key for unrestricted access';

COMMENT ON POLICY "staff_full_access" ON contacts IS
    'Simple staff model: all authenticated users have full access (suitable for small trusted teams <5-7 people). See docs/FUTURE_RLS_MIGRATION.md when team grows.';
