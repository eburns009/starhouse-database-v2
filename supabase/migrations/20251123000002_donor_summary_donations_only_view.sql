-- Migration: Create v_donor_summary_donations_only view
-- Purpose: Provide donor summary with amounts recalculated excluding membership transactions
-- This supports the "Donations Only" toggle in the Donors UI

CREATE OR REPLACE VIEW v_donor_summary_donations_only AS
SELECT
    d.id as donor_id,
    d.contact_id,
    c.email,
    c.first_name,
    c.last_name,
    c.phone,
    c.city,
    c.state,
    d.status as donor_status,
    -- Recalculate amounts excluding memberships
    COALESCE((SELECT SUM(t.amount)
              FROM transactions t
              WHERE t.contact_id = c.id
              AND t.is_donation = true
              AND (t.donation_subcategory IS NULL OR t.donation_subcategory NOT LIKE '%Membership%')), 0) as lifetime_amount,
    COALESCE((SELECT COUNT(*)
              FROM transactions t
              WHERE t.contact_id = c.id
              AND t.is_donation = true
              AND (t.donation_subcategory IS NULL OR t.donation_subcategory NOT LIKE '%Membership%')), 0) as lifetime_count,
    -- Keep other fields from donors table
    d.largest_gift,
    d.average_gift,
    d.first_gift_date,
    d.last_gift_date,
    d.ytd_amount,
    d.ytd_count,
    d.is_major_donor,
    d.do_not_solicit,
    d.do_not_call,
    d.recognition_name,
    d.anonymous
FROM donors d
JOIN contacts c ON d.contact_id = c.id;

COMMENT ON VIEW v_donor_summary_donations_only IS 'Donor summary with lifetime amounts calculated excluding membership transactions';
