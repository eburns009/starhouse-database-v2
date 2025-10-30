-- ============================================================================
-- STARHOUSE CONTACT DATABASE - PRODUCTION SCHEMA V2
-- ============================================================================
-- FAANG-Grade Architecture:
-- - UUID primary keys (immutable, globally unique)
-- - Email as citext (case-insensitive, normalized)
-- - DB-level enums (type safety)
-- - Proper foreign key constraints
-- - Unique constraints on junctions (prevent duplicates)
-- - Audit columns (created_at, updated_at)
-- - Automatic timestamp triggers
-- - Indexes for performance
-- - Data validation constraints
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- ============================================================================
-- CUSTOM TYPES (Enums)
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE subscription_status AS ENUM ('active', 'paused', 'canceled', 'expired', 'trial');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded', 'disputed');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE transaction_type AS ENUM ('purchase', 'subscription', 'refund', 'adjustment');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- CONTACTS - Central contact registry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contacts (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core Identity (email is unique, case-insensitive)
    email citext NOT NULL,
    first_name text,
    last_name text,
    
    -- Contact Information
    phone text,
    address_line_1 text,
    address_line_2 text,
    city text,
    state text,
    postal_code text,
    country text,
    
    -- Communication Preferences
    email_subscribed boolean DEFAULT false,
    
    -- Source System Tracking (data provenance)
    source_system text NOT NULL DEFAULT 'kajabi',
    kajabi_id text,
    kajabi_member_id text,
    ticket_tailor_id text,
    zoho_id text,
    quickbooks_id text,
    mailchimp_id text,
    
    -- Metadata
    notes text,
    
    -- Audit Columns
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT contacts_email_check CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    CONSTRAINT contacts_source_system_check CHECK (source_system IN ('kajabi', 'zoho', 'ticket_tailor', 'quickbooks', 'mailchimp', 'manual'))
);

-- Unique constraint on email (case-insensitive via citext)
CREATE UNIQUE INDEX IF NOT EXISTS ux_contacts_email ON contacts(email);

-- Indexes for lookups and foreign keys
CREATE INDEX IF NOT EXISTS idx_contacts_kajabi_id ON contacts(kajabi_id) WHERE kajabi_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_contacts_source_system ON contacts(source_system);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_email_subscribed ON contacts(email_subscribed) WHERE email_subscribed IS TRUE;

-- Source system composite indexes (for incremental imports)
CREATE INDEX IF NOT EXISTS idx_contacts_source_lookup ON contacts(source_system, kajabi_id) WHERE kajabi_id IS NOT NULL;

COMMENT ON TABLE contacts IS 'Central contact registry - master list of all contacts across all systems';
COMMENT ON COLUMN contacts.email IS 'Primary email (citext = case-insensitive, unique)';
COMMENT ON COLUMN contacts.source_system IS 'Primary source system for this contact';

-- ----------------------------------------------------------------------------
-- TAGS - Categorization labels
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name text NOT NULL,
    name_norm text GENERATED ALWAYS AS (lower(trim(name))) STORED,
    description text,
    category text, -- e.g., 'event', 'membership', 'program', 'status'
    
    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Unique constraint on normalized name (case-insensitive)
CREATE UNIQUE INDEX IF NOT EXISTS ux_tags_name_norm ON tags(name_norm);
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category) WHERE category IS NOT NULL;

COMMENT ON TABLE tags IS 'Reusable tags for categorizing contacts';

-- ----------------------------------------------------------------------------
-- PRODUCTS - Courses, memberships, offerings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name text NOT NULL,
    name_norm text GENERATED ALWAYS AS (lower(trim(name))) STORED,
    description text,
    product_type text, -- e.g., 'course', 'membership', 'event', 'service'
    
    -- Source tracking
    kajabi_offer_id text,
    
    -- Status
    active boolean DEFAULT true,
    archived_at timestamptz,
    
    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_products_name_norm ON products(name_norm);
CREATE INDEX IF NOT EXISTS idx_products_kajabi_offer_id ON products(kajabi_offer_id) WHERE kajabi_offer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_active ON products(active) WHERE active IS TRUE;

COMMENT ON TABLE products IS 'Products, courses, memberships, and services offered';

-- ============================================================================
-- JUNCTION TABLES (Many-to-Many Relationships)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- CONTACT_TAGS - Links contacts to tags
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_tags (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    
    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    
    -- Prevent duplicate contact-tag pairs
    CONSTRAINT uq_contact_tag UNIQUE (contact_id, tag_id)
);

