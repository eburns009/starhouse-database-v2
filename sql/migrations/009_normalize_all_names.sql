-- Migration: 009_normalize_all_names.sql
-- Purpose: Normalize all name variations into contact_names table
-- Date: 2025-11-10
-- Author: Claude Code (Sonnet 4.5)
--
-- Problem:
-- - 1,003 contacts (15.3%) have name variations stored in different fields
-- - Names stored in: paypal_first_name, paypal_last_name, paypal_business_name, additional_name, and transaction raw_source
-- - Search only works on first_name + last_name, missing all variations
-- - Examples:
--   * "Rose Petal" pays as "Robert Henderson" (20 transactions)
--   * "Danny Balgooyen" pays as "Daniel Balgooyen"
--   * "Bjorn Brie" pays as "Temple of the Golden Light"
--
-- Solution:
-- - Create contact_names table to store all name variations
-- - Migrate all names from various sources
-- - Update search_contacts() to search across ALL names
-- - Create set_primary_name() for UI
-- - Track source and verification status

-- ==============================================================================
-- STEP 0: PRE-MIGRATION DIAGNOSTICS
-- ==============================================================================

DO $diagnostics$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'PRE-MIGRATION DIAGNOSTICS';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE '';
END;
$diagnostics$;

-- Count contacts with name variations
DO $pre_check$
DECLARE
  v_total_contacts INTEGER;
  v_paypal_names INTEGER;
  v_business_names INTEGER;
  v_additional_names INTEGER;
  v_transaction_names INTEGER;
  v_unique_with_variants INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_total_contacts FROM contacts WHERE deleted_at IS NULL;

  SELECT COUNT(*) INTO v_paypal_names
  FROM contacts
  WHERE deleted_at IS NULL
    AND (paypal_first_name IS NOT NULL OR paypal_last_name IS NOT NULL);

  SELECT COUNT(*) INTO v_business_names
  FROM contacts
  WHERE deleted_at IS NULL
    AND paypal_business_name IS NOT NULL
    AND paypal_business_name <> '';

  SELECT COUNT(*) INTO v_additional_names
  FROM contacts
  WHERE deleted_at IS NULL
    AND additional_name IS NOT NULL
    AND additional_name <> '';

  SELECT COUNT(DISTINCT contact_id) INTO v_transaction_names
  FROM transactions
  WHERE source_system = 'paypal'
    AND raw_source ? 'full_name'
    AND raw_source->>'full_name' IS NOT NULL
    AND raw_source->>'full_name' <> '';

  WITH all_variants AS (
    SELECT DISTINCT id as contact_id FROM contacts
    WHERE deleted_at IS NULL
      AND (paypal_first_name IS NOT NULL
           OR paypal_business_name IS NOT NULL
           OR additional_name IS NOT NULL)
    UNION
    SELECT DISTINCT contact_id FROM transactions
    WHERE source_system = 'paypal' AND raw_source ? 'full_name'
  )
  SELECT COUNT(*) INTO v_unique_with_variants FROM all_variants;

  RAISE NOTICE 'Total contacts: %', v_total_contacts;
  RAISE NOTICE 'Contacts with PayPal names: %', v_paypal_names;
  RAISE NOTICE 'Contacts with business names: %', v_business_names;
  RAISE NOTICE 'Contacts with additional_name: %', v_additional_names;
  RAISE NOTICE 'Contacts with transaction names: %', v_transaction_names;
  RAISE NOTICE 'Unique contacts with name variations: % (%.1f%%)',
    v_unique_with_variants,
    (v_unique_with_variants::NUMERIC / v_total_contacts * 100);
  RAISE NOTICE '';
END;
$pre_check$;

-- ==============================================================================
-- STEP 1: CREATE BACKUP (if contact_names already exists)
-- ==============================================================================

DO $backup$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'contact_names') THEN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'STEP 1: CREATE BACKUP';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';

    DROP TABLE IF EXISTS contact_names_backup_20251110 CASCADE;
    CREATE TABLE contact_names_backup_20251110 AS SELECT * FROM contact_names;

    RAISE NOTICE 'Backed up % rows to contact_names_backup_20251110',
      (SELECT COUNT(*) FROM contact_names_backup_20251110);
    RAISE NOTICE '';
  END IF;
END;
$backup$;

