-- ============================================================================
-- FIX SUBSCRIPTION PROTECTION GAPS
-- ============================================================================
-- Purpose: Protect ALL opt-ins from being overwritten, not just Ticket Tailor
-- Author: Claude Code
-- Date: 2025-11-11
--
-- CRITICAL: Current state only protects 73 opt-ins (Ticket Tailor + Zoho)
--           Need to protect ALL 3,757 opt-ins across all sources
-- ============================================================================

BEGIN;

-- 1. Protect Manual opt-ins (252 contacts)
-- ============================================================================
UPDATE contacts
SET
  subscription_protected = TRUE,
  subscription_protected_reason = 'Manual opt-in - staff entered, trusted source'
WHERE
  deleted_at IS NULL
  AND source_system = 'manual'
  AND email_subscribed = TRUE
  AND (subscription_protected IS NULL OR subscription_protected = FALSE);

-- 2. Protect PayPal opt-ins (33 contacts)
-- ============================================================================
UPDATE contacts
SET
  subscription_protected = TRUE,
  subscription_protected_reason = 'PayPal opt-in - transaction-based consent'
WHERE
  deleted_at IS NULL
  AND source_system = 'paypal'
  AND email_subscribed = TRUE
  AND (subscription_protected IS NULL OR subscription_protected = FALSE);

-- 3. Protect Kajabi opt-ins FROM NON-KAJABI imports (3,389 contacts)
-- ============================================================================
-- Note: Kajabi opt-ins should be protected from PayPal/Zoho/Manual imports,
--       but CAN be updated by Kajabi imports (Kajabi is source of truth)
UPDATE contacts
SET
  subscription_protected = TRUE,
  subscription_protected_reason = 'Kajabi opt-in - only Kajabi can update'
WHERE
  deleted_at IS NULL
  AND source_system = 'kajabi'
  AND email_subscribed = TRUE
  AND (subscription_protected IS NULL OR subscription_protected = FALSE);

-- 4. Verification
-- ============================================================================
SELECT
  'Subscription Protection Coverage' as report,
  source_system,
  COUNT(*) as total_subscribed,
  COUNT(CASE WHEN subscription_protected THEN 1 END) as protected,
  COUNT(CASE WHEN NOT subscription_protected OR subscription_protected IS NULL THEN 1 END) as unprotected
FROM contacts
WHERE deleted_at IS NULL
  AND email_subscribed = TRUE
GROUP BY source_system
ORDER BY total_subscribed DESC;

-- Overall stats
SELECT
  'TOTAL OPT-INS' as metric,
  COUNT(*) as count
FROM contacts
WHERE deleted_at IS NULL AND email_subscribed = TRUE

UNION ALL

SELECT
  'Protected' as metric,
  COUNT(*) as count
FROM contacts
WHERE deleted_at IS NULL
  AND email_subscribed = TRUE
  AND subscription_protected = TRUE

UNION ALL

SELECT
  'Unprotected (SHOULD BE 0!)' as metric,
  COUNT(*) as count
FROM contacts
WHERE deleted_at IS NULL
  AND email_subscribed = TRUE
  AND (subscription_protected IS NULL OR subscription_protected = FALSE);

COMMIT;
