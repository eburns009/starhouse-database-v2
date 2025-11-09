-- ============================================================================
-- ADD TRANSACTION SUMMARY FIELDS TO CONTACTS TABLE
-- ============================================================================
-- This migration adds computed fields from transaction data to the contacts table
-- Run this BEFORE importing the updated transaction data
-- ============================================================================

-- Add new columns to contacts table
ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS total_spent NUMERIC(10,2) DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS transaction_count INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS first_transaction_date TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_transaction_date TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS has_active_subscription BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS favorite_payment_method TEXT,
  ADD COLUMN IF NOT EXISTS total_coupons_used INTEGER DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN contacts.total_spent IS 'Total lifetime value from all completed transactions';
COMMENT ON COLUMN contacts.transaction_count IS 'Total number of completed transactions';
COMMENT ON COLUMN contacts.first_transaction_date IS 'Date of first transaction';
COMMENT ON COLUMN contacts.last_transaction_date IS 'Date of most recent transaction';
COMMENT ON COLUMN contacts.has_active_subscription IS 'Whether contact has at least one active subscription';
COMMENT ON COLUMN contacts.favorite_payment_method IS 'Most frequently used payment method';
COMMENT ON COLUMN contacts.total_coupons_used IS 'Number of transactions where a coupon was used';

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_contacts_total_spent ON contacts(total_spent DESC) WHERE total_spent > 0;
CREATE INDEX IF NOT EXISTS idx_contacts_transaction_count ON contacts(transaction_count DESC) WHERE transaction_count > 0;
CREATE INDEX IF NOT EXISTS idx_contacts_last_transaction_date ON contacts(last_transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_contacts_has_active_subscription ON contacts(has_active_subscription) WHERE has_active_subscription IS TRUE;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Successfully added transaction summary fields to contacts table';
    RAISE NOTICE 'New columns: total_spent, transaction_count, first_transaction_date, last_transaction_date, has_active_subscription, favorite_payment_method, total_coupons_used';
END $$;
