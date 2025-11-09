-- Verification Script for Program Partner Compliance System
-- Run this to verify the system is working correctly

-- 1. Check that the contacts table has the new field
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'contacts'
  AND column_name = 'is_expected_program_partner';

-- 2. Check how many expected partners are marked
SELECT
  COUNT(*) as total_expected_partners
FROM contacts
WHERE is_expected_program_partner = TRUE;

-- 3. Check the compliance view exists
SELECT EXISTS (
  SELECT 1
  FROM information_schema.views
  WHERE table_name = 'program_partner_compliance'
) as compliance_view_exists;

-- 4. Check compliance statistics
SELECT
  compliance_status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM program_partner_compliance
GROUP BY compliance_status
ORDER BY count DESC;

-- 5. Sample of compliant partners (first 5)
SELECT
  first_name,
  last_name,
  email,
  current_membership,
  compliance_message
FROM program_partner_compliance
WHERE compliance_status = 'compliant'
ORDER BY last_name
LIMIT 5;

-- 6. Sample of non-compliant partners who need upgrade (first 5)
SELECT
  first_name,
  last_name,
  email,
  current_membership,
  compliance_message
FROM program_partner_compliance
WHERE compliance_status = 'needs_upgrade'
ORDER BY last_name
LIMIT 5;

-- 7. Check that the contact list view has the new fields
SELECT
  column_name,
  data_type
FROM information_schema.columns
WHERE table_name = 'v_contact_list_with_subscriptions'
  AND column_name IN ('is_expected_program_partner', 'partner_compliance_status', 'partner_compliance_message')
ORDER BY column_name;

-- 8. Sample query from the view (first 5 expected partners)
SELECT
  first_name,
  last_name,
  email,
  membership_level,
  is_expected_program_partner,
  partner_compliance_status,
  partner_compliance_message
FROM v_contact_list_with_subscriptions
WHERE is_expected_program_partner = TRUE
ORDER BY partner_compliance_status, last_name
LIMIT 5;

-- 9. Verify the 6 Program Partner products exist
SELECT
  name,
  kajabi_offer_id,
  active
FROM products
WHERE product_type = 'program_partner'
ORDER BY
  CASE
    WHEN name LIKE '%Luminary%' THEN 1
    WHEN name LIKE '%Celestial%' THEN 2
    WHEN name LIKE '%Astral%' THEN 3
  END,
  CASE
    WHEN name LIKE '%monthly%' THEN 1
    WHEN name LIKE '%Annual%' THEN 2
  END;

-- 10. Count active subscriptions by partner tier
SELECT
  mp.membership_level,
  COUNT(*) as active_subscriptions,
  SUM(s.amount) as total_monthly_revenue
FROM subscriptions s
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active'
  AND mp.membership_group = 'Program Partner'
GROUP BY mp.membership_level
ORDER BY total_monthly_revenue DESC;

-- Success message
SELECT '✅ All verification checks completed!' as status;