-- ==============================================================================
-- STEP 2: CREATE contact_names TABLE
-- ==============================================================================

DO $create_table$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 2: CREATE contact_names TABLE';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$create_table$;

DROP TABLE IF EXISTS contact_names CASCADE;

CREATE TABLE contact_names (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
  name_text TEXT NOT NULL,
  name_type TEXT NOT NULL DEFAULT 'full_name',
  is_primary BOOLEAN NOT NULL DEFAULT false,
  source TEXT NOT NULL,
  verified BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT contact_names_contact_id_name_text_unique UNIQUE (contact_id, name_text),
  CONSTRAINT contact_names_name_text_not_empty CHECK (LENGTH(TRIM(name_text)) > 0),
  CONSTRAINT contact_names_name_type_valid CHECK (
    name_type IN ('full_name', 'business', 'legal', 'nickname', 'maiden', 'other')
  ),
  CONSTRAINT contact_names_source_valid CHECK (
    source IN ('kajabi', 'paypal', 'paypal_transaction', 'zoho', 'ticket_tailor', 'quickbooks', 'mailchimp', 'manual')
  )
);

-- Unique partial index: exactly ONE primary name per contact
CREATE UNIQUE INDEX ux_contact_names_one_primary
ON contact_names(contact_id)
WHERE is_primary = true;

-- Indexes for performance
CREATE INDEX idx_contact_names_contact_id ON contact_names(contact_id);
CREATE INDEX idx_contact_names_name_text ON contact_names(name_text);
CREATE INDEX idx_contact_names_name_text_trgm ON contact_names USING gin(name_text gin_trgm_ops);
CREATE INDEX idx_contact_names_is_primary ON contact_names(is_primary) WHERE is_primary = true;
CREATE INDEX idx_contact_names_source ON contact_names(source);

-- Updated at trigger
CREATE TRIGGER contact_names_set_updated_at
  BEFORE UPDATE ON contact_names
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();

-- Add RLS policies
ALTER TABLE contact_names ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access" ON contact_names
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "staff_full_access" ON contact_names
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Add comments
COMMENT ON TABLE contact_names IS 'Normalized storage for all name variations per contact';
COMMENT ON COLUMN contact_names.name_text IS 'The full name text (could be person or business name)';
COMMENT ON COLUMN contact_names.name_type IS 'Type: full_name, business, legal, nickname, maiden, other';
COMMENT ON COLUMN contact_names.is_primary IS 'TRUE = display name, FALSE = alternate name (exactly 1 primary per contact)';
COMMENT ON COLUMN contact_names.source IS 'Where this name came from: kajabi, paypal, paypal_transaction, manual, etc.';
COMMENT ON COLUMN contact_names.verified IS 'Whether this name has been verified/confirmed';

DO $create_complete$
BEGIN
  RAISE NOTICE 'Created contact_names table with constraints and indexes ✓';
  RAISE NOTICE '';
END;
$create_complete$;

-- ==============================================================================
-- STEP 3: MIGRATE PRIMARY NAMES
-- ==============================================================================

DO $primary_names$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 3: MIGRATE PRIMARY NAMES';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$primary_names$;

INSERT INTO contact_names (contact_id, name_text, name_type, is_primary, source, verified, created_at)
SELECT
  c.id,
  TRIM(c.first_name || ' ' || COALESCE(c.last_name, ''))::TEXT as name_text,
  'full_name'::TEXT as name_type,
  true as is_primary,
  CASE
    WHEN c.source_system IN ('kajabi', 'paypal', 'zoho', 'ticket_tailor', 'quickbooks', 'mailchimp')
      THEN c.source_system
    ELSE 'manual'
  END::TEXT as source,
  true as verified,
  c.created_at
FROM contacts c
WHERE c.deleted_at IS NULL
  AND c.first_name IS NOT NULL
  AND TRIM(c.first_name) <> ''
ON CONFLICT (contact_id, name_text) DO NOTHING;

DO $primary_complete$
DECLARE
  v_inserted INTEGER;
BEGIN
  GET DIAGNOSTICS v_inserted = ROW_COUNT;
  RAISE NOTICE 'Migrated % primary names from contacts.first_name + last_name ✓', v_inserted;
  RAISE NOTICE '';
END;
$primary_complete$;