-- Indexes for efficient lookups in both directions
CREATE INDEX IF NOT EXISTS idx_contact_tags_contact_id ON contact_tags(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_tags_tag_id ON contact_tags(tag_id);

COMMENT ON TABLE contact_tags IS 'Many-to-many: Contacts ↔ Tags';

-- ----------------------------------------------------------------------------
-- CONTACT_PRODUCTS - Links contacts to products they've accessed/purchased
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_products (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id uuid NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    product_id uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    -- Additional context
    access_granted_at timestamptz,
    access_expires_at timestamptz,
    
    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    
    -- Prevent duplicate contact-product pairs
    CONSTRAINT uq_contact_product UNIQUE (contact_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_contact_products_contact_id ON contact_products(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_products_product_id ON contact_products(product_id);
CREATE INDEX IF NOT EXISTS idx_contact_products_expires ON contact_products(access_expires_at)
    WHERE access_expires_at IS NOT NULL;

COMMENT ON TABLE contact_products IS 'Many-to-many: Contacts ↔ Products (access/purchase history)';

-- ============================================================================
-- TRANSACTIONAL TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SUBSCRIPTIONS - Recurring subscription records
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscriptions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign Keys (UUID-based, immutable)
    contact_id uuid NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,
    product_id uuid REFERENCES products(id) ON DELETE RESTRICT,
    
    -- Source Tracking
    kajabi_subscription_id text,
    
    -- Subscription Details
    status subscription_status NOT NULL DEFAULT 'active',
    amount numeric(12,2), -- Support up to $9,999,999,999.99
    currency text DEFAULT 'USD',
    billing_cycle text, -- e.g., 'monthly', 'annual', 'one-time'
    
    -- Dates
    start_date timestamptz,
    trial_end_date timestamptz,
    cancellation_date timestamptz,
    next_billing_date timestamptz,
    
    -- Payment Processing
    payment_processor text, -- e.g., 'stripe', 'paypal', 'kajabi'
    coupon_code text,
    
    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT subscriptions_amount_positive CHECK (amount IS NULL OR amount >= 0),
    CONSTRAINT subscriptions_currency_check CHECK (currency ~* '^[A-Z]{3}$') -- ISO 4217
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_contact_id ON subscriptions(contact_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_product_id ON subscriptions(product_id) WHERE product_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_kajabi_id ON subscriptions(kajabi_subscription_id) WHERE kajabi_subscription_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_subscriptions_next_billing ON subscriptions(next_billing_date) WHERE next_billing_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(contact_id, status);

COMMENT ON TABLE subscriptions IS 'Recurring subscription records with full lifecycle tracking';

-- ----------------------------------------------------------------------------
-- TRANSACTIONS - One-time and recurring payment transactions
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Foreign Keys
    contact_id uuid NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,
    product_id uuid REFERENCES products(id) ON DELETE RESTRICT,
    subscription_id uuid REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Source Tracking
    kajabi_transaction_id text,
    order_number text,
    
    -- Transaction Details
    transaction_type transaction_type NOT NULL DEFAULT 'purchase',
    status payment_status NOT NULL DEFAULT 'completed',
    amount numeric(12,2) NOT NULL,
    currency text DEFAULT 'USD',
    tax_amount numeric(12,2),
    quantity integer DEFAULT 1,
    
    -- Payment Details
    payment_method text, -- e.g., 'credit_card', 'paypal', 'bank_transfer'
    payment_processor text,
    
    -- Marketing
    coupon_code text,
    
    -- Dates
    transaction_date timestamptz NOT NULL DEFAULT now(),
    
    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT transactions_amount_check CHECK (
        (transaction_type = 'refund' AND amount <= 0) OR 
        (transaction_type != 'refund' AND amount >= 0)
    ),
    CONSTRAINT transactions_quantity_positive CHECK (quantity > 0),
    CONSTRAINT transactions_currency_check CHECK (currency ~* '^[A-Z]{3}$')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_transactions_contact_id ON transactions(contact_id);
CREATE INDEX IF NOT EXISTS idx_transactions_product_id ON transactions(product_id) WHERE product_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_subscription_id ON transactions(subscription_id) WHERE subscription_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_kajabi_id ON transactions(kajabi_transaction_id) WHERE kajabi_transaction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_order_number ON transactions(order_number) WHERE order_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);

-- Composite index for reporting
CREATE INDEX IF NOT EXISTS idx_transactions_contact_date ON transactions(contact_id, transaction_date DESC);

COMMENT ON TABLE transactions IS 'Complete transaction history with payment details';

-- ============================================================================
-- TRIGGERS - Automatic timestamp management
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER contacts_set_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER tags_set_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER products_set_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER subscriptions_set_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER transactions_set_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- VALIDATION VIEWS (for monitoring data quality)
-- ============================================================================

-- View: Contacts with multiple source IDs (potential duplicates)
CREATE OR REPLACE VIEW v_potential_duplicate_contacts AS
SELECT 
    email,
    COUNT(*) as contact_count,
    array_agg(id) as contact_ids
FROM contacts
GROUP BY email
HAVING COUNT(*) > 1;

-- View: Active subscriptions
CREATE OR REPLACE VIEW v_active_subscriptions AS
SELECT 
    s.*,
    c.email,
    c.first_name,
    c.last_name,
    p.name as product_name
FROM subscriptions s
JOIN contacts c ON s.contact_id = c.id
LEFT JOIN products p ON s.product_id = p.id
WHERE s.status = 'active';

-- View: Contact summary statistics
CREATE OR REPLACE VIEW v_contact_summary AS
SELECT 
    c.id,
    c.email,
    c.first_name,
    c.last_name,
    COUNT(DISTINCT ct.tag_id) as tag_count,
    COUNT(DISTINCT cp.product_id) as product_count,
    COUNT(DISTINCT s.id) as subscription_count,
    COUNT(DISTINCT t.id) as transaction_count,
    SUM(CASE WHEN t.transaction_type != 'refund' THEN t.amount ELSE 0 END) as total_revenue,
    MAX(t.transaction_date) as last_transaction_date
FROM contacts c
LEFT JOIN contact_tags ct ON c.id = ct.contact_id
LEFT JOIN contact_products cp ON c.id = cp.contact_id
LEFT JOIN subscriptions s ON c.id = s.contact_id
LEFT JOIN transactions t ON c.id = t.contact_id
GROUP BY c.id, c.email, c.first_name, c.last_name;

COMMENT ON VIEW v_contact_summary IS 'Aggregated contact metrics for reporting';

-- ============================================================================
-- INITIAL DATA VALIDATION QUERIES
-- ============================================================================

-- Run these after import to verify data quality:

/*
-- No duplicate emails (should return 0 rows)
SELECT email, COUNT(*) 
FROM contacts 
GROUP BY email 
HAVING COUNT(*) > 1;

-- No orphaned contact_tags (should return 0)
SELECT COUNT(*) 
FROM contact_tags ct 
LEFT JOIN contacts c ON ct.contact_id = c.id 
WHERE c.id IS NULL;

-- No orphaned contact_products (should return 0)
SELECT COUNT(*) 
FROM contact_products cp 
LEFT JOIN contacts c ON cp.contact_id = c.id 
WHERE c.id IS NULL;

-- No orphaned subscriptions (should return 0)
SELECT COUNT(*) 
FROM subscriptions s 
LEFT JOIN contacts c ON s.contact_id = c.id 
WHERE c.id IS NULL;

-- No orphaned transactions (should return 0)
SELECT COUNT(*) 
FROM transactions t 
LEFT JOIN contacts c ON t.contact_id = c.id 
WHERE c.id IS NULL;

-- Row counts
SELECT 
    'contacts' as table_name, COUNT(*) as rows FROM contacts
UNION ALL SELECT 'tags', COUNT(*) FROM tags
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'contact_tags', COUNT(*) FROM contact_tags
UNION ALL SELECT 'contact_products', COUNT(*) FROM contact_products
UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL SELECT 'transactions', COUNT(*) FROM transactions;
*/

-- ============================================================================
-- SECURITY - Row Level Security (RLS)
-- ============================================================================
-- Note: Enable RLS AFTER import, not before
-- Example policies (customize for your auth requirements):

/*
-- Enable RLS
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Example: Allow service role full access (for admin operations)
CREATE POLICY "Service role has full access" ON contacts
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Example: Allow authenticated users to read their own contact info
CREATE POLICY "Users can view their own contact" ON contacts
    FOR SELECT TO authenticated
    USING (auth.jwt()->>'email' = email);

-- Add more policies as needed for your application
*/

-- ============================================================================
-- POST-IMPORT OPTIMIZATION
-- ============================================================================

-- After import, update table statistics for query planner
-- ANALYZE;

-- For bulk imports, consider using COPY instead of INSERT:
/*
COPY contacts FROM '/path/to/v2_contacts.csv' 
  WITH (FORMAT CSV, HEADER true, ENCODING 'UTF-8');
*/

-- For incremental/idempotent loads (staging approach):
/*
CREATE TEMP TABLE staging_contacts AS SELECT * FROM contacts WHERE false;

COPY staging_contacts FROM '/path/to/v2_contacts.csv' 
  WITH (FORMAT CSV, HEADER true, ENCODING 'UTF-8');

INSERT INTO contacts 
SELECT * FROM staging_contacts
ON CONFLICT (email) DO UPDATE SET
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name,
  updated_at = now();

DROP TABLE staging_contacts;
*/

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

COMMENT ON SCHEMA public IS 'StarHouse Contact Database - Production V2 (FAANG-grade architecture)';
