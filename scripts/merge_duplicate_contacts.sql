-- ============================================================================
-- DUPLICATE CONTACT MERGE SCRIPT
-- ============================================================================
-- FAANG-Quality Safe Merge Process with Rollback Support
--
-- USAGE:
--   1. Review the two contact records
--   2. Set PRIMARY_ID (record to keep) and DUPLICATE_ID (record to merge)
--   3. Run this script in a transaction
--   4. Verify results before COMMIT
--   5. If anything looks wrong: ROLLBACK
--
-- SAFETY:
--   - Wrapped in transaction (ROLLBACK if needed)
--   - Creates backup table before merge
--   - Preserves all data (no data loss)
--   - Audit trail in backup table
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: CREATE BACKUP TABLE (First run only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contacts_merge_backup (
  backup_id SERIAL PRIMARY KEY,
  merged_at TIMESTAMP DEFAULT NOW(),
  primary_contact_id UUID,
  duplicate_contact_id UUID,
  duplicate_contact_data JSONB,
  merged_tags TEXT[],
  merged_transactions_count INTEGER,
  notes TEXT
);

-- ============================================================================
-- STEP 2: SET THE IDS FOR THIS MERGE
-- ============================================================================
-- EDIT THESE VALUES FOR EACH MERGE:

\set PRIMARY_ID '293ac973-dc30-4856-9e39-ecf8e518b7b7'
\set DUPLICATE_ID '8cec6487-8a09-4e75-84f8-b754b13ba52c'

-- Primary: karenderreumaux@gmail.com (newer, more complete)
-- Duplicate: karenderreumaux@exede.net (older, migrate to additional_email)

-- ============================================================================
-- STEP 3: BACKUP THE DUPLICATE RECORD
-- ============================================================================

INSERT INTO contacts_merge_backup (
  primary_contact_id,
  duplicate_contact_id,
  duplicate_contact_data,
  notes
)
SELECT
  :'PRIMARY_ID'::uuid,
  :'DUPLICATE_ID'::uuid,
  row_to_json(c.*)::jsonb,
  'Merge: Karen Derreumaux - Email migration from @exede.net to @gmail.com'
FROM contacts c
WHERE c.id = :'DUPLICATE_ID'::uuid;

-- ============================================================================
-- STEP 4: MERGE DATA INTO PRIMARY RECORD
-- ============================================================================

-- Update primary contact with additional data from duplicate
UPDATE contacts
SET
  -- Add duplicate's email to additional_email field
  additional_email = CASE
    WHEN additional_email IS NULL THEN (SELECT email FROM contacts WHERE id = :'DUPLICATE_ID'::uuid)
    ELSE additional_email
  END,

  -- Add duplicate's phone to additional_phone if different
  additional_phone = CASE
    WHEN additional_phone IS NULL AND phone != (SELECT phone FROM contacts WHERE id = :'DUPLICATE_ID'::uuid)
      THEN (SELECT phone FROM contacts WHERE id = :'DUPLICATE_ID'::uuid)
    ELSE additional_phone
  END,

  -- Keep the earliest created_at (provenance tracking)
  created_at = LEAST(
    created_at,
    (SELECT created_at FROM contacts WHERE id = :'DUPLICATE_ID'::uuid)
  ),

  updated_at = NOW()

WHERE id = :'PRIMARY_ID'::uuid;

-- ============================================================================
-- STEP 5: REASSIGN TRANSACTIONS
-- ============================================================================

UPDATE transactions
SET
  contact_id = :'PRIMARY_ID'::uuid,
  updated_at = NOW()
WHERE contact_id = :'DUPLICATE_ID'::uuid;

-- Update backup with transaction count
UPDATE contacts_merge_backup
SET merged_transactions_count = (
  SELECT COUNT(*)
  FROM transactions
  WHERE contact_id = :'PRIMARY_ID'::uuid
)
WHERE duplicate_contact_id = :'DUPLICATE_ID'::uuid
  AND merged_at > NOW() - INTERVAL '1 minute';

-- ============================================================================
-- STEP 6: MERGE TAGS (Keep all unique tags)
-- ============================================================================

-- Copy tags from duplicate to primary (if not already there)
INSERT INTO contact_tags (contact_id, tag_id)
SELECT DISTINCT
  :'PRIMARY_ID'::uuid as contact_id,
  ct.tag_id
FROM contact_tags ct
WHERE ct.contact_id = :'DUPLICATE_ID'::uuid
  AND NOT EXISTS (
    SELECT 1 FROM contact_tags ct2
    WHERE ct2.contact_id = :'PRIMARY_ID'::uuid
      AND ct2.tag_id = ct.tag_id
  )
ON CONFLICT (contact_id, tag_id) DO NOTHING;

-- Update backup with merged tags
UPDATE contacts_merge_backup
SET merged_tags = (
  SELECT ARRAY_AGG(t.name)
  FROM contact_tags ct
  JOIN tags t ON ct.tag_id = t.id
  WHERE ct.contact_id = :'PRIMARY_ID'::uuid
)
WHERE duplicate_contact_id = :'DUPLICATE_ID'::uuid
  AND merged_at > NOW() - INTERVAL '1 minute';

-- ============================================================================
-- STEP 7: DELETE DUPLICATE CONTACT TAGS
-- ============================================================================

DELETE FROM contact_tags
WHERE contact_id = :'DUPLICATE_ID'::uuid;

-- ============================================================================
-- STEP 8: DELETE DUPLICATE RECORD
-- ============================================================================

DELETE FROM contacts
WHERE id = :'DUPLICATE_ID'::uuid;

-- ============================================================================
-- STEP 9: VERIFICATION QUERIES
-- ============================================================================

-- Show the merged contact
SELECT
  'MERGED CONTACT' as status,
  id,
  first_name,
  last_name,
  email,
  additional_email,
  phone,
  source_system,
  created_at
FROM contacts
WHERE id = :'PRIMARY_ID'::uuid;

-- Show transaction count
SELECT
  'TRANSACTION COUNT' as status,
  contact_id,
  COUNT(*) as transaction_count,
  SUM(amount) as total_amount
FROM transactions
WHERE contact_id = :'PRIMARY_ID'::uuid
GROUP BY contact_id;

-- Show tags
SELECT
  'MERGED TAGS' as status,
  t.name as tag_name
FROM contact_tags ct
JOIN tags t ON ct.tag_id = t.id
WHERE ct.contact_id = :'PRIMARY_ID'::uuid
ORDER BY t.name;

-- Show backup record
SELECT
  'BACKUP RECORD' as status,
  backup_id,
  merged_at,
  notes,
  merged_transactions_count,
  array_length(merged_tags, 1) as tag_count
FROM contacts_merge_backup
WHERE duplicate_contact_id = :'DUPLICATE_ID'::uuid
ORDER BY merged_at DESC
LIMIT 1;

-- ============================================================================
-- STEP 10: COMMIT OR ROLLBACK
-- ============================================================================

-- Review the output above. If everything looks good:
-- COMMIT;

-- If something looks wrong:
-- ROLLBACK;

-- IMPORTANT: You MUST run either COMMIT or ROLLBACK to complete this transaction!

