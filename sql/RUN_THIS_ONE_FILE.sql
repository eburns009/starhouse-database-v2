-- ============================================================================
-- COMPLETE DATABASE OPTIMIZATION - Copy this entire file and run in Supabase
-- ============================================================================

-- STEP 1: Enable performance tracking
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- STEP 2: Add all performance indexes (MOST IMPORTANT!)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_updated_at_desc ON contacts(updated_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_total_spent_desc ON contacts(total_spent DESC NULLS LAST) WHERE total_spent > 0;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_last_transaction ON contacts(last_transaction_date DESC NULLS LAST) WHERE last_transaction_date IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_transaction_count ON contacts(transaction_count DESC NULLS LAST) WHERE transaction_count > 0;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_source_email ON contacts(source_system, email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_active_subscription ON contacts(has_active_subscription) WHERE has_active_subscription = TRUE;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_contact_date ON transactions(contact_id, transaction_date DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_status_date ON transactions(status, transaction_date DESC) WHERE status IN ('completed', 'pending');
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_date_amount ON transactions(transaction_date DESC, amount DESC) WHERE status = 'completed';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_type_status ON transactions(transaction_type, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_contact_status ON subscriptions(contact_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_next_billing ON subscriptions(next_billing_date) WHERE status = 'active' AND next_billing_date IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_tags_tag_contact ON contact_tags(tag_id, contact_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_products_product_contact ON contact_products(product_id, contact_id);

-- STEP 3: Update table statistics
ANALYZE contacts;
ANALYZE transactions;
ANALYZE subscriptions;
ANALYZE products;
ANALYZE tags;
ANALYZE contact_tags;
ANALYZE contact_products;

-- STEP 4: Create monitoring view
CREATE OR REPLACE VIEW v_system_health AS
SELECT
  (SELECT count(*) FROM pg_stat_activity) as total_connections,
  (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
  (SELECT count(*) FROM contacts) as total_contacts,
  (SELECT count(*) FROM contacts WHERE transaction_count > 0) as paying_customers,
  (SELECT count(*) FROM transactions WHERE status = 'completed') as completed_transactions,
  (SELECT COALESCE(SUM(amount), 0)::numeric(10,2) FROM transactions WHERE status = 'completed') as total_revenue,
  (SELECT count(*) FROM subscriptions WHERE status = 'active') as active_subscriptions,
  (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size,
  NOW() as snapshot_time;

-- DONE! Now run this to verify it worked:
SELECT * FROM v_system_health;
