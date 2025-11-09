-- Add PayPal-specific fields to contacts table
-- This prevents duplicate contacts when customers use different emails in PayPal vs Kajabi

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_email citext;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_first_name text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_last_name text;

-- Add index for faster PayPal email lookups
CREATE INDEX IF NOT EXISTS idx_contacts_paypal_email ON contacts(paypal_email);

-- Add index for name-based matching (used to find existing contacts)
CREATE INDEX IF NOT EXISTS idx_contacts_name_match ON contacts(first_name, last_name);

-- Comment the columns
COMMENT ON COLUMN contacts.paypal_email IS 'Email address used in PayPal transactions (may differ from primary email)';
COMMENT ON COLUMN contacts.paypal_first_name IS 'First name from PayPal payer info';
COMMENT ON COLUMN contacts.paypal_last_name IS 'Last name from PayPal payer info';
