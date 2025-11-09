-- ============================================================================
-- STEP 3: UPDATE TABLE STATISTICS - Helps database make smart query decisions
-- ============================================================================
-- Copy and paste this entire section into Supabase SQL Editor

ANALYZE contacts;
ANALYZE transactions;
ANALYZE subscriptions;
ANALYZE products;
ANALYZE tags;
ANALYZE contact_tags;
ANALYZE contact_products;
