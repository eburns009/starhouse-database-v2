-- Add additional contact fields for enrichment
-- These fields capture alternate contact information discovered through data matching

-- Add additional contact fields
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS additional_phone text,
ADD COLUMN IF NOT EXISTS additional_email citext,
ADD COLUMN IF NOT EXISTS additional_name text,
ADD COLUMN IF NOT EXISTS additional_phone_source text,
ADD COLUMN IF NOT EXISTS additional_email_source text,
ADD COLUMN IF NOT EXISTS additional_name_source text;

-- Add comments for documentation
COMMENT ON COLUMN contacts.additional_phone IS 'Third phone number found in transaction data (beyond phone and paypal_phone)';
COMMENT ON COLUMN contacts.additional_email IS 'Third email address found in transaction data (beyond email and paypal_email)';
COMMENT ON COLUMN contacts.additional_name IS 'Alternate name variations found in transaction data';
COMMENT ON COLUMN contacts.additional_phone_source IS 'Source system where additional_phone was discovered (e.g., paypal_2024, kajabi)';
COMMENT ON COLUMN contacts.additional_email_source IS 'Source system where additional_email was discovered (e.g., paypal_2024, kajabi)';
COMMENT ON COLUMN contacts.additional_name_source IS 'Source system where additional_name was discovered (e.g., paypal_2024, kajabi)';

-- Add index for fuzzy matching on additional name
CREATE INDEX IF NOT EXISTS idx_contacts_additional_name_trgm
ON contacts USING gin (additional_name gin_trgm_ops)
WHERE additional_name IS NOT NULL;

-- Add index for additional email lookups
CREATE INDEX IF NOT EXISTS idx_contacts_additional_email
ON contacts (additional_email)
WHERE additional_email IS NOT NULL;

-- Verification query
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'contacts'
  AND column_name IN ('additional_phone', 'additional_email', 'additional_name',
                      'additional_phone_source', 'additional_email_source', 'additional_name_source')
ORDER BY column_name;
