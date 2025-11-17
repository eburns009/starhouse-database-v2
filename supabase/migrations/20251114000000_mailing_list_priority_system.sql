-- ============================================================================
-- MAILING LIST PRIORITY SYSTEM - PHASE 1 IMPLEMENTATION
-- ============================================================================
-- Date: 2025-11-14
-- Purpose: Create address scoring algorithm to determine best mailing address
-- ============================================================================

-- Step 1: Create the address scoring function
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_address_score(
  address_type TEXT,  -- 'billing' or 'shipping'
  contact_id UUID
) RETURNS INTEGER AS $$
DECLARE
  score INTEGER := 0;
  update_date TIMESTAMP WITH TIME ZONE;
  usps_date TIMESTAMP WITH TIME ZONE;
  verified BOOLEAN;
  source TEXT;
  last_txn_date TIMESTAMP WITH TIME ZONE;
  contact_record RECORD;
BEGIN
  -- Get the contact record
  SELECT * INTO contact_record FROM contacts WHERE id = contact_id;
  
  IF NOT FOUND THEN
    RETURN 0;
  END IF;
  
  -- Get the right fields based on address type
  IF address_type = 'billing' THEN
    update_date := contact_record.billing_address_updated_at;
    usps_date := contact_record.billing_usps_validated_at;
    verified := contact_record.billing_address_verified;
    source := contact_record.billing_address_source;
  ELSIF address_type = 'shipping' THEN
    update_date := contact_record.shipping_address_updated_at;
    usps_date := contact_record.shipping_usps_validated_at;
    verified := contact_record.shipping_address_verified;
    source := contact_record.shipping_address_source;
  ELSE
    RETURN 0;
  END IF;
  
  last_txn_date := contact_record.last_transaction_date;
  
  -- FACTOR 1: RECENCY (40 points max)
  -- More recently updated = more likely to be current
  IF update_date IS NOT NULL THEN
    IF update_date > NOW() - INTERVAL '30 days' THEN
      score := score + 40;
    ELSIF update_date > NOW() - INTERVAL '90 days' THEN
      score := score + 30;
    ELSIF update_date > NOW() - INTERVAL '180 days' THEN
      score := score + 20;
    ELSIF update_date > NOW() - INTERVAL '365 days' THEN
      score := score + 10;
    END IF;
  END IF;
  
  -- FACTOR 2: USPS VALIDATION (25 points max)
  -- USPS validated addresses are deliverable
  IF usps_date IS NOT NULL THEN
    IF usps_date > NOW() - INTERVAL '90 days' THEN
      score := score + 25;
    ELSIF usps_date > NOW() - INTERVAL '365 days' THEN
      score := score + 20;
    ELSE
      score := score + 10;
    END IF;
  ELSIF verified THEN
    score := score + 5;
  END IF;
  
  -- FACTOR 3: TRANSACTION RECENCY (25 points max)
  -- Active customers likely have current addresses
  IF last_txn_date IS NOT NULL THEN
    IF last_txn_date > NOW() - INTERVAL '30 days' THEN
      score := score + 25;
    ELSIF last_txn_date > NOW() - INTERVAL '90 days' THEN
      score := score + 20;
    ELSIF last_txn_date > NOW() - INTERVAL '180 days' THEN
      score := score + 15;
    ELSIF last_txn_date > NOW() - INTERVAL '365 days' THEN
      score := score + 10;
    ELSE
      score := score + 5;
    END IF;
  END IF;
  
  -- FACTOR 4: SOURCE TRUST (10 points max, with penalties)
  -- PayPal addresses from actual transactions are most reliable
  IF source = 'paypal' THEN
    score := score + 10;
  ELSIF source = 'kajabi' THEN
    score := score + 8;
  ELSIF source = 'manual' THEN
    score := score + 7;
  ELSIF source = 'copied_from_billing' THEN
    score := score - 10;  -- PENALTY: derived data, not authoritative
  ELSIF source = 'unknown_legacy' THEN
    score := score - 5;   -- PENALTY: old data, uncertain origin
  END IF;
  
  RETURN score;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION calculate_address_score IS 
  'Scores an address (0-100) based on recency, validation, transaction history, and source trust';


-- Step 2: Create the mailing list priority view
-- ============================================================================

