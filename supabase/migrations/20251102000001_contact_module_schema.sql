-- ============================================
-- CONTACT MODULE - SCHEMA
-- StarHouse CRM Database
-- ============================================
-- Purpose: Multi-email support, external identity reconciliation,
--          role-based classification, and staff notes
-- Created: 2025-11-02
-- Migration: 20251102000001
-- ============================================

-- ============================================
-- EXTENSIONS
-- ============================================
-- Enable trigram indexing for fast fuzzy search on names/emails
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function: set_updated_by()
-- Purpose: Automatically track which user made changes to a record
-- Usage: Trigger function for audit columns
CREATE OR REPLACE FUNCTION set_updated_by()
RETURNS TRIGGER AS $$
BEGIN
    -- Try to get current user from Supabase Auth context
    -- Falls back to 'system' if no auth context exists
    NEW.updated_by = COALESCE(
        auth.uid(),
        NEW.updated_by,
        '00000000-0000-0000-0000-000000000000'::uuid
    );
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION set_updated_by() IS
'Trigger function: Sets updated_by to current auth user and updated_at to NOW()';

-- ============================================
-- TABLE: contact_emails
-- ============================================
-- Purpose: Support multiple email addresses per contact with source tracking
-- Business Rules:
--   - Every contact MUST have exactly 1 primary email (is_primary=true)
--   - Every contact MUST have exactly 1 outreach email (is_outreach=true)
--   - Primary and outreach can be the same email or different
--   - Track source system, verification status, and deliverability

CREATE TABLE contact_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

    -- Email data
    email CITEXT NOT NULL,
    email_type TEXT CHECK (email_type IN ('personal', 'work', 'other')) DEFAULT 'personal',

    -- Flags
    is_primary BOOLEAN NOT NULL DEFAULT false,
    is_outreach BOOLEAN NOT NULL DEFAULT false,

    -- Source tracking
    source TEXT NOT NULL CHECK (source IN (
        'kajabi', 'paypal', 'ticket_tailor', 'zoho',
        'quickbooks', 'mailchimp', 'manual', 'import'
    )),

    -- Verification & quality
    verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMPTZ,
    deliverable BOOLEAN,  -- NULL = unknown, true = deliverable, false = bounced
    last_bounce_at TIMESTAMPTZ,
    bounce_reason TEXT,

    -- Audit fields
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Data quality constraints
    CONSTRAINT valid_email_format CHECK (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);

-- Indexes for performance
CREATE INDEX idx_contact_emails_contact_id ON contact_emails(contact_id);
CREATE INDEX idx_contact_emails_email ON contact_emails(email);
CREATE INDEX idx_contact_emails_primary ON contact_emails(contact_id) WHERE is_primary = true;
CREATE INDEX idx_contact_emails_outreach ON contact_emails(contact_id) WHERE is_outreach = true;
CREATE INDEX idx_contact_emails_source ON contact_emails(source);
CREATE INDEX idx_contact_emails_deliverable ON contact_emails(deliverable) WHERE deliverable IS NOT NULL;

-- Trigram index for fuzzy email search (supports LIKE, ILIKE, similarity())
CREATE INDEX idx_contact_emails_email_trgm ON contact_emails USING gin(email gin_trgm_ops);

-- Business rule: Exactly one primary email per contact
CREATE UNIQUE INDEX ux_contact_emails_one_primary
    ON contact_emails(contact_id)
    WHERE is_primary = true;

-- Business rule: Exactly one outreach email per contact
CREATE UNIQUE INDEX ux_contact_emails_one_outreach
    ON contact_emails(contact_id)
    WHERE is_outreach = true;

-- Prevent duplicate emails for same contact
CREATE UNIQUE INDEX ux_contact_emails_unique_per_contact
    ON contact_emails(contact_id, email);

-- Triggers
CREATE TRIGGER contact_emails_set_updated_by
    BEFORE UPDATE ON contact_emails
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_by();

-- Row Level Security (RLS)
ALTER TABLE contact_emails ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read all contact emails
CREATE POLICY "contact_emails_select_policy"
    ON contact_emails FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Authenticated users can insert contact emails
CREATE POLICY "contact_emails_insert_policy"
    ON contact_emails FOR INSERT
    TO authenticated
    WITH CHECK (created_by = auth.uid());

-- Policy: Authenticated users can update contact emails
CREATE POLICY "contact_emails_update_policy"
    ON contact_emails FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (updated_by = auth.uid());

-- Policy: Only admins can delete contact emails (via service_role)
-- No DELETE policy for authenticated = only service_role can delete

COMMENT ON TABLE contact_emails IS
'Multi-email support for contacts. Every contact must have exactly 1 primary and 1 outreach email.';

-- ============================================
-- TABLE: external_identities
-- ============================================
-- Purpose: Normalize cross-system ID tracking (replaces kajabi_id, zoho_id, etc columns)
-- Benefits:
--   - Clean contacts table
--   - Easy to add new integrations
--   - Track verification and sync status

