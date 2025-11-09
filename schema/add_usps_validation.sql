-- Add USPS address validation fields to contacts table
-- This migration adds comprehensive USPS validation metadata for both billing and shipping addresses

BEGIN;

-- Billing Address USPS Validation Fields
ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS billing_usps_validated_at timestamp with time zone,
  ADD COLUMN IF NOT EXISTS billing_usps_dpv_match_code text,
  ADD COLUMN IF NOT EXISTS billing_usps_precision text,
  ADD COLUMN IF NOT EXISTS billing_usps_delivery_line_1 text,
  ADD COLUMN IF NOT EXISTS billing_usps_delivery_line_2 text,
  ADD COLUMN IF NOT EXISTS billing_usps_last_line text,
  ADD COLUMN IF NOT EXISTS billing_usps_latitude numeric(10,7),
  ADD COLUMN IF NOT EXISTS billing_usps_longitude numeric(10,7),
  ADD COLUMN IF NOT EXISTS billing_usps_county text,
  ADD COLUMN IF NOT EXISTS billing_usps_rdi text,
  ADD COLUMN IF NOT EXISTS billing_usps_footnotes text,
  ADD COLUMN IF NOT EXISTS billing_usps_vacant boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS billing_usps_active boolean DEFAULT true;

-- Shipping Address USPS Validation Fields
ALTER TABLE contacts
  ADD COLUMN IF NOT EXISTS shipping_usps_validated_at timestamp with time zone,
  ADD COLUMN IF NOT EXISTS shipping_usps_dpv_match_code text,
  ADD COLUMN IF NOT EXISTS shipping_usps_precision text,
  ADD COLUMN IF NOT EXISTS shipping_usps_delivery_line_1 text,
  ADD COLUMN IF NOT EXISTS shipping_usps_delivery_line_2 text,
  ADD COLUMN IF NOT EXISTS shipping_usps_last_line text,
  ADD COLUMN IF NOT EXISTS shipping_usps_latitude numeric(10,7),
  ADD COLUMN IF NOT EXISTS shipping_usps_longitude numeric(10,7),
  ADD COLUMN IF NOT EXISTS shipping_usps_county text,
  ADD COLUMN IF NOT EXISTS shipping_usps_rdi text,
  ADD COLUMN IF NOT EXISTS shipping_usps_footnotes text,
  ADD COLUMN IF NOT EXISTS shipping_usps_vacant boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS shipping_usps_active boolean DEFAULT true;

-- Add comments for documentation
COMMENT ON COLUMN contacts.billing_usps_validated_at IS 'Timestamp when address was validated with USPS';
COMMENT ON COLUMN contacts.billing_usps_dpv_match_code IS 'USPS Delivery Point Validation: Y=confirmed, D=missing secondary, N=not confirmed';
COMMENT ON COLUMN contacts.billing_usps_precision IS 'Address precision: Zip9, Zip7, Zip5, Unknown';
COMMENT ON COLUMN contacts.billing_usps_delivery_line_1 IS 'USPS standardized delivery address line 1';
COMMENT ON COLUMN contacts.billing_usps_delivery_line_2 IS 'USPS standardized delivery address line 2 (if applicable)';
COMMENT ON COLUMN contacts.billing_usps_last_line IS 'USPS standardized last line: City ST ZIP+4';
COMMENT ON COLUMN contacts.billing_usps_latitude IS 'Geocoded latitude';
COMMENT ON COLUMN contacts.billing_usps_longitude IS 'Geocoded longitude';
COMMENT ON COLUMN contacts.billing_usps_county IS 'County name';
COMMENT ON COLUMN contacts.billing_usps_rdi IS 'Residential Delivery Indicator: Residential, Commercial, or Unknown';
COMMENT ON COLUMN contacts.billing_usps_footnotes IS 'Human-readable validation notes from USPS';
COMMENT ON COLUMN contacts.billing_usps_vacant IS 'Is the delivery point vacant';
COMMENT ON COLUMN contacts.billing_usps_active IS 'Is the delivery point active';

COMMENT ON COLUMN contacts.shipping_usps_validated_at IS 'Timestamp when address was validated with USPS';
COMMENT ON COLUMN contacts.shipping_usps_dpv_match_code IS 'USPS Delivery Point Validation: Y=confirmed, D=missing secondary, N=not confirmed';
COMMENT ON COLUMN contacts.shipping_usps_precision IS 'Address precision: Zip9, Zip7, Zip5, Unknown';
COMMENT ON COLUMN contacts.shipping_usps_delivery_line_1 IS 'USPS standardized delivery address line 1';
COMMENT ON COLUMN contacts.shipping_usps_delivery_line_2 IS 'USPS standardized delivery address line 2 (if applicable)';
COMMENT ON COLUMN contacts.shipping_usps_last_line IS 'USPS standardized last line: City ST ZIP+4';
COMMENT ON COLUMN contacts.shipping_usps_latitude IS 'Geocoded latitude';
COMMENT ON COLUMN contacts.shipping_usps_longitude IS 'Geocoded longitude';
COMMENT ON COLUMN contacts.shipping_usps_county IS 'County name';
COMMENT ON COLUMN contacts.shipping_usps_rdi IS 'Residential Delivery Indicator: Residential, Commercial, or Unknown';
COMMENT ON COLUMN contacts.shipping_usps_footnotes IS 'Human-readable validation notes from USPS';
COMMENT ON COLUMN contacts.shipping_usps_vacant IS 'Is the delivery point vacant';
COMMENT ON COLUMN contacts.shipping_usps_active IS 'Is the delivery point active';

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_contacts_billing_usps_validated
  ON contacts(billing_usps_validated_at)
  WHERE billing_usps_validated_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_billing_usps_precision
  ON contacts(billing_usps_precision)
  WHERE billing_usps_precision IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_billing_usps_location
  ON contacts(billing_usps_latitude, billing_usps_longitude)
  WHERE billing_usps_latitude IS NOT NULL AND billing_usps_longitude IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_shipping_usps_validated
  ON contacts(shipping_usps_validated_at)
  WHERE shipping_usps_validated_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_shipping_usps_precision
  ON contacts(shipping_usps_precision)
  WHERE shipping_usps_precision IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_shipping_usps_location
  ON contacts(shipping_usps_latitude, shipping_usps_longitude)
  WHERE shipping_usps_latitude IS NOT NULL AND shipping_usps_longitude IS NOT NULL;

-- Create index for county-based queries
CREATE INDEX IF NOT EXISTS idx_contacts_billing_usps_county
  ON contacts(billing_usps_county)
  WHERE billing_usps_county IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_shipping_usps_county
  ON contacts(shipping_usps_county)
  WHERE shipping_usps_county IS NOT NULL;

COMMIT;
