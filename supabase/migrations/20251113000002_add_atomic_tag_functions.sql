-- ============================================
-- ATOMIC TAG OPERATIONS FOR CONTACTS
-- StarHouse CRM Database
-- ============================================
-- Purpose: Provide race-condition-free tag operations using PostgreSQL array functions
-- Created: 2025-11-13
-- Migration: 20251113000002
-- ============================================
-- FAANG Standard: Use database-level atomic operations to prevent race conditions
-- when multiple clients/requests modify the same contact's tags concurrently.
-- ============================================

-- Function: add_contact_tag
-- Purpose: Atomically add a tag to a contact's tags array
-- Features:
--   - Prevents duplicate tags
--   - Case-insensitive (normalizes to lowercase)
--   - Trims whitespace
--   - Validates length (max 50 chars)
--   - Returns updated contact row for UI sync
CREATE OR REPLACE FUNCTION add_contact_tag(
  p_contact_id UUID,
  p_new_tag TEXT
) RETURNS JSONB AS $$
DECLARE
  v_normalized_tag TEXT;
  v_updated_row contacts%ROWTYPE;
BEGIN
  -- Validate and normalize tag
  v_normalized_tag := LOWER(TRIM(p_new_tag));

  -- Validation checks
  IF v_normalized_tag = '' THEN
    RAISE EXCEPTION 'Tag cannot be empty';
  END IF;

  IF LENGTH(v_normalized_tag) > 50 THEN
    RAISE EXCEPTION 'Tag cannot exceed 50 characters';
  END IF;

  -- Check max tags limit (prevent unbounded growth)
  IF (SELECT array_length(tags, 1) FROM contacts WHERE id = p_contact_id) >= 50 THEN
    RAISE EXCEPTION 'Maximum 50 tags per contact';
  END IF;

  -- Atomic update: Add tag only if it doesn't already exist
  -- This prevents race conditions when multiple requests add the same tag
  -- RLS policies automatically enforce staff permissions
  UPDATE contacts
  SET
    tags = CASE
      WHEN tags IS NULL THEN ARRAY[v_normalized_tag]
      WHEN v_normalized_tag = ANY(tags) THEN tags  -- Already exists, no-op
      ELSE array_append(tags, v_normalized_tag)
    END,
    updated_at = NOW()
  WHERE id = p_contact_id
  RETURNING * INTO v_updated_row;

  -- Check if contact exists or permission denied (RLS enforces this)
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Contact not found or permission denied';
  END IF;

  -- Return the updated tags array for UI sync
  RETURN jsonb_build_object(
    'success', true,
    'tags', COALESCE(v_updated_row.tags, ARRAY[]::TEXT[]),
    'added', v_normalized_tag
  );
END;
$$ LANGUAGE plpgsql;  -- Removed SECURITY DEFINER (RLS handles permissions)

COMMENT ON FUNCTION add_contact_tag IS
'Atomically adds a tag to a contact. Prevents duplicates and race conditions. Returns updated tags array.';

-- Function: remove_contact_tag
-- Purpose: Atomically remove a tag from a contact's tags array
-- Features:
--   - Case-insensitive removal
--   - Handles tag not existing gracefully
--   - Returns updated contact row for UI sync
CREATE OR REPLACE FUNCTION remove_contact_tag(
  p_contact_id UUID,
  p_tag_to_remove TEXT
) RETURNS JSONB AS $$
DECLARE
  v_normalized_tag TEXT;
  v_updated_row contacts%ROWTYPE;
BEGIN
  -- Normalize tag for case-insensitive comparison
  v_normalized_tag := LOWER(TRIM(p_tag_to_remove));

  -- Atomic update: Remove all instances of the tag
  -- array_remove handles the case where tag doesn't exist
  -- RLS policies automatically enforce staff permissions
  UPDATE contacts
  SET
    tags = array_remove(tags, v_normalized_tag),
    updated_at = NOW()
  WHERE id = p_contact_id
  RETURNING * INTO v_updated_row;

  -- Check if contact exists or permission denied (RLS enforces this)
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Contact not found or permission denied';
  END IF;

  -- Return the updated tags array for UI sync
  RETURN jsonb_build_object(
    'success', true,
    'tags', COALESCE(v_updated_row.tags, ARRAY[]::TEXT[]),
    'removed', v_normalized_tag
  );
END;
$$ LANGUAGE plpgsql;  -- Removed SECURITY DEFINER (RLS handles permissions)

COMMENT ON FUNCTION remove_contact_tag IS
'Atomically removes a tag from a contact. Returns updated tags array.';

-- Function: bulk_add_contact_tags
-- Purpose: Atomically add multiple tags at once
-- Use case: Importing contacts with tags, or bulk tagging operations
CREATE OR REPLACE FUNCTION bulk_add_contact_tags(
  p_contact_id UUID,
  p_new_tags TEXT[]
) RETURNS JSONB AS $$
DECLARE
  v_normalized_tags TEXT[];
  v_tag TEXT;
  v_updated_row contacts%ROWTYPE;
BEGIN
  -- Normalize all tags
  v_normalized_tags := ARRAY[]::TEXT[];
  FOREACH v_tag IN ARRAY p_new_tags
  LOOP
    v_tag := LOWER(TRIM(v_tag));
    IF v_tag != '' AND LENGTH(v_tag) <= 50 THEN
      v_normalized_tags := array_append(v_normalized_tags, v_tag);
    END IF;
  END LOOP;

  -- Atomic update: Merge tags, removing duplicates
  UPDATE contacts
  SET
    tags = (
      SELECT ARRAY_AGG(DISTINCT tag ORDER BY tag)
      FROM (
        SELECT UNNEST(COALESCE(tags, ARRAY[]::TEXT[])) AS tag
        UNION
        SELECT UNNEST(v_normalized_tags) AS tag
      ) combined
    ),
    updated_at = NOW()
  WHERE id = p_contact_id
  RETURNING * INTO v_updated_row;

  -- Check if contact exists
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Contact not found: %', p_contact_id;
  END IF;

  -- Return the updated tags array
  RETURN jsonb_build_object(
    'success', true,
    'tags', COALESCE(v_updated_row.tags, ARRAY[]::TEXT[]),
    'added_count', array_length(v_normalized_tags, 1)
  );
END;
$$ LANGUAGE plpgsql;  -- Removed SECURITY DEFINER (RLS handles permissions)

COMMENT ON FUNCTION bulk_add_contact_tags IS
'Atomically adds multiple tags to a contact. Prevents duplicates. Returns updated tags array.';

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION add_contact_tag TO authenticated;
GRANT EXECUTE ON FUNCTION remove_contact_tag TO authenticated;
GRANT EXECUTE ON FUNCTION bulk_add_contact_tags TO authenticated;

-- Performance verification query (for testing)
-- Run this to verify the GIN index is being used:
-- EXPLAIN ANALYZE SELECT * FROM contacts WHERE 'vip' = ANY(tags);
-- Expected: "Bitmap Index Scan on idx_contacts_tags"
