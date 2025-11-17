-- ============================================================================
-- MAILING LIST PROTECTION - RLS POLICIES
-- ============================================================================
-- Date: 2025-11-14
-- Purpose: Protect mailing list views with Row Level Security
-- ============================================================================

-- Enable RLS on contacts table if not already enabled
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- Create policy for mailing list views access
-- Only staff members can view mailing list data
CREATE POLICY "Staff can view mailing list data"
ON contacts
FOR SELECT
USING (
  -- Check if user is a staff member
  EXISTS (
    SELECT 1
    FROM staff_members sm
    WHERE sm.email = auth.jwt() ->> 'email'
    AND sm.active = true
  )
);

-- Grant access to mailing list views for authenticated users
-- (RLS will still check staff_allowlist)
GRANT SELECT ON mailing_list_priority TO authenticated;
GRANT SELECT ON mailing_list_export TO authenticated;
GRANT SELECT ON mailing_list_stats TO authenticated;

-- Create function to check if user can export mailing lists
CREATE OR REPLACE FUNCTION can_export_mailing_list()
RETURNS BOOLEAN AS $$
BEGIN
  -- Only active staff can export mailing lists
  RETURN EXISTS (
    SELECT 1
    FROM staff_members
    WHERE email = auth.jwt() ->> 'email'
    AND is_active = true
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit log table for mailing list exports
CREATE TABLE IF NOT EXISTS mailing_list_exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exported_by TEXT NOT NULL,
  exported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  export_type TEXT NOT NULL, -- 'high_confidence', 'all', 'medium_low'
  contact_count INTEGER NOT NULL,
  filters JSONB, -- Store any filters applied
  ip_address TEXT,
  user_agent TEXT
);

-- Enable RLS on export log
ALTER TABLE mailing_list_exports ENABLE ROW LEVEL SECURITY;

-- Only staff can view export logs
CREATE POLICY "Staff can view export logs"
ON mailing_list_exports
FOR SELECT
USING (
  EXISTS (
    SELECT 1
    FROM staff_members sm
    WHERE sm.email = auth.jwt() ->> 'email'
    AND sm.active = true
  )
);

-- Only staff can insert export logs
CREATE POLICY "Staff can log exports"
ON mailing_list_exports
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1
    FROM staff_members sm
    WHERE sm.email = auth.jwt() ->> 'email'
    AND sm.active = true
  )
);

-- Create function to log mailing list exports
CREATE OR REPLACE FUNCTION log_mailing_list_export(
  p_export_type TEXT,
  p_contact_count INTEGER,
  p_filters JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_export_id UUID;
BEGIN
  -- Check permission
  IF NOT can_export_mailing_list() THEN
    RAISE EXCEPTION 'Unauthorized: Only staff can export mailing lists';
  END IF;

  -- Log the export
  INSERT INTO mailing_list_exports (
    exported_by,
    export_type,
    contact_count,
    filters
  ) VALUES (
    auth.jwt() ->> 'email',
    p_export_type,
    p_contact_count,
    p_filters
  )
  RETURNING id INTO v_export_id;

  RETURN v_export_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create view for export history
CREATE OR REPLACE VIEW mailing_list_export_history AS
SELECT
  mle.id,
  mle.exported_by,
  mle.exported_at,
  mle.export_type,
  mle.contact_count,
  mle.filters,
  sm.role as staff_role
FROM mailing_list_exports mle
LEFT JOIN staff_members sm ON sm.email = mle.exported_by
ORDER BY mle.exported_at DESC;

GRANT SELECT ON mailing_list_export_history TO authenticated;

-- Add comments
COMMENT ON TABLE mailing_list_exports IS 'Audit log for all mailing list exports';
COMMENT ON FUNCTION can_export_mailing_list IS 'Check if current user can export mailing lists';
COMMENT ON FUNCTION log_mailing_list_export IS 'Log a mailing list export with audit trail';
COMMENT ON VIEW mailing_list_export_history IS 'Export history with staff names';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_mailing_list_exports_exported_by
ON mailing_list_exports(exported_by);

CREATE INDEX IF NOT EXISTS idx_mailing_list_exports_exported_at
ON mailing_list_exports(exported_at DESC);
