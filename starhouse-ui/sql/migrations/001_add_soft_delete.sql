-- ============================================================================
-- MIGRATION 001: Add soft delete support to all core tables
-- ============================================================================
-- Purpose: Enable soft delete pattern (deleted_at column) for data recovery
-- FAANG Standard: Never hard delete user data; maintain audit trail
-- ============================================================================

-- Add deleted_at column to contacts
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

-- Add deleted_at column to tags
ALTER TABLE tags ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

-- Add deleted_at column to products
ALTER TABLE products ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

-- Add deleted_at column to subscriptions
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

-- Add deleted_at column to transactions (rarely used, but for completeness)
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS deleted_at timestamptz;

-- Indexes for performance (filtering out deleted records)
CREATE INDEX IF NOT EXISTS idx_contacts_not_deleted
  ON contacts(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tags_not_deleted
  ON tags(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_products_not_deleted
  ON products(id) WHERE deleted_at IS NULL;

-- Create view for active (non-deleted) contacts
CREATE OR REPLACE VIEW v_active_contacts AS
SELECT * FROM contacts WHERE deleted_at IS NULL;

-- Create view for active products
CREATE OR REPLACE VIEW v_active_products AS
SELECT * FROM products WHERE deleted_at IS NULL AND active = true;

COMMENT ON COLUMN contacts.deleted_at IS 'Soft delete timestamp - NULL means active';
COMMENT ON VIEW v_active_contacts IS 'Contacts that have not been soft-deleted';