CREATE OR REPLACE VIEW mailing_list_priority AS
WITH address_scores AS (
  SELECT 
    c.id,
    c.email,
    c.first_name,
    c.last_name,
    
    -- Billing address
    c.address_line_1 as billing_line1,
    c.address_line_2 as billing_line2,
    c.city as billing_city,
    c.state as billing_state,
    c.postal_code as billing_zip,
    c.country as billing_country,
    
    -- Shipping address
    c.shipping_address_line_1 as shipping_line1,
    c.shipping_address_line_2 as shipping_line2,
    c.shipping_city,
    c.shipping_state,
    c.shipping_postal_code as shipping_zip,
    c.shipping_country,
    
    -- Metadata
    c.billing_address_updated_at,
    c.shipping_address_updated_at,
    c.billing_usps_validated_at,
    c.billing_address_verified,
    c.shipping_address_verified,
    c.last_transaction_date,
    c.billing_address_source,
    c.shipping_address_source,
    c.preferred_mailing_address,
    
    -- Calculate scores
    CASE 
      WHEN c.address_line_1 IS NOT NULL 
      THEN calculate_address_score('billing', c.id)
      ELSE 0
    END as billing_score,
    
    CASE 
      WHEN c.shipping_address_line_1 IS NOT NULL 
      THEN calculate_address_score('shipping', c.id)
      ELSE 0
    END as shipping_score
    
  FROM contacts c
  WHERE c.address_line_1 IS NOT NULL OR c.shipping_address_line_1 IS NOT NULL
)
SELECT 
  *,
  
  -- Determine recommended address (with manual override support)
  CASE 
    -- Manual override takes precedence
    WHEN preferred_mailing_address = 'billing' THEN 'billing'
    WHEN preferred_mailing_address = 'shipping' THEN 'shipping'
    
    -- Algorithm: 15 point threshold for switching
    WHEN billing_score >= shipping_score + 15 THEN 'billing'
    WHEN shipping_score >= billing_score + 15 THEN 'shipping'
    
    -- Tie: default to billing
    ELSE 'billing'
  END as recommended_address,
  
  -- Confidence level based on winning score
  CASE 
    WHEN GREATEST(billing_score, shipping_score) >= 75 THEN 'very_high'
    WHEN GREATEST(billing_score, shipping_score) >= 60 THEN 'high'
    WHEN GREATEST(billing_score, shipping_score) >= 45 THEN 'medium'
    WHEN GREATEST(billing_score, shipping_score) >= 30 THEN 'low'
    ELSE 'very_low'
  END as confidence,
  
  -- Override flag
  CASE 
    WHEN preferred_mailing_address IS NOT NULL THEN true
    ELSE false
  END as is_manual_override
  
FROM address_scores;

COMMENT ON VIEW mailing_list_priority IS 
  'Prioritizes billing vs shipping addresses using multi-factor scoring algorithm. Supports manual overrides via preferred_mailing_address column.';


-- Step 3: Add preferred_mailing_address column for manual overrides
-- ============================================================================

DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'contacts' 
    AND column_name = 'preferred_mailing_address'
  ) THEN
    ALTER TABLE contacts ADD COLUMN preferred_mailing_address TEXT;
    
    ALTER TABLE contacts ADD CONSTRAINT preferred_mailing_address_check 
      CHECK (preferred_mailing_address IN ('billing', 'shipping') OR preferred_mailing_address IS NULL);
      
    COMMENT ON COLUMN contacts.preferred_mailing_address IS 
      'Staff override for mailing address selection. Values: billing, shipping, or NULL (use algorithm)';
      
    RAISE NOTICE 'Added preferred_mailing_address column';
  ELSE
    RAISE NOTICE 'preferred_mailing_address column already exists';
  END IF;
END $$;


-- Step 4: Create helper view for final mailing list export
-- ============================================================================

CREATE OR REPLACE VIEW mailing_list_export AS
SELECT 
  first_name,
  last_name,
  email,
  
  -- Selected address fields
  CASE 
    WHEN recommended_address = 'billing' THEN billing_line1
    ELSE shipping_line1
  END as address_line_1,
  
  CASE 
    WHEN recommended_address = 'billing' THEN billing_line2
    ELSE shipping_line2
  END as address_line_2,
  
  CASE 
    WHEN recommended_address = 'billing' THEN billing_city
    ELSE shipping_city
  END as city,
  
  CASE 
    WHEN recommended_address = 'billing' THEN billing_state
    ELSE shipping_state
  END as state,
  
  CASE 
    WHEN recommended_address = 'billing' THEN billing_zip
    ELSE shipping_zip
  END as postal_code,
  
  CASE 
    WHEN recommended_address = 'billing' THEN billing_country
    ELSE shipping_country
  END as country,
  
  -- Metadata
  recommended_address as address_source,
  confidence,
  billing_score,
  shipping_score,
  is_manual_override,
  last_transaction_date
  
FROM mailing_list_priority
WHERE recommended_address IS NOT NULL;

COMMENT ON VIEW mailing_list_export IS 
  'Ready-to-export mailing list with selected addresses and metadata';


-- Step 5: Create statistics view
-- ============================================================================

CREATE OR REPLACE VIEW mailing_list_stats AS
SELECT 
  COUNT(*) as total_contacts,
  COUNT(CASE WHEN recommended_address = 'billing' THEN 1 END) as using_billing,
  COUNT(CASE WHEN recommended_address = 'shipping' THEN 1 END) as using_shipping,
  COUNT(CASE WHEN confidence = 'very_high' THEN 1 END) as very_high_confidence,
  COUNT(CASE WHEN confidence = 'high' THEN 1 END) as high_confidence,
  COUNT(CASE WHEN confidence = 'medium' THEN 1 END) as medium_confidence,
  COUNT(CASE WHEN confidence = 'low' THEN 1 END) as low_confidence,
  COUNT(CASE WHEN confidence = 'very_low' THEN 1 END) as very_low_confidence,
  COUNT(CASE WHEN is_manual_override THEN 1 END) as manual_overrides,
  ROUND(AVG(GREATEST(billing_score, shipping_score)), 1) as avg_score
FROM mailing_list_priority;

COMMENT ON VIEW mailing_list_stats IS 
  'Summary statistics for mailing list quality';

