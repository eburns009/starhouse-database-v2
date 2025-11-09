-- Program Partner Compliance Tracking
-- Created: 2025-11-04
-- Purpose: Track which contacts should be Program Partners and their compliance status

-- Add field to contacts table to mark expected Program Partners
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS is_expected_program_partner BOOLEAN DEFAULT FALSE;

-- Add index for filtering
CREATE INDEX IF NOT EXISTS idx_contacts_expected_partner
ON contacts(is_expected_program_partner)
WHERE is_expected_program_partner = TRUE;

-- Mark the 41 contacts from partners.csv as expected Program Partners
UPDATE contacts
SET is_expected_program_partner = TRUE
WHERE LOWER(email) IN (
    'dan.balgooyen@gmail.com', 'kali.basman@gmail.com', 'carbone2002@gmail.com',
    'mcohen1966@gmail.com', 'michael@earthbasedinstitute.org', 'risingrootswellness@gmail.com',
    'yoginijeanie@gmail.com', 'scottamedina@gmail.com', 'shanti@energizeshanti.com',
    'info@pavanjeet.com', 'danielapapi@gmail.com', 'melissa@goldenbridge.org',
    'jeremy@jeremyroske.com', 'spencer.jacobson@gmail.com', 'amber@the360emergence.com',
    'taragape@gmail.com', 'jonathan@door4.org', 'kimberlyjhan@gmail.com',
    'mikaylawilder@gmail.com', 'coeur@carlyraemer.com', 'brieandbjorn@gmail.com',
    'melissabauknight@gmail.com', 'taylor.bratches@gmail.com', 'melody@liveinresonance.com',
    'gurpreetgill2@hotmail.com', 'fieldspatricia@comcast.net', 'mackensey@breathtosoul.com',
    'harwood.ferguson@gmail.com', 'iain@sangha.one', 'laura.k.bales@gmail.com',
    'alec@sacredsons.com', 'anemeraldearth@gmail.com', 'dan@peacefulvibes.com',
    'artemisiaandrose@gmail.com', 'natalie@ayurvedawellnesscoach.com', 'wendy@centerforsomaticgrieving.com',
    'dustinost32@gmail.com', 'jewels@becomingbioquantum.com', 'mason@sacredsons.com',
    'hbwebb@google.com', 'ellie@mindfulbellie.com'
);

-- Create a view for Program Partner compliance status
CREATE OR REPLACE VIEW program_partner_compliance AS
WITH membership_ranking AS (
  SELECT
    c.id,
    c.first_name,
    c.last_name,
    c.email,
    c.is_expected_program_partner,
    mp.membership_level,
    mp.membership_group,
    mp.monthly_price,
    mp.annual_price,
    mp.sort_order,
    s.status,
    s.amount,
    s.billing_cycle,
    s.next_billing_date,
    ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY
      CASE WHEN mp.membership_group = 'Program Partner' THEN 1 ELSE 2 END,
      mp.sort_order
    ) as rn
  FROM contacts c
  LEFT JOIN subscriptions s ON c.id = s.contact_id AND s.status IN ('active', 'trial')
  LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
  WHERE c.is_expected_program_partner = TRUE
)
SELECT
  id,
  first_name,
  last_name,
  email,
  is_expected_program_partner,
  COALESCE(membership_level, 'No Active Membership') as current_membership,
  COALESCE(membership_group, '') as membership_group,
  status as subscription_status,
  billing_cycle,
  amount as monthly_payment,
  next_billing_date,
  CASE
    WHEN membership_group = 'Program Partner' AND status = 'active' THEN 'compliant'
    WHEN membership_group = 'Individual' AND status = 'active' THEN 'needs_upgrade'
    WHEN status = 'trial' THEN 'trial'
    ELSE 'no_membership'
  END as compliance_status,
  CASE
    WHEN membership_group = 'Program Partner' AND status = 'active' THEN 'In Compliance'
    WHEN membership_group = 'Individual' AND status = 'active'
      THEN 'Has ' || membership_level || ' - Needs Upgrade to Program Partner'
    WHEN status = 'trial' THEN 'In Trial Period'
    ELSE 'No Active Membership - Action Required'
  END as compliance_message
FROM membership_ranking
WHERE rn = 1 OR rn IS NULL;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT ON program_partner_compliance TO your_app_user;

-- Verification queries
-- Show compliance summary
-- SELECT
--   compliance_status,
--   COUNT(*) as count,
--   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
-- FROM program_partner_compliance
-- GROUP BY compliance_status
-- ORDER BY count DESC;

-- Show all non-compliant members
-- SELECT * FROM program_partner_compliance
-- WHERE compliance_status != 'compliant'
-- ORDER BY compliance_status, last_name, first_name;
