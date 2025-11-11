-- ============================================================================
-- MIGRATION 004: Saved Views for Data Tables
-- ============================================================================
-- Purpose: Save custom filters, sorts, and column configurations
-- FAANG Standard: Users expect to save their workspace preferences
-- UX: Critical for daily productivity with large datasets
-- ============================================================================

CREATE TABLE IF NOT EXISTS saved_views (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Ownership
    user_id uuid NOT NULL,

    -- View details
    name text NOT NULL,
    entity text NOT NULL,  -- 'contacts', 'transactions', 'subscriptions', etc.
    is_default boolean DEFAULT false,

    -- View configuration
    filters jsonb NOT NULL DEFAULT '{}',  -- Filter criteria
    sort jsonb,  -- Sort configuration
    columns jsonb,  -- Visible columns + order

    -- Sharing (future feature)
    share_scope text DEFAULT 'private',  -- 'private', 'team', 'public'

    -- Metadata
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT saved_views_entity_check CHECK (entity IN ('contacts', 'transactions', 'subscriptions', 'products', 'tags', 'members', 'donors', 'events')),
    CONSTRAINT saved_views_share_scope_check CHECK (share_scope IN ('private', 'team', 'public')),
    CONSTRAINT saved_views_unique_default UNIQUE (user_id, entity, is_default) DEFERRABLE INITIALLY DEFERRED
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_saved_views_user_id ON saved_views(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_views_entity ON saved_views(entity);

-- Composite index for loading user's views for an entity
CREATE INDEX IF NOT EXISTS idx_saved_views_user_entity ON saved_views(user_id, entity);

-- Updated timestamp trigger
CREATE TRIGGER saved_views_set_updated_at
    BEFORE UPDATE ON saved_views
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- Function to ensure only one default view per user per entity
CREATE OR REPLACE FUNCTION ensure_single_default_view()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = true THEN
        -- Unset other default views for this user and entity
        UPDATE saved_views
        SET is_default = false
        WHERE user_id = NEW.user_id
          AND entity = NEW.entity
          AND id != NEW.id
          AND is_default = true;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_single_default_view_trigger
    BEFORE INSERT OR UPDATE ON saved_views
    FOR EACH ROW
    WHEN (NEW.is_default = true)
    EXECUTE FUNCTION ensure_single_default_view();

COMMENT ON TABLE saved_views IS 'User-saved table views with filters, sorts, and column preferences';
COMMENT ON COLUMN saved_views.filters IS 'Filter criteria (JSON) - e.g., {source: "kajabi", email_subscribed: true}';
COMMENT ON COLUMN saved_views.sort IS 'Sort configuration (JSON) - e.g., {field: "created_at", direction: "desc"}';
COMMENT ON COLUMN saved_views.columns IS 'Visible columns and order (JSON) - e.g., ["name", "email", "created_at"]';
COMMENT ON COLUMN saved_views.is_default IS 'Load this view by default for this entity';
