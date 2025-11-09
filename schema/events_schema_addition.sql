-- ============================================================================
-- EVENTS MODULE - Schema Addition for Ticket Tailor Integration
-- ============================================================================
-- Add this to your existing Supabase schema for the Events module

-- ----------------------------------------------------------------------------
-- EVENTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event Details
    name text NOT NULL,
    description text,
    event_type text, -- e.g., 'retreat', 'workshop', 'conference', 'webinar'

    -- Date & Time
    start_date timestamptz NOT NULL,
    end_date timestamptz,
    timezone text DEFAULT 'UTC',

    -- Location
    venue_name text,
    venue_address text,
    city text,
    state text,
    country text,
    is_online boolean DEFAULT false,
    online_link text,

    -- Capacity
    total_capacity integer,
    spots_remaining integer,

    -- Pricing
    base_price numeric(12, 2),
    currency text DEFAULT 'USD',

    -- Status
    status text DEFAULT 'upcoming', -- 'upcoming', 'live', 'completed', 'cancelled'
    is_published boolean DEFAULT true,

    -- External IDs
    ticket_tailor_event_id text UNIQUE,
    kajabi_product_id uuid,

    -- Audit
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),

    -- Foreign Keys
    CONSTRAINT fk_events_product FOREIGN KEY (kajabi_product_id)
        REFERENCES products(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT events_status_check CHECK (status IN ('upcoming', 'live', 'completed', 'cancelled'))
);

-- ----------------------------------------------------------------------------
-- EVENT REGISTRATIONS (Ticket purchases)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_registrations (
    -- Primary Key
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    event_id uuid NOT NULL,
    contact_id uuid NOT NULL,

    -- Ticket Details
    ticket_type text, -- e.g., 'early_bird', 'vip', 'general_admission'
    quantity integer DEFAULT 1,
    total_paid numeric(12, 2),
    currency text DEFAULT 'USD',

    -- Status
    status text DEFAULT 'confirmed', -- 'confirmed', 'cancelled', 'refunded', 'waitlist'
    attended boolean DEFAULT false,
    checked_in_at timestamptz,

    -- External IDs
    ticket_tailor_booking_id text UNIQUE,
    transaction_id uuid, -- Link to transactions table if payment tracked

    -- Audit
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),

    -- Foreign Keys
    CONSTRAINT fk_event_registrations_event FOREIGN KEY (event_id)
        REFERENCES events(id) ON DELETE CASCADE,
    CONSTRAINT fk_event_registrations_contact FOREIGN KEY (contact_id)
        REFERENCES contacts(id) ON DELETE CASCADE,
    CONSTRAINT fk_event_registrations_transaction FOREIGN KEY (transaction_id)
        REFERENCES transactions(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT event_registrations_status_check CHECK (status IN ('confirmed', 'cancelled', 'refunded', 'waitlist')),
    CONSTRAINT event_registrations_quantity_check CHECK (quantity > 0),

    -- Prevent duplicate registrations
    UNIQUE(event_id, contact_id, ticket_tailor_booking_id)
);

-- ----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- ----------------------------------------------------------------------------

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_ticket_tailor ON events(ticket_tailor_event_id);
CREATE INDEX IF NOT EXISTS idx_events_upcoming ON events(start_date) WHERE status = 'upcoming';

-- Registration indexes
CREATE INDEX IF NOT EXISTS idx_registrations_event ON event_registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_registrations_contact ON event_registrations(contact_id);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON event_registrations(status);
CREATE INDEX IF NOT EXISTS idx_registrations_ticket_tailor ON event_registrations(ticket_tailor_booking_id);

-- ----------------------------------------------------------------------------
-- UPDATED_AT TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER set_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_event_registrations_updated_at
    BEFORE UPDATE ON event_registrations
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ----------------------------------------------------------------------------
-- USEFUL VIEWS
-- ----------------------------------------------------------------------------

-- View: Upcoming events with registration counts
CREATE OR REPLACE VIEW v_upcoming_events AS
SELECT
    e.id,
    e.name,
    e.start_date,
    e.end_date,
    e.venue_name,
    e.city,
    e.total_capacity,
    e.spots_remaining,
    e.base_price,
    COUNT(er.id) as total_registrations,
    COUNT(er.id) FILTER (WHERE er.status = 'confirmed') as confirmed_registrations,
    COUNT(er.id) FILTER (WHERE er.attended = true) as total_attended
FROM events e
LEFT JOIN event_registrations er ON e.id = er.event_id
WHERE e.status = 'upcoming' AND e.start_date > now()
GROUP BY e.id
ORDER BY e.start_date;

-- View: Contact event history
CREATE OR REPLACE VIEW v_contact_events AS
SELECT
    c.id as contact_id,
    c.email,
    c.first_name,
    c.last_name,
    e.id as event_id,
    e.name as event_name,
    e.start_date,
    er.ticket_type,
    er.status as registration_status,
    er.attended,
    er.total_paid
FROM contacts c
JOIN event_registrations er ON c.id = er.contact_id
JOIN events e ON er.event_id = e.id
ORDER BY e.start_date DESC;

-- ============================================================================
-- READY TO DEPLOY!
-- Run this in Supabase SQL Editor after the main schema
-- ============================================================================