-- ==============================================================================
-- STEP 4: MIGRATE PAYPAL NAMES
-- ==============================================================================

DO $paypal_names$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 4: MIGRATE PAYPAL NAMES';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$paypal_names$;

INSERT INTO contact_names (contact_id, name_text, name_type, is_primary, source, verified, created_at)
SELECT
  c.id,
  TRIM(c.paypal_first_name || ' ' || COALESCE(c.paypal_last_name, ''))::TEXT as name_text,
  'full_name'::TEXT as name_type,
  false as is_primary,
  'paypal'::TEXT as source,
  true as verified,
  c.created_at
FROM contacts c
WHERE c.deleted_at IS NULL
  AND c.paypal_first_name IS NOT NULL
  AND TRIM(c.paypal_first_name) <> ''
  -- Skip if same as primary name
  AND TRIM(c.paypal_first_name || ' ' || COALESCE(c.paypal_last_name, '')) <>
      TRIM(c.first_name || ' ' || COALESCE(c.last_name, ''))
ON CONFLICT (contact_id, name_text) DO NOTHING;

DO $paypal_complete$
DECLARE
  v_inserted INTEGER;
BEGIN
  GET DIAGNOSTICS v_inserted = ROW_COUNT;
  RAISE NOTICE 'Migrated % PayPal names from contacts.paypal_first_name + paypal_last_name ✓', v_inserted;
  RAISE NOTICE '';
END;
$paypal_complete$;

-- ==============================================================================
-- STEP 5: MIGRATE BUSINESS NAMES
-- ==============================================================================

DO $business_names$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 5: MIGRATE BUSINESS NAMES';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$business_names$;

INSERT INTO contact_names (contact_id, name_text, name_type, is_primary, source, verified, created_at)
SELECT
  c.id,
  TRIM(c.paypal_business_name)::TEXT as name_text,
  'business'::TEXT as name_type,
  false as is_primary,
  'paypal'::TEXT as source,
  true as verified,
  c.created_at
FROM contacts c
WHERE c.deleted_at IS NULL
  AND c.paypal_business_name IS NOT NULL
  AND TRIM(c.paypal_business_name) <> ''
ON CONFLICT (contact_id, name_text) DO NOTHING;

DO $business_complete$
DECLARE
  v_inserted INTEGER;
BEGIN
  GET DIAGNOSTICS v_inserted = ROW_COUNT;
  RAISE NOTICE 'Migrated % business names from contacts.paypal_business_name ✓', v_inserted;
  RAISE NOTICE '';
END;
$business_complete$;

-- ==============================================================================
-- STEP 6: MIGRATE ADDITIONAL NAMES
-- ==============================================================================

DO $additional_names$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 6: MIGRATE ADDITIONAL NAMES';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$additional_names$;

INSERT INTO contact_names (contact_id, name_text, name_type, is_primary, source, verified, created_at)
SELECT
  c.id,
  TRIM(c.additional_name)::TEXT as name_text,
  'full_name'::TEXT as name_type,
  false as is_primary,
  CASE
    WHEN c.additional_name_source LIKE 'paypal%' THEN 'paypal'
    WHEN c.additional_name_source IN ('kajabi', 'zoho', 'ticket_tailor', 'quickbooks', 'mailchimp')
      THEN c.additional_name_source
    ELSE 'manual'
  END::TEXT as source,
  false as verified,
  c.created_at
FROM contacts c
WHERE c.deleted_at IS NULL
  AND c.additional_name IS NOT NULL
  AND TRIM(c.additional_name) <> ''
ON CONFLICT (contact_id, name_text) DO NOTHING;

DO $additional_complete$
DECLARE
  v_inserted INTEGER;
BEGIN
  GET DIAGNOSTICS v_inserted = ROW_COUNT;
  RAISE NOTICE 'Migrated % additional names from contacts.additional_name ✓', v_inserted;
  RAISE NOTICE '';
END;
$additional_complete$;

-- ==============================================================================
-- STEP 7: MIGRATE PAYPAL TRANSACTION NAMES
-- ==============================================================================

DO $transaction_names$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 7: MIGRATE PAYPAL TRANSACTION NAMES';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$transaction_names$;

