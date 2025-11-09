-- ============================================================================
-- ENHANCE CONTACTS TABLE WITH PAYPAL DATA
-- ============================================================================
-- Purpose: Add comprehensive PayPal data fields to contacts table
-- This preserves ALL PayPal contact information including:
-- - Business names (for organizational contacts)
-- - Complete shipping addresses
-- - Secondary contact info
-- - PayPal-specific identifiers
-- - Membership group classification (Individual vs Program Partner)
-- ============================================================================

-- Add PayPal business/organization fields
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_business_name text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_payer_id text;

-- Add shipping address fields (separate from billing address)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_address_line_1 text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_address_line_2 text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_city text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_state text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_postal_code text;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_country text;

-- Add shipping address status (Confirmed, Unconfirmed, None)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS shipping_address_status text;

-- Add secondary contact phone (many PayPal transactions include phone)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_phone text;

-- Add PayPal subscription reference (for linking to recurring subscriptions)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS paypal_subscription_reference text;

-- Add membership classification
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS membership_group text; -- 'Individual' or 'Program Partner'
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS membership_level text; -- Nova, Antares, etc.
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS membership_tier text;  -- Entry, Standard, Premium, Elite, Partner
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS is_legacy_member boolean DEFAULT false;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_paypal_business_name
  ON contacts(paypal_business_name)
  WHERE paypal_business_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_paypal_payer_id
  ON contacts(paypal_payer_id)
  WHERE paypal_payer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_membership_group
  ON contacts(membership_group)
  WHERE membership_group IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_membership_level
  ON contacts(membership_level)
  WHERE membership_level IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_membership_tier
  ON contacts(membership_tier)
  WHERE membership_tier IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_paypal_subscription_reference
  ON contacts(paypal_subscription_reference)
  WHERE paypal_subscription_reference IS NOT NULL;

-- Add column comments
COMMENT ON COLUMN contacts.paypal_business_name IS 'Business or organization name from PayPal (for non-individual accounts)';
COMMENT ON COLUMN contacts.paypal_payer_id IS 'PayPal payer ID for tracking recurring subscribers';
COMMENT ON COLUMN contacts.shipping_address_line_1 IS 'Shipping address line 1 from PayPal transactions';
COMMENT ON COLUMN contacts.shipping_address_line_2 IS 'Shipping address line 2 from PayPal transactions';
COMMENT ON COLUMN contacts.shipping_city IS 'Shipping city from PayPal transactions';
COMMENT ON COLUMN contacts.shipping_state IS 'Shipping state/province from PayPal transactions';
COMMENT ON COLUMN contacts.shipping_postal_code IS 'Shipping postal/zip code from PayPal transactions';
COMMENT ON COLUMN contacts.shipping_country IS 'Shipping country from PayPal transactions';
COMMENT ON COLUMN contacts.shipping_address_status IS 'PayPal address verification status (Confirmed, Unconfirmed, None)';
COMMENT ON COLUMN contacts.paypal_phone IS 'Phone number from PayPal transactions';
COMMENT ON COLUMN contacts.paypal_subscription_reference IS 'PayPal subscription reference ID (I-XXXXX format) for tracking recurring subscriptions';
COMMENT ON COLUMN contacts.membership_group IS 'Membership category: Individual or Program Partner';
COMMENT ON COLUMN contacts.membership_level IS 'Membership level: Nova, Antares, Aldebaran, Spica, Luminary, Celestial, Astral, Friend, Advocate';
COMMENT ON COLUMN contacts.membership_tier IS 'Membership tier: Entry, Standard, Premium, Elite, Partner, Legacy';
COMMENT ON COLUMN contacts.is_legacy_member IS 'True if this is a legacy/grandfathered membership';

-- ============================================================================
-- CREATE MEMBERSHIP PRODUCTS TABLE
-- ============================================================================
-- This table maps PayPal "Item Title" to standardized membership products

