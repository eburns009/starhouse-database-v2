-- Migration: Add Address & Phone Metadata Tracking
-- Purpose: Track verification status and source for addresses/phone numbers
-- Approach: Hybrid - enhance existing denormalized schema with metadata
-- Date: 2025-11-01

BEGIN;

-- ============================================
-- PHONE ENHANCEMENTS
-- ============================================

ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS phone_country_code text,
  ADD COLUMN IF NOT EXISTS phone_verified boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS phone_source text; -- 'kajabi', 'ticket_tailor', 'paypal', 'manual'

COMMENT ON COLUMN contacts.phone_country_code IS 'ISO 3166-1 alpha-2 country code for phone number (e.g., US, CA, GB)';
COMMENT ON COLUMN contacts.phone_verified IS 'Whether phone number has been verified (e.g., via SMS, carrier lookup)';
COMMENT ON COLUMN contacts.phone_source IS 'System that provided this phone number: kajabi, ticket_tailor, paypal, manual';

-- ============================================
-- BILLING ADDRESS METADATA
-- ============================================

ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS billing_address_source text, -- 'kajabi', 'paypal', 'ticket_tailor', 'manual', 'unknown_legacy'
  ADD COLUMN IF NOT EXISTS billing_address_verified boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS billing_address_updated_at timestamptz;

COMMENT ON COLUMN contacts.billing_address_source IS 'System that provided billing address: kajabi, paypal, ticket_tailor, manual, unknown_legacy';
COMMENT ON COLUMN contacts.billing_address_verified IS 'Whether billing address has been verified by payment processor or USPS';
COMMENT ON COLUMN contacts.billing_address_updated_at IS 'When billing address was last updated';

-- ============================================
-- SHIPPING ADDRESS METADATA
-- ============================================

ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS shipping_address_source text, -- 'paypal', 'manual', 'copied_from_billing', 'unknown_legacy'
  ADD COLUMN IF NOT EXISTS shipping_address_verified boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS shipping_address_updated_at timestamptz;

COMMENT ON COLUMN contacts.shipping_address_source IS 'System that provided shipping address: paypal, manual, copied_from_billing, unknown_legacy';
COMMENT ON COLUMN contacts.shipping_address_verified IS 'Whether shipping address has been verified (e.g., PayPal verified, USPS verified)';
COMMENT ON COLUMN contacts.shipping_address_updated_at IS 'When shipping address was last updated';

-- ============================================
-- BACKFILL EXISTING DATA
-- ============================================

-- Mark existing shipping addresses based on shipping_address_status
UPDATE contacts
SET
  shipping_address_source = CASE
    WHEN shipping_address_status = 'Confirmed' THEN 'unknown_legacy'
    WHEN address_line_1 = shipping_address_line_1
      AND city = shipping_city
      AND state = shipping_state
      AND postal_code = shipping_postal_code
      THEN 'copied_from_billing'
    ELSE 'unknown_legacy'
  END,
  shipping_address_verified = CASE
    WHEN shipping_address_status = 'Confirmed' THEN true
    ELSE false
  END,
  shipping_address_updated_at = COALESCE(updated_at, created_at)
WHERE shipping_address_line_1 IS NOT NULL
  AND shipping_address_line_1 != ''
  AND shipping_address_source IS NULL;

-- Mark existing billing addresses
UPDATE contacts
SET
  billing_address_source = 'unknown_legacy',
  billing_address_verified = false,
  billing_address_updated_at = COALESCE(updated_at, created_at)
WHERE address_line_1 IS NOT NULL
  AND address_line_1 != ''
  AND billing_address_source IS NULL;

-- Mark existing phone numbers
UPDATE contacts
SET
  phone_source = CASE
    WHEN source_system = 'kajabi' THEN 'kajabi'
    WHEN source_system = 'ticket_tailor' THEN 'ticket_tailor'
    WHEN paypal_phone IS NOT NULL THEN 'paypal'
    ELSE 'unknown_legacy'
  END,
  phone_verified = false
WHERE phone IS NOT NULL
  AND phone != ''
  AND phone_source IS NULL;

-- ============================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_contacts_billing_verified
  ON contacts(billing_address_verified)
  WHERE address_line_1 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_shipping_verified
  ON contacts(shipping_address_verified)
  WHERE shipping_address_line_1 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_phone_verified
  ON contacts(phone_verified)
  WHERE phone IS NOT NULL;

-- ============================================
-- MONITORING VIEWS
-- ============================================

-- View: Address verification rates by source
CREATE OR REPLACE VIEW address_verification_stats AS
SELECT
  'billing' as address_type,
  billing_address_source as source,
  COUNT(*) as total_addresses,
  SUM(CASE WHEN billing_address_verified THEN 1 ELSE 0 END) as verified_count,
  ROUND(100.0 * SUM(CASE WHEN billing_address_verified THEN 1 ELSE 0 END) / COUNT(*), 2) as verified_pct
FROM contacts
WHERE address_line_1 IS NOT NULL AND address_line_1 != ''
GROUP BY billing_address_source

UNION ALL

SELECT
  'shipping' as address_type,
  shipping_address_source as source,
  COUNT(*) as total_addresses,
  SUM(CASE WHEN shipping_address_verified THEN 1 ELSE 0 END) as verified_count,
  ROUND(100.0 * SUM(CASE WHEN shipping_address_verified THEN 1 ELSE 0 END) / COUNT(*), 2) as verified_pct
FROM contacts
WHERE shipping_address_line_1 IS NOT NULL AND shipping_address_line_1 != ''
GROUP BY shipping_address_source

