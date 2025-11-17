-- ============================================
-- SECURE FINANCIAL TABLES - RLS POLICIES
-- StarHouse CRM Database
-- ============================================
-- Purpose: Add proper RLS to transactions and subscriptions tables
-- Security: Restrict financial data access to verified staff only
-- Created: 2025-11-13
-- Migration: 20251113000005
-- ============================================

-- ============================================
-- STEP 1: DROP OVERLY PERMISSIVE POLICIES
-- ============================================
-- These policies allow ANY authenticated user to access financial data
-- This is a critical security vulnerability

DROP POLICY IF EXISTS "staff_full_access" ON transactions;
DROP POLICY IF EXISTS "staff_full_access" ON subscriptions;

-- ============================================
-- STEP 2: ADD SECURE RLS POLICIES - TRANSACTIONS
-- ============================================

-- Policy: Verified staff can view all transactions
CREATE POLICY "verified_staff_select_transactions"
    ON transactions FOR SELECT
    TO authenticated
    USING (is_verified_staff());

COMMENT ON POLICY "verified_staff_select_transactions" ON transactions IS
'Only users in staff_members allowlist can view transactions. Checked via is_verified_staff().';

-- Policy: Verified staff can insert transactions (manual entry)
CREATE POLICY "verified_staff_insert_transactions"
    ON transactions FOR INSERT
    TO authenticated
    WITH CHECK (is_verified_staff());

COMMENT ON POLICY "verified_staff_insert_transactions" ON transactions IS
'Only verified staff can create new transactions (manual entry).';

-- Policy: Verified staff can update transactions
CREATE POLICY "verified_staff_update_transactions"
    ON transactions FOR UPDATE
    TO authenticated
    USING (is_verified_staff())
    WITH CHECK (is_verified_staff());

COMMENT ON POLICY "verified_staff_update_transactions" ON transactions IS
'Only verified staff can update transactions.';

-- Policy: Only admins can delete transactions
CREATE POLICY "admin_delete_transactions"
    ON transactions FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );

COMMENT ON POLICY "admin_delete_transactions" ON transactions IS
'Only admins can delete transactions. Consider soft delete (deleted_at) instead.';

-- ============================================
-- STEP 3: ADD SECURE RLS POLICIES - SUBSCRIPTIONS
-- ============================================

-- Policy: Verified staff can view all subscriptions
CREATE POLICY "verified_staff_select_subscriptions"
    ON subscriptions FOR SELECT
    TO authenticated
    USING (is_verified_staff());

COMMENT ON POLICY "verified_staff_select_subscriptions" ON subscriptions IS
'Only users in staff_members allowlist can view subscriptions. Checked via is_verified_staff().';

-- Policy: Verified staff can insert subscriptions (manual entry)
CREATE POLICY "verified_staff_insert_subscriptions"
    ON subscriptions FOR INSERT
    TO authenticated
    WITH CHECK (is_verified_staff());

COMMENT ON POLICY "verified_staff_insert_subscriptions" ON subscriptions IS
'Only verified staff can create new subscriptions (manual entry).';

-- Policy: Verified staff can update subscriptions
CREATE POLICY "verified_staff_update_subscriptions"
    ON subscriptions FOR UPDATE
    TO authenticated
    USING (is_verified_staff())
    WITH CHECK (is_verified_staff());

COMMENT ON POLICY "verified_staff_update_subscriptions" ON subscriptions IS
'Only verified staff can update subscriptions.';

-- Policy: Only admins can delete subscriptions
CREATE POLICY "admin_delete_subscriptions"
    ON subscriptions FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );

COMMENT ON POLICY "admin_delete_subscriptions" ON subscriptions IS
'Only admins can delete subscriptions. Consider soft delete (deleted_at) instead.';

-- ============================================
-- STEP 4: KEEP SERVICE ROLE POLICIES
-- ============================================
-- Service role needs full access for webhook processing
-- These policies already exist, just documenting them here

-- transactions: service_role_full_access (already exists)
-- subscriptions: service_role_full_access (already exists)

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these after migration to verify setup:

-- 1. Check policies are in place:
--    SELECT schemaname, tablename, policyname, cmd, roles
--    FROM pg_policies
--    WHERE tablename IN ('transactions', 'subscriptions')
--    ORDER BY tablename, cmd, policyname;
--    Expected: 8 new policies (4 per table) + 2 service_role policies

-- 2. Test as verified staff (should work):
--    SELECT COUNT(*) FROM transactions;
--    SELECT COUNT(*) FROM subscriptions;

-- 3. Test as non-staff authenticated user (should fail):
--    -- Log in as user NOT in staff_members
--    SELECT COUNT(*) FROM transactions;  -- Should return: permission denied
--    SELECT COUNT(*) FROM subscriptions; -- Should return: permission denied

-- ============================================
-- ROLLBACK PROCEDURE (If Needed)
-- ============================================
-- If something goes wrong, run this to restore old policies:
--
-- DROP POLICY IF EXISTS "verified_staff_select_transactions" ON transactions;
-- DROP POLICY IF EXISTS "verified_staff_insert_transactions" ON transactions;
-- DROP POLICY IF EXISTS "verified_staff_update_transactions" ON transactions;
-- DROP POLICY IF EXISTS "admin_delete_transactions" ON transactions;
-- DROP POLICY IF EXISTS "verified_staff_select_subscriptions" ON subscriptions;
-- DROP POLICY IF EXISTS "verified_staff_insert_subscriptions" ON subscriptions;
-- DROP POLICY IF EXISTS "verified_staff_update_subscriptions" ON subscriptions;
-- DROP POLICY IF EXISTS "admin_delete_subscriptions" ON subscriptions;
--
-- CREATE POLICY "staff_full_access" ON transactions
--     FOR ALL TO authenticated USING (true) WITH CHECK (true);
-- CREATE POLICY "staff_full_access" ON subscriptions
--     FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- ============================================
-- SUMMARY
-- ============================================
-- BEFORE: Any authenticated user could access ALL financial data
-- AFTER:  Only verified staff (in staff_members table) can access financial data
--
-- Security Improvement:
-- - Transactions table now protected by is_verified_staff()
-- - Subscriptions table now protected by is_verified_staff()
-- - Only admins can delete financial records
-- - Service role maintains full access for webhooks
-- - Consistent with contacts table security model
