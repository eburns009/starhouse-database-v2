# StarHouse Database Schema Summary v2

**Generated:** 2025-11-28
**Status:** Current State + Planned Tables
**Reference:** STARHOUSE_MASTER_PLAN_v3.1.md

---

## Overview

This document describes both **existing tables** (currently in production) and **planned tables** (defined in Master Plan v3.1 for upcoming phases).

---

## 1. TABLE INVENTORY

### Existing Tables (Production)

| Table | Purpose | Primary Key | Status |
|-------|---------|-------------|--------|
| `contacts` | Central contact registry - master list of all contacts across all systems | `id` (UUID) | ✅ Active |
| `tags` | Reusable categorization labels for contacts | `id` (UUID) | ✅ Active |
| `products` | Courses, memberships, events, and services offered | `id` (UUID) | ✅ Active |
| `contact_tags` | Junction: Contacts ↔ Tags (many-to-many) | `id` (UUID) | ✅ Active |
| `contact_products` | Junction: Contacts ↔ Products (access/purchase history) | `id` (UUID) | ✅ Active |
| `subscriptions` | Recurring subscription records with lifecycle tracking | `id` (UUID) | ✅ Active |
| `transactions` | Complete transaction history with payment details | `id` (UUID) | ✅ Active |
| `events` | Event details from Ticket Tailor integration | `id` (UUID) | ✅ Active |
| `event_registrations` | Ticket purchases / event registrations | `id` (UUID) | ✅ Active |
| `webhook_events` | Audit trail and idempotency tracking for webhooks | `id` (UUID) | ✅ Active |
| `webhook_rate_limits` | Token bucket rate limiting for webhooks | `(source, bucket_key)` | ✅ Active |
| `webhook_nonces` | Prevents intra-window replay attacks | `id` (UUID) | ✅ Active |
| `contact_emails` | Multi-email support per contact with source tracking | `id` (UUID) | ✅ Active |
| `external_identities` | Cross-system identity reconciliation (Kajabi, PayPal, etc.) | `id` (UUID) | ✅ Active |
| `contact_roles` | Time-bound role tracking (member, donor, volunteer, etc.) | `id` (UUID) | ✅ Active |
| `contact_notes` | Staff notes, call logs, meeting notes | `id` (UUID) | ✅ Active |
| `audit_log` | Append-only audit trail for all data modifications | `id` (UUID) | ✅ Active |
| `jobs` | Background job queue for long-running operations | `id` (UUID) | ✅ Active |
| `saved_views` | User-saved table views with filters/sorts/columns | `id` (UUID) | ✅ Active |
| `health_check_log` | Historical health check results for trending | `id` (UUID) | ✅ Active |
| `membership_products` | Referenced in RLS policies | Unknown | ⚠️ Schema not found |
| `dlq_events` | Dead letter queue | Unknown | ⚠️ Schema not found |

### Planned Tables (Master Plan v3.1)

| Table | Purpose | Phase | Priority |
|-------|---------|-------|----------|
| `contact_phones` | Multi-phone support per contact | Phase 1 | High |
| `contact_addresses` | Multi-address support with mailing flags | Phase 1 | High |
| `venues` | Rental spaces with rates and capacity | Phase 3 | High |
| `booking_inquiries` | Inbound rental inquiries from Wix webhooks | Phase 3 | High |
| `bookings` | Confirmed venue rentals with workflow status | Phase 3 | High |
| `course_enrollments` | Course/workshop enrollments with progress tracking | Phase 5 | Medium |
| `campaigns` | Fundraising campaigns (phone, mail, email, event) | Phase 6 | Medium |
| `campaign_contacts` | Junction: Campaigns ↔ Contacts with outcome tracking | Phase 6 | Medium |
| `acknowledgments` | Donation acknowledgment tracking | Phase 6 | Medium |

---

## 2. PLANNED TABLE SCHEMAS

### Phase 1: Contact Foundation

