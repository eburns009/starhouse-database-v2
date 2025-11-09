-- ============================================================================
-- ZIP CODE ENRICHMENT FROM CITY/STATE
-- ============================================================================
-- Strategy: Use lookup table for top cities (covers ~400 contacts)
-- Note: For complete coverage, use external API (Zippopotam.us, USPS)
-- Total opportunity: 839 contacts with city/state but no zip
-- ============================================================================

BEGIN;

\echo '════════════════════════════════════════════════════════════'
\echo 'ZIP CODE ENRICHMENT FROM CITY/STATE'
\echo '════════════════════════════════════════════════════════════'
\echo ''

-- Create temporary lookup table for common cities
-- Note: Cities can have multiple zip codes; using primary/downtown zip
CREATE TEMP TABLE city_zip_lookup (
  city TEXT,
  state TEXT,
  zipcode TEXT,
  note TEXT
);

INSERT INTO city_zip_lookup (city, state, zipcode, note) VALUES
-- Colorado (majority of contacts)
('Boulder', 'CO', '80301', 'Downtown Boulder'),
('Denver', 'CO', '80202', 'Downtown Denver'),
('Longmont', 'CO', '80501', 'Central Longmont'),
('Lafayette', 'CO', '80026', 'Lafayette'),
('Littleton', 'CO', '80120', 'Central Littleton'),
('Louisville', 'CO', '80027', 'Louisville'),
('Lakewood', 'CO', '80226', 'Central Lakewood'),
('Westminster', 'CO', '80030', 'Central Westminster'),
('Golden', 'CO', '80401', 'Downtown Golden'),
('Broomfield', 'CO', '80020', 'Broomfield'),
('Fort Collins', 'CO', '80521', 'Central Fort Collins'),
('Lyons', 'CO', '80540', 'Lyons'),
('Arvada', 'CO', '80002', 'Central Arvada'),
('Aurora', 'CO', '80010', 'Central Aurora'),
('Colorado Springs', 'CO', '80903', 'Downtown Colorado Springs'),
('Nederland', 'CO', '80466', 'Nederland'),
('Niwot', 'CO', '80544', 'Niwot'),
-- California
('Sacramento', 'CA', '95814', 'Downtown Sacramento'),
('Fair Oaks', 'CA', '95628', 'Fair Oaks'),
('Sebastopol', 'CA', '95472', 'Sebastopol'),
('San Francisco', 'CA', '94102', 'Downtown SF'),
('Los Angeles', 'CA', '90012', 'Downtown LA'),
('San Diego', 'CA', '92101', 'Downtown San Diego'),
-- Oregon
('Portland', 'OR', '97205', 'Downtown Portland'),
-- Texas
('Austin', 'TX', '78701', 'Downtown Austin'),
('Houston', 'TX', '77002', 'Downtown Houston'),
-- Michigan
('Ann Arbor', 'MI', '48104', 'Central Ann Arbor'),
-- Other common cities
('New York', 'NY', '10001', 'Manhattan'),
('Chicago', 'IL', '60601', 'Downtown Chicago'),
('Seattle', 'WA', '98101', 'Downtown Seattle');

\echo 'Created zip code lookup table'
\echo ''

-- Backup before enrichment
INSERT INTO contacts_enrichment_backup (contact_id, field_name, old_value, new_value, enrichment_type, notes)
SELECT
  c.id,
  'zipcode',
  c.zipcode,
  l.zipcode,
  'city_state_lookup',
  'Enriched from city/state: ' || c.city || ', ' || c.state || ' → ' || l.zipcode || ' (' || l.note || ')'
FROM contacts c
INNER JOIN city_zip_lookup l
  ON LOWER(TRIM(c.city)) = LOWER(TRIM(l.city))
  AND UPPER(TRIM(c.state)) = UPPER(TRIM(l.state))
WHERE (c.zipcode IS NULL OR c.zipcode = '');

-- Apply enrichment
UPDATE contacts c
SET
  zipcode = l.zipcode,
  updated_at = NOW()
FROM city_zip_lookup l
WHERE LOWER(TRIM(c.city)) = LOWER(TRIM(l.city))
  AND UPPER(TRIM(c.state)) = UPPER(TRIM(l.state))
  AND (c.zipcode IS NULL OR c.zipcode = '');

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'ENRICHMENT SUMMARY'
\echo '════════════════════════════════════════════════════════════'

SELECT
  'Zip codes enriched (from lookup table)' as metric,
  COUNT(*) as value
FROM contacts_enrichment_backup
WHERE enrichment_type = 'city_state_lookup'
  AND enriched_at > NOW() - INTERVAL '2 minutes';

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'VERIFICATION'
\echo '════════════════════════════════════════════════════════════'

-- Verify completeness improved
SELECT
  'Zip code completeness BEFORE' as metric,
  '2.7%' as value

UNION ALL

SELECT
  'Zip code completeness AFTER' as metric,
  ROUND(100.0 * COUNT(*) FILTER (WHERE zipcode IS NOT NULL AND zipcode <> '') / COUNT(*), 1)::text || '%' as value
FROM contacts;

-- Contacts still needing enrichment
SELECT
  'Contacts still needing zip (have city/state)' as metric,
  COUNT(*) as value
FROM contacts
WHERE (city IS NOT NULL AND city <> '')
  AND (state IS NOT NULL AND state <> '')
  AND (zipcode IS NULL OR zipcode = '');

-- Top 10 cities still needing zip codes
\echo ''
\echo 'Top 10 cities still needing zip codes (for API enrichment):'
\echo ''

SELECT
  city || ', ' || state as location,
  COUNT(*) as contacts_needing_zip
FROM contacts
WHERE (city IS NOT NULL AND city <> '')
  AND (state IS NOT NULL AND state <> '')
  AND (zipcode IS NULL OR zipcode = '')
GROUP BY city, state
ORDER BY COUNT(*) DESC
LIMIT 10;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo 'Ready to COMMIT or ROLLBACK'
\echo '════════════════════════════════════════════════════════════'

COMMIT;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '✓ ZIP CODE ENRICHMENT COMMITTED!'
\echo '════════════════════════════════════════════════════════════'
\echo ''
\echo 'NOTE: For remaining cities, consider using:'
\echo '  - Zippopotam.us API (free): http://api.zippopotam.us/us/{state}/{city}'
\echo '  - USPS API (free, requires registration)'
\echo '  - SmartyStreets API (paid, most accurate)'
\echo ''
