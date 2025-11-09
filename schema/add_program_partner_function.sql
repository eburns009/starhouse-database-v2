-- Add Program Partner Status Function
-- Complement to remove function - allows adding contacts as Program Partners

CREATE OR REPLACE FUNCTION add_program_partner_status(
  p_contact_id UUID,
  p_reason TEXT DEFAULT 'Manually added as Program Partner',
  p_notes TEXT DEFAULT NULL,
  p_changed_by TEXT DEFAULT 'system'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_previous_status BOOLEAN;
  v_contact_name TEXT;
  v_result JSONB;
BEGIN
  -- Get current status and name
  SELECT is_expected_program_partner, first_name || ' ' || COALESCE(last_name, '')
  INTO v_previous_status, v_contact_name
  FROM contacts
  WHERE id = p_contact_id;

  -- Check if contact exists
  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Contact not found'
    );
  END IF;

  -- Check if already a partner
  IF v_previous_status = TRUE THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Contact is already a Program Partner'
    );
  END IF;

  -- Update contact status
  UPDATE contacts
  SET
    is_expected_program_partner = TRUE,
    partner_status_notes = p_notes,
    updated_at = NOW()
  WHERE id = p_contact_id;

  -- Log the change
  INSERT INTO program_partner_audit_log (
    contact_id,
    action,
    previous_value,
    new_value,
    reason,
    notes,
    changed_by
  ) VALUES (
    p_contact_id,
    'status_added',
    jsonb_build_object('was_partner', COALESCE(v_previous_status, false)),
    jsonb_build_object('was_partner', true, 'contact_name', v_contact_name),
    p_reason,
    p_notes,
    p_changed_by
  );

  RETURN jsonb_build_object(
    'success', true,
    'message', 'Added as Program Partner successfully',
    'contact_name', v_contact_name
  );
END;
$$;

-- Verify function created
SELECT 'Function created successfully!' as status;
