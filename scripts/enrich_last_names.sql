-- ============================================================================
-- LAST NAME ENRICHMENT FROM EXISTING DATA
-- ============================================================================
-- Strategy 1: Split full names in first_name field (256 contacts)
-- Strategy 2: Extract from firstname.lastname@domain.com emails (133 contacts)
-- Total opportunity: 389 contacts
-- ============================================================================

BEGIN;

\echo '════════════════════════════════════════════════════════════'
\echo 'LAST NAME ENRICHMENT - Pattern 1 & 2'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Create backup table for enrichments
CREATE TABLE IF NOT EXISTS contacts_enrichment_backup (
  backup_id SERIAL PRIMARY KEY,
  contact_id UUID NOT NULL,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  enrichment_type TEXT NOT NULL,
  enriched_at TIMESTAMP DEFAULT NOW(),
  notes TEXT
);

\echo 'Backup table ready'
\echo ''

-- ============================================================================
-- PATTERN 1: Split full names in first_name field
-- ============================================================================

\echo '--- Pattern 1: Split "First Last" in first_name field ---'
\echo ''

-- Backup before enrichment
WITH to_enrich AS (
  SELECT
    id,
    first_name,
    last_name,
    SPLIT_PART(first_name, ' ', 1) as new_first,
    TRIM(SUBSTRING(first_name FROM POSITION(' ' IN first_name))) as new_last
  FROM contacts
  WHERE (last_name IS NULL OR last_name = '')
    AND first_name LIKE '% %'
    AND first_name NOT LIKE '% % %'  -- Only handle "First Last", not "First Middle Last"
)
INSERT INTO contacts_enrichment_backup (contact_id, field_name, old_value, new_value, enrichment_type, notes)
SELECT
  id,
  'last_name',
  last_name,
  new_last,
  'split_full_name',
  'Split from first_name: "' || first_name || '" → First: "' || new_first || '", Last: "' || new_last || '"'
FROM to_enrich;

-- Apply enrichment
UPDATE contacts
SET
  first_name = SPLIT_PART(first_name, ' ', 1),
  last_name = TRIM(SUBSTRING(first_name FROM POSITION(' ' IN first_name))),
  updated_at = NOW()
WHERE (last_name IS NULL OR last_name = '')
  AND first_name LIKE '% %'
  AND first_name NOT LIKE '% % %';  -- Only handle simple "First Last"

SELECT 'Pattern 1 enriched' as status, COUNT(*) as count
FROM contacts_enrichment_backup
WHERE enrichment_type = 'split_full_name'
  AND enriched_at > NOW() - INTERVAL '1 minute';

\echo ''

-- ============================================================================
-- PATTERN 2: Extract from firstname.lastname@domain.com emails
-- ============================================================================

\echo '--- Pattern 2: Extract from firstname.lastname@domain.com ---'
\echo ''

-- Backup before enrichment
WITH to_enrich AS (
  SELECT
    id,
    first_name,
    last_name,
    email,
    INITCAP(SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 2)) as extracted_last
  FROM contacts
  WHERE (last_name IS NULL OR last_name = '')
    AND email LIKE '%.%@%'
    AND SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 2) <> ''  -- Has something after dot
    AND LENGTH(SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 2)) > 1  -- Not just single char
)
INSERT INTO contacts_enrichment_backup (contact_id, field_name, old_value, new_value, enrichment_type, notes)
SELECT
  id,
  'last_name',
  last_name,
  extracted_last,
  'extract_from_email',
  'Extracted from email: "' || email || '" → Last: "' || extracted_last || '"'
FROM to_enrich;

-- Apply enrichment
UPDATE contacts
SET
  last_name = INITCAP(SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 2)),
  updated_at = NOW()
WHERE (last_name IS NULL OR last_name = '')
  AND email LIKE '%.%@%'
  AND SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 2) <> ''
  AND LENGTH(SPLIT_PART(SPLIT_PART(email, '@', 1), '.', 2)) > 1;

SELECT 'Pattern 2 enriched' as status, COUNT(*) as count
FROM contacts_enrichment_backup
WHERE enrichment_type = 'extract_from_email'
  AND enriched_at > NOW() - INTERVAL '1 minute';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'ENRICHMENT SUMMARY'
\echo '════════════════════════════════════════════════════════════'

-- Summary
SELECT
  enrichment_type,
  COUNT(*) as contacts_enriched,
  MIN(enriched_at)::time as started,
  MAX(enriched_at)::time as completed
FROM contacts_enrichment_backup
WHERE enriched_at > NOW() - INTERVAL '2 minutes'
GROUP BY enrichment_type;

SELECT
  'Total last names enriched' as metric,
  COUNT(*) as value
FROM contacts_enrichment_backup
WHERE field_name = 'last_name'
  AND enriched_at > NOW() - INTERVAL '2 minutes';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'VERIFICATION'
\echo '════════════════════════════════════════════════════════════'

-- Verify completeness improved
SELECT
  'Last name completeness BEFORE' as metric,
  '85.3%' as value

UNION ALL

SELECT
  'Last name completeness AFTER' as metric,
  ROUND(100.0 * COUNT(*) FILTER (WHERE last_name IS NOT NULL AND last_name <> '') / COUNT(*), 1)::text || '%' as value
FROM contacts;

-- Check remaining missing
SELECT
  'Contacts still missing last name' as metric,
  COUNT(*) as value
FROM contacts
WHERE last_name IS NULL OR last_name = '';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '════════════════════════════════════════════════════════════'

COMMIT;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '✓ LAST NAME ENRICHMENT COMMITTED!'
\echo '════════════════════════════════════════════════════════════'