ORDER BY address_type, total_addresses DESC;

COMMENT ON VIEW address_verification_stats IS 'Shows verification rates for addresses by source system';

-- View: Phone verification stats
CREATE OR REPLACE VIEW phone_verification_stats AS
SELECT
  phone_source as source,
  COUNT(*) as total_phones,
  SUM(CASE WHEN phone_verified THEN 1 ELSE 0 END) as verified_count,
  ROUND(100.0 * SUM(CASE WHEN phone_verified THEN 1 ELSE 0 END) / COUNT(*), 2) as verified_pct,
  COUNT(DISTINCT phone_country_code) as countries
FROM contacts
WHERE phone IS NOT NULL AND phone != ''
GROUP BY phone_source
ORDER BY total_phones DESC;

COMMENT ON VIEW phone_verification_stats IS 'Shows verification rates for phone numbers by source system';

-- ============================================
-- VALIDATION FUNCTION
-- ============================================

-- Function to validate and standardize country codes
CREATE OR REPLACE FUNCTION standardize_country_code(input_country text)
RETURNS char(2) AS $$
DECLARE
  country_upper text;
  country_map jsonb := '{
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "USA": "US",
    "CANADA": "CA",
    "UNITED KINGDOM": "GB",
    "UK": "GB",
    "GREAT BRITAIN": "GB",
    "AUSTRALIA": "AU",
    "NEW ZEALAND": "NZ",
    "FRANCE": "FR",
    "GERMANY": "DE",
    "SPAIN": "ES",
    "ITALY": "IT",
    "NETHERLANDS": "NL",
    "BELGIUM": "BE",
    "SWITZERLAND": "CH",
    "AUSTRIA": "AT",
    "DENMARK": "DK",
    "SWEDEN": "SE",
    "NORWAY": "NO",
    "FINLAND": "FI",
    "IRELAND": "IE",
    "POLAND": "PL",
    "CZECH REPUBLIC": "CZ",
    "PORTUGAL": "PT",
    "GREECE": "GR",
    "HUNGARY": "HU",
    "ROMANIA": "RO",
    "BULGARIA": "BG",
    "CROATIA": "HR",
    "SLOVAKIA": "SK",
    "SLOVENIA": "SI",
    "LITHUANIA": "LT",
    "LATVIA": "LV",
    "ESTONIA": "EE",
    "MEXICO": "MX",
    "BRAZIL": "BR",
    "ARGENTINA": "AR",
    "CHILE": "CL",
    "COLOMBIA": "CO",
    "PERU": "PE",
    "VENEZUELA": "VE",
    "JAPAN": "JP",
    "CHINA": "CN",
    "SOUTH KOREA": "KR",
    "INDIA": "IN",
    "SINGAPORE": "SG",
    "MALAYSIA": "MY",
    "THAILAND": "TH",
    "VIETNAM": "VN",
    "PHILIPPINES": "PH",
    "INDONESIA": "ID",
    "TAIWAN": "TW",
    "HONG KONG": "HK",
    "ISRAEL": "IL",
    "SAUDI ARABIA": "SA",
    "UAE": "AE",
    "SOUTH AFRICA": "ZA",
    "EGYPT": "EG",
    "NIGERIA": "NG",
    "KENYA": "KE",
    "RUSSIA": "RU",
    "TURKEY": "TR",
    "COSTA RICA": "CR"
  }'::jsonb;
BEGIN
  -- Return NULL for empty input
  IF input_country IS NULL OR input_country = '' THEN
    RETURN NULL;
  END IF;

  country_upper := UPPER(TRIM(input_country));

  -- Check if it's in the mapping
  IF country_map ? country_upper THEN
    RETURN (country_map ->> country_upper)::char(2);
  END IF;

  -- If already 2 characters, assume it's ISO code
  IF LENGTH(country_upper) = 2 THEN
    RETURN country_upper::char(2);
  END IF;

  -- Otherwise, take first 2 characters (may need manual cleanup)
  RETURN SUBSTRING(country_upper, 1, 2)::char(2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION standardize_country_code IS 'Converts country name or code to ISO 3166-1 alpha-2 format';

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant read access to views
GRANT SELECT ON address_verification_stats TO authenticated;
GRANT SELECT ON phone_verification_stats TO authenticated;

-- ============================================
-- VERIFICATION
-- ============================================

-- Show stats after migration
DO $$
BEGIN
  RAISE NOTICE '===========================================';
  RAISE NOTICE 'Migration Complete: Address & Phone Metadata';
  RAISE NOTICE '===========================================';
  RAISE NOTICE '';
  RAISE NOTICE 'Run these queries to verify:';
  RAISE NOTICE '';
  RAISE NOTICE '1. SELECT * FROM address_verification_stats;';
  RAISE NOTICE '2. SELECT * FROM phone_verification_stats;';
  RAISE NOTICE '';
  RAISE NOTICE '3. Check billing addresses:';
  RAISE NOTICE '   SELECT billing_address_source, COUNT(*) FROM contacts';
  RAISE NOTICE '   WHERE address_line_1 IS NOT NULL GROUP BY 1;';
  RAISE NOTICE '';
  RAISE NOTICE '4. Check shipping addresses:';
  RAISE NOTICE '   SELECT shipping_address_source, COUNT(*) FROM contacts';
  RAISE NOTICE '   WHERE shipping_address_line_1 IS NOT NULL GROUP BY 1;';
  RAISE NOTICE '';
END $$;

COMMIT;
