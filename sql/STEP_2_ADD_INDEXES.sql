-- ============================================================================
-- STEP 2: ADD PERFORMANCE INDEXES - This makes queries MUCH faster!
-- ============================================================================
-- Copy and paste this entire section into Supabase SQL Editor
-- CONCURRENTLY means zero downtime - database stays available while building

-- Optimize contact queries (most common queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_updated_at_desc ON contacts(updated_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_total_spent_desc ON contacts(total_spent DESC NULLS LAST) WHERE total_spent > 0;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_last_transaction ON contacts(last_transaction_date DESC NULLS LAST) WHERE last_transaction_date IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_transaction_count ON contacts(transaction_count DESC NULLS LAST) WHERE transaction_count > 0;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_source_email ON contacts(source_system, email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_active_subscription ON contacts(has_active_subscription) WHERE has_active_subscription = TRUE;

-- Optimize transaction queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_contact_date ON transactions(contact_id, transaction_date DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_status_date ON transactions(status, transaction_date DESC) WHERE status IN ('completed', 'pending');
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_date_amount ON transactions(transaction_date DESC, amount DESC) WHERE status = 'completed';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_type_status ON transactions(transaction_type, status);

-- Optimize subscription queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_contact_status ON subscriptions(contact_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_next_billing ON subscriptions(next_billing_date) WHERE status = 'active' AND next_billing_date IS NOT NULL;

-- Optimize junction tables (for tag and product queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_tags_tag_contact ON contact_tags(tag_id, contact_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contact_products_product_contact ON contact_products(product_id, contact_id);
