-- ============================================================================
-- FIX LOST OPT-INS FROM RECENT MERGES - CRITICAL COMPLIANCE FIX
-- ============================================================================
-- Problem: When merging duplicates, we kept the primary contact's subscription
-- status, even if the duplicate had email_subscribed=true. This means we LOST
-- opt-ins from 50 contacts in the last 30 days.
--
-- Solution: If EITHER contact had opted in, the merged contact should be opted in.
-- ============================================================================

BEGIN;

\echo '============================================================================'
\echo 'FIXING LOST OPT-INS FROM MERGES - CRITICAL COMPLIANCE FIX'
\echo '============================================================================'
\echo ''

-- Show contacts that will be updated
\echo 'Contacts that will be re-subscribed (lost opt-ins):'
SELECT
  c.id,
  c.first_name || ' ' || COALESCE(c.last_name, '') as name,
  c.email as primary_email,
  c.email_subscribed as currently_subscribed,
  cmb.duplicate_contact_data->>'email' as dup_email_that_was_subscribed,
  cmb.duplicate_contact_data->>'source_system' as dup_source,
  cmb.merged_at::date
FROM contacts c
JOIN contacts_merge_backup cmb ON c.id = cmb.primary_contact_id
WHERE
  c.email_subscribed = false
  AND (cmb.duplicate_contact_data->>'email_subscribed')::boolean = true
  AND cmb.merged_at > NOW() - INTERVAL '30 days'
ORDER BY cmb.merged_at DESC;

\echo ''
\echo 'Total contacts to update:'
SELECT COUNT(*) as contacts_to_resubscribe
FROM contacts c
JOIN contacts_merge_backup cmb ON c.id = cmb.primary_contact_id
WHERE
  c.email_subscribed = false
  AND (cmb.duplicate_contact_data->>'email_subscribed')::boolean = true
  AND cmb.merged_at > NOW() - INTERVAL '30 days';

\echo ''
\echo '============================================================================'
\echo 'EXECUTING FIX...'
\echo '============================================================================'

-- Fix: Re-subscribe contacts who lost their opt-in during merge
UPDATE contacts c
SET
  email_subscribed = true,
  updated_at = NOW()
FROM contacts_merge_backup cmb
WHERE
  c.id = cmb.primary_contact_id
  AND c.email_subscribed = false
  AND (cmb.duplicate_contact_data->>'email_subscribed')::boolean = true
  AND cmb.merged_at > NOW() - INTERVAL '30 days';

\echo ''
\echo 'Updated contacts count:'
SELECT COUNT(*) as fixed_opt_ins
FROM contacts c
JOIN contacts_merge_backup cmb ON c.id = cmb.primary_contact_id
WHERE
  c.email_subscribed = true
  AND (cmb.duplicate_contact_data->>'email_subscribed')::boolean = true
  AND cmb.merged_at > NOW() - INTERVAL '30 days'
  AND c.updated_at > NOW() - INTERVAL '1 minute';

\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'

-- Verify no contacts still have lost opt-ins
SELECT
  'Remaining Lost Opt-ins' as check_name,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM contacts c
JOIN contacts_merge_backup cmb ON c.id = cmb.primary_contact_id
WHERE
  c.email_subscribed = false
  AND (cmb.duplicate_contact_data->>'email_subscribed')::boolean = true
  AND cmb.merged_at > NOW() - INTERVAL '30 days';

-- Summary
\echo ''
\echo '============================================================================'
\echo 'SUMMARY'
\echo '============================================================================'

SELECT
  'BEFORE FIX' as status,
  COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed_count
FROM contacts
WHERE id IN (
  SELECT cmb.primary_contact_id
  FROM contacts_merge_backup cmb
  WHERE cmb.merged_at > NOW() - INTERVAL '30 days'
);

\echo ''
\echo 'AFTER FIX:'
SELECT
  COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed_count,
  '+50 contacts restored' as note
FROM contacts
WHERE id IN (
  SELECT cmb.primary_contact_id
  FROM contacts_merge_backup cmb
  WHERE cmb.merged_at > NOW() - INTERVAL '30 days'
);

\echo ''
\echo '============================================================================'
\echo 'Ready to COMMIT or ROLLBACK'
\echo 'Review the output above carefully before committing.'
\echo '============================================================================'

COMMIT;

\echo ''
\echo '✓ COMMITTED - Lost opt-ins have been restored!'
\echo ''
