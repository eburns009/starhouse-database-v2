-- ============================================================================
-- ADD ZOHO CONTACT ENRICHMENT FIELDS
-- ============================================================================
-- Purpose: Add fields to support Zoho CRM contact data import and enrichment
-- Author: StarHouse Development Team
-- Date: 2025-11-08
-- FAANG Standard: Idempotent migration with rollback support
-- ============================================================================

BEGIN;

-- Add Zoho email field (for alternate email from Zoho)
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS zoho_email TEXT;

COMMENT ON COLUMN contacts.zoho_email IS
'Email address from Zoho CRM (may differ from primary email)';

-- Add Zoho phone field (for alternate phone from Zoho)
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS zoho_phone TEXT;

COMMENT ON COLUMN contacts.zoho_phone IS
'Phone number from Zoho CRM (may differ from primary phone)';

-- Add source tracking for Zoho phone
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS zoho_phone_source TEXT;

COMMENT ON COLUMN contacts.zoho_phone_source IS
'Source system for Zoho phone number (e.g., zoho_crm)';

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_contacts_zoho_email
ON contacts(zoho_email)
WHERE zoho_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_zoho_phone
ON contacts(zoho_phone)
WHERE zoho_phone IS NOT NULL;

-- Add validation constraint for email format (if not empty)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_zoho_email_format'
    ) THEN
        ALTER TABLE contacts
        ADD CONSTRAINT check_zoho_email_format
        CHECK (
            zoho_email IS NULL OR
            zoho_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        );
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify columns were created
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'contacts'
    AND column_name IN ('zoho_email', 'zoho_phone', 'zoho_phone_source');

    IF column_count < 3 THEN
        RAISE EXCEPTION 'Failed to create all required Zoho columns';
    END IF;

    RAISE NOTICE 'Successfully added % Zoho contact fields', column_count;
END $$;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================
/*
BEGIN;

-- Drop indexes
DROP INDEX IF EXISTS idx_contacts_zoho_email;
DROP INDEX IF EXISTS idx_contacts_zoho_phone;

-- Drop constraint
ALTER TABLE contacts DROP CONSTRAINT IF EXISTS check_zoho_email_format;

-- Drop columns
ALTER TABLE contacts DROP COLUMN IF EXISTS zoho_email;
ALTER TABLE contacts DROP COLUMN IF EXISTS zoho_phone;
ALTER TABLE contacts DROP COLUMN IF EXISTS zoho_phone_source;

COMMIT;
*/