#### contact_phones
```sql
CREATE TABLE IF NOT EXISTS contact_phones (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  phone TEXT NOT NULL,
  type TEXT CHECK (type IN ('mobile', 'home', 'work', 'other')),
  is_primary BOOLEAN DEFAULT false,
  source_system TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER contact_phones_set_updated_at
  BEFORE UPDATE ON contact_phones
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE contact_phones ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON contact_phones
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

#### contact_addresses
```sql
CREATE TABLE IF NOT EXISTS contact_addresses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  street_address TEXT,
  city TEXT,
  state TEXT,
  postal_code TEXT,
  country TEXT DEFAULT 'USA',
  type TEXT CHECK (type IN ('billing', 'shipping', 'mailing', 'home', 'work', 'other')),
  is_primary BOOLEAN DEFAULT false,
  is_mailing BOOLEAN DEFAULT false,
  is_verified BOOLEAN DEFAULT false,
  source_system TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER contact_addresses_set_updated_at
  BEFORE UPDATE ON contact_addresses
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE contact_addresses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON contact_addresses
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

### Phase 3: Events Module (Zoho Replacement)

#### venues
```sql
CREATE TABLE IF NOT EXISTS venues (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  capacity INT,
  hourly_rate DECIMAL(10,2),
  daily_rate DECIMAL(10,2),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER venues_set_updated_at
  BEFORE UPDATE ON venues
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON venues
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

#### booking_inquiries
```sql
CREATE TABLE IF NOT EXISTS booking_inquiries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source TEXT DEFAULT 'wix',
  
  -- Contact info (may or may not match existing contact)
  contact_name TEXT,
  contact_email TEXT,
  contact_phone TEXT,
  contact_id UUID REFERENCES contacts(id),
  
  -- Request details
  event_name TEXT,
  event_type TEXT,
  venue_requested TEXT,
  requested_date DATE,
  requested_start_time TIME,
  requested_end_time TIME,
  expected_attendance INT,
  message TEXT,
  
  -- Workflow
  status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'converted', 'declined', 'spam')),
  staff_notes TEXT,
  assigned_to UUID,
  converted_to_booking_id UUID,
  
  -- Audit
  raw_payload JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER booking_inquiries_set_updated_at
  BEFORE UPDATE ON booking_inquiries
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE booking_inquiries ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON booking_inquiries
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

#### bookings
```sql
CREATE TABLE IF NOT EXISTS bookings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  inquiry_id UUID REFERENCES booking_inquiries(id),
  contact_id UUID REFERENCES contacts(id) NOT NULL,
  venue_id UUID REFERENCES venues(id),
  
  -- Event details
  event_name TEXT NOT NULL,
  event_type TEXT,
  start_datetime TIMESTAMPTZ NOT NULL,
  end_datetime TIMESTAMPTZ NOT NULL,
  setup_time INTERVAL,
  teardown_time INTERVAL,
  expected_attendance INT,
  actual_attendance INT,
  
  -- Status workflow
  status TEXT DEFAULT 'tentative' CHECK (status IN ('tentative', 'confirmed', 'cancelled', 'completed')),
  confirmed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,
  completed_at TIMESTAMPTZ,
  
  -- Financial (reference only — Wix/QB handles actual invoicing)
  quoted_amount DECIMAL(10,2),
  deposit_required DECIMAL(10,2),
  deposit_received BOOLEAN DEFAULT false,
  deposit_received_at TIMESTAMPTZ,
  invoice_sent BOOLEAN DEFAULT false,
  invoice_sent_at TIMESTAMPTZ,
  invoice_reference TEXT,
  payment_received BOOLEAN DEFAULT false,
  payment_received_at TIMESTAMPTZ,
  payment_reference TEXT,
  
  -- Membership validation
  membership_verified BOOLEAN DEFAULT false,
  membership_level_at_booking TEXT,
  membership_override BOOLEAN DEFAULT false,
  membership_override_reason TEXT,
  
  -- Audit
  staff_notes TEXT,
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER bookings_set_updated_at
  BEFORE UPDATE ON bookings
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON bookings
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

### Phase 5: School for Souls

#### course_enrollments
```sql
CREATE TABLE IF NOT EXISTS course_enrollments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  
  -- Enrollment
  enrolled_at TIMESTAMPTZ DEFAULT NOW(),
  source TEXT,
  
  -- Progress (for online courses)
  progress_percent INT DEFAULT 0,
  last_activity_at TIMESTAMPTZ,
  
  -- Completion
  completed BOOLEAN DEFAULT false,
  completed_at TIMESTAMPTZ,
  certificate_issued BOOLEAN DEFAULT false,
  
  -- Attendance (for in-person)
  attended BOOLEAN,
  attendance_notes TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER course_enrollments_set_updated_at
  BEFORE UPDATE ON course_enrollments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE course_enrollments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON course_enrollments
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

