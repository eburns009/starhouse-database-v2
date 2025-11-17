-- ============================================================================
-- FIX CRITICAL BUGS IN ADDRESS SCORING
-- ============================================================================
-- Date: 2025-11-14
-- Purpose: Fix P0 critical bugs found in FAANG code review
-- Issues Fixed:
--   1. USPS validation doesn't check DPV match code
--   2. No vacant address detection
--   3. No address completeness validation
-- ============================================================================

-- Step 1: Create address completeness checker
-- ============================================================================

CREATE OR REPLACE FUNCTION is_address_complete(
  address_type TEXT,
  contact_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
  contact_record RECORD;
BEGIN
  SELECT * INTO contact_record FROM contacts WHERE id = contact_id;

  IF NOT FOUND THEN
    RETURN FALSE;
  END IF;

  IF address_type = 'billing' THEN
    RETURN contact_record.address_line_1 IS NOT NULL
       AND contact_record.city IS NOT NULL
       AND contact_record.state IS NOT NULL
       AND contact_record.postal_code IS NOT NULL
       AND LENGTH(TRIM(contact_record.address_line_1)) > 0
       AND LENGTH(TRIM(contact_record.city)) > 0
       AND LENGTH(TRIM(contact_record.state)) > 0
       AND LENGTH(TRIM(contact_record.postal_code)) > 0;

  ELSIF address_type = 'shipping' THEN
    RETURN contact_record.shipping_address_line_1 IS NOT NULL
       AND contact_record.shipping_city IS NOT NULL
       AND contact_record.shipping_state IS NOT NULL
       AND contact_record.shipping_postal_code IS NOT NULL
       AND LENGTH(TRIM(contact_record.shipping_address_line_1)) > 0
       AND LENGTH(TRIM(contact_record.shipping_city)) > 0
       AND LENGTH(TRIM(contact_record.shipping_state)) > 0
       AND LENGTH(TRIM(contact_record.shipping_postal_code)) > 0;
  END IF;

  RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_address_complete IS
  'Check if an address has all required fields (line1, city, state, zip) and they are non-empty';


-- Step 2: Fix the scoring function with all critical bugs
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_address_score(
  address_type TEXT,  -- 'billing' or 'shipping'
  contact_id UUID
) RETURNS INTEGER AS $$
DECLARE
  score INTEGER := 0;
  update_date TIMESTAMP WITH TIME ZONE;
  usps_date TIMESTAMP WITH TIME ZONE;
  usps_dpv_match TEXT;
  usps_vacant TEXT;
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

  -- CRITICAL: Check address completeness FIRST
  -- Incomplete address = unusable, return 0 immediately
  IF NOT is_address_complete(address_type, contact_id) THEN
    RETURN 0;
  END IF;

  -- Get the right fields based on address type
  IF address_type = 'billing' THEN
    update_date := contact_record.billing_address_updated_at;
    usps_date := contact_record.billing_usps_validated_at;
    usps_dpv_match := contact_record.billing_usps_dpv_match_code;
    usps_vacant := contact_record.billing_usps_vacant;
    verified := contact_record.billing_address_verified;
    source := contact_record.billing_address_source;
  ELSIF address_type = 'shipping' THEN
    update_date := contact_record.shipping_address_updated_at;
    usps_date := contact_record.shipping_usps_validated_at;
    usps_dpv_match := contact_record.shipping_usps_dpv_match_code;
    usps_vacant := contact_record.shipping_usps_vacant;
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
  -- FIX #1: Check BOTH validation date AND DPV match code
  -- FIX #2: Penalize vacant addresses
  IF usps_date IS NOT NULL THEN
    -- CRITICAL: Check if validation PASSED
    IF usps_dpv_match = 'Y' THEN
      -- Full DPV match = deliverable address
      IF usps_date > NOW() - INTERVAL '90 days' THEN
        score := score + 25;
      ELSIF usps_date > NOW() - INTERVAL '365 days' THEN
        score := score + 20;
      ELSE
        score := score + 10;
      END IF;

    ELSIF usps_dpv_match IN ('S', 'D') THEN
      -- Partial match (missing secondary or primary)
      score := score + 15;

    ELSIF usps_dpv_match = 'N' THEN
      -- VALIDATED but FAILED = penalty
      score := score - 20;
    END IF;

    -- CRITICAL FIX #2: Vacant address penalty
    IF usps_vacant = 'Y' THEN
      score := score - 50;  -- Harsh penalty: vacant = don't mail
    END IF;

  ELSIF verified THEN
    -- Manual verification (not USPS)
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

  -- FACTOR 4: SOURCE TRUST (10 points max)
  -- Reduced penalties per FAANG review
  -- Validation status is more important than source
  IF source = 'paypal' THEN
    score := score + 10;
  ELSIF source = 'kajabi' THEN
    score := score + 8;
  ELSIF source = 'manual' THEN
    score := score + 7;
  ELSIF source = 'copied_from_billing' THEN
    score := score - 2;  -- Reduced from -10
  ELSIF source = 'unknown_legacy' THEN
    score := score - 5;
  END IF;

  -- Ensure score stays in valid range
  IF score < 0 THEN
    score := 0;
  ELSIF score > 100 THEN
    score := 100;
  END IF;

  RETURN score;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION calculate_address_score IS
  'Scores an address (0-100) based on completeness, recency, USPS validation (DPV + vacant check), transaction history, and source trust. Returns 0 for incomplete addresses.';


-- Step 3: Refresh the view to use new scoring logic
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
    c.shipping_usps_validated_at,
    c.billing_usps_dpv_match_code,
    c.shipping_usps_dpv_match_code,
    c.billing_usps_vacant,
    c.shipping_usps_vacant,
    c.billing_address_verified,
    c.shipping_address_verified,
    c.last_transaction_date,
    c.billing_address_source,
    c.shipping_address_source,
    c.preferred_mailing_address,

    -- Calculate scores (will be 0 if incomplete)
    calculate_address_score('billing', c.id) as billing_score,
    calculate_address_score('shipping', c.id) as shipping_score,

    -- Check completeness flags
    is_address_complete('billing', c.id) as billing_complete,
    is_address_complete('shipping', c.id) as shipping_complete

  FROM contacts c
  WHERE c.address_line_1 IS NOT NULL OR c.shipping_address_line_1 IS NOT NULL
)
SELECT
  *,

  -- Determine recommended address (with manual override support)
  CASE
    -- Manual override takes precedence (if address is complete)
    WHEN preferred_mailing_address = 'billing' AND billing_complete THEN 'billing'
    WHEN preferred_mailing_address = 'shipping' AND shipping_complete THEN 'shipping'

    -- If manual override points to incomplete address, fall back to algorithm
    WHEN preferred_mailing_address IS NOT NULL AND NOT billing_complete AND shipping_complete THEN 'shipping'
    WHEN preferred_mailing_address IS NOT NULL AND billing_complete AND NOT shipping_complete THEN 'billing'

    -- Algorithm: 15 point threshold for switching
    -- (15 points ≈ 6 months recency difference OR validation status difference)
    WHEN billing_score >= shipping_score + 15 THEN 'billing'
    WHEN shipping_score >= billing_score + 15 THEN 'shipping'

    -- Tie: prefer whichever is complete
    WHEN billing_score = shipping_score AND billing_complete AND NOT shipping_complete THEN 'billing'
    WHEN billing_score = shipping_score AND shipping_complete AND NOT billing_complete THEN 'shipping'

    -- Both incomplete or both complete with tie: default to billing
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

