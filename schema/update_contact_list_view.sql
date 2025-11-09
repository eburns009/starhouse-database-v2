-- Update contact list view to include Program Partner compliance fields
-- Created: 2025-11-04

CREATE OR REPLACE VIEW v_contact_list_with_subscriptions AS
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
  active_subscriptions AS (
    SELECT DISTINCT ON (s.contact_id)
      s.contact_id,
      s.status,
      s.amount,
      s.currency,
      s.is_annual,
      s.start_date as member_since,
      mp.is_legacy,
      mp.membership_group
    FROM subscriptions s
    LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
    WHERE s.status IN ('active', 'trial')
    ORDER BY s.contact_id,
      CASE
        WHEN mp.membership_group = 'Program Partner' THEN 1
        WHEN mp.membership_group = 'Individual' THEN 2
        ELSE 3
      END,
      s.updated_at DESC
  ),
  partner_compliance AS (
    SELECT
      c.id,
      c.is_expected_program_partner,
      CASE
        WHEN c.is_expected_program_partner AND mp.membership_group = 'Program Partner' AND s.status = 'active' THEN 'compliant'
        WHEN c.is_expected_program_partner AND mp.membership_group = 'Individual' AND s.status = 'active' THEN 'needs_upgrade'
        WHEN c.is_expected_program_partner AND s.status = 'trial' THEN 'trial'
        WHEN c.is_expected_program_partner THEN 'no_membership'
        ELSE NULL
      END as partner_compliance_status,
      CASE
        WHEN c.is_expected_program_partner AND mp.membership_group = 'Program Partner' AND s.status = 'active' THEN 'In Compliance'
        WHEN c.is_expected_program_partner AND mp.membership_group = 'Individual' AND s.status = 'active'
          THEN 'Has ' || COALESCE(mp.membership_level, 'Individual') || ' - Needs Upgrade'
        WHEN c.is_expected_program_partner AND s.status = 'trial' THEN 'In Trial Period'
        WHEN c.is_expected_program_partner THEN 'No Active Membership'
        ELSE NULL
      END as partner_compliance_message
    FROM contacts c
    LEFT JOIN subscriptions s ON c.id = s.contact_id AND s.status IN ('active', 'trial')
    LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
  )
SELECT
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
  s_active.status as subscription_status,
  s_active.is_annual,
  s_active.member_since,
  s_active.amount as subscription_amount,
  s_active.currency as subscription_currency,
  s_active.is_legacy,
  s_active.membership_group,
  -- New Program Partner compliance fields
  c.is_expected_program_partner,
  pc.partner_compliance_status,
  pc.partner_compliance_message
FROM contacts c
LEFT JOIN contact_roles vcr ON c.id = vcr.contact_id
LEFT JOIN outreach_emails voe ON c.id = voe.contact_id
LEFT JOIN active_subscriptions s_active ON c.id = s_active.contact_id
LEFT JOIN partner_compliance pc ON c.id = pc.id;

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON v_contact_list_with_subscriptions TO your_app_user;