CREATE TABLE external_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

    -- Identity data
    system TEXT NOT NULL CHECK (system IN (
        'kajabi', 'kajabi_member', 'paypal', 'ticket_tailor',
        'zoho', 'quickbooks', 'mailchimp', 'stripe', 'other'
    )),
    external_id TEXT NOT NULL,

    -- Metadata
    verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    sync_status TEXT CHECK (sync_status IN ('active', 'stale', 'error', 'disabled')),
    metadata JSONB,  -- Store system-specific data

    -- Audit fields
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_external_identities_contact_id ON external_identities(contact_id);
CREATE INDEX idx_external_identities_system ON external_identities(system);
CREATE INDEX idx_external_identities_external_id ON external_identities(external_id);
CREATE INDEX idx_external_identities_lookup ON external_identities(system, external_id);

-- Prevent duplicate external IDs per system
CREATE UNIQUE INDEX ux_external_identities_system_id
    ON external_identities(system, external_id);

-- Prevent duplicate system per contact (one Kajabi ID per contact, one PayPal ID, etc)
CREATE UNIQUE INDEX ux_external_identities_contact_system
    ON external_identities(contact_id, system);

-- Triggers
CREATE TRIGGER external_identities_set_updated_by
    BEFORE UPDATE ON external_identities
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_by();

-- Row Level Security
ALTER TABLE external_identities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "external_identities_select_policy"
    ON external_identities FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "external_identities_insert_policy"
    ON external_identities FOR INSERT
    TO authenticated
    WITH CHECK (created_by = auth.uid());

CREATE POLICY "external_identities_update_policy"
    ON external_identities FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (updated_by = auth.uid());

COMMENT ON TABLE external_identities IS
'Cross-system identity reconciliation. Maps contacts to external system IDs (Kajabi, PayPal, etc).';

-- ============================================
-- TABLE: contact_roles
-- ============================================
-- Purpose: Track contact roles over time (member, donor, volunteer, attendee, subscriber)
-- Benefits:
--   - Historical tracking (when did they become a donor?)
--   - Multiple simultaneous roles (can be both member AND volunteer)
--   - Time-bound roles with start/end dates

CREATE TABLE contact_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

    -- Role data
    role TEXT NOT NULL CHECK (role IN (
        'member', 'donor', 'volunteer', 'attendee',
        'subscriber', 'staff', 'board', 'partner'
    )),
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'expired')) DEFAULT 'active',

    -- Time bounds
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,

    -- Metadata
    source TEXT,  -- How did they get this role? ('subscription', 'donation', 'event', 'manual')
    notes TEXT,
    metadata JSONB,  -- Role-specific data (donation amount, event name, etc)

    -- Audit fields
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Business rule: ended_at must be after started_at
    CONSTRAINT valid_date_range CHECK (ended_at IS NULL OR ended_at >= started_at)
);

-- Indexes
CREATE INDEX idx_contact_roles_contact_id ON contact_roles(contact_id);
CREATE INDEX idx_contact_roles_role ON contact_roles(role);
CREATE INDEX idx_contact_roles_status ON contact_roles(status);
CREATE INDEX idx_contact_roles_active ON contact_roles(contact_id, role) WHERE status = 'active';
CREATE INDEX idx_contact_roles_started_at ON contact_roles(started_at DESC);

-- Allow multiple roles per contact, but prevent duplicate active roles
CREATE UNIQUE INDEX ux_contact_roles_unique_active
    ON contact_roles(contact_id, role)
    WHERE status = 'active';

-- Triggers
CREATE TRIGGER contact_roles_set_updated_by
    BEFORE UPDATE ON contact_roles
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_by();

-- Trigger: Auto-set ended_at when status changes from active to inactive/expired
CREATE OR REPLACE FUNCTION set_role_ended_at()
RETURNS TRIGGER AS $$
BEGIN
    -- If status changed from active to inactive/expired, set ended_at
    IF OLD.status = 'active' AND NEW.status IN ('inactive', 'expired') AND NEW.ended_at IS NULL THEN
        NEW.ended_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contact_roles_set_ended_at
    BEFORE UPDATE ON contact_roles
    FOR EACH ROW
    EXECUTE FUNCTION set_role_ended_at();

-- Row Level Security
ALTER TABLE contact_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "contact_roles_select_policy"
    ON contact_roles FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "contact_roles_insert_policy"
    ON contact_roles FOR INSERT
    TO authenticated
    WITH CHECK (created_by = auth.uid());

CREATE POLICY "contact_roles_update_policy"
    ON contact_roles FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (updated_by = auth.uid());

COMMENT ON TABLE contact_roles IS
'Time-bound role tracking for contacts. Supports multiple simultaneous roles with historical data.';

-- ============================================
-- TABLE: contact_notes
-- ============================================
-- Purpose: Staff notes, call logs, email summaries, meeting notes
-- Replaces: contacts.notes column (will be migrated)

