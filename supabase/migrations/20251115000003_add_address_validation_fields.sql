-- Migration: Add Address Validation and Duplicate Management Fields
-- Date: 2025-11-15
-- Purpose: Enable mailing list quality tracking and duplicate consolidation
-- Impact: Schema enhancement for Phase 2 & 3 mailing list improvements

-- ============================================================================
-- ADDRESS VALIDATION FIELDS
-- ============================================================================

-- Track if address has been validated with USPS or other service
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS address_validated BOOLEAN DEFAULT FALSE;

-- Store USPS DPV (Delivery Point Validation) confirmation code
-- 'Y' = Confirmed, 'N' = Not confirmed, 'S' = Secondary confirmed, 'D' = Missing secondary
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS usps_dpv_confirmation VARCHAR(1) CHECK (usps_dpv_confirmation IN ('Y', 'N', 'S', 'D'));

-- Track when address was last validated
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS usps_validation_date TIMESTAMP WITH TIME ZONE;

-- Store USPS RDI (Residential Delivery Indicator)
-- 'Residential' or 'Commercial'
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS usps_rdi VARCHAR(20);

-- NCOA (National Change of Address) tracking
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS ncoa_move_date DATE;

ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS ncoa_new_address TEXT;

-- Address quality score (0-100)
-- 100 = Perfect (validated, DPV confirmed, no NCOA)
-- 50-99 = Good (validated, minor issues)
-- 0-49 = Poor (not validated or failed validation)
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS address_quality_score INTEGER CHECK (address_quality_score BETWEEN 0 AND 100);

-- ============================================================================
-- MAILING LIST READINESS
-- ============================================================================

-- Computed column: Is contact ready for mailing?
-- Requires: complete address + validation
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS mailing_list_ready BOOLEAN
GENERATED ALWAYS AS (
    address_line_1 IS NOT NULL
    AND city IS NOT NULL
    AND state IS NOT NULL
    AND postal_code IS NOT NULL
    AND (address_validated = TRUE OR address_validated IS NULL)
) STORED;

-- ============================================================================
-- HOUSEHOLD MANAGEMENT
-- ============================================================================

-- Group household members together (same address, different people)
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS household_id UUID;

-- Mark primary contact for household mailings (send one piece per household)
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS is_primary_household_contact BOOLEAN DEFAULT TRUE;

-- ============================================================================
-- DUPLICATE CONSOLIDATION
-- ============================================================================

-- Store secondary/alternate emails (for phone duplicates - same person, multiple emails)
-- Format: ["email1@example.com", "email2@example.com"]
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS secondary_emails JSONB DEFAULT '[]';

-- If this contact is an alias of another (duplicate)
-- Points to the primary contact record
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS is_alias_of UUID REFERENCES contacts(id) ON DELETE SET NULL;

-- Track merge history
-- Format: [{"merged_from_id": "uuid", "merged_at": "timestamp", "reason": "phone_duplicate"}]
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS merge_history JSONB DEFAULT '[]';

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index for mailing list queries
CREATE INDEX IF NOT EXISTS idx_contacts_mailing_ready
ON contacts(mailing_list_ready)
WHERE mailing_list_ready = TRUE;

-- Index for address validation status
CREATE INDEX IF NOT EXISTS idx_contacts_address_validated
ON contacts(address_validated)
WHERE address_validated = TRUE;

-- Index for household grouping
CREATE INDEX IF NOT EXISTS idx_contacts_household_id
ON contacts(household_id)
WHERE household_id IS NOT NULL;

-- Index for finding aliases
CREATE INDEX IF NOT EXISTS idx_contacts_is_alias_of
ON contacts(is_alias_of)
WHERE is_alias_of IS NOT NULL;

-- Index for USPS validation lookups
CREATE INDEX IF NOT EXISTS idx_contacts_usps_validation
ON contacts(usps_dpv_confirmation, usps_validation_date);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON COLUMN contacts.address_validated IS 'Whether address has been validated with USPS or other service';
COMMENT ON COLUMN contacts.usps_dpv_confirmation IS 'USPS DPV code: Y=Confirmed, N=Not confirmed, S=Secondary, D=Missing secondary';
COMMENT ON COLUMN contacts.usps_validation_date IS 'Timestamp of last USPS validation';
COMMENT ON COLUMN contacts.usps_rdi IS 'USPS Residential Delivery Indicator: Residential or Commercial';
COMMENT ON COLUMN contacts.ncoa_move_date IS 'Date contact moved to new address (from NCOA database)';
COMMENT ON COLUMN contacts.ncoa_new_address IS 'New address from NCOA if contact has moved';
COMMENT ON COLUMN contacts.address_quality_score IS 'Address quality score 0-100 (100=perfect, validated)';
COMMENT ON COLUMN contacts.mailing_list_ready IS 'Computed: Has complete validated address ready for mailing';
COMMENT ON COLUMN contacts.household_id IS 'Groups household members at same address';
COMMENT ON COLUMN contacts.is_primary_household_contact IS 'Primary contact for household mailings';
COMMENT ON COLUMN contacts.secondary_emails IS 'Array of secondary/alternate email addresses';
COMMENT ON COLUMN contacts.is_alias_of IS 'References primary contact if this is a duplicate/alias';
COMMENT ON COLUMN contacts.merge_history IS 'History of merged contact records';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify columns were added
DO $$
DECLARE
    missing_columns TEXT[];
BEGIN
    SELECT ARRAY_AGG(column_name)
    INTO missing_columns
    FROM (
        VALUES
            ('address_validated'),
            ('usps_dpv_confirmation'),
            ('usps_validation_date'),
            ('mailing_list_ready'),
            ('household_id'),
            ('secondary_emails'),
            ('is_alias_of')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'contacts'
        AND column_name = expected.column_name
    );

    IF missing_columns IS NOT NULL THEN
        RAISE EXCEPTION 'Migration failed: Missing columns: %', array_to_string(missing_columns, ', ');
    ELSE
        RAISE NOTICE 'Migration successful: All columns added';
    END IF;
END $$;