### Phase 6: Donor Advanced Features

#### campaigns
```sql
CREATE TABLE IF NOT EXISTS campaigns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  type TEXT CHECK (type IN ('phone', 'mail', 'email', 'event', 'online')),
  goal_amount DECIMAL(10,2),
  start_date DATE,
  end_date DATE,
  status TEXT DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER campaigns_set_updated_at
  BEFORE UPDATE ON campaigns
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON campaigns
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

#### campaign_contacts
```sql
CREATE TABLE IF NOT EXISTS campaign_contacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  contact_id UUID REFERENCES contacts(id),
  
  -- Outreach tracking
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'attempted', 'contacted', 'pledged', 'donated', 'declined', 'removed')),
  assigned_to UUID,
  
  -- Attempts
  attempt_count INT DEFAULT 0,
  last_attempt_at TIMESTAMPTZ,
  last_attempt_outcome TEXT,
  
  -- Results
  contacted_at TIMESTAMPTZ,
  pledged_amount DECIMAL(10,2),
  pledged_at TIMESTAMPTZ,
  donation_id UUID REFERENCES transactions(id),
  outcome_notes TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(campaign_id, contact_id)
);

CREATE TRIGGER campaign_contacts_set_updated_at
  BEFORE UPDATE ON campaign_contacts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE campaign_contacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON campaign_contacts
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

#### acknowledgments
```sql
CREATE TABLE IF NOT EXISTS acknowledgments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  transaction_id UUID REFERENCES transactions(id),
  contact_id UUID REFERENCES contacts(id),
  
  -- Status
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
  
  -- Delivery
  method TEXT CHECK (method IN ('email', 'mail', 'manual')),
  sent_at TIMESTAMPTZ,
  sent_by UUID,
  
  -- Email specifics
  email_address TEXT,
  email_template TEXT,
  
  -- Mail specifics  
  mailing_address TEXT,
  
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER acknowledgments_set_updated_at
  BEFORE UPDATE ON acknowledgments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE acknowledgments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON acknowledgments
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

## 3. PLANNED VIEWS

### Phase 1: Contact Foundation

#### v_contact_360
```sql
CREATE OR REPLACE VIEW v_contact_360 AS
SELECT 
  c.*,
  (SELECT COUNT(*) FROM transactions t WHERE t.contact_id = c.id AND t.deleted_at IS NULL) as transaction_count,
  (SELECT COALESCE(SUM(amount), 0) FROM transactions t WHERE t.contact_id = c.id AND t.is_donation = true AND t.deleted_at IS NULL) as lifetime_giving,
  (SELECT COUNT(*) FROM event_registrations er WHERE er.contact_id = c.id) as event_count,
  (SELECT COUNT(*) FROM contact_products cp WHERE cp.contact_id = c.id) as product_count,
  get_membership_status(c.id) as membership_status,
  is_current_member(c.id) as is_member
FROM contacts c
WHERE c.deleted_at IS NULL;
```

#### v_contact_purchases
```sql
CREATE OR REPLACE VIEW v_contact_purchases AS
SELECT 
  cp.contact_id,
  p.name as product_name,
  p.product_type,
  t.amount,
  t.transaction_date,
  t.source_system
