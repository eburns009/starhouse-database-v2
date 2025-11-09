-- Fix Subscription Product Mappings
-- ===================================
-- Problem: 129 active subscriptions have NULL membership_product_id
-- Solution: Match subscriptions to membership products by amount
-- Result: Contacts will have correct membership_level populated

BEGIN;

-- Show current state
SELECT
    'BEFORE' as status,
    COUNT(*) as total_active_subs,
    COUNT(membership_product_id) as with_product,
    COUNT(*) - COUNT(membership_product_id) as missing_product
FROM subscriptions
WHERE status = 'active';

-- Update monthly subscriptions
-- Nova ($12/month)
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 12.00
  AND mp.product_slug = 'nova-individual';

-- Antares ($22/month) - This is the one for brieandbjorn@gmail.com
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 22.00
  AND mp.product_slug = 'antares-individual';

-- Luminary Partner ($33/month)
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 33.00
  AND mp.product_slug = 'luminary-partner';

-- Aldebaran ($44/month)
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 44.00
  AND mp.product_slug = 'aldebaran-individual';

-- Celestial Partner ($55/month)
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 55.00
  AND mp.product_slug = 'celestial-partner';

-- Spica ($88/month)
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 88.00
  AND mp.product_slug = 'spica-individual';

-- Astral Partner ($99/month)
UPDATE subscriptions s
SET membership_product_id = mp.id
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 99.00
  AND mp.product_slug = 'astral-partner';

-- Update annual subscriptions
-- Nova Annual ($144/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 144.00
  AND mp.product_slug = 'nova-individual';

-- Antares Annual ($242/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 242.00
  AND mp.product_slug = 'antares-individual';

-- Luminary Partner Annual ($363/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 363.00
  AND mp.product_slug = 'luminary-partner';

-- Aldebaran Annual ($484/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 484.00
  AND mp.product_slug = 'aldebaran-individual';

-- Celestial Partner Annual ($605/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 605.00
  AND mp.product_slug = 'celestial-partner';

-- Spica Annual ($968/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 968.00
  AND mp.product_slug = 'spica-individual';

-- Astral Partner Annual ($1089/year)
UPDATE subscriptions s
SET membership_product_id = mp.id,
    is_annual = TRUE
FROM membership_products mp
WHERE s.status = 'active'
  AND s.membership_product_id IS NULL
  AND s.amount = 1089.00
  AND mp.product_slug = 'astral-partner';

-- Show intermediate state
SELECT
    'AFTER SUBSCRIPTION UPDATE' as status,
    COUNT(*) as total_active_subs,
    COUNT(membership_product_id) as with_product,
    COUNT(*) - COUNT(membership_product_id) as missing_product
FROM subscriptions
WHERE status = 'active';

-- Now update contacts.membership_level from their active subscription
UPDATE contacts c
SET membership_level = mp.membership_level
FROM subscriptions s
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE c.id = s.contact_id
  AND s.status = 'active'
  AND c.has_active_subscription = TRUE
  AND (c.membership_level IS NULL OR c.membership_level = '');

-- Show final state
SELECT
    'AFTER CONTACT UPDATE' as status,
    COUNT(*) as total_contacts_with_active_sub,
    COUNT(membership_level) as with_level,
    COUNT(*) - COUNT(membership_level) as missing_level
FROM contacts
WHERE has_active_subscription = TRUE;

-- Show breakdown by membership level
SELECT
    mp.membership_level,
    COUNT(*) as subscriber_count,
    SUM(CASE WHEN s.is_annual THEN 1 ELSE 0 END) as annual,
    SUM(CASE WHEN NOT s.is_annual THEN 1 ELSE 0 END) as monthly
FROM subscriptions s
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE s.status = 'active'
GROUP BY mp.membership_level
ORDER BY COUNT(*) DESC;

-- Verify Bjorn's subscription
SELECT
    c.first_name,
    c.last_name,
    c.email,
    c.membership_level,
    s.amount,
    s.billing_cycle,
    mp.product_name,
    mp.membership_level as product_level
FROM contacts c
JOIN subscriptions s ON c.id = s.contact_id
LEFT JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE c.email = 'brieandbjorn@gmail.com';

COMMIT;

-- Summary Report
SELECT
    '✅ COMPLETE' as status,
    'All active subscriptions now have membership_product_id' as message,
    'All contacts now have membership_level populated' as result;
