-- ============================================================================
-- MIGRATION 003: Background Jobs Table
-- ============================================================================
-- Purpose: Track long-running operations (bulk imports, exports, merges)
-- FAANG Standard: Never block user requests; queue background work
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE job_type AS ENUM (
        'bulk_import',
        'bulk_export',
        'bulk_merge',
        'bulk_tag',
        'bulk_delete',
        'report_generation',
        'data_cleanup'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS jobs (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job details
    type job_type NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',

    -- Who created it
    user_id uuid,
    user_email text,

    -- Job configuration
    payload jsonb NOT NULL,  -- Input parameters

    -- Execution details
    started_at timestamptz,
    completed_at timestamptz,

    -- Progress tracking
    total_items integer,
    processed_items integer DEFAULT 0,
    failed_items integer DEFAULT 0,

    -- Results
    result jsonb,  -- Output data (e.g., download URL, summary stats)
    error_message text,
    error_details jsonb,

    -- Metadata
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT jobs_progress_check CHECK (
        processed_items >= 0 AND
        failed_items >= 0 AND
        (total_items IS NULL OR total_items >= 0)
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Composite index for user's job history
CREATE INDEX IF NOT EXISTS idx_jobs_user_timeline ON jobs(user_id, created_at DESC) WHERE user_id IS NOT NULL;

-- Composite index for processing queue
CREATE INDEX IF NOT EXISTS idx_jobs_pending_queue ON jobs(status, created_at) WHERE status IN ('pending', 'running');

-- Updated timestamp trigger
CREATE TRIGGER jobs_set_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE jobs IS 'Background job queue for long-running operations';
COMMENT ON COLUMN jobs.payload IS 'Job input configuration (JSON)';
COMMENT ON COLUMN jobs.result IS 'Job output/summary (JSON) - e.g., {download_url, stats}';
COMMENT ON COLUMN jobs.total_items IS 'Total items to process (NULL if unknown)';
COMMENT ON COLUMN jobs.processed_items IS 'Successfully processed items';
COMMENT ON COLUMN jobs.failed_items IS 'Failed items (with error details in error_details)';