FROM contact_products cp
JOIN products p ON p.id = cp.product_id
LEFT JOIN transactions t ON t.contact_id = cp.contact_id AND t.product_id = cp.product_id
WHERE p.deleted_at IS NULL
ORDER BY t.transaction_date DESC;
```

### Phase 2: Donor Module

#### v_donor_classification
```sql
CREATE OR REPLACE VIEW v_donor_classification AS
SELECT 
  c.id,
  c.full_name,
  c.email,
  COALESCE(SUM(t.amount), 0) as lifetime_giving,
  CASE 
    WHEN COALESCE(SUM(t.amount), 0) >= 500 THEN 'Major'
    WHEN COALESCE(SUM(t.amount), 0) >= 100 THEN 'Mid-Level'
    ELSE 'Standard'
  END as donor_level,
  MAX(t.transaction_date) as last_gift_date,
  COUNT(t.id) as gift_count
FROM contacts c
LEFT JOIN transactions t ON t.contact_id = c.id 
  AND t.is_donation = true 
  AND t.deleted_at IS NULL
GROUP BY c.id, c.full_name, c.email;
```

### Phase 3: Events Module

#### v_events_kpi
```sql
CREATE OR REPLACE VIEW v_events_kpi AS
SELECT
  COUNT(*) FILTER (WHERE status = 'confirmed' AND start_datetime >= date_trunc('year', NOW())) as ytd_confirmed,
  COUNT(*) FILTER (WHERE status = 'confirmed' AND start_datetime BETWEEN NOW() AND NOW() + INTERVAL '30 days') as upcoming_30_days,
  COUNT(*) FILTER (WHERE status = 'tentative') as pending_confirmation,
  (SELECT COUNT(*) FROM booking_inquiries WHERE status = 'new') as new_inquiries,
  (SELECT COUNT(*) FROM booking_inquiries WHERE created_at >= NOW() - INTERVAL '7 days') as inquiries_last_7_days,
  COALESCE(SUM(quoted_amount) FILTER (WHERE status IN ('confirmed', 'completed') AND start_datetime >= date_trunc('year', NOW())), 0) as ytd_revenue
FROM bookings;
```

### Phase 4: Membership Module

#### v_memberships_expiring
```sql
CREATE OR REPLACE VIEW v_memberships_expiring AS
SELECT 
  c.id,
  c.full_name,
  c.email,
  s.current_period_end,
  s.current_period_end - NOW() as days_until_expiry,
  CASE 
    WHEN s.current_period_end <= NOW() + INTERVAL '30 days' THEN 'urgent'
    WHEN s.current_period_end <= NOW() + INTERVAL '60 days' THEN 'soon'
    WHEN s.current_period_end <= NOW() + INTERVAL '90 days' THEN 'upcoming'
  END as urgency
FROM contacts c
JOIN subscriptions s ON s.contact_id = c.id AND s.status = 'active'
WHERE s.current_period_end <= NOW() + INTERVAL '90 days'
ORDER BY s.current_period_end;
```

#### v_program_partner_rental_usage
```sql
CREATE OR REPLACE VIEW v_program_partner_rental_usage AS
SELECT 
  c.id as contact_id,
  c.full_name,
  get_membership_status(c.id) as membership_status,
  p.name as membership_level,
  p.rental_dates_allowed,
  COUNT(b.id) FILTER (WHERE b.start_datetime >= date_trunc('year', NOW())) as rentals_ytd,
  p.rental_dates_allowed - COUNT(b.id) FILTER (WHERE b.start_datetime >= date_trunc('year', NOW())) as rentals_remaining
FROM contacts c
JOIN subscriptions s ON s.contact_id = c.id AND s.status = 'active'
JOIN products p ON p.id = s.product_id AND p.membership_type = 'program_partner'
LEFT JOIN bookings b ON b.contact_id = c.id AND b.status IN ('confirmed', 'completed')
GROUP BY c.id, c.full_name, p.name, p.rental_dates_allowed;
```

#### v_members_needing_upgrade
```sql
CREATE OR REPLACE VIEW v_members_needing_upgrade AS
SELECT 
  c.id,
  c.full_name,
  c.email,
  get_membership_status(c.id) as current_status,
  p.name as current_level,
  p.membership_type,
  COUNT(b.id) as booking_count
