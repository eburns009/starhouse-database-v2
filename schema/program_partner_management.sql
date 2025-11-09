-- Program Partner Management System
-- FAANG-level implementation with audit trails and payment tracking
-- Created: 2025-11-04

-- ============================================================================
-- 1. AUDIT LOG TABLE
-- ============================================================================
-- Track all changes to Program Partner status
CREATE TABLE IF NOT EXISTS program_partner_audit_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

  -- Action details
  action TEXT NOT NULL CHECK (action IN ('status_removed', 'status_added', 'payment_method_updated')),
  previous_value JSONB,
  new_value JSONB,

  -- Reason and notes
  reason TEXT,
  notes TEXT,

  -- Audit fields
  changed_by TEXT, -- User who made the change (email or user ID)
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ip_address INET,
  user_agent TEXT,

  -- Metadata
  metadata JSONB
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_partner_audit_contact_id ON program_partner_audit_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_partner_audit_action ON program_partner_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_partner_audit_changed_at ON program_partner_audit_log(changed_at DESC);

-- ============================================================================
-- 2. PAYMENT METHOD TRACKING
-- ============================================================================
-- Add payment method fields to contacts table
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS payment_method TEXT CHECK (payment_method IN ('credit_card', 'paypal', 'check', 'cash', 'wire_transfer', 'other')),
ADD COLUMN IF NOT EXISTS payment_method_notes TEXT,
ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS partner_status_notes TEXT;

-- Also add to subscriptions for more granular tracking
ALTER TABLE subscriptions
ADD COLUMN IF NOT EXISTS payment_method TEXT CHECK (payment_method IN ('credit_card', 'paypal', 'check', 'cash', 'wire_transfer', 'other')),
ADD COLUMN IF NOT EXISTS payment_notes TEXT;

-- ============================================================================
-- 3. FUNCTIONS FOR STATUS MANAGEMENT
-- ============================================================================

-- Function to remove Program Partner status
CREATE OR REPLACE FUNCTION remove_program_partner_status(
  p_contact_id UUID,
  p_reason TEXT,
  p_notes TEXT DEFAULT NULL,
  p_changed_by TEXT DEFAULT 'system'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_previous_status BOOLEAN;
  v_result JSONB;
BEGIN
  -- Get current status
  SELECT is_expected_program_partner INTO v_previous_status
  FROM contacts
  WHERE id = p_contact_id;

  -- Check if contact exists
  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Contact not found'
    );
  END IF;

  -- Check if already not a partner
  IF v_previous_status = FALSE OR v_previous_status IS NULL THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Contact is not currently a Program Partner'
    );
  END IF;

  -- Update contact status
  UPDATE contacts
  SET
    is_expected_program_partner = FALSE,
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
    'status_removed',
    jsonb_build_object('was_partner', true),
    jsonb_build_object('was_partner', false),
    p_reason,
    p_notes,
    p_changed_by
  );

  RETURN jsonb_build_object(
    'success', true,
    'message', 'Program Partner status removed successfully'
  );
END;
$$;

-- Function to update payment method
CREATE OR REPLACE FUNCTION update_payment_method(
  p_contact_id UUID,
  p_payment_method TEXT,
  p_payment_notes TEXT DEFAULT NULL,
  p_changed_by TEXT DEFAULT 'system'
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_previous_method TEXT;
  v_result JSONB;
BEGIN
  -- Get current payment method
  SELECT payment_method INTO v_previous_method
  FROM contacts
  WHERE id = p_contact_id;

  -- Check if contact exists
  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Contact not found'
    );
  END IF;

  -- Validate payment method
  IF p_payment_method NOT IN ('credit_card', 'paypal', 'check', 'cash', 'wire_transfer', 'other') THEN
    RETURN jsonb_build_object(
      'success', false,
      'error', 'Invalid payment method'
    );
  END IF;

  -- Update contact payment method
  UPDATE contacts
  SET
    payment_method = p_payment_method,
    payment_method_notes = p_payment_notes,
    last_payment_date = NOW(),
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
    'payment_method_updated',
    jsonb_build_object('payment_method', v_previous_method),
    jsonb_build_object('payment_method', p_payment_method),
    'Payment method updated',
    p_payment_notes,
    p_changed_by
  );

  RETURN jsonb_build_object(
    'success', true,
    'message', 'Payment method updated successfully',
    'payment_method', p_payment_method
  );
END;
$$;

-- ============================================================================
-- 4. VIEW FOR AUDIT HISTORY
-- ============================================================================
CREATE OR REPLACE VIEW program_partner_audit_history AS
SELECT
  pal.id,
  pal.contact_id,
  c.first_name,
  c.last_name,
  c.email,
  pal.action,
  pal.reason,
  pal.notes,
  pal.previous_value,
  pal.new_value,
  pal.changed_by,
  pal.changed_at,
  pal.ip_address
FROM program_partner_audit_log pal
JOIN contacts c ON pal.contact_id = c.id
ORDER BY pal.changed_at DESC;

-- ============================================================================
-- 5. GRANT PERMISSIONS (adjust as needed for your setup)
-- ============================================================================
-- GRANT SELECT ON program_partner_audit_log TO your_app_user;
-- GRANT SELECT ON program_partner_audit_history TO your_app_user;
-- GRANT EXECUTE ON FUNCTION remove_program_partner_status TO your_app_user;
-- GRANT EXECUTE ON FUNCTION update_payment_method TO your_app_user;

-- ============================================================================
-- 6. VERIFICATION QUERIES
-- ============================================================================
SELECT 'Schema created successfully!' as status;

-- Show table structure
SELECT
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'program_partner_audit_log'
ORDER BY ordinal_position;
