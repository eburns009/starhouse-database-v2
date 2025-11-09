-- Fix membership_products to match ACTUAL PayPal Item Titles
-- Based on analysis of actual PayPal export data

-- Clear existing data
TRUNCATE TABLE membership_products CASCADE;

-- Insert with CORRECT PayPal Item Title variations
INSERT INTO membership_products (
    product_name,
    product_slug,
    membership_group,
    membership_level,
    membership_tier,
    monthly_price,
    annual_price,
    paypal_item_titles,
    description,
    is_active,
    is_legacy,
    sort_order
) VALUES
    -- INDIVIDUAL MEMBERSHIPS
    (
        'Nova Individual Membership',
        'nova-individual',
        'Individual',
        'Nova',
        'Entry',
        12.00,
        144.00,
        ARRAY[
            'Nova StarHouse Membership',
            'nova starhouse membership',
            'Nova Starhouse Membership',
            'NOVA STARHOUSE MEMBERSHIP'
        ],
        'Entry-level individual StarHouse membership',
        true,
        false,
        1
    ),
    (
        'Antares Individual Membership',
        'antares-individual',
        'Individual',
        'Antares',
        'Standard',
        22.00,
        242.00,
        ARRAY[
            'Antares StarHouse Membership',
            'antares starhouse membership',
            'Antares Starhouse Membership',
            'ANTARES STARHOUSE MEMBERSHIP'
        ],
        'Standard individual StarHouse membership - Most Popular!',
        true,
        false,
        2
    ),
    (
        'Aldebaran Individual Membership',
        'aldebaran-individual',
        'Individual',
        'Aldebaran',
        'Premium',
        44.00,
        484.00,
        ARRAY[
            'Aldebaran StarHouse Membership',
            'aldebaran starhouse membership',
            'Aldebaran Starhouse Membership',
            'ALDEBARAN STARHOUSE MEMBERSHIP'
        ],
        'Premium individual StarHouse membership',
        true,
        false,
        3
    ),
    (
        'Spica Individual Membership',
        'spica-individual',
        'Individual',
        'Spica',
        'Elite',
        88.00,
        968.00,
        ARRAY[
            'Spica StarHouse Membership',
            'spica starhouse membership',
            'Spica Starhouse Membership',
            'SPICA STARHOUSE MEMBERSHIP'
        ],
        'Elite individual StarHouse membership',
        true,
        false,
        4
    ),
    (
        'Friend Membership',
        'friend-legacy',
        'Individual',
        'Friend',
        'Legacy',
        NULL,
        NULL,
        ARRAY[
            'Friend',
            'friend',
            'FRIEND',
            'Friend Membership'
        ],
        'Legacy Friend membership level',
        false,
        true,
        5
    ),
    (
        'Advocate Membership',
        'advocate-legacy',
        'Individual',
        'Advocate',
        'Legacy',
        NULL,
        NULL,
        ARRAY[
            'Advocate',
            'advocate',
            'ADVOCATE',
            'Advocate Individual',
            'Advocate Membership'
        ],
        'Legacy Advocate membership level',
        false,
        true,
        6
    ),

    -- PROGRAM PARTNER MEMBERSHIPS
    (
        'Luminary Partner',
        'luminary-partner',
        'Program Partner',
        'Luminary Partner',
        'Partner',
        33.00,
        363.00,
        ARRAY[
            'Program Partner Luminary',
            'program partner luminary',
            'Luminary Partner',
            'luminary partner',
            'PROGRAM PARTNER LUMINARY',
            'Program Partners Luminary',
            'Program Partners Luminary Tier'
        ],
        'Luminary Program Partner membership',
        true,
        false,
        7
    ),
    (
        'Celestial Partner',
        'celestial-partner',
        'Program Partner',
        'Celestial Partner',
        'Partner',
        55.00,
        605.00,
        ARRAY[
            'Program Partners Celestial Tier',
            'program partners celestial tier',
            'Celestial Partner',
            'celestial partner',
            'PROGRAM PARTNERS CELESTIAL TIER',
            'Program Partner Celestial',
            'Celestial Tier'
        ],
        'Celestial Program Partner membership',
        true,
        false,
        8
    ),
    (
        'Astral Partner',
        'astral-partner',
        'Program Partner',
        'Astral Partner',
        'Partner',
        99.00,
        1089.00,
        ARRAY[
            'Program Partners Astral Tier',
            'program partners astral tier',
            'Astral Partner',
            'astral partner',
            'PROGRAM PARTNERS ASTRAL TIER',
            'Program Partner Astral',
            'Astral Tier'
        ],
        'Astral Program Partner membership - Highest tier!',
        true,
        false,
        9
    )
ON CONFLICT DO NOTHING;

-- Verify
SELECT
    product_name,
    membership_group,
    membership_level,
    array_length(paypal_item_titles, 1) as title_variations,
    is_active
FROM membership_products
ORDER BY sort_order;