CREATE TABLE contact_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

    -- Note data
    note_type TEXT NOT NULL CHECK (note_type IN (
        'call', 'email', 'meeting', 'general',
        'system', 'donation', 'event', 'issue'
    )) DEFAULT 'general',
    subject TEXT,  -- Optional title/subject line
    content TEXT NOT NULL,

    -- Author tracking
    author_user_id UUID,  -- Links to auth.users if Supabase Auth
    author_name TEXT NOT NULL,  -- Display name (fallback if no auth)

    -- Metadata
    is_pinned BOOLEAN NOT NULL DEFAULT false,  -- Pin important notes to top
    is_private BOOLEAN NOT NULL DEFAULT false,  -- Hide from some users
    tags TEXT[],  -- Array of tags for filtering

    -- Audit fields
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_contact_notes_contact_id ON contact_notes(contact_id, created_at DESC);
CREATE INDEX idx_contact_notes_note_type ON contact_notes(note_type);
CREATE INDEX idx_contact_notes_author ON contact_notes(author_user_id) WHERE author_user_id IS NOT NULL;
CREATE INDEX idx_contact_notes_pinned ON contact_notes(contact_id) WHERE is_pinned = true;
CREATE INDEX idx_contact_notes_tags ON contact_notes USING gin(tags) WHERE tags IS NOT NULL;

-- Full-text search on note content
CREATE INDEX idx_contact_notes_content_fts ON contact_notes USING gin(to_tsvector('english', content));

-- Trigram search on subject
CREATE INDEX idx_contact_notes_subject_trgm ON contact_notes USING gin(subject gin_trgm_ops);

-- Triggers
CREATE TRIGGER contact_notes_set_updated_by
    BEFORE UPDATE ON contact_notes
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_by();

-- Auto-set author_user_id from auth context if not provided
CREATE OR REPLACE FUNCTION set_note_author()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.author_user_id IS NULL THEN
        NEW.author_user_id = auth.uid();
    END IF;

    -- If author_name not provided, try to get from auth.users
    IF NEW.author_name IS NULL OR NEW.author_name = '' THEN
        NEW.author_name = COALESCE(
            (SELECT raw_user_meta_data->>'full_name' FROM auth.users WHERE id = NEW.author_user_id),
            (SELECT email FROM auth.users WHERE id = NEW.author_user_id),
            'Unknown User'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER contact_notes_set_author
    BEFORE INSERT ON contact_notes
    FOR EACH ROW
    EXECUTE FUNCTION set_note_author();

-- Row Level Security
ALTER TABLE contact_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "contact_notes_select_policy"
    ON contact_notes FOR SELECT
    TO authenticated
    USING (
        -- Can see all notes unless they're private
        NOT is_private
        -- OR note belongs to current user
        OR author_user_id = auth.uid()
        -- TODO: Add admin role check
    );

CREATE POLICY "contact_notes_insert_policy"
    ON contact_notes FOR INSERT
    TO authenticated
    WITH CHECK (author_user_id = auth.uid() OR author_user_id IS NULL);

CREATE POLICY "contact_notes_update_policy"
    ON contact_notes FOR UPDATE
    TO authenticated
    USING (
        -- Can only edit own notes
        author_user_id = auth.uid()
        -- TODO: Add admin role check
    )
    WITH CHECK (updated_by = auth.uid());

-- Policy: Can only delete own notes (or admin)
CREATE POLICY "contact_notes_delete_policy"
    ON contact_notes FOR DELETE
    TO authenticated
    USING (
        author_user_id = auth.uid()
        -- TODO: Add admin role check
    );

COMMENT ON TABLE contact_notes IS
'Staff notes and activity logs for contacts. Supports pinning, privacy, and full-text search.';

-- ============================================
-- GRANTS
-- ============================================
-- Ensure authenticated users can access tables
GRANT SELECT, INSERT, UPDATE ON contact_emails TO authenticated;
GRANT SELECT, INSERT, UPDATE ON external_identities TO authenticated;
GRANT SELECT, INSERT, UPDATE ON contact_roles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON contact_notes TO authenticated;

-- Service role has full access
GRANT ALL ON contact_emails TO service_role;
GRANT ALL ON external_identities TO service_role;
GRANT ALL ON contact_roles TO service_role;
GRANT ALL ON contact_notes TO service_role;

-- ============================================
-- ROLLBACK INSTRUCTIONS
-- ============================================
-- To rollback this migration, run:
/*
DROP TABLE IF EXISTS contact_notes CASCADE;
DROP TABLE IF EXISTS contact_roles CASCADE;
DROP TABLE IF EXISTS external_identities CASCADE;
DROP TABLE IF EXISTS contact_emails CASCADE;
DROP FUNCTION IF EXISTS set_note_author() CASCADE;
DROP FUNCTION IF EXISTS set_role_ended_at() CASCADE;
DROP FUNCTION IF EXISTS set_updated_by() CASCADE;
-- Note: Keep pg_trgm extension if other tables use it
-- DROP EXTENSION IF EXISTS pg_trgm;
*/
