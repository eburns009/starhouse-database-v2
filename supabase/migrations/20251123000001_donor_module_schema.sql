-- ============================================================================
-- STARHOUSE DONOR MODULE SCHEMA
-- ============================================================================
-- Purpose: Track donations, donor relationships, acknowledgments, and outreach
--
-- Tables:
--   1. donors - Donor profiles linked to contacts
--   2. transactions (extended) - Additional donation-specific fields
--   3. donation_acknowledgments - Acknowledgment tracking
--   4. donor_outreach - Phone-a-thon campaign tracking
--
-- Design Principles:
--   - UUID primary keys (immutable)
--   - Foreign keys with appropriate cascade behavior
--   - Indexes for 10+ year historical queries
--   - RLS policies for staff access control
--   - Audit columns on all tables
-- ============================================================================

-- ============================================================================
-- CUSTOM TYPES (Enums)
-- ============================================================================

-- Donor status for segmentation
DO $$ BEGIN
    CREATE TYPE donor_status AS ENUM (
        'prospect',      -- Never donated, potential donor
        'first_time',    -- Single donation
        'active',        -- Multiple donations in last 12 months
        'lapsed',        -- No donation in 12-24 months
        'dormant',       -- No donation in 24+ months
        'major',         -- Lifetime giving > threshold (e.g., $1000)
        'deceased'       -- Marked as deceased
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Acknowledgment status tracking
DO $$ BEGIN
    CREATE TYPE acknowledgment_status AS ENUM (
        'pending_review',    -- Manual entry, needs staff review
        'auto_queued',       -- QB import <90 days, queued for send
        'sent',              -- Acknowledgment sent
        'skipped_old',       -- QB import >90 days, skipped
        'external',          -- Online donation, external acknowledgment
        'not_required'       -- Below threshold or opted out
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Outreach call outcomes
DO $$ BEGIN
    CREATE TYPE outreach_outcome AS ENUM (
        'pledged',           -- Donor pledged amount
        'declined',          -- Donor declined
        'callback',          -- Requested callback
        'no_answer',         -- No answer
        'wrong_number',      -- Invalid contact info
        'do_not_call',       -- Requested no future calls
        'voicemail',         -- Left voicemail
        'not_reached'        -- Other reason not reached
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Donation source/entry method
DO $$ BEGIN
    CREATE TYPE donation_source AS ENUM (
        'quickbooks',        -- Imported from QuickBooks
        'online',            -- Online donation (PayPal, Venmo, etc.)
        'manual',            -- Manual staff entry
        'phone',             -- Phone pledge
        'event',             -- Event donation
        'mail'               -- Mailed check
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- DONORS TABLE - Donor profiles linked to contacts
-- ============================================================================
-- Tracks lifetime giving, donor status, and preferences
-- One donor per contact (1:1 relationship)
-- ============================================================================

CREATE TABLE IF NOT EXISTS donors (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Link to contact (1:1, unique)
    contact_id uuid NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,

    -- Donor Status
    status donor_status NOT NULL DEFAULT 'prospect',

    -- Lifetime Giving Metrics (denormalized for performance)
    lifetime_amount numeric(12,2) NOT NULL DEFAULT 0,
    lifetime_count integer NOT NULL DEFAULT 0,
    largest_gift numeric(12,2),
    first_gift_date timestamptz,
    last_gift_date timestamptz,
    average_gift numeric(12,2),

    -- Current Year Metrics
    ytd_amount numeric(12,2) NOT NULL DEFAULT 0,
    ytd_count integer NOT NULL DEFAULT 0,

    -- Communication Preferences
    acknowledgment_preference text DEFAULT 'email', -- email, mail, none
    solicitation_preference text DEFAULT 'all', -- all, major_only, none
    do_not_solicit boolean DEFAULT false,
    do_not_call boolean DEFAULT false,

    -- Recognition
    recognition_name text, -- Name for recognition (if different from contact)
    anonymous boolean DEFAULT false, -- Prefers anonymous recognition

    -- Major Donor Tracking
    major_donor_threshold numeric(12,2) DEFAULT 1000, -- Configurable per donor
    is_major_donor boolean GENERATED ALWAYS AS (lifetime_amount >= major_donor_threshold) STORED,

    -- External IDs
    quickbooks_customer_id text,

    -- Notes
    notes text,

    -- Audit Columns
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT donors_contact_unique UNIQUE (contact_id),
    CONSTRAINT donors_lifetime_positive CHECK (lifetime_amount >= 0),
    CONSTRAINT donors_ytd_positive CHECK (ytd_amount >= 0),
    CONSTRAINT donors_count_positive CHECK (lifetime_count >= 0 AND ytd_count >= 0)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_donors_contact_id ON donors(contact_id);
CREATE INDEX IF NOT EXISTS idx_donors_status ON donors(status);
CREATE INDEX IF NOT EXISTS idx_donors_last_gift_date ON donors(last_gift_date DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_donors_first_gift_date ON donors(first_gift_date);
CREATE INDEX IF NOT EXISTS idx_donors_lifetime_amount ON donors(lifetime_amount DESC);
CREATE INDEX IF NOT EXISTS idx_donors_is_major ON donors(is_major_donor) WHERE is_major_donor = true;
CREATE INDEX IF NOT EXISTS idx_donors_quickbooks_id ON donors(quickbooks_customer_id) WHERE quickbooks_customer_id IS NOT NULL;

-- Composite indexes for phone-a-thon queries
CREATE INDEX IF NOT EXISTS idx_donors_status_last_gift ON donors(status, last_gift_date DESC);
CREATE INDEX IF NOT EXISTS idx_donors_lapsed_query ON donors(status, last_gift_date)
    WHERE status IN ('lapsed', 'dormant');

COMMENT ON TABLE donors IS 'Donor profiles with lifetime giving metrics and preferences';
COMMENT ON COLUMN donors.contact_id IS 'Links to contacts table (1:1 relationship)';
COMMENT ON COLUMN donors.lifetime_amount IS 'Denormalized total of all donations';
COMMENT ON COLUMN donors.is_major_donor IS 'Computed: lifetime_amount >= major_donor_threshold';

-- ============================================================================
-- EXTEND TRANSACTIONS TABLE - Add donation-specific fields
-- ============================================================================
-- These fields extend the existing transactions table for donation tracking
-- ============================================================================

-- Add donation-specific columns to transactions table
DO $$ BEGIN
    -- Donation category (from QuickBooks "Full name" column)
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS donation_category text;

    -- Donation subcategory (second level of hierarchy)
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS donation_subcategory text;

    -- Source of the transaction
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS donation_source donation_source;

    -- QuickBooks specific fields
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS quickbooks_invoice_num text;
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS quickbooks_customer_name text;
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS quickbooks_class text;
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS quickbooks_memo text;

    -- Service/event date (when the service was rendered, vs transaction date)
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS service_date date;

    -- Campaign/appeal tracking
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS campaign text;
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS appeal text;

    -- Fund designation
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS fund text;

    -- Is this a donation? (vs purchase)
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_donation boolean DEFAULT false;

    -- Acknowledgment tracking
    ALTER TABLE transactions ADD COLUMN IF NOT EXISTS acknowledgment_id uuid;
EXCEPTION
    WHEN duplicate_column THEN NULL;
END $$;

-- Indexes for donation queries
CREATE INDEX IF NOT EXISTS idx_transactions_is_donation ON transactions(is_donation) WHERE is_donation = true;
CREATE INDEX IF NOT EXISTS idx_transactions_donation_category ON transactions(donation_category) WHERE donation_category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_campaign ON transactions(campaign) WHERE campaign IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_fund ON transactions(fund) WHERE fund IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_qb_invoice ON transactions(quickbooks_invoice_num) WHERE quickbooks_invoice_num IS NOT NULL;

-- Composite index for donation reporting by date range
CREATE INDEX IF NOT EXISTS idx_transactions_donation_date_range ON transactions(transaction_date, donation_category)
    WHERE is_donation = true;

-- Composite index for year-over-year queries
CREATE INDEX IF NOT EXISTS idx_transactions_donation_yearly ON transactions(
    date_trunc('year', transaction_date),
    donation_category
) WHERE is_donation = true;

COMMENT ON COLUMN transactions.donation_category IS 'Top-level category (e.g., DEVELOPMENT, STARHOUSE REVENUE)';
COMMENT ON COLUMN transactions.donation_subcategory IS 'Subcategory (e.g., General Donations, Fundraising)';
COMMENT ON COLUMN transactions.is_donation IS 'True if this is a donation (not a purchase)';

-- ============================================================================
-- DONATION_ACKNOWLEDGMENTS TABLE - Track acknowledgment status
-- ============================================================================
-- Tracks the status of thank-you letters/emails for donations
-- Implements the acknowledgment logic:
--   - Manual entry → pending_review → staff sends
--   - QB import <90 days → auto_queued → staff sends
--   - QB import >90 days → skipped_old
--   - Online → external (already acknowledged by payment processor)
-- ============================================================================

CREATE TABLE IF NOT EXISTS donation_acknowledgments (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Keys
    transaction_id uuid NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    donor_id uuid NOT NULL REFERENCES donors(id) ON DELETE CASCADE,

    -- Status
    status acknowledgment_status NOT NULL DEFAULT 'pending_review',

    -- Acknowledgment Details
    acknowledgment_type text, -- 'email', 'letter', 'phone', 'in_person'
    template_used text, -- Template name/ID used

    -- Dates
    queued_at timestamptz, -- When queued for sending
    sent_at timestamptz, -- When actually sent

    -- Staff Tracking
    reviewed_by uuid, -- Staff member who reviewed (links to staff_members)
    sent_by uuid, -- Staff member who sent

    -- Merge Fields (snapshot at time of acknowledgment)
    donor_name text,
    donation_amount numeric(12,2),
    donation_date date,
    fund_designation text,

    -- Content
    subject text, -- Email subject or letter header
    body_preview text, -- First 500 chars of acknowledgment

    -- Notes
    notes text,

    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT acknowledgments_transaction_unique UNIQUE (transaction_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_acknowledgments_transaction_id ON donation_acknowledgments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_acknowledgments_donor_id ON donation_acknowledgments(donor_id);
CREATE INDEX IF NOT EXISTS idx_acknowledgments_status ON donation_acknowledgments(status);
CREATE INDEX IF NOT EXISTS idx_acknowledgments_pending ON donation_acknowledgments(status, created_at)
    WHERE status IN ('pending_review', 'auto_queued');
CREATE INDEX IF NOT EXISTS idx_acknowledgments_sent_date ON donation_acknowledgments(sent_at DESC)
    WHERE sent_at IS NOT NULL;

COMMENT ON TABLE donation_acknowledgments IS 'Tracks acknowledgment status for each donation';
COMMENT ON COLUMN donation_acknowledgments.status IS 'Workflow status: pending_review → sent or skipped';

-- ============================================================================
-- DONOR_OUTREACH TABLE - Phone-a-thon and campaign tracking
-- ============================================================================
-- Tracks outreach attempts, pledges, and outcomes
-- Supports 10+ year historical queries for trend analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS donor_outreach (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Foreign Keys
    donor_id uuid NOT NULL REFERENCES donors(id) ON DELETE CASCADE,

    -- Campaign Information
    campaign_name text NOT NULL, -- e.g., "2024 Annual Appeal", "Fire Mitigation Drive"
    campaign_year integer NOT NULL,

    -- Outreach Details
    outreach_type text NOT NULL DEFAULT 'phone', -- phone, email, mail, in_person
    outreach_date timestamptz NOT NULL DEFAULT now(),

    -- Assignment
    assigned_to uuid, -- Staff member assigned (links to staff_members)
    caller_name text, -- For phone-a-thon volunteers

    -- Outcome
    outcome outreach_outcome,
    outcome_date timestamptz,

    -- Pledge Information
    pledge_amount numeric(12,2),
    pledge_fulfilled boolean DEFAULT false,
    pledge_fulfilled_date date,
    fulfillment_transaction_id uuid REFERENCES transactions(id) ON DELETE SET NULL,

    -- Contact Attempt Tracking
    attempt_number integer DEFAULT 1, -- 1st, 2nd, 3rd attempt
    callback_requested_date date,

    -- Notes
    notes text,

    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT outreach_pledge_positive CHECK (pledge_amount IS NULL OR pledge_amount >= 0),
    CONSTRAINT outreach_year_reasonable CHECK (campaign_year >= 2000 AND campaign_year <= 2100)
);

-- Indexes for historical queries (10+ years)
CREATE INDEX IF NOT EXISTS idx_outreach_donor_id ON donor_outreach(donor_id);
CREATE INDEX IF NOT EXISTS idx_outreach_campaign_name ON donor_outreach(campaign_name);
CREATE INDEX IF NOT EXISTS idx_outreach_campaign_year ON donor_outreach(campaign_year DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_outcome ON donor_outreach(outcome);
CREATE INDEX IF NOT EXISTS idx_outreach_date ON donor_outreach(outreach_date DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_outreach_campaign_outcomes ON donor_outreach(campaign_name, campaign_year, outcome);
CREATE INDEX IF NOT EXISTS idx_outreach_donor_history ON donor_outreach(donor_id, campaign_year DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_callbacks ON donor_outreach(callback_requested_date, outcome)
    WHERE outcome = 'callback';
CREATE INDEX IF NOT EXISTS idx_outreach_pledges ON donor_outreach(campaign_year, pledge_amount)
    WHERE pledge_amount IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_outreach_unfulfilled ON donor_outreach(pledge_fulfilled, campaign_year)
    WHERE pledge_amount IS NOT NULL AND pledge_fulfilled = false;

-- Partitioning note: For very large datasets, consider range partitioning by campaign_year
-- This would require converting to partitioned table structure

COMMENT ON TABLE donor_outreach IS 'Phone-a-thon and campaign outreach tracking with 10+ year history support';
COMMENT ON COLUMN donor_outreach.campaign_year IS 'Year for historical queries and partitioning';
COMMENT ON COLUMN donor_outreach.attempt_number IS 'Track multiple attempts per campaign';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Apply updated_at trigger to new tables
CREATE TRIGGER donors_set_updated_at
    BEFORE UPDATE ON donors
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER acknowledgments_set_updated_at
    BEFORE UPDATE ON donation_acknowledgments
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER outreach_set_updated_at
    BEFORE UPDATE ON donor_outreach
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ============================================================================
-- FUNCTIONS - Donor metrics update
-- ============================================================================

-- Function to recalculate donor metrics from transactions
CREATE OR REPLACE FUNCTION update_donor_metrics(p_donor_id uuid)
RETURNS void AS $$
DECLARE
    v_contact_id uuid;
BEGIN
    -- Get contact_id for this donor
    SELECT contact_id INTO v_contact_id FROM donors WHERE id = p_donor_id;

    IF v_contact_id IS NULL THEN
        RETURN;
    END IF;

    -- Update lifetime and YTD metrics
    UPDATE donors
    SET
        lifetime_amount = COALESCE((
            SELECT SUM(amount)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
        ), 0),
        lifetime_count = COALESCE((
            SELECT COUNT(*)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
        ), 0),
        largest_gift = (
            SELECT MAX(amount)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
        ),
        first_gift_date = (
            SELECT MIN(transaction_date)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
        ),
        last_gift_date = (
            SELECT MAX(transaction_date)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
        ),
        ytd_amount = COALESCE((
            SELECT SUM(amount)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
              AND date_trunc('year', transaction_date) = date_trunc('year', now())
        ), 0),
        ytd_count = COALESCE((
            SELECT COUNT(*)
            FROM transactions
            WHERE contact_id = v_contact_id
              AND is_donation = true
              AND status = 'completed'
              AND transaction_type != 'refund'
              AND date_trunc('year', transaction_date) = date_trunc('year', now())
        ), 0),
        updated_at = now()
    WHERE id = p_donor_id;

    -- Calculate average gift
    UPDATE donors
    SET average_gift = CASE
        WHEN lifetime_count > 0 THEN lifetime_amount / lifetime_count
        ELSE 0
    END
    WHERE id = p_donor_id;

    -- Update donor status based on giving history
    UPDATE donors
    SET status = CASE
        WHEN lifetime_count = 0 THEN 'prospect'
        WHEN lifetime_count = 1 THEN 'first_time'
        WHEN last_gift_date >= now() - interval '12 months' THEN 'active'
        WHEN last_gift_date >= now() - interval '24 months' THEN 'lapsed'
        ELSE 'dormant'
    END
    WHERE id = p_donor_id
      AND status NOT IN ('major', 'deceased'); -- Don't override these statuses

    -- Check for major donor status
    UPDATE donors
    SET status = 'major'
    WHERE id = p_donor_id
      AND is_major_donor = true
      AND status NOT IN ('deceased');
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_donor_metrics IS 'Recalculate donor lifetime/YTD metrics from transactions';

-- Function to auto-set acknowledgment status based on donation source
CREATE OR REPLACE FUNCTION set_acknowledgment_status()
RETURNS trigger AS $$
BEGIN
    -- Set status based on donation source and age
    IF NEW.donation_source = 'online' THEN
        -- Online donations already acknowledged by payment processor
        NEW.status := 'external';
    ELSIF NEW.donation_source = 'quickbooks' THEN
        -- QB imports: auto-queue if <90 days, skip if older
        IF NEW.donation_date >= CURRENT_DATE - interval '90 days' THEN
            NEW.status := 'auto_queued';
            NEW.queued_at := now();
        ELSE
            NEW.status := 'skipped_old';
        END IF;
    ELSE
        -- Manual entry: needs staff review
        NEW.status := 'pending_review';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to donation_acknowledgments
CREATE TRIGGER acknowledgment_auto_status
    BEFORE INSERT ON donation_acknowledgments
    FOR EACH ROW
    WHEN (NEW.status = 'pending_review') -- Only if not explicitly set
    EXECUTE FUNCTION set_acknowledgment_status();

-- ============================================================================
-- VIEWS - Donor reporting
-- ============================================================================

-- Donor summary view with contact information
CREATE OR REPLACE VIEW v_donor_summary AS
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
    d.lifetime_amount,
    d.lifetime_count,
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

COMMENT ON VIEW v_donor_summary IS 'Donor profiles with contact information for reporting';

-- Pending acknowledgments view
CREATE OR REPLACE VIEW v_pending_acknowledgments AS
SELECT
    a.id as acknowledgment_id,
    a.status,
    a.donor_name,
    a.donation_amount,
    a.donation_date,
    a.fund_designation,
    a.created_at as queued_at,
    c.email,
    c.first_name,
    c.last_name,
    c.address_line_1,
    c.city,
    c.state,
    c.postal_code,
    t.id as transaction_id,
    t.donation_source
FROM donation_acknowledgments a
JOIN transactions t ON a.transaction_id = t.id
JOIN donors d ON a.donor_id = d.id
JOIN contacts c ON d.contact_id = c.id
WHERE a.status IN ('pending_review', 'auto_queued')
ORDER BY a.created_at;

COMMENT ON VIEW v_pending_acknowledgments IS 'Acknowledgments pending staff action';

-- Phone-a-thon work list view
CREATE OR REPLACE VIEW v_phonathon_worklist AS
SELECT
    d.id as donor_id,
    c.first_name,
    c.last_name,
    c.phone,
    c.email,
    d.status as donor_status,
    d.lifetime_amount,
    d.last_gift_date,
    d.largest_gift,
    d.do_not_call,
    -- Last outreach info
    o.campaign_name as last_campaign,
    o.outcome as last_outcome,
    o.outreach_date as last_outreach_date,
    o.pledge_amount as last_pledge,
    -- Callback info
    CASE
        WHEN o.outcome = 'callback' THEN o.callback_requested_date
        ELSE NULL
    END as callback_date
FROM donors d
JOIN contacts c ON d.contact_id = c.id
LEFT JOIN LATERAL (
    SELECT *
    FROM donor_outreach
    WHERE donor_id = d.id
    ORDER BY outreach_date DESC
    LIMIT 1
) o ON true
WHERE d.do_not_call = false
  AND d.status NOT IN ('deceased')
ORDER BY d.last_gift_date DESC NULLS LAST;

COMMENT ON VIEW v_phonathon_worklist IS 'Phone-a-thon call list with donor history';

-- Campaign performance view
CREATE OR REPLACE VIEW v_campaign_performance AS
SELECT
    campaign_name,
    campaign_year,
    COUNT(*) as total_attempts,
    COUNT(*) FILTER (WHERE outcome = 'pledged') as pledged_count,
    COUNT(*) FILTER (WHERE outcome = 'declined') as declined_count,
    COUNT(*) FILTER (WHERE outcome = 'callback') as callback_count,
    COUNT(*) FILTER (WHERE outcome IN ('no_answer', 'voicemail', 'not_reached')) as not_reached_count,
    SUM(pledge_amount) as total_pledged,
    SUM(pledge_amount) FILTER (WHERE pledge_fulfilled = true) as total_fulfilled,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE outcome = 'pledged') / NULLIF(COUNT(*), 0),
        1
    ) as pledge_rate_pct
FROM donor_outreach
GROUP BY campaign_name, campaign_year
ORDER BY campaign_year DESC, campaign_name;

COMMENT ON VIEW v_campaign_performance IS 'Campaign metrics and conversion rates';

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all donor tables
ALTER TABLE donors ENABLE ROW LEVEL SECURITY;
ALTER TABLE donation_acknowledgments ENABLE ROW LEVEL SECURITY;
ALTER TABLE donor_outreach ENABLE ROW LEVEL SECURITY;

-- Service role full access (for imports and backend operations)
CREATE POLICY "Service role full access on donors"
    ON donors FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on acknowledgments"
    ON donation_acknowledgments FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on outreach"
    ON donor_outreach FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Staff access policies (all authenticated staff have full access)
-- Using auth.role() for proper Supabase Auth integration
CREATE POLICY "staff_all_donors"
    ON donors FOR ALL
    USING (auth.role() = 'authenticated');

-- Acknowledgments policies
CREATE POLICY "staff_all_acknowledgments"
    ON donation_acknowledgments FOR ALL
    USING (auth.role() = 'authenticated');

-- Outreach policies
CREATE POLICY "staff_all_outreach"
    ON donor_outreach FOR ALL
    USING (auth.role() = 'authenticated');

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

/*
-- Find all lapsed donors (no gift in 12-24 months)
SELECT * FROM v_donor_summary
WHERE donor_status = 'lapsed'
ORDER BY last_gift_date DESC;

-- Phone-a-thon worklist for specific campaign
SELECT * FROM v_phonathon_worklist
WHERE donor_status IN ('active', 'lapsed', 'major')
  AND phone IS NOT NULL;

-- 10-year giving history for a donor
SELECT
    date_trunc('year', transaction_date) as year,
    COUNT(*) as gift_count,
    SUM(amount) as total
FROM transactions t
JOIN donors d ON t.contact_id = d.contact_id
WHERE d.id = 'donor-uuid-here'
  AND t.is_donation = true
  AND t.status = 'completed'
GROUP BY date_trunc('year', transaction_date)
ORDER BY year DESC;

-- Campaign year-over-year comparison
SELECT * FROM v_campaign_performance
WHERE campaign_name = 'Annual Appeal'
ORDER BY campaign_year DESC
LIMIT 10;

-- Pending acknowledgments to send
SELECT * FROM v_pending_acknowledgments
ORDER BY donation_date DESC;

-- Update donor metrics after import
SELECT update_donor_metrics(id) FROM donors;
*/

-- ============================================================================
-- END OF DONOR MODULE SCHEMA
-- ============================================================================