CREATE TABLE IF NOT EXISTS membership_products (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Product identification
    product_name text NOT NULL,
    product_slug text NOT NULL UNIQUE,

    -- Membership classification
    membership_group text NOT NULL, -- 'Individual' or 'Program Partner'
    membership_level text NOT NULL, -- Nova, Antares, Aldebaran, Spica, etc.
    membership_tier text NOT NULL,  -- Entry, Standard, Premium, Elite, Partner, Legacy

    -- Pricing
    monthly_price numeric(10,2),
    annual_price numeric(10,2),

    -- PayPal Item Title variations (for matching)
    paypal_item_titles text[] NOT NULL,

    -- Features/Description
    description text,
    features jsonb,

    -- Status
    is_active boolean DEFAULT true,
    is_legacy boolean DEFAULT false,

    -- Display order
    sort_order integer,

    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT membership_products_group_check CHECK (
        membership_group IN ('Individual', 'Program Partner')
    ),
    CONSTRAINT membership_products_level_check CHECK (
        membership_level IN ('Nova', 'Antares', 'Aldebaran', 'Spica', 'Luminary Partner', 'Celestial Partner', 'Astral Partner', 'Friend', 'Advocate')
    ),
    CONSTRAINT membership_products_tier_check CHECK (
        membership_tier IN ('Entry', 'Standard', 'Premium', 'Elite', 'Partner', 'Legacy')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_membership_products_group ON membership_products(membership_group);
CREATE INDEX IF NOT EXISTS idx_membership_products_level ON membership_products(membership_level);
CREATE INDEX IF NOT EXISTS idx_membership_products_tier ON membership_products(membership_tier);
CREATE INDEX IF NOT EXISTS idx_membership_products_active ON membership_products(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_membership_products_legacy ON membership_products(is_legacy) WHERE is_legacy = true;

-- Gin index for array matching
CREATE INDEX IF NOT EXISTS idx_membership_products_paypal_titles
  ON membership_products USING gin(paypal_item_titles);

COMMENT ON TABLE membership_products IS 'Standardized membership products mapped from PayPal Item Titles';

-- ============================================================================
-- POPULATE MEMBERSHIP PRODUCTS
-- ============================================================================
-- Based on actual StarHouse membership structure:
-- - Individual Membership: Nova, Antares, Aldebaran, Spica, Friend (legacy), Advocate (legacy)
-- - Program Partner: Luminary, Celestial, Astral

INSERT INTO membership_products (
    product_name,
    product_slug,
    membership_group,
    membership_level,
    membership_tier,
    monthly_price,
    annual_price,
    paypal_item_titles,
    description,
    is_active,
    is_legacy,
    sort_order
) VALUES
    -- INDIVIDUAL MEMBERSHIPS
    (
        'Nova Individual Membership',
        'nova-individual',
        'Individual',
        'Nova',
        'Entry',
        12.00,
        144.00,
        ARRAY['Nova StarHouse Membership', 'nova starhouse membership'],
        'Entry-level individual StarHouse membership',
        true,
        false,
        1
    ),
    (
        'Antares Individual Membership',
        'antares-individual',
        'Individual',
        'Antares',
        'Standard',
        22.00,
        242.00,
        ARRAY['Antares StarHouse Membership', 'antares starhouse membership'],
        'Standard individual StarHouse membership - Most Popular!',
        true,
        false,
        2
    ),
    (
        'Aldebaran Individual Membership',
        'aldebaran-individual',
        'Individual',
        'Aldebaran',
        'Premium',
        44.00,
        484.00,
        ARRAY['Aldebaran StarHouse Membership', 'aldebaran starhouse membership'],
        'Premium individual StarHouse membership',
        true,
        false,
        3
    ),
    (
        'Spica Individual Membership',
        'spica-individual',
        'Individual',
        'Spica',
        'Elite',
        88.00,
        986.00,
        ARRAY['Spica StarHouse Membership', 'spica starhouse membership'],
        'Elite individual StarHouse membership with all benefits',
        true,
        false,
        4
    ),
    (
        'Friend Membership',
        'friend-membership',
        'Individual',
        'Friend',
        'Legacy',
        45.00,
        NULL,
        ARRAY['Friend', 'friend membership'],
        'Legacy Friend membership (grandfathered)',
        true,
        true,
        5
    ),
    (
        'Advocate Individual Membership',
        'advocate-individual',
        'Individual',
        'Advocate',
        'Legacy',
        450.00,
        NULL,
        ARRAY['Advocate Individual'],
        'Legacy Advocate individual membership',
        true,
        true,
        6
    ),

    -- PROGRAM PARTNER MEMBERSHIPS
    (
        'Luminary Partner',
        'luminary-partner',
        'Program Partner',
        'Luminary Partner',
        'Partner',
        33.00,
        363.00,
        ARRAY['Program Partner Luminary', 'Luminary Partner'],
        'Program Partner at Luminary level',
        true,
        false,
        7
    ),
    (
        'Celestial Partner',
        'celestial-partner',
        'Program Partner',
        'Celestial Partner',
        'Partner',
        55.00,
        605.00,
        ARRAY['Program Partners Celestial Tier', 'Celestial Partner'],
        'Program Partner at Celestial level',
        true,
        false,
        8
    ),
    (
        'Astral Partner',
        'astral-partner',
        'Program Partner',
        'Astral Partner',
        'Partner',
        99.00,
        1089.00,
        ARRAY['Program Partners Astral Tier', 'Astral Partner'],
        'Program Partner at Astral level',
        true,
        false,
        9
    )
ON CONFLICT (product_slug) DO UPDATE SET
    membership_group = EXCLUDED.membership_group,
    membership_level = EXCLUDED.membership_level,
    membership_tier = EXCLUDED.membership_tier,
    monthly_price = EXCLUDED.monthly_price,
    annual_price = EXCLUDED.annual_price,
    paypal_item_titles = EXCLUDED.paypal_item_titles,
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active,
    is_legacy = EXCLUDED.is_legacy,
    updated_at = now();

-- ============================================================================
-- HELPER FUNCTION: Get membership product from PayPal Item Title
-- ============================================================================

CREATE OR REPLACE FUNCTION get_membership_product_from_title(item_title text)
RETURNS TABLE(
    product_id uuid,
    product_name text,
    membership_group text,
    membership_level text,
    membership_tier text,
    monthly_price numeric,
    annual_price numeric,
    is_legacy boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mp.id,
        mp.product_name,
        mp.membership_group,
        mp.membership_level,
        mp.membership_tier,
        mp.monthly_price,
        mp.annual_price,
        mp.is_legacy
    FROM membership_products mp
    WHERE item_title ILIKE ANY(mp.paypal_item_titles)
       OR item_title = ANY(mp.paypal_item_titles)
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_membership_product_from_title IS 'Returns standardized membership product from PayPal Item Title string';

-- ============================================================================
-- HELPER FUNCTION: Detect if amount is annual payment
-- ============================================================================

CREATE OR REPLACE FUNCTION is_annual_payment(item_title text, amount numeric)
RETURNS boolean AS $$
DECLARE
    product record;
BEGIN
    -- Get product info
    SELECT * INTO product FROM get_membership_product_from_title(item_title);

    IF product IS NULL THEN
        RETURN false;
    END IF;

    -- Check if amount matches annual price (with some tolerance for fees)
    IF product.annual_price IS NOT NULL THEN
        RETURN abs(amount - product.annual_price) < 5; -- Within $5 tolerance
    END IF;

    RETURN false;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_annual_payment IS 'Detects if a payment amount represents an annual subscription';

-- ============================================================================
-- ADD SUBSCRIPTION TABLE ENHANCEMENTS
-- ============================================================================

-- Add membership product reference to subscriptions
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS membership_product_id uuid
    REFERENCES membership_products(id);

-- Add PayPal subscription reference
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS paypal_subscription_reference text;

-- Add billing frequency flag
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_annual boolean DEFAULT false;

-- Add index
CREATE INDEX IF NOT EXISTS idx_subscriptions_membership_product
    ON subscriptions(membership_product_id)
    WHERE membership_product_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_subscriptions_paypal_reference
    ON subscriptions(paypal_subscription_reference)
    WHERE paypal_subscription_reference IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_subscriptions_annual
    ON subscriptions(is_annual)
    WHERE is_annual = true;

COMMENT ON COLUMN subscriptions.membership_product_id IS 'Links subscription to standardized membership product';
COMMENT ON COLUMN subscriptions.paypal_subscription_reference IS 'PayPal subscription reference ID (I-XXXXX format)';
COMMENT ON COLUMN subscriptions.is_annual IS 'True if this is an annual subscription (vs monthly)';

-- ============================================================================
-- CREATE VIEW: Membership Summary by Group
-- ============================================================================

CREATE OR REPLACE VIEW v_membership_summary_by_group AS
SELECT
    c.membership_group,
    c.membership_level,
    c.membership_tier,
    COUNT(*) as member_count,
    COUNT(*) FILTER (WHERE c.is_legacy_member = true) as legacy_count,
    COUNT(*) FILTER (WHERE s.status = 'active') as active_subscriptions,
    SUM(s.amount) FILTER (WHERE s.status = 'active') as total_monthly_revenue,
    AVG(s.amount) FILTER (WHERE s.status = 'active') as avg_subscription_amount
FROM contacts c
LEFT JOIN subscriptions s ON c.id = s.contact_id
    AND s.id = (
        SELECT s2.id FROM subscriptions s2
        WHERE s2.contact_id = c.id
        ORDER BY s2.created_at DESC
        LIMIT 1
    )
WHERE c.membership_level IS NOT NULL
GROUP BY c.membership_group, c.membership_level, c.membership_tier
ORDER BY
    CASE c.membership_group
        WHEN 'Individual' THEN 1
        WHEN 'Program Partner' THEN 2
        ELSE 3
    END,
    c.sort_order;

COMMENT ON VIEW v_membership_summary_by_group IS 'Membership statistics grouped by Individual vs Program Partner';

-- ============================================================================
-- CREATE TABLE: Legacy Program Partner Corrections
-- ============================================================================
-- This table tracks members who are Individual but should be Program Partners

CREATE TABLE IF NOT EXISTS legacy_program_partner_corrections (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id uuid REFERENCES contacts(id),
    contact_email text NOT NULL,
    current_group text NOT NULL, -- Current (incorrect) group
    correct_group text NOT NULL, -- Should be 'Program Partner'
    correct_level text,          -- Correct partner level
    notes text,
    corrected boolean DEFAULT false,
    corrected_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT legacy_corrections_groups_check CHECK (
        current_group IN ('Individual', 'Program Partner') AND
        correct_group IN ('Individual', 'Program Partner')
    )
);

CREATE INDEX IF NOT EXISTS idx_legacy_corrections_contact
    ON legacy_program_partner_corrections(contact_id);

CREATE INDEX IF NOT EXISTS idx_legacy_corrections_uncorrected
    ON legacy_program_partner_corrections(corrected)
    WHERE corrected = false;

COMMENT ON TABLE legacy_program_partner_corrections IS 'Tracks members that need to be reclassified from Individual to Program Partner';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Contacts table enhanced with PayPal data fields';
    RAISE NOTICE '✅ Membership products table created with 9 membership levels:';
    RAISE NOTICE '   📋 Individual: Nova, Antares, Aldebaran, Spica, Friend (legacy), Advocate (legacy)';
    RAISE NOTICE '   📋 Program Partner: Luminary, Celestial, Astral';
    RAISE NOTICE '✅ Subscription table enhanced with annual billing support';
    RAISE NOTICE '✅ Legacy program partner corrections table created';
    RAISE NOTICE '✅ Helper functions created:';
    RAISE NOTICE '   - get_membership_product_from_title()';
    RAISE NOTICE '   - is_annual_payment()';
    RAISE NOTICE '✅ Ready to import PayPal transaction data!';
END $$;
