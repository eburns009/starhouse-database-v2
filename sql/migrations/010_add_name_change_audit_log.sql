-- Migration: Add audit logging for name changes
-- Date: 2025-11-18
-- Purpose: Track all modifications to contact names to prevent silent data corruption

-- Create audit log table
CREATE TABLE IF NOT EXISTS contact_name_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

  -- Old values
  old_first_name TEXT,
  old_last_name TEXT,
  old_display_name TEXT,

  -- New values
  new_first_name TEXT,
  new_last_name TEXT,
  new_display_name TEXT,

  -- Metadata
  changed_by TEXT, -- 'kajabi_webhook', 'paypal_webhook', 'manual_update', 'enrichment_script', etc.
  change_source TEXT, -- Additional context (webhook event ID, script name, user ID, etc.)
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Add index for fast lookups
  CONSTRAINT contact_name_audit_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_contact_name_audit_contact_id ON contact_name_audit(contact_id);
CREATE INDEX idx_contact_name_audit_changed_at ON contact_name_audit(changed_at DESC);

-- Create trigger function to log name changes
CREATE OR REPLACE FUNCTION log_contact_name_change()
RETURNS TRIGGER AS $$
BEGIN
  -- Only log if name actually changed
  IF (OLD.first_name IS DISTINCT FROM NEW.first_name) OR
     (OLD.last_name IS DISTINCT FROM NEW.last_name) OR
     (OLD.display_name IS DISTINCT FROM NEW.display_name) THEN

    INSERT INTO contact_name_audit (
      contact_id,
      old_first_name,
      old_last_name,
      old_display_name,
      new_first_name,
      new_last_name,
      new_display_name,
      changed_by,
      change_source
    ) VALUES (
      NEW.id,
      OLD.first_name,
      OLD.last_name,
      OLD.display_name,
      NEW.first_name,
      NEW.last_name,
      NEW.display_name,
      COALESCE(current_setting('app.change_source', true), 'unknown'),
      COALESCE(current_setting('app.change_context', true), '')
    );

    -- Log to console for immediate visibility
    RAISE NOTICE 'Name changed for contact %: "% %" -> "% %" (source: %)',
      NEW.id,
      OLD.first_name, OLD.last_name,
      NEW.first_name, NEW.last_name,
      COALESCE(current_setting('app.change_source', true), 'unknown');
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to contacts table
DROP TRIGGER IF EXISTS trigger_log_contact_name_change ON contacts;

CREATE TRIGGER trigger_log_contact_name_change
  BEFORE UPDATE ON contacts
  FOR EACH ROW
  EXECUTE FUNCTION log_contact_name_change();

-- Create helper function to view name change history for a contact
CREATE OR REPLACE FUNCTION get_contact_name_history(p_contact_id UUID)
RETURNS TABLE (
  changed_at TIMESTAMPTZ,
  old_name TEXT,
  new_name TEXT,
  changed_by TEXT,
  change_source TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    a.changed_at,
    CONCAT_WS(' ', a.old_first_name, a.old_last_name) as old_name,
    CONCAT_WS(' ', a.new_first_name, a.new_last_name) as new_name,
    a.changed_by,
    a.change_source
  FROM contact_name_audit a
  WHERE a.contact_id = p_contact_id
  ORDER BY a.changed_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE contact_name_audit IS 'Audit log for all contact name changes to track data mutations';
COMMENT ON FUNCTION get_contact_name_history IS 'Get complete name change history for a contact';