FROM contacts c
JOIN subscriptions s ON s.contact_id = c.id AND s.status = 'active'
JOIN products p ON p.id = s.product_id
LEFT JOIN bookings b ON b.contact_id = c.id
WHERE p.membership_type = 'individual'
  AND EXISTS (SELECT 1 FROM bookings WHERE contact_id = c.id)
GROUP BY c.id, c.full_name, c.email, p.name, p.membership_type;
```

### Phase 5: School for Souls

#### v_top_courses
```sql
CREATE OR REPLACE VIEW v_top_courses AS
SELECT 
  p.id,
  p.name,
  p.course_type,
  COUNT(DISTINCT ce.contact_id) as enrollment_count,
  COUNT(DISTINCT ce.contact_id) FILTER (WHERE ce.completed) as completion_count,
  COALESCE(SUM(t.amount), 0) as revenue
FROM products p
LEFT JOIN course_enrollments ce ON ce.product_id = p.id
LEFT JOIN transactions t ON t.product_id = p.id AND t.deleted_at IS NULL
WHERE p.is_active = true
  AND p.product_type IN ('course', 'workshop', 'event')
GROUP BY p.id, p.name, p.course_type
ORDER BY enrollment_count DESC;
```

#### v_school_kpi
```sql
CREATE OR REPLACE VIEW v_school_kpi AS
SELECT
  (SELECT COUNT(DISTINCT contact_id) FROM course_enrollments WHERE enrolled_at >= date_trunc('year', NOW())) as ytd_students,
  (SELECT COUNT(*) FROM course_enrollments WHERE enrolled_at >= NOW() - INTERVAL '30 days') as enrollments_30_days,
  (SELECT COUNT(*) FROM course_enrollments WHERE completed AND completed_at >= date_trunc('year', NOW())) as ytd_completions,
  (SELECT COUNT(*) FROM events WHERE start_datetime BETWEEN NOW() AND NOW() + INTERVAL '30 days') as upcoming_events;
```

### Phase 6: Donor Advanced

#### v_campaign_results
```sql
CREATE OR REPLACE VIEW v_campaign_results AS
SELECT 
  c.id,
  c.name,
  c.type,
  c.goal_amount,
  c.status,
  COUNT(cc.id) as total_contacts,
  COUNT(cc.id) FILTER (WHERE cc.status = 'contacted') as contacted_count,
  COUNT(cc.id) FILTER (WHERE cc.status = 'pledged') as pledged_count,
  COUNT(cc.id) FILTER (WHERE cc.status = 'donated') as donated_count,
  COALESCE(SUM(cc.pledged_amount), 0) as total_pledged,
  COALESCE(SUM(t.amount), 0) as total_raised,
  CASE WHEN c.goal_amount > 0 THEN ROUND(COALESCE(SUM(t.amount), 0) / c.goal_amount * 100, 1) ELSE 0 END as percent_of_goal
FROM campaigns c
LEFT JOIN campaign_contacts cc ON cc.campaign_id = c.id
LEFT JOIN transactions t ON t.id = cc.donation_id
GROUP BY c.id, c.name, c.type, c.goal_amount, c.status;
```

---

## 4. PLANNED FUNCTIONS

### Phase 3: Events Module

#### validate_booking_membership
```sql
CREATE OR REPLACE FUNCTION validate_booking_membership(p_contact_id UUID)
RETURNS TABLE (
  is_valid BOOLEAN, 
  membership_status TEXT,
  message TEXT
) AS $$
DECLARE
  v_status TEXT;
BEGIN
  v_status := get_membership_status(p_contact_id);
  
  IF v_status IS NULL OR v_status = 'none' THEN
    RETURN QUERY SELECT false, v_status, 'Contact is not a member. Membership required for venue rental.';
  ELSIF v_status = 'expired' THEN
    RETURN QUERY SELECT false, v_status, 'Membership has expired. Please renew before booking.';
  ELSE
    RETURN QUERY SELECT true, v_status, 'Membership valid.';
  END IF;
