-- ============================================================================
-- MIGRATION 002: Audit Log Table
-- ============================================================================
-- Purpose: Complete audit trail for all data modifications
-- FAANG Standard: Every mutation must be auditable
-- Compliance: SOC2, GDPR, HIPAA requirements
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Who did it
    user_id uuid,  -- NULL for system actions
    user_email text,

    -- What happened
    action text NOT NULL,  -- 'create', 'update', 'delete', 'restore', 'merge'
    table_name text NOT NULL,
    record_id uuid NOT NULL,

    -- Change details
    old_values jsonb,  -- Previous state (for updates/deletes)
    new_values jsonb,  -- New state (for creates/updates)

    -- Context
    ip_address inet,
    user_agent text,
    metadata jsonb,  -- Additional context (e.g., reason, bulk operation ID)

    -- When
    created_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT audit_log_action_check CHECK (action IN ('create', 'update', 'delete', 'restore', 'merge', 'bulk_update'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Composite index for user activity timeline
CREATE INDEX IF NOT EXISTS idx_audit_log_user_timeline ON audit_log(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Never allow updates or deletes on audit log (append-only)
CREATE POLICY "Audit log is append-only" ON audit_log
    FOR ALL TO public
    USING (false)
    WITH CHECK (true);

COMMENT ON TABLE audit_log IS 'Append-only audit trail for all data modifications (FAANG standard)';
COMMENT ON COLUMN audit_log.user_id IS 'User who performed the action (NULL for system)';
COMMENT ON COLUMN audit_log.old_values IS 'State before change (JSON)';
COMMENT ON COLUMN audit_log.new_values IS 'State after change (JSON)';
COMMENT ON COLUMN audit_log.metadata IS 'Additional context (reason, bulk_op_id, etc.)';
