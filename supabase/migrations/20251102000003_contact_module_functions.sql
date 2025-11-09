-- ============================================
-- CONTACT MODULE - FUNCTIONS
-- StarHouse CRM Database
-- ============================================
-- Purpose: High-performance functions for contact activity and search
-- Created: 2025-11-02
-- Migration: 20251102000003
-- ============================================

-- ============================================
-- FUNCTION: get_contact_activity
-- ============================================
-- Purpose: Unified activity timeline for a contact
-- Sources: webhook_events, transactions, contact_tags, contact_notes, contact_roles
-- Performance: Uses function instead of view for better query planning
-- Target: <300ms for 50 records with proper indexes

CREATE OR REPLACE FUNCTION get_contact_activity(
    p_contact_id UUID,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    activity_id UUID,
    activity_type TEXT,
    activity_name TEXT,
    activity_date TIMESTAMPTZ,
    activity_status TEXT,
    details TEXT,
    amount NUMERIC(10,2),
    metadata JSONB,
    source_table TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM (
        -- Webhook events
        SELECT
            we.id AS activity_id,
            'webhook'::TEXT AS activity_type,
            we.source || '.' || we.event_type AS activity_name,
            we.received_at AS activity_date,
            we.status AS activity_status,
            COALESCE(we.error_message, 'Webhook received') AS details,
            NULL::NUMERIC(10,2) AS amount,
            jsonb_build_object(
                'source', we.source,
                'event_type', we.event_type,
                'webhook_id', we.id
            ) AS metadata,
            'webhook_events'::TEXT AS source_table
        FROM webhook_events we
        WHERE we.contact_id = p_contact_id

        UNION ALL

        -- Transactions
        SELECT
            t.id AS activity_id,
            'transaction'::TEXT AS activity_type,
            t.transaction_type AS activity_name,
            t.transaction_date AS activity_date,
            t.status AS activity_status,
            'Order #' || COALESCE(t.order_number, t.external_order_id, 'N/A') AS details,
            t.amount,
            jsonb_build_object(
                'transaction_type', t.transaction_type,
                'payment_method', t.payment_method,
                'source_system', t.source_system
            ) AS metadata,
            'transactions'::TEXT AS source_table
        FROM transactions t
        WHERE t.contact_id = p_contact_id

        UNION ALL

        -- Tags added
        SELECT
            ct.id AS activity_id,
            'tag'::TEXT AS activity_type,
            'tag.added' AS activity_name,
            ct.created_at AS activity_date,
            'added'::TEXT AS activity_status,
            'Tag: ' || t.name AS details,
            NULL::NUMERIC(10,2) AS amount,
            jsonb_build_object(
                'tag_id', t.id,
                'tag_name', t.name,
                'tag_type', t.tag_type
            ) AS metadata,
            'contact_tags'::TEXT AS source_table
        FROM contact_tags ct
        JOIN tags t ON ct.tag_id = t.id
        WHERE ct.contact_id = p_contact_id

        UNION ALL

        -- Contact notes
        SELECT
            cn.id AS activity_id,
            'note'::TEXT AS activity_type,
            'note.' || cn.note_type AS activity_name,
            cn.created_at AS activity_date,
            'created'::TEXT AS activity_status,
            COALESCE(cn.subject, left(cn.content, 100)) AS details,
            NULL::NUMERIC(10,2) AS amount,
            jsonb_build_object(
                'note_type', cn.note_type,
                'author_name', cn.author_name,
                'is_pinned', cn.is_pinned,
                'full_content', cn.content
            ) AS metadata,
            'contact_notes'::TEXT AS source_table
        FROM contact_notes cn
        WHERE cn.contact_id = p_contact_id
          AND (cn.is_private = false OR cn.author_user_id = auth.uid())

        UNION ALL

        -- Role changes
        SELECT
            cr.id AS activity_id,
            'role'::TEXT AS activity_type,
            'role.' || cr.role || '.' || cr.status AS activity_name,
            CASE
                WHEN cr.status IN ('inactive', 'expired') AND cr.ended_at IS NOT NULL
                    THEN cr.ended_at
                ELSE cr.started_at
            END AS activity_date,
            cr.status AS activity_status,
            'Role: ' || initcap(cr.role) || ' (' || initcap(cr.status) || ')' AS details,
            NULL::NUMERIC(10,2) AS amount,
            jsonb_build_object(
                'role', cr.role,
                'status', cr.status,
                'started_at', cr.started_at,
                'ended_at', cr.ended_at,
                'source', cr.source
            ) AS metadata,
            'contact_roles'::TEXT AS source_table
        FROM contact_roles cr
        WHERE cr.contact_id = p_contact_id

        UNION ALL

        -- Subscriptions (lifecycle events)
        SELECT
            s.id AS activity_id,
            'subscription'::TEXT AS activity_type,
            'subscription.' || s.status AS activity_name,
            COALESCE(s.start_date, s.created_at) AS activity_date,
            s.status AS activity_status,
            'Subscription: $' || COALESCE(s.amount::TEXT, 'N/A') || ' ' || COALESCE(s.billing_cycle, '') AS details,
            s.amount,
            jsonb_build_object(
                'subscription_id', s.id,
                'status', s.status,
                'billing_cycle', s.billing_cycle,
                'next_billing_date', s.next_billing_date,
                'payment_processor', s.payment_processor
            ) AS metadata,
            'subscriptions'::TEXT AS source_table
        FROM subscriptions s
        WHERE s.contact_id = p_contact_id

    ) AS unified_activity
    ORDER BY activity_date DESC NULLS LAST
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_contact_activity(UUID, INTEGER, INTEGER) IS
'Returns unified activity timeline for a contact. Combines webhooks, transactions, tags, notes, roles, and subscriptions.';

-- Performance indexes (if not already exist)
CREATE INDEX IF NOT EXISTS idx_webhook_events_contact_timeline
    ON webhook_events(contact_id, received_at DESC)
    WHERE contact_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_transactions_contact_timeline
    ON transactions(contact_id, transaction_date DESC);

CREATE INDEX IF NOT EXISTS idx_contact_tags_timeline
    ON contact_tags(contact_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_subscriptions_contact_timeline
    ON subscriptions(contact_id, start_date DESC);

-- ============================================
-- FUNCTION: search_contacts
-- ============================================
-- Purpose: Fast full-text and fuzzy search across contacts
-- Search Fields: name, email, phone, external IDs
-- Performance: Uses trigram indexes for fuzzy matching
-- Target: <200ms for search results with pg_trgm

CREATE OR REPLACE FUNCTION search_contacts(
    p_query TEXT,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    contact_id UUID,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    total_spent NUMERIC(10,2),
    is_member BOOLEAN,
    is_donor BOOLEAN,
    match_score REAL,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH search_matches AS (
        -- Match 1: Email exact match (highest priority)
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            1.0::REAL AS match_score,
            'email_exact'::TEXT AS match_type
        FROM contacts c
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE LOWER(c.email) = LOWER(p_query)
           OR EXISTS (
               SELECT 1 FROM contact_emails ce
               WHERE ce.contact_id = c.id
                 AND LOWER(ce.email) = LOWER(p_query)
           )

        UNION

        -- Match 2: Email similarity (trigram fuzzy match)
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.9::REAL * similarity(c.email::TEXT, p_query) AS match_score,
            'email_fuzzy'::TEXT AS match_type
        FROM contacts c
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE c.email % p_query  -- Trigram similarity operator
          AND similarity(c.email::TEXT, p_query) > 0.3
          AND LOWER(c.email::TEXT) != LOWER(p_query)  -- Exclude exact matches already found

        UNION

        -- Match 3: Contact_emails table fuzzy match
        SELECT DISTINCT ON (c.id)
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.85::REAL * similarity(ce.email::TEXT, p_query) AS match_score,
            'contact_email_fuzzy'::TEXT AS match_type
        FROM contacts c
        JOIN contact_emails ce ON ce.contact_id = c.id
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE ce.email % p_query
          AND similarity(ce.email::TEXT, p_query) > 0.3
          AND LOWER(ce.email::TEXT) != LOWER(p_query)

        UNION

        -- Match 4: Name exact match (case-insensitive)
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.95::REAL AS match_score,
            'name_exact'::TEXT AS match_type
        FROM contacts c
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE LOWER(c.first_name || ' ' || COALESCE(c.last_name, '')) = LOWER(p_query)
           OR LOWER(c.first_name) = LOWER(p_query)
           OR LOWER(c.last_name) = LOWER(p_query)

        UNION

        -- Match 5: Name fuzzy match (trigram)
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.8::REAL * GREATEST(
                similarity(c.first_name, p_query),
                similarity(COALESCE(c.last_name, ''), p_query),
                similarity(c.first_name || ' ' || COALESCE(c.last_name, ''), p_query)
            ) AS match_score,
            'name_fuzzy'::TEXT AS match_type
        FROM contacts c
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE (
                c.first_name % p_query
                OR COALESCE(c.last_name, '') % p_query
                OR (c.first_name || ' ' || COALESCE(c.last_name, '')) % p_query
            )
          AND GREATEST(
                similarity(c.first_name, p_query),
                similarity(COALESCE(c.last_name, ''), p_query),
                similarity(c.first_name || ' ' || COALESCE(c.last_name, ''), p_query)
            ) > 0.3

        UNION

        -- Match 6: Phone number match (strip formatting)
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.9::REAL AS match_score,
            'phone'::TEXT AS match_type
        FROM contacts c
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE regexp_replace(COALESCE(c.phone, ''), '[^0-9]', '', 'g') LIKE '%' || regexp_replace(p_query, '[^0-9]', '', 'g') || '%'
          AND length(regexp_replace(p_query, '[^0-9]', '', 'g')) >= 7  -- At least 7 digits

        UNION

        -- Match 7: External ID match
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.85::REAL AS match_score,
            'external_id.' || ei.system AS match_type
        FROM contacts c
        JOIN external_identities ei ON ei.contact_id = c.id
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE ei.external_id ILIKE '%' || p_query || '%'

        UNION

        -- Match 8: Legacy external ID columns (during migration)
        SELECT
            c.id AS contact_id,
            c.first_name || ' ' || COALESCE(c.last_name, '') AS full_name,
            voe.outreach_email AS email,
            c.phone AS phone,
            c.total_spent,
            vcr.is_member,
            vcr.is_donor,
            0.8::REAL AS match_score,
            'legacy_id'::TEXT AS match_type
        FROM contacts c
        LEFT JOIN v_contact_outreach_email voe ON c.id = voe.contact_id
        LEFT JOIN v_contact_roles_quick vcr ON c.id = vcr.contact_id
        WHERE c.kajabi_id ILIKE '%' || p_query || '%'
           OR c.ticket_tailor_id ILIKE '%' || p_query || '%'
           OR c.zoho_id ILIKE '%' || p_query || '%'
           OR c.quickbooks_id ILIKE '%' || p_query || '%'
           OR c.mailchimp_id ILIKE '%' || p_query || '%'
           OR c.paypal_payer_id ILIKE '%' || p_query || '%'
    )
    SELECT DISTINCT ON (sm.contact_id)
        sm.contact_id,
        sm.full_name,
        sm.email,
        sm.phone,
        sm.total_spent,
        sm.is_member,
        sm.is_donor,
        sm.match_score,
        sm.match_type
    FROM search_matches sm
    ORDER BY sm.contact_id, sm.match_score DESC, sm.match_type
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION search_contacts(TEXT, INTEGER, INTEGER) IS
'Full-text and fuzzy search across contacts. Returns ranked results with match type and score.';

-- Performance indexes for search
CREATE INDEX IF NOT EXISTS idx_contacts_first_name_trgm
    ON contacts USING gin(first_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_contacts_last_name_trgm
    ON contacts USING gin(last_name gin_trgm_ops)
    WHERE last_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_contacts_full_name_trgm
    ON contacts USING gin((first_name || ' ' || COALESCE(last_name, '')) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_contacts_email_trgm
    ON contacts USING gin(email gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_contacts_phone_digits
    ON contacts(regexp_replace(phone, '[^0-9]', '', 'g'))
    WHERE phone IS NOT NULL;

-- ============================================
-- GRANTS
-- ============================================
GRANT EXECUTE ON FUNCTION get_contact_activity(UUID, INTEGER, INTEGER) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION search_contacts(TEXT, INTEGER, INTEGER) TO authenticated, anon;

-- ============================================
-- ROLLBACK INSTRUCTIONS
-- ============================================
-- To rollback this migration, run:
/*
DROP FUNCTION IF EXISTS search_contacts(TEXT, INTEGER, INTEGER);
DROP FUNCTION IF EXISTS get_contact_activity(UUID, INTEGER, INTEGER);

DROP INDEX IF EXISTS idx_contacts_phone_digits;
DROP INDEX IF EXISTS idx_contacts_email_trgm;
DROP INDEX IF EXISTS idx_contacts_full_name_trgm;
DROP INDEX IF EXISTS idx_contacts_last_name_trgm;
DROP INDEX IF EXISTS idx_contacts_first_name_trgm;
DROP INDEX IF EXISTS idx_subscriptions_contact_timeline;
DROP INDEX IF EXISTS idx_contact_tags_timeline;
DROP INDEX IF EXISTS idx_transactions_contact_timeline;
DROP INDEX IF EXISTS idx_webhook_events_contact_timeline;
*/