-- Insert distinct transaction names
INSERT INTO contact_names (contact_id, name_text, name_type, is_primary, source, verified, created_at)
SELECT DISTINCT
  t.contact_id,
  TRIM(t.raw_source->>'full_name')::TEXT as name_text,
  CASE
    WHEN TRIM(t.raw_source->>'full_name') ILIKE '%llc%'
      OR TRIM(t.raw_source->>'full_name') ILIKE '%inc%'
      OR TRIM(t.raw_source->>'full_name') ILIKE '%corp%'
      OR TRIM(t.raw_source->>'full_name') ILIKE '%foundation%'
      THEN 'business'
    ELSE 'full_name'
  END::TEXT as name_type,
  false as is_primary,
  'paypal_transaction'::TEXT as source,
  true as verified,  -- Came from actual payment
  MIN(t.transaction_date) as created_at
FROM transactions t
WHERE t.source_system = 'paypal'
  AND t.raw_source ? 'full_name'
  AND t.raw_source->>'full_name' IS NOT NULL
  AND TRIM(t.raw_source->>'full_name') <> ''
GROUP BY t.contact_id, TRIM(t.raw_source->>'full_name')
ON CONFLICT (contact_id, name_text) DO NOTHING;

DO $transaction_complete$
DECLARE
  v_inserted INTEGER;
BEGIN
  GET DIAGNOSTICS v_inserted = ROW_COUNT;
  RAISE NOTICE 'Migrated % unique PayPal transaction names ✓', v_inserted;
  RAISE NOTICE '';
END;
$transaction_complete$;

-- ==============================================================================
-- STEP 8: UPDATE search_contacts() FUNCTION
-- ==============================================================================

DO $update_search$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 8: UPDATE search_contacts() FUNCTION';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$update_search$;

