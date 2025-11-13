-- ============================================
-- ADD TAGS TO CONTACTS TABLE
-- StarHouse CRM Database
-- ============================================
-- Purpose: Enable tagging of contacts for categorization and filtering
-- Created: 2025-11-13
-- Migration: 20251113000001
-- ============================================

-- Add tags column to contacts table
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Add GIN index for efficient array searching
CREATE INDEX IF NOT EXISTS idx_contacts_tags
ON contacts USING gin(tags)
WHERE tags IS NOT NULL AND array_length(tags, 1) > 0;

-- Add comment
COMMENT ON COLUMN contacts.tags IS
'Array of tags for categorizing and filtering contacts. Examples: VIP, Board Member, Volunteer, etc.';

-- Example queries that this index will optimize:
-- SELECT * FROM contacts WHERE 'VIP' = ANY(tags);
-- SELECT * FROM contacts WHERE tags @> ARRAY['VIP', 'Donor'];
-- SELECT * FROM contacts WHERE tags && ARRAY['VIP', 'Board Member'];
