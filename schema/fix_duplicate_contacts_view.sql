-- Fix Duplicate Contacts in View
-- Issue: Some contacts have multiple subscriptions, causing duplicates
-- Solution: Use DISTINCT ON to get one row per contact, prioritizing Program Partner subscriptions

DROP VIEW IF EXISTS v_contact_list_with_subscriptions CASCADE;

CREATE VIEW v_contact_list_with_subscriptions AS
WITH
  contact_roles AS (
    SELECT
      contact_id,
      BOOL_OR(role = 'member') as is_member,
      BOOL_OR(role = 'donor') as is_donor,
      BOOL_OR(role = 'volunteer') as is_volunteer,
      ARRAY_AGG(DISTINCT role) FILTER (WHERE role IS NOT NULL) as active_roles
    FROM contact_roles
    GROUP BY contact_id
  ),
  outreach_emails AS (
    SELECT DISTINCT ON (contact_id)
      contact_id,
      email as outreach_email,
      source as outreach_source
    FROM contact_emails
    WHERE is_primary = true OR verified = true
    ORDER BY contact_id, is_primary DESC NULLS LAST, verified DESC NULLS LAST, created_at DESC
  ),
  -- Get the BEST subscription for each contact (prioritize Program Partner over Individual)
  best_subscription AS (
    SELECT DISTINCT ON (s.contact_id)
      s.contact_id,
      s.status,
      s.amount,
      s.currency,
      s.is_annual,
      s.start_date as member_since,
      mp.is_legacy,
      mp.membership_group,
      mp.membership_level
    FROM subscriptions s
    LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
    WHERE s.status IN ('active', 'trial')
    ORDER BY s.contact_id,
      -- Prioritize Program Partner subscriptions first
      CASE WHEN mp.membership_group = 'Program Partner' THEN 1 ELSE 2 END,
      -- Then by tier (higher tiers first)
      mp.sort_order NULLS LAST,
      s.updated_at DESC
  ),
  partner_compliance AS (
    SELECT DISTINCT ON (c.id)
      c.id,
      c.is_expected_program_partner,
      CASE
        WHEN c.is_expected_program_partner AND bs.membership_group = 'Program Partner' AND bs.status = 'active' THEN 'compliant'
        WHEN c.is_expected_program_partner AND bs.membership_group = 'Individual' AND bs.status = 'active' THEN 'needs_upgrade'
        WHEN c.is_expected_program_partner AND bs.status = 'trial' THEN 'trial'
        WHEN c.is_expected_program_partner THEN 'no_membership'
        ELSE NULL
      END as partner_compliance_status,
      CASE
        WHEN c.is_expected_program_partner AND bs.membership_group = 'Program Partner' AND bs.status = 'active' THEN 'In Compliance'
        WHEN c.is_expected_program_partner AND bs.membership_group = 'Individual' AND bs.status = 'active'
          THEN 'Has ' || COALESCE(bs.membership_level, 'Individual') || ' - Needs Upgrade'
        WHEN c.is_expected_program_partner AND bs.status = 'trial' THEN 'In Trial Period'
        WHEN c.is_expected_program_partner THEN 'No Active Membership'
        ELSE NULL
      END as partner_compliance_message
    FROM contacts c
    LEFT JOIN best_subscription bs ON c.id = bs.contact_id
    ORDER BY c.id
  )
SELECT DISTINCT ON (c.id)
  c.id,
  c.first_name,
  c.last_name,
  c.first_name || ' ' || COALESCE(c.last_name, '') as full_name,
  voe.outreach_email as email,
  voe.outreach_source,
  c.total_spent,
  c.transaction_count,
  c.has_active_subscription,
  c.last_transaction_date,
  vcr.is_member,
  vcr.is_donor,
  vcr.is_volunteer,
  vcr.active_roles,
  c.membership_level,
  c.membership_tier,
  c.email_subscribed,
  c.updated_at,
  c.created_at,
  bs.status as subscription_status,
  bs.is_annual,
  bs.member_since,
  bs.amount as subscription_amount,
  bs.currency as subscription_currency,
  bs.is_legacy,
  bs.membership_group,
  -- Program Partner compliance fields
  c.is_expected_program_partner,
  pc.partner_compliance_status,
  pc.partner_compliance_message
FROM contacts c
LEFT JOIN contact_roles vcr ON c.id = vcr.contact_id
LEFT JOIN outreach_emails voe ON c.id = voe.contact_id
LEFT JOIN best_subscription bs ON c.id = bs.contact_id
LEFT JOIN partner_compliance pc ON c.id = pc.id
ORDER BY c.id;

-- Verify no duplicates
SELECT 'Checking for duplicates...' as status;

SELECT
  email,
  COUNT(*) as count
FROM v_contact_list_with_subscriptions
WHERE is_expected_program_partner = TRUE
GROUP BY email
HAVING COUNT(*) > 1;

-- If no rows returned above, we're good!
SELECT '✅ Duplicates fixed!' as result WHERE NOT EXISTS (
  SELECT 1
  FROM v_contact_list_with_subscriptions
  WHERE is_expected_program_partner = TRUE
  GROUP BY email
  HAVING COUNT(*) > 1
);
