-- ============================================
-- CONTACT MODULE - VIEWS
-- StarHouse CRM Database
-- ============================================
-- Purpose: Convenience views for common contact queries
-- Created: 2025-11-02
-- Migration: 20251102000002
-- ============================================

-- ============================================
-- VIEW: v_contact_roles_quick
-- ============================================
-- Purpose: Fast array aggregation of active roles per contact
-- Use Case: Filter contacts by role (show me all 'members' or 'donors')
-- Performance: Indexed on contact_roles(contact_id, role) WHERE status = 'active'

CREATE OR REPLACE VIEW v_contact_roles_quick AS
SELECT
    contact_id,

    -- Array of all active role names
    array_agg(DISTINCT role ORDER BY role) FILTER (WHERE status = 'active') AS active_roles,

    -- Boolean flags for quick filtering
    bool_or(role = 'member' AND status = 'active') AS is_member,
    bool_or(role = 'donor' AND status = 'active') AS is_donor,
    bool_or(role = 'volunteer' AND status = 'active') AS is_volunteer,
    bool_or(role = 'attendee' AND status = 'active') AS is_attendee,
    bool_or(role = 'subscriber' AND status = 'active') AS is_subscriber,
    bool_or(role = 'staff' AND status = 'active') AS is_staff,
    bool_or(role = 'board' AND status = 'active') AS is_board,
    bool_or(role = 'partner' AND status = 'active') AS is_partner,

    -- Count of active roles
    count(*) FILTER (WHERE status = 'active') AS active_role_count,

    -- Latest role activity
    max(started_at) AS latest_role_started_at,
    max(updated_at) AS latest_role_updated_at

FROM contact_roles
GROUP BY contact_id;

-- Index for fast joins
CREATE INDEX idx_v_contact_roles_quick_contact_id ON contact_roles(contact_id);

COMMENT ON VIEW v_contact_roles_quick IS
'Fast role aggregation per contact. Use for filtering by role (is_member, is_donor, etc).';

-- ============================================
-- VIEW: v_contact_outreach_email
-- ============================================
-- Purpose: Deterministic outreach email selection with fallback logic
-- Business Rule: NEVER return NULL - every contact must have an outreach email
-- Fallback Order:
--   1. Email marked is_outreach=true (preferred)
--   2. Email marked is_primary=true (fallback)
--   3. First verified email (emergency fallback)
--   4. Any email (last resort)

CREATE OR REPLACE VIEW v_contact_outreach_email AS
SELECT
    c.id AS contact_id,

    -- Outreach email (guaranteed non-NULL)
    COALESCE(
        -- Preferred: Explicit outreach email
        (SELECT ce.email
         FROM contact_emails ce
         WHERE ce.contact_id = c.id AND ce.is_outreach = true
         LIMIT 1),

        -- Fallback 1: Primary email
        (SELECT ce.email
         FROM contact_emails ce
         WHERE ce.contact_id = c.id AND ce.is_primary = true
         LIMIT 1),

        -- Fallback 2: First verified email
        (SELECT ce.email
         FROM contact_emails ce
         WHERE ce.contact_id = c.id AND ce.verified = true
         ORDER BY ce.created_at ASC
         LIMIT 1),

        -- Fallback 3: Any email (last resort)
        (SELECT ce.email
         FROM contact_emails ce
         WHERE ce.contact_id = c.id
         ORDER BY ce.created_at ASC
         LIMIT 1),

        -- Ultimate fallback: Legacy contacts.email column (during migration)
        c.email
    ) AS outreach_email,

    -- Metadata about which fallback was used
    CASE
        WHEN EXISTS (SELECT 1 FROM contact_emails ce WHERE ce.contact_id = c.id AND ce.is_outreach = true)
            THEN 'explicit_outreach'
        WHEN EXISTS (SELECT 1 FROM contact_emails ce WHERE ce.contact_id = c.id AND ce.is_primary = true)
            THEN 'primary_fallback'
        WHEN EXISTS (SELECT 1 FROM contact_emails ce WHERE ce.contact_id = c.id AND ce.verified = true)
            THEN 'verified_fallback'
        WHEN EXISTS (SELECT 1 FROM contact_emails ce WHERE ce.contact_id = c.id)
            THEN 'any_email_fallback'
        ELSE 'legacy_contacts_table'
    END AS outreach_source,

    -- Deliverability status of the outreach email
    (SELECT ce.deliverable
     FROM contact_emails ce
     WHERE ce.contact_id = c.id
       AND ce.email = COALESCE(
           (SELECT ce2.email FROM contact_emails ce2 WHERE ce2.contact_id = c.id AND ce2.is_outreach = true LIMIT 1),
           (SELECT ce2.email FROM contact_emails ce2 WHERE ce2.contact_id = c.id AND ce2.is_primary = true LIMIT 1),
           (SELECT ce2.email FROM contact_emails ce2 WHERE ce2.contact_id = c.id AND ce2.verified = true ORDER BY ce2.created_at ASC LIMIT 1),
           (SELECT ce2.email FROM contact_emails ce2 WHERE ce2.contact_id = c.id ORDER BY ce2.created_at ASC LIMIT 1)
       )
     LIMIT 1
    ) AS is_deliverable,

    -- Warning flags
    (SELECT ce.deliverable = false
     FROM contact_emails ce
     WHERE ce.contact_id = c.id AND ce.is_outreach = true
     LIMIT 1
    ) AS outreach_email_bounced,

    -- Count of total emails for this contact
    (SELECT count(*) FROM contact_emails ce WHERE ce.contact_id = c.id) AS total_email_count

FROM contacts c;