FROM address_scores
WHERE billing_complete OR shipping_complete;  -- Only show contacts with at least ONE complete address

COMMENT ON VIEW mailing_list_priority IS
  'Prioritizes billing vs shipping addresses using multi-factor scoring algorithm. Only includes contacts with at least one COMPLETE address. Supports manual overrides via preferred_mailing_address column.';


-- Step 4: Update export view to enforce completeness
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
  billing_complete,
  shipping_complete,
  is_manual_override,
  last_transaction_date

FROM mailing_list_priority
WHERE recommended_address IS NOT NULL
  AND ((recommended_address = 'billing' AND billing_complete) OR
       (recommended_address = 'shipping' AND shipping_complete));

COMMENT ON VIEW mailing_list_export IS
  'Ready-to-export mailing list with selected COMPLETE addresses and metadata. Only includes addresses that pass completeness validation.';


-- Step 5: Add data quality view
-- ============================================================================

CREATE OR REPLACE VIEW mailing_list_quality_issues AS
SELECT
  c.id,
  c.email,
  c.first_name,
  c.last_name,

  CASE
    WHEN c.billing_usps_vacant = 'Y' THEN 'Billing address is vacant'
    WHEN c.shipping_usps_vacant = 'Y' THEN 'Shipping address is vacant'
    WHEN c.billing_usps_dpv_match_code = 'N' THEN 'Billing address failed USPS validation'
    WHEN c.shipping_usps_dpv_match_code = 'N' THEN 'Shipping address failed USPS validation'
    WHEN c.address_line_1 IS NOT NULL AND (c.city IS NULL OR c.state IS NULL OR c.postal_code IS NULL) THEN 'Billing address incomplete'
    WHEN c.shipping_address_line_1 IS NOT NULL AND (c.shipping_city IS NULL OR c.shipping_state IS NULL OR c.shipping_postal_code IS NULL) THEN 'Shipping address incomplete'
    ELSE 'Unknown issue'
  END as issue_type,

  c.billing_usps_dpv_match_code,
  c.billing_usps_vacant,
  c.shipping_usps_dpv_match_code,
  c.shipping_usps_vacant

FROM contacts c
WHERE
  -- Vacant addresses
  c.billing_usps_vacant = 'Y' OR
  c.shipping_usps_vacant = 'Y' OR

  -- Failed USPS validation
  c.billing_usps_dpv_match_code = 'N' OR
  c.shipping_usps_dpv_match_code = 'N' OR

  -- Incomplete addresses
  (c.address_line_1 IS NOT NULL AND (c.city IS NULL OR c.state IS NULL OR c.postal_code IS NULL)) OR
  (c.shipping_address_line_1 IS NOT NULL AND (c.shipping_city IS NULL OR c.shipping_state IS NULL OR c.shipping_postal_code IS NULL));

COMMENT ON VIEW mailing_list_quality_issues IS
  'Identifies contacts with data quality issues: vacant addresses, failed USPS validation, or incomplete addresses. Use for cleanup and monitoring.';