CREATE OR REPLACE FUNCTION search_contacts(
  p_query TEXT,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  contact_id UUID,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  total_spent NUMERIC,
  is_member BOOLEAN,
  is_donor BOOLEAN,
  match_score REAL,
  match_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ON (c.id)
    c.id,
    CONCAT_WS(' ', c.first_name, c.last_name) as full_name,
    c.email::TEXT,
    c.phone,
    COALESCE(c.total_spent, 0) as total_spent,
    COALESCE(c.has_active_subscription, false) as is_member,
    (COALESCE(c.total_spent, 0) > 0) as is_donor,
    CASE
      -- Highest priority: exact name match
      WHEN c.first_name ILIKE p_query OR c.last_name ILIKE p_query THEN 1.0
      -- Name contains query
      WHEN c.first_name ILIKE '%' || p_query || '%' OR c.last_name ILIKE '%' || p_query || '%' THEN 0.9
      -- Name variation exact match
      WHEN cn.name_text ILIKE p_query THEN 0.85
      -- Name variation contains query
      WHEN cn.name_text ILIKE '%' || p_query || '%' THEN 0.8
      -- Email matches
      WHEN c.email ILIKE '%' || p_query || '%' OR ce.email ILIKE '%' || p_query || '%' THEN 0.7
      -- Phone matches
      WHEN c.phone ILIKE '%' || p_query || '%' THEN 0.6
      ELSE 0.5
    END::REAL as match_score,
    CASE
      WHEN c.first_name ILIKE '%' || p_query || '%' OR c.last_name ILIKE '%' || p_query || '%' THEN 'primary_name'
      WHEN cn.name_text ILIKE '%' || p_query || '%' THEN 'alternate_name'
      WHEN c.email ILIKE '%' || p_query || '%' THEN 'primary_email'
      WHEN ce.email ILIKE '%' || p_query || '%' THEN 'additional_email'
      WHEN c.phone ILIKE '%' || p_query || '%' THEN 'phone'
      ELSE 'other'
    END::TEXT as match_type
  FROM contacts c
  LEFT JOIN contact_emails ce ON c.id = ce.contact_id
  LEFT JOIN contact_names cn ON c.id = cn.contact_id
  WHERE c.deleted_at IS NULL
    AND (
      -- Search primary name
      c.first_name ILIKE '%' || p_query || '%'
      OR c.last_name ILIKE '%' || p_query || '%'
      -- Search all name variations
      OR cn.name_text ILIKE '%' || p_query || '%'
      -- Search phone
      OR c.phone ILIKE '%' || p_query || '%'
      -- Search all emails
      OR c.email ILIKE '%' || p_query || '%'
      OR ce.email ILIKE '%' || p_query || '%'
    )
  ORDER BY c.id, match_score DESC, c.created_at DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

DO $search_complete$
BEGIN
  RAISE NOTICE 'Updated search_contacts() function to search ALL names ✓';
  RAISE NOTICE '';
END;
$search_complete$;

-- ==============================================================================
-- STEP 9: CREATE set_primary_name() FUNCTION
-- ==============================================================================

DO $create_function$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 9: CREATE set_primary_name() FUNCTION';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$create_function$;

CREATE OR REPLACE FUNCTION set_primary_name(
  p_contact_id UUID,
  p_new_primary_name TEXT
)
RETURNS TABLE(
  success BOOLEAN,
  message TEXT,
  old_primary_name TEXT,
  new_primary_name TEXT
) AS $$
DECLARE
  v_old_primary_name TEXT;
  v_name_exists BOOLEAN;
  v_new_first_name TEXT;
  v_new_last_name TEXT;
BEGIN
  -- Validate: Check if name exists for this contact
  SELECT EXISTS(
    SELECT 1 FROM contact_names
    WHERE contact_id = p_contact_id
      AND name_text = p_new_primary_name
  ) INTO v_name_exists;

  IF NOT v_name_exists THEN
    RETURN QUERY SELECT
      false,
      'Name not found for this contact'::TEXT,
      NULL::TEXT,
      NULL::TEXT;
    RETURN;
  END IF;

  -- Get current primary name
  SELECT name_text INTO v_old_primary_name
  FROM contact_names
  WHERE contact_id = p_contact_id
    AND is_primary = true;

  -- Check if already primary
  IF v_old_primary_name = p_new_primary_name THEN
    RETURN QUERY SELECT
      true,
      'Name is already primary'::TEXT,
      v_old_primary_name,
      p_new_primary_name;
    RETURN;
  END IF;

  -- ATOMIC OPERATION: Change primary name
  -- Step 1: Unset old primary
  UPDATE contact_names
  SET is_primary = false
  WHERE contact_id = p_contact_id
    AND is_primary = true;

  -- Step 2: Set new primary
  UPDATE contact_names
  SET is_primary = true
  WHERE contact_id = p_contact_id
    AND name_text = p_new_primary_name;

  -- Step 3: Parse name and update contacts table for backward compatibility
  -- Simple split on last space (handles "First Last" and "First Middle Last")
  IF p_new_primary_name LIKE '% %' THEN
    v_new_first_name := SPLIT_PART(p_new_primary_name, ' ', 1);
    v_new_last_name := SUBSTRING(p_new_primary_name FROM LENGTH(v_new_first_name) + 2);
  ELSE
    v_new_first_name := p_new_primary_name;
    v_new_last_name := NULL;
  END IF;

  UPDATE contacts
  SET
    first_name = v_new_first_name,
    last_name = v_new_last_name,
    updated_at = NOW()
  WHERE id = p_contact_id;

  -- Return success
  RETURN QUERY SELECT
    true,
    'Primary name changed successfully'::TEXT,
    v_old_primary_name,
    p_new_primary_name;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_primary_name IS 'Atomically change which name is primary for a contact. Updates both contact_names and contacts tables.';

DO $function_complete$
BEGIN
  RAISE NOTICE 'Created set_primary_name() function ✓';
  RAISE NOTICE '';
END;
$function_complete$;

-- ==============================================================================
-- STEP 10: CREATE MONITORING VIEW
-- ==============================================================================

DO $create_view$
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'STEP 10: CREATE MONITORING VIEW';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END;
$create_view$;

CREATE OR REPLACE VIEW name_sync_health AS
SELECT 'Total contacts' as metric, COUNT(*)::TEXT as count
FROM contacts WHERE deleted_at IS NULL

UNION ALL

SELECT 'Contacts with primary in contact_names', COUNT(DISTINCT contact_id)::TEXT
FROM contact_names WHERE is_primary = true

UNION ALL

SELECT 'MISSING primary names', COUNT(*)::TEXT
FROM contacts c
WHERE c.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM contact_names cn
    WHERE cn.contact_id = c.id AND cn.is_primary = true
  )

UNION ALL

SELECT 'Total names in contact_names', COUNT(*)::TEXT
FROM contact_names

UNION ALL