COMMENT ON VIEW v_contact_outreach_email IS
'Deterministic outreach email selection with fallback logic. Guaranteed non-NULL for email campaigns.';

-- ============================================
-- VIEW: v_contact_detail_enriched
-- ============================================
-- Purpose: Complete contact profile with all related data
-- Use Case: Contact detail page, full profile export
-- Performance: Use for single contact lookups, not list queries

CREATE OR REPLACE VIEW v_contact_detail_enriched AS
SELECT
    c.*,

    -- Primary contact info (from contact_emails)
    (SELECT ce.email
     FROM contact_emails ce
     WHERE ce.contact_id = c.id AND ce.is_primary = true
     LIMIT 1
    ) AS primary_email,

    -- Outreach email (from v_contact_outreach_email)
    voe.outreach_email,
    voe.outreach_source,
    voe.is_deliverable AS outreach_deliverable,

    -- All emails as JSON array
    (SELECT json_agg(json_build_object(
        'email', ce.email,
        'type', ce.email_type,
        'is_primary', ce.is_primary,
        'is_outreach', ce.is_outreach,
        'source', ce.source,
        'verified', ce.verified,
        'deliverable', ce.deliverable
    ) ORDER BY ce.is_primary DESC, ce.is_outreach DESC, ce.created_at ASC)
     FROM contact_emails ce
     WHERE ce.contact_id = c.id
    ) AS all_emails,

    -- External identities as JSON
    (SELECT json_agg(json_build_object(
        'system', ei.system,
        'external_id', ei.external_id,
        'verified', ei.verified,
        'last_synced_at', ei.last_synced_at,
        'sync_status', ei.sync_status
    ))
     FROM external_identities ei
     WHERE ei.contact_id = c.id
    ) AS external_identities,

    -- Active roles
    vcr.active_roles,
    vcr.is_member,
    vcr.is_donor,
    vcr.is_volunteer,
    vcr.is_attendee,
    vcr.is_subscriber,
    vcr.active_role_count,

    -- Contact statistics
    (SELECT count(*) FROM contact_notes cn WHERE cn.contact_id = c.id) AS note_count,
    (SELECT count(*) FROM contact_tags ct WHERE ct.contact_id = c.id) AS tag_count,
    (SELECT count(*) FROM transactions t WHERE t.contact_id = c.id) AS transaction_count_actual,
    (SELECT count(*) FROM subscriptions s WHERE s.contact_id = c.id) AS subscription_count,
    (SELECT count(*) FROM webhook_events we WHERE we.contact_id = c.id) AS webhook_event_count,

    -- Latest activity timestamp
    GREATEST(
        c.updated_at,
        COALESCE((SELECT max(cn.created_at) FROM contact_notes cn WHERE cn.contact_id = c.id), '1970-01-01'::timestamptz),
        COALESCE((SELECT max(t.transaction_date) FROM transactions t WHERE t.contact_id = c.id), '1970-01-01'::timestamptz),
        COALESCE((SELECT max(we.received_at) FROM webhook_events we WHERE we.contact_id = c.id), '1970-01-01'::timestamptz),
        COALESCE(vcr.latest_role_updated_at, '1970-01-01'::timestamptz)
    ) AS last_activity_at

FROM contacts c
LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id;

COMMENT ON VIEW v_contact_detail_enriched IS
'Complete contact profile with emails, identities, roles, and stats. Use for detail views only.';

-- ============================================
-- VIEW: v_contact_list_optimized
-- ============================================
-- Purpose: Optimized view for contact list/table displays
-- Use Case: Contact list page with search/filter/sort
-- Performance: Minimal joins, indexed columns only

CREATE OR REPLACE VIEW v_contact_list_optimized AS
SELECT
    c.id,
    c.first_name,
    c.last_name,
    c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,

    -- Email (from v_contact_outreach_email for consistency)
    voe.outreach_email AS email,
    voe.outreach_source,

    -- Quick stats (from contacts table - pre-computed)
    c.total_spent,
    c.transaction_count,
    c.has_active_subscription,
    c.last_transaction_date,

    -- Role flags (from v_contact_roles_quick)
    vcr.is_member,
    vcr.is_donor,
    vcr.is_volunteer,
    vcr.active_roles,

    -- Membership info
    c.membership_level,
    c.membership_tier,

    -- Activity
    c.email_subscribed,
    c.updated_at,
    c.created_at

FROM contacts c
LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id;

-- Index hint for common sorts
CREATE INDEX idx_contacts_full_name_sort ON contacts((first_name || ' ' || COALESCE(last_name, '')));

COMMENT ON VIEW v_contact_list_optimized IS
'Optimized contact list view. Use for table displays with pagination. Fast query performance.';

-- ============================================
-- GRANTS
-- ============================================
GRANT SELECT ON v_contact_roles_quick TO authenticated, anon;
GRANT SELECT ON v_contact_outreach_email TO authenticated, anon;
GRANT SELECT ON v_contact_detail_enriched TO authenticated, anon;
GRANT SELECT ON v_contact_list_optimized TO authenticated, anon;

-- ============================================
-- ROLLBACK INSTRUCTIONS
-- ============================================
-- To rollback this migration, run:
/*
DROP VIEW IF EXISTS v_contact_list_optimized CASCADE;
DROP VIEW IF EXISTS v_contact_detail_enriched CASCADE;
DROP VIEW IF EXISTS v_contact_outreach_email CASCADE;
DROP VIEW IF EXISTS v_contact_roles_quick CASCADE;
DROP INDEX IF EXISTS idx_contacts_full_name_sort;
DROP INDEX IF EXISTS idx_v_contact_roles_quick_contact_id;
*/