END;
$$ LANGUAGE plpgsql;
```

---

## 5. SCHEMA MODIFICATIONS TO EXISTING TABLES

### contacts table
```sql
-- Add business_name if missing
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS business_name TEXT;
```

### products table
```sql
-- Add membership-specific fields for Program Partner tracking
ALTER TABLE products ADD COLUMN IF NOT EXISTS membership_type TEXT CHECK (membership_type IN ('individual', 'program_partner'));
ALTER TABLE products ADD COLUMN IF NOT EXISTS rental_dates_allowed INT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS rental_priority INT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS course_type TEXT CHECK (course_type IN ('in_person', 'online', 'hybrid'));
ALTER TABLE products ADD COLUMN IF NOT EXISTS duration_hours DECIMAL(5,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS max_participants INT;
```

---

## 6. EXISTING RELATIONSHIPS

### Foreign Key Relationships (Parent → Child)

| Parent Table | Child Table | FK Column | ON DELETE |
|--------------|-------------|-----------|-----------|
| `contacts` | `contact_tags` | `contact_id` | CASCADE |
| `contacts` | `contact_products` | `contact_id` | CASCADE |
| `contacts` | `subscriptions` | `contact_id` | RESTRICT |
| `contacts` | `transactions` | `contact_id` | RESTRICT |
| `contacts` | `event_registrations` | `contact_id` | CASCADE |
| `contacts` | `webhook_events` | `contact_id` | SET NULL |
| `contacts` | `contact_emails` | `contact_id` | CASCADE |
| `contacts` | `external_identities` | `contact_id` | CASCADE |
| `contacts` | `contact_roles` | `contact_id` | CASCADE |
| `contacts` | `contact_notes` | `contact_id` | CASCADE |
| `tags` | `contact_tags` | `tag_id` | CASCADE |
| `products` | `contact_products` | `product_id` | CASCADE |
| `products` | `subscriptions` | `product_id` | RESTRICT |
| `products` | `transactions` | `product_id` | RESTRICT |
| `products` | `events` | `kajabi_product_id` | SET NULL |
| `subscriptions` | `transactions` | `subscription_id` | SET NULL |
| `subscriptions` | `webhook_events` | `subscription_id` | SET NULL |
| `transactions` | `webhook_events` | `transaction_id` | SET NULL |
| `transactions` | `event_registrations` | `transaction_id` | SET NULL |
| `events` | `event_registrations` | `event_id` | CASCADE |

### Planned Foreign Key Relationships (New Tables)

| Parent Table | Child Table | FK Column | ON DELETE |
|--------------|-------------|-----------|-----------|
| `contacts` | `contact_phones` | `contact_id` | CASCADE |
| `contacts` | `contact_addresses` | `contact_id` | CASCADE |
| `contacts` | `booking_inquiries` | `contact_id` | SET NULL |
| `contacts` | `bookings` | `contact_id` | RESTRICT |
| `contacts` | `course_enrollments` | `contact_id` | CASCADE |
| `contacts` | `campaign_contacts` | `contact_id` | SET NULL |
| `contacts` | `acknowledgments` | `contact_id` | SET NULL |
| `venues` | `bookings` | `venue_id` | SET NULL |
| `booking_inquiries` | `bookings` | `inquiry_id` | SET NULL |
| `products` | `course_enrollments` | `product_id` | SET NULL |
| `campaigns` | `campaign_contacts` | `campaign_id` | CASCADE |
| `transactions` | `campaign_contacts` | `donation_id` | SET NULL |
| `transactions` | `acknowledgments` | `transaction_id` | SET NULL |

---

## 7. EXISTING SUPABASE FEATURES

### Triggers (19 defined)

| Trigger | Table | Function | Purpose |
|---------|-------|----------|---------|
| `contacts_set_updated_at` | `contacts` | `set_updated_at()` | Auto-update timestamp |
| `tags_set_updated_at` | `tags` | `set_updated_at()` | Auto-update timestamp |
| `products_set_updated_at` | `products` | `set_updated_at()` | Auto-update timestamp |
| `subscriptions_set_updated_at` | `subscriptions` | `set_updated_at()` | Auto-update timestamp |
| `transactions_set_updated_at` | `transactions` | `set_updated_at()` | Auto-update timestamp |
| `set_events_updated_at` | `events` | `set_updated_at()` | Auto-update timestamp |
| `set_event_registrations_updated_at` | `event_registrations` | `set_updated_at()` | Auto-update timestamp |
| `webhook_events_set_updated_at` | `webhook_events` | `set_updated_at()` | Auto-update timestamp |
| `contact_emails_set_updated_by` | `contact_emails` | `set_updated_by()` | Track who made changes |
| `external_identities_set_updated_by` | `external_identities` | `set_updated_by()` | Track who made changes |
| `contact_roles_set_updated_by` | `contact_roles` | `set_updated_by()` | Track who made changes |
| `contact_roles_set_ended_at` | `contact_roles` | `set_role_ended_at()` | Auto-set end date |
| `contact_notes_set_updated_by` | `contact_notes` | `set_updated_by()` | Track who made changes |
| `contact_notes_set_author` | `contact_notes` | `set_note_author()` | Auto-set author |
| `jobs_set_updated_at` | `jobs` | `set_updated_at()` | Auto-update timestamp |
| `saved_views_set_updated_at` | `saved_views` | `set_updated_at()` | Auto-update timestamp |
| `ensure_single_default_view_trigger` | `saved_views` | `ensure_single_default_view()` | Enforce one default |

### Existing Functions (20+)

| Function | Purpose | Type |
|----------|---------|------|
| `set_updated_at()` | Update timestamp on row update | Trigger |
| `set_updated_by()` | Track user who modified record | Trigger |
| `set_note_author()` | Auto-populate note author | Trigger |
| `set_role_ended_at()` | Auto-set end date on role deactivation | Trigger |
| `ensure_single_default_view()` | Enforce one default saved view | Trigger |
| `is_current_member(uuid)` | Check if contact is active member | Helper |
| `get_membership_status(uuid)` | Get membership status string | Helper |
| `get_active_member_emails()` | Get emails for active members | Helper |
| `is_webhook_processed(text)` | Check webhook idempotency | Security |
| `is_replay_attack(timestamptz)` | Detect replay attacks | Security |
| `is_duplicate_payload(text, text)` | Detect duplicate payloads | Security |
| `is_nonce_used(text, text)` | Check if nonce was used | Security |
| `record_nonce(text, text)` | Record nonce atomically | Security |
| `process_webhook_atomically(...)` | Atomic webhook processing | Security |
| `get_webhook_stats(int)` | Webhook monitoring stats | Monitoring |
| `cleanup_old_webhook_events()` | Delete old webhook events | Maintenance |
| `cleanup_old_nonces()` | Delete old nonces | Maintenance |
| `checkout_rate_limit(...)` | Token bucket rate limiting | Security |
| `get_rate_limit_info(...)` | Rate limit debugging | Monitoring |
| `cleanup_stale_rate_limits()` | Clean stale rate limit entries | Maintenance |
| `daily_health_check()` | Comprehensive health check | Monitoring |
| `log_health_check()` | Store health check results | Monitoring |
| `find_probable_duplicate_transaction(...)` | Find cross-source duplicates | Data Quality |

### Existing Views (18)

| View | Purpose |
|------|---------|
| `v_potential_duplicate_contacts` | Contacts with same email |
| `v_active_subscriptions` | Active subscriptions with contact info |
| `v_contact_summary` | Aggregated contact metrics |
| `v_upcoming_events` | Upcoming events with registration counts |
| `v_contact_events` | Contact event history |
| `v_membership_status` | Real-time membership status |
| `v_active_members` | Current active members only |
| `v_membership_metrics` | Membership dashboard stats |
| `v_failed_webhooks` | Recent failed webhooks |
| `v_webhook_security_alerts` | Security alerts |
| `v_rate_limit_status` | Rate limit bucket status |
| `v_database_health` | Overall database health |
| `v_performance_metrics` | Database performance stats |
| `v_recent_health_alerts` | Recent health check failures |
| `v_active_contacts` | Non-deleted contacts |
| `v_active_products` | Non-deleted, active products |
| `v_potential_duplicate_transactions` | Transaction duplicates |
| `v_revenue_by_source` | Revenue report by source system |
| `v_transactions_missing_provenance` | Missing source tracking |

### Extensions in Use

| Extension | Purpose |
|-----------|---------|
| `uuid-ossp` | UUID generation (`uuid_generate_v4()`) |
| `citext` | Case-insensitive text for emails |
| `pg_trgm` | Trigram indexing for fuzzy search |

### Custom Types (Enums)

| Type | Values |
|------|--------|
| `subscription_status` | `active`, `paused`, `canceled`, `expired`, `trial` |
| `payment_status` | `pending`, `completed`, `failed`, `refunded`, `disputed` |
| `transaction_type` | `purchase`, `subscription`, `refund`, `adjustment` |
| `job_status` | `pending`, `running`, `completed`, `failed`, `cancelled` |
| `job_type` | `bulk_import`, `bulk_export`, `bulk_merge`, `bulk_tag`, `bulk_delete`, `report_generation`, `data_cleanup` |

---

## 8. RLS STATUS

### Tables with RLS Enabled

| Table | RLS Enabled | Policy |
|-------|-------------|--------|
| `contacts` | ✅ Yes | Staff + service_role full access |
| `transactions` | ✅ Yes | Staff + service_role full access |
| `subscriptions` | ✅ Yes | Staff + service_role full access |
| `products` | ✅ Yes | Staff + service_role full access |
| `tags` | ✅ Yes | Staff + service_role full access |
| `contact_tags` | ✅ Yes | Staff + service_role full access |
| `contact_products` | ✅ Yes | Staff + service_role full access |
| `webhook_events` | ✅ Yes | service_role only |
| `contact_emails` | ✅ Yes | Authenticated users |
| `external_identities` | ✅ Yes | Authenticated users |
| `contact_roles` | ✅ Yes | Authenticated users |
| `contact_notes` | ✅ Yes | Author-based policies |
| `audit_log` | ✅ Yes | Append-only |
| `jobs` | ✅ Yes | User owns their own |
| `saved_views` | ✅ Yes | User owns their own |
| `events` | ❓ Unknown | Needs verification |
| `event_registrations` | ❓ Unknown | Needs verification |

### Planned Tables: All will use standard staff policy
```sql
ALTER TABLE [table] ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON [table]
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

## 9. KNOWN ISSUES & GAPS

### Missing Table Schemas
| Table | Status | Action |
|-------|--------|--------|
| `membership_products` | Referenced in RLS | Define or remove reference |
| `dlq_events` | Referenced in health monitoring | Define or remove reference |

### Standards Violations
| Issue | Location | Standard |
|-------|----------|----------|
| Mutable field as lookup key | `contacts.email` | Email is unique but mutable |
| Missing soft delete | `events`, `event_registrations`, others | Add `deleted_at` columns |
| Hard delete possible | Some CASCADE deletes | Could orphan audit trail |
| Legacy external ID columns | `contacts.kajabi_id`, etc. | Migrate to `external_identities` |

### Data Integrity Items
| Issue | Mitigation |
|-------|------------|
| Cross-source duplicate transactions | `v_potential_duplicate_transactions` view |
| Name duplicates | `v_database_health` monitoring |
| P0: Duplicate transactions in donor view | **Must resolve in Phase 0** |

---

## 10. TABLE CREATION CHECKLIST

When creating any new table, follow this pattern:

```sql
-- 1. Create table with UUID PK and timestamps
CREATE TABLE IF NOT EXISTS new_table (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- ... columns ...
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add updated_at trigger
CREATE TRIGGER new_table_set_updated_at
  BEFORE UPDATE ON new_table
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 3. Enable RLS with staff policy
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON new_table
  FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- 4. Add to service_role policy if needed for webhooks
CREATE POLICY "service_role_full_access" ON new_table
  FOR ALL TO service_role USING (true) WITH CHECK (true);
```

---

## Summary

**Existing:** 22+ tables, 19 triggers, 20+ functions, 18 views, comprehensive RLS

**Planned:** 9 new tables, 10+ new views, 1+ new functions across Phases 1-6

**Architecture:** Supabase-first — business logic in functions/views, not application code

**Reference:** See STARHOUSE_MASTER_PLAN_v3.1.md for phase details and acceptance criteria
