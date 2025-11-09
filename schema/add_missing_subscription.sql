-- Add Missing PayPal Subscription: I-62RBW0RK1J8L
-- ================================================
-- Contact: Scott Medina (mysticcker@aol.com)
-- Product: Astral Partner Annual ($1089/year)
-- Payment Date: Feb 18, 2025

BEGIN;

-- Get contact ID
DO $$
DECLARE
    v_contact_id UUID;
    v_product_id UUID;
BEGIN
    -- Get contact ID
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE email = 'mysticcker@aol.com';

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact not found: mysticcker@aol.com';
    END IF;

    -- Get membership product ID
    SELECT id INTO v_product_id
    FROM membership_products
    WHERE product_slug = 'astral-partner';

    IF v_product_id IS NULL THEN
        RAISE EXCEPTION 'Membership product not found: astral-partner';
    END IF;

    RAISE NOTICE 'Contact ID: %', v_contact_id;
    RAISE NOTICE 'Product ID: %', v_product_id;

    -- Insert the missing subscription
    INSERT INTO subscriptions (
        contact_id,
        membership_product_id,
        paypal_subscription_reference,
        status,
        amount,
        currency,
        billing_cycle,
        start_date,
        next_billing_date,
        payment_processor,
        is_annual
    ) VALUES (
        v_contact_id,
        v_product_id,
        'I-62RBW0RK1J8L',
        'active',  -- Assuming active since payment was in Feb 2025
        1089.00,
        'USD',
        'annual',
        '2025-02-18'::date,
        '2026-02-18'::date,  -- Next billing in 1 year
        'PayPal',
        TRUE
    );

    RAISE NOTICE 'Subscription added successfully';

    -- Update contact's active subscription flag
    UPDATE contacts
    SET has_active_subscription = TRUE
    WHERE id = v_contact_id;

    RAISE NOTICE 'Contact updated: has_active_subscription = TRUE';

END $$;

-- Verify the insertion
SELECT
    c.first_name,
    c.last_name,
    c.email,
    c.membership_level,
    c.has_active_subscription,
    s.paypal_subscription_reference,
    s.amount,
    s.billing_cycle,
    s.status,
    mp.product_name,
    mp.membership_level as product_level
FROM contacts c
JOIN subscriptions s ON c.id = s.contact_id
JOIN membership_products mp ON s.membership_product_id = mp.id
WHERE c.email = 'mysticcker@aol.com';

COMMIT;

SELECT '✅ COMPLETE: Added missing subscription for Scott Medina (Astral Partner Annual)' as result;