SELECT 'Contacts with multiple names', COUNT(*)::TEXT
FROM (
  SELECT contact_id
  FROM contact_names
  GROUP BY contact_id
  HAVING COUNT(*) > 1
) multi_name_contacts

UNION ALL

SELECT 'Primary names synced with contacts.first_name', COUNT(*)::TEXT
FROM contacts c
JOIN contact_names cn ON c.id = cn.contact_id AND cn.is_primary = true
WHERE c.deleted_at IS NULL
  AND TRIM(c.first_name || ' ' || COALESCE(c.last_name, '')) = cn.name_text

UNION ALL

SELECT 'Names by source: kajabi', COUNT(*)::TEXT FROM contact_names WHERE source = 'kajabi'
UNION ALL
SELECT 'Names by source: paypal', COUNT(*)::TEXT FROM contact_names WHERE source = 'paypal'
UNION ALL
SELECT 'Names by source: paypal_transaction', COUNT(*)::TEXT FROM contact_names WHERE source = 'paypal_transaction'
UNION ALL
SELECT 'Names by source: manual', COUNT(*)::TEXT FROM contact_names WHERE source = 'manual'

UNION ALL

SELECT 'Names by type: full_name', COUNT(*)::TEXT FROM contact_names WHERE name_type = 'full_name'
UNION ALL
SELECT 'Names by type: business', COUNT(*)::TEXT FROM contact_names WHERE name_type = 'business';

COMMENT ON VIEW name_sync_health IS 'Health monitoring for contact_names table and sync with contacts table';

DO $view_complete$
BEGIN
  RAISE NOTICE 'Created name_sync_health monitoring view ✓';
  RAISE NOTICE '';
END;
$view_complete$;

-- ==============================================================================
-- STEP 11: POST-MIGRATION VERIFICATION
-- ==============================================================================

DO $verification$
DECLARE
  v_total_names INTEGER;
  v_unique_contacts INTEGER;
  v_contacts_with_multiple INTEGER;
  v_missing_primary INTEGER;
BEGIN
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'POST-MIGRATION VERIFICATION';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE '';

  SELECT COUNT(*) INTO v_total_names FROM contact_names;
  SELECT COUNT(DISTINCT contact_id) INTO v_unique_contacts FROM contact_names;

  SELECT COUNT(*) INTO v_contacts_with_multiple
  FROM (
    SELECT contact_id
    FROM contact_names
    GROUP BY contact_id
    HAVING COUNT(*) > 1
  ) multi;

  SELECT COUNT(*) INTO v_missing_primary
  FROM contacts c
  WHERE c.deleted_at IS NULL
    AND NOT EXISTS (
      SELECT 1 FROM contact_names cn
      WHERE cn.contact_id = c.id AND cn.is_primary = true
    );

  RAISE NOTICE 'Total names in contact_names: %', v_total_names;
  RAISE NOTICE 'Unique contacts with names: %', v_unique_contacts;
  RAISE NOTICE 'Contacts with multiple names: %', v_contacts_with_multiple;
  RAISE NOTICE 'Contacts missing primary name: %', v_missing_primary;
  RAISE NOTICE '';

  IF v_missing_primary = 0 THEN
    RAISE NOTICE '✓ SUCCESS: All contacts have primary names';
  ELSE
    RAISE WARNING '⚠ WARNING: % contacts missing primary names', v_missing_primary;
  END IF;

  RAISE NOTICE '';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE 'MIGRATION COMPLETE';
  RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  RAISE NOTICE '';
END;
$verification$;

-- ==============================================================================
-- DEPRECATION NOTICE
-- ==============================================================================

COMMENT ON COLUMN contacts.paypal_first_name IS 'DEPRECATED: Migrated to contact_names table. Use contact_names for all name variations.';
COMMENT ON COLUMN contacts.paypal_last_name IS 'DEPRECATED: Migrated to contact_names table. Use contact_names for all name variations.';
COMMENT ON COLUMN contacts.paypal_business_name IS 'DEPRECATED: Migrated to contact_names table. Use contact_names for all name variations.';
COMMENT ON COLUMN contacts.additional_name IS 'DEPRECATED: Migrated to contact_names table. Use contact_names for all name variations.';
COMMENT ON COLUMN contacts.additional_name_source IS 'DEPRECATED: Migrated to contact_names table. Use contact_names for all name variations.';

-- End of migration
