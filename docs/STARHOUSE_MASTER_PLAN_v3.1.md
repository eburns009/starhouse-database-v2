# StarHouse Platform - Master Development Plan v3.1

**Version:** 3.1  
**Date:** 2025-11-28  
**Author:** Senior Technical Advisor  
**Approved By:** Ed Burns (Tech Lead)

---

## Executive Summary

StarHouse Platform is a **staff-facing workflow and reporting layer** — not a full application rebuild. We leverage existing platforms for what they do best and build only what we must.

**Core Philosophy: Build Only What We Must**

| Platform | Their Job | Our Job |
|----------|-----------|---------|
| **Wix** | Public-facing: website, forms, payments, courses, email | Receive data via webhooks |
| **Stripe (via Wix)** | Payment processing, invoicing, subscriptions | Receive payment confirmations |
| **Supabase** | Database, Auth, RLS, Functions, Triggers, Views | Design schema, configure — not code |
| **Vercel** | Hosting, cron jobs, edge functions, monitoring | Configure — not code |
| **QuickBooks** | Accounting, financial records | Sync or manual reconciliation |
| **StarHouse** | **Workflow, relationships, staff UI, KPIs, reporting** | **BUILD THIS ONLY** |

---

## Data Source Matrix

| Module | Primary Source | Secondary Source | Webhook From | Already Imported? |
|--------|---------------|------------------|--------------|-------------------|
| **Contacts** | All sources | JotForm (enrichment) | Wix Forms | ✅ Mostly complete |
| **Events/Venue** | Wix (future) | Zoho Invoices (historical) | Wix Forms | ❌ Zoho Invoices missing |
| **School for Souls** | Ticket Tailor (in-person) | Kajabi/Wix (online) | Wix | ⚠️ Partial |
| **Membership** | Wix/Stripe (future) | PayPal (current) | Wix/Stripe | ⚠️ Partial |
| **Donors** | QuickBooks | JotForm, Wix (future) | Wix Forms | ✅ QB imported |

**Key Insight:** As Wix becomes the public platform, it becomes the primary webhook source for all new data. Historical data from Zoho, Kajabi, PayPal, Ticket Tailor imported for continuity only.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PUBLIC LAYER (Wix)                              │
│                                                                         │
│  • Website & Content          • Rental Inquiry Form                     │
│  • Donation Form              • Membership Signup                       │
│  • Course Enrollment          • Event/Workshop Registration             │
│  • Email Marketing            • Payment (Stripe)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Webhooks (Vercel Edge receives)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                               │
│                                                                         │
│  ┌─────────────────────────┐    ┌─────────────────────────────────┐    │
│  │        VERCEL           │    │          SUPABASE               │    │
│  │                         │    │                                 │    │
│  │  • Hosting (Next.js)    │    │  • PostgreSQL Database          │    │
│  │  • Edge Functions       │    │  • Auth (login, sessions)       │    │
│  │  • Cron Jobs            │    │  • RLS (permissions)            │    │
│  │  • Webhook Receivers    │    │  • Triggers (audit trails)      │    │
│  │  • Analytics            │    │  • Views (reports, health)      │    │
│  │                         │    │  • Functions (business logic)   │    │
│  │                         │    │  • Storage (files)              │    │
│  └─────────────────────────┘    └─────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STARHOUSE APPLICATION (What We Build)                │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Contacts   │  │   Events/   │  │ Membership  │  │   Donors    │    │
│  │   Module    │  │   Rentals   │  │   Module    │  │   Module    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                         │
│                          ┌─────────────┐                               │
│                          │ School for  │                               │
│                          │   Souls     │                               │
│                          └─────────────┘                               │
│                                                                         │
│  STAFF-ONLY CAPABILITIES:                                               │
│  • View & manage contacts         • Workflow state management          │
│  • Process inquiries → bookings   • Business rule enforcement          │
│  • Track memberships              • KPI dashboards                     │
│  • Manage donor relationships     • Reporting & exports                │
│  • Add notes, tags, roles         • Data quality tools                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Sync (manual or automated)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ACCOUNTING LAYER (QuickBooks)                      │
│                                                                         │
│  • Financial records    • Tax reporting    • Revenue by category       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## What We DON'T Build

| Capability | Use Instead | Notes |
|------------|-------------|-------|
| Public forms | Wix Forms | Inquiry, donation, registration forms |
| Payment processing | Stripe via Wix | Credit cards, subscriptions |
| Invoice generation | Wix or QuickBooks | Send invoices from there |
| Email marketing | Wix | Newsletters, campaigns |
| Course hosting | Wix | Online course delivery |
| User authentication | Supabase Auth | Login, sessions, password reset |
| Session management | Supabase Auth | JWT tokens handled |
| Row-level security | Supabase RLS | Already configured |
| Audit trails | Supabase Triggers | `set_updated_at`, `set_updated_by` exist |
| Duplicate detection | Supabase Views | `v_potential_duplicate_*` exist |
| Health monitoring | Supabase Functions | `daily_health_check()` exists |
| Scheduled jobs | Vercel Cron | Config only, no code |
| Webhook receivers | Vercel Edge Functions | Fast, simple |
| File storage | Supabase Storage | If needed |
| Hosting & deployment | Vercel | Automatic |

---

## What We BUILD

| Capability | Why We Build It |
|------------|-----------------|
| **Staff UI** | Internal interface for operations |
| **Contact Management** | Central identity across all data sources |
| **Workflow Management** | Inquiry → Booking → Confirmed → Completed |
| **Relationship Views** | See all of a contact's activity in one place |
| **Business Rule Enforcement** | Membership validation, Program Partner rules |
| **KPI Dashboards** | Metrics that matter to operations |
| **Reporting & Exports** | Data staff needs to make decisions |
| **Data Quality Tools** | Merge duplicates, enrich contacts |
| **Notes & Tags** | Staff annotations on contacts |

---

## Platform Capabilities Reference

### Wix (Research Needed)

| Capability | Available? | Webhook/API? | StarHouse Receives |
|------------|------------|--------------|-------------------|
| Forms | ✅ Yes | ? | Form submissions |
| Payments (Stripe) | ✅ Yes | ? | Payment confirmations |
| Subscriptions | ? | ? | Membership changes |
| Invoicing | ? | ? | Invoice status |
| Courses | ? | ? | Enrollments |
| Events/Tickets | ? | ? | Registrations |
| Email Marketing | ✅ Yes | ? | (May not need) |

**Action:** Research Wix webhook/API capabilities before finalizing module designs.

---

### Supabase (Already Available)

| Feature | Status | Use For |
|---------|--------|---------|
| PostgreSQL | ✅ Active | All data storage |
| Auth | ✅ Configured | Staff login |
| RLS Policies | ✅ Configured | Permission enforcement |
| Triggers | ✅ 19 defined | Audit trails, timestamps |
| Functions | ✅ 20+ defined | Business logic, health checks |
| Views | ✅ 15+ defined | Reports, duplicate detection |
| Extensions | ✅ Active | `uuid-ossp`, `citext`, `pg_trgm` |
| Storage | ✅ Available | File uploads if needed |
| Realtime | ✅ Available | Live updates (if needed) |

---

### Vercel (Available)

| Feature | Use For | Configuration |
|---------|---------|---------------|
| Hosting | Next.js app | ✅ Already configured |
| Edge Functions | Webhook receivers | Simple API routes |
| Cron Jobs | Scheduled tasks | `vercel.json` config |
| Analytics | Usage tracking | Enable in dashboard |
| Speed Insights | Performance | Enable in dashboard |
| Preview Deploys | PR testing | ✅ Automatic |

**Vercel Cron Setup:**
```json
{
  "crons": [
    {
      "path": "/api/cron/daily-health-check",
      "schedule": "0 6 * * *"
    },
    {
      "path": "/api/cron/membership-expiry-alerts",
      "schedule": "0 8 * * 1"
    },
    {
      "path": "/api/cron/cleanup-old-webhooks",
      "schedule": "0 0 * * 0"
    }
  ]
}
```

---

## Business Process Audit Template

*Use this template for each module before building.*

### Module: [Name]

**Current State:**
1. What platform(s) are used today?
2. Who uses it? (Which staff roles?)
3. How often is it used?

**Workflow:**
1. How does the process start?
2. What information is collected?
3. What decisions are made?
4. What actions are taken?
5. How does it end?
6. What follow-up happens?

**Pain Points:**
1. What's frustrating about the current process?
2. What takes too long?
3. What errors happen frequently?
4. What information is hard to find?

**Requirements:**
1. What MUST the new system do?
2. What SHOULD it do (nice to have)?
3. What reporting is needed?
4. What integrations are needed?

**Success Criteria:**
1. How will we know the module is working?
2. What metrics matter?
3. When can we turn off the old platform?

---

## Platform Elimination Checklist

*Use for each platform being replaced.*

### Platform: [Name]

**Pre-Elimination:**
- [ ] New module captures all required data
- [ ] Staff trained on new workflow
- [ ] Historical data imported (if required)
- [ ] Reporting meets or exceeds old platform
- [ ] 2 weeks parallel operation successful

**Elimination:**
- [ ] All new work done in StarHouse
- [ ] Old platform set to read-only
- [ ] Final data export archived
- [ ] Subscription/account cancelled
- [ ] Documentation updated

**Post-Elimination:**
- [ ] Monitor for issues (2 weeks)
- [ ] Staff feedback collected
- [ ] Iteration on pain points

---

## Development Phases

---

### Phase 0: Data Integrity & Auth Foundation
**Timeline:** Week 1-2  
**Build:** Minimal — mostly configuration and fixes

---

#### 0.1 P0: Fix Duplicate Transactions
**Estimate:** 2-4 hours

**This is data cleanup, not building.**

```sql
-- Diagnostic
SELECT * FROM v_potential_duplicate_transactions LIMIT 20;

-- Find duplicates by QuickBooks invoice
SELECT 
  quickbooks_invoice_num, 
  contact_id, 
  amount, 
  transaction_date, 
  COUNT(*) as dupe_count
FROM transactions
WHERE is_donation = true
  AND deleted_at IS NULL
GROUP BY quickbooks_invoice_num, contact_id, amount, transaction_date
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 20;
```

**Requirements before fix:**
- [ ] Root cause identified
- [ ] Backup created
- [ ] DRY-RUN count shown
- [ ] Ed approval

**Acceptance Criteria:**
- [ ] Root cause documented
- [ ] Duplicates removed
- [ ] Prevention mechanism confirmed
- [ ] Zero duplicates verified via `v_potential_duplicate_transactions`

---

#### 0.2 Complete Supabase Auth
**Estimate:** 4-6 hours

**This is configuration, not building.**

- [ ] Audit current custom auth code
- [ ] Remove custom staff/session tables if any
- [ ] Verify Supabase Auth works
- [ ] Verify RLS policies work with `auth.uid()`
- [ ] Test login → data access → logout

**Use Supabase Auth UI components if possible** — don't build custom login forms.

**Acceptance Criteria:**
- [ ] Staff can log in via Supabase Auth
- [ ] RLS policies work with `auth.uid()`
- [ ] No custom session management remains
- [ ] Anon users blocked from all data

---

### Phase 1: Contact Foundation
**Timeline:** Week 2-3  
**Build:** Staff UI for contact management

---

#### 1.1 Edit Contact Function
**Estimate:** 3-4 hours

**Build:** Modal or inline edit form

**Fields to edit:**
- Name (first, last, full)
- Primary email
- Primary phone
- Primary address
- Business name (add field if missing)

**Don't build:** Validation logic in app — use database constraints

```sql
-- Supabase handles via constraints
ALTER TABLE contacts 
ADD CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Add business_name if missing
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS business_name TEXT;
```

---

#### 1.2 Multi-Email/Phone/Address UI
**Estimate:** 4-6 hours

**Build:** UI to display and manage related records

**Don't build:** 
- Duplicate email prevention — Supabase constraints exist
- Audit trails — Supabase triggers exist

**Schema additions (if needed):**
```sql
-- contact_phones (if doesn't exist)
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

-- contact_addresses (if doesn't exist)
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
  is_mailing BOOLEAN DEFAULT false, -- Use for mail campaigns
  is_verified BOOLEAN DEFAULT false,
  source_system TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add triggers (use existing pattern)
CREATE TRIGGER contact_phones_set_updated_at
  BEFORE UPDATE ON contact_phones
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER contact_addresses_set_updated_at
  BEFORE UPDATE ON contact_addresses
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Add RLS (use existing pattern)
ALTER TABLE contact_phones ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_addresses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON contact_phones FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "staff_full_access" ON contact_addresses FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

#### 1.3 Address Strategy for Mailing Campaigns
**Estimate:** 1 hour

**Decision:** Which address to use for mail campaigns?

**Implementation:**
- `is_mailing` flag on addresses (schema above)
- Default: most recently updated, verified address
- Staff can override per contact
- Export uses `is_mailing = true`

---

#### 1.4 Display Kajabi Tags
**Estimate:** 2 hours

**Current State:** Tags imported from Kajabi exist in `tags` and `contact_tags`

**Build:** 
- Display tags on contact card
- Filter contacts by tag
- Show tag source (Kajabi vs manual)

**Don't build:** Tag management UI yet — display only for now

---

#### 1.5 Display Purchase History ("What was purchased")
**Estimate:** 2-3 hours

**From original outline:** "Find a way to change purchase to what was purchased"

**Build:** 
- Contact card section showing products purchased
- Pull from `contact_products` and `transactions` with `product_id`
- Show product name, date, amount

**Supabase view:**
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

---

#### 1.6 Deduplication UI
**Estimate:** 2-3 hours

**Build:** UI to review and merge duplicates

**Don't build:** Duplicate detection — `v_potential_duplicate_contacts` view exists

**UI Flow:**
1. Display results from existing view
2. Show side-by-side comparison
3. Select winner, merge action
4. Supabase function handles merge logic

**Current backlog:** 66 duplicate contact sets

---

#### 1.7 Contact Card Redesign
**Estimate:** 3-4 hours

**Build:** Unified contact view showing all relationships

**Key Features:**
- Display `business_name` in header (field added in 1.1)
- Reusable `ContactCard` component for use across all modules (Donors, Members, Events)
- Edit button opens ContactEditModal

```
┌─────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                  │
│ Name | Business Name | Primary Email | Primary Phone | Primary Address │
│ [Edit Button]                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ LEFT COLUMN                    │ RIGHT COLUMN                          │
│────────────────────────────────│───────────────────────────────────────│
│ All Emails (source badges)     │ Transaction History                   │
│ All Phones (type labels)       │  • Donations                          │
│ All Addresses (mailing flag)   │  • Purchases (product names!)         │
│                                │  • Subscriptions                      │
│ Tags (Kajabi + manual)         │                                       │
│ Roles                          │ Event Registrations                   │
│ External IDs                   │                                       │
│                                │ Membership Status                     │
│ Notes (staff)                  │ Course Enrollments                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Supabase view for 360° contact:**
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

---

#### 1.8 Review Other Platforms for UI Best Practices
**Estimate:** 2 hours (research task)

**From original outline:** "Review other platforms and best principles to see if we can redesign UI for very easy user experience"

**Action:** Before finalizing Contact Card UI, review:
- HubSpot contact view
- Salesforce contact view
- Zoho CRM contact view
- Identify patterns that work well

**Deliverable:** UI recommendations document

---

**Phase 1 Acceptance Criteria:**
- [ ] Edit contact works (including business name)
- [ ] Multi-email/phone/address UI functional
- [ ] Mailing address flag works
- [ ] Kajabi tags display
- [ ] Purchase history displays with product names
- [ ] Duplicate merge UI works
- [ ] 66 duplicate sets resolved
- [ ] Contact card redesign deployed

---

### Phase 2: Donor Module — Functional Complete
**Timeline:** Week 3-4  
**Build:** Staff UI for donor management

---

#### 2.1 Complete Remaining Imports
**Estimate:** 4-6 hours

**Current State:**
- 672 donors imported
- 356 need contacts created
- 17 joint donors need strategy

**Tasks:**
1. Create contacts for 356 unmatched donors
2. Joint donor decision: household or split?
3. Import remaining donors
4. Verify totals match QuickBooks

**Target:** ~1,000 total donors

---

#### 2.2 Donor List UI
**Estimate:** 2-3 hours

**Build:** 
- Sortable columns (click header)
- Phone column in list view
- Pagination (50 rows, "Show All" option)
- Filter: donors missing email/phone/address
- Export CSV for enrichment

**Don't build:** 
- Sorting logic — use Supabase query `ORDER BY`
- Filtering logic — use Supabase query `WHERE`
- Pagination — use Supabase `.range()`

---

#### 2.3 Donor Classification
**Estimate:** 1 hour

**Don't build in app — use Supabase view:**

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

**UI:** Badge showing donor level, filter by level

---

#### 2.4 Manual Donation Entry
**Estimate:** 2-3 hours

**Build:** Simple form for staff to record donations

**Fields:**
- Select contact (search/autocomplete)
- Amount
- Date
- Payment method
- Notes
- Campaign (optional — for Phase 6)

**Don't build:**
- Duplicate checking — Supabase constraint handles
- Audit trail — Supabase trigger handles

---

#### 2.5 Fix "nan" Donor Names
**Estimate:** 1-2 hours

**Issue:** Some donors display "nan" as first/last name from QuickBooks import

**Investigation:**
1. Query contacts with `first_name = 'nan'` or `last_name = 'nan'`
2. Check source data in QuickBooks export
3. Determine if these are business names incorrectly parsed

**Fix:**
- Correct data in database (manual or script)
- Update import script to handle "nan" values as NULL
- Business names should populate `business_name` field, not name fields

---

#### 2.6 Prevention Trigger for NULL external_transaction_id
**Estimate:** 1-2 hours

**Issue:** Duplicate transactions occur when `external_transaction_id` is NULL

**Build:** Database constraint or trigger to prevent inserts with NULL external_transaction_id for donation transactions

```sql
-- Option 1: Constraint (stricter)
ALTER TABLE transactions
ADD CONSTRAINT require_external_id_for_donations
CHECK (NOT is_donation OR external_transaction_id IS NOT NULL);

-- Option 2: Trigger (allows soft enforcement with logging)
CREATE OR REPLACE FUNCTION check_donation_external_id()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.is_donation = true AND NEW.external_transaction_id IS NULL THEN
    RAISE WARNING 'Donation transaction inserted without external_transaction_id: %', NEW.id;
    -- Or RAISE EXCEPTION to block the insert
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_donation_external_id
BEFORE INSERT ON transactions
FOR EACH ROW EXECUTE FUNCTION check_donation_external_id();
```

---

**Phase 2 Acceptance Criteria:**
- [ ] ~1,000 donors imported
- [ ] Zero duplicate transactions
- [ ] List view with sort/filter/pagination
- [ ] Donor classification badges
- [ ] Manual entry works
- [ ] Export works
- [ ] No "nan" donor names displayed
- [ ] NULL external_transaction_id prevention active

**DEFERRED to Phase 6:**
- Campaign tracking
- Phone-a-thon module
- Direct mail campaigns
- Acknowledgment sending

---

### Phase 3: Events Module — Zoho Replacement
**Timeline:** Week 4-7  
**Build:** Staff workflow UI for event/rental management  
**Goal:** Eliminate Zoho

---

#### 3.1 Business Process Audit
**Estimate:** 2-3 hours (conversation with Ed)

**Use template above. Key questions:**

**Current Workflow:**
1. How does a rental inquiry arrive today? (Email? Zoho form? Phone?)
2. What information is collected at inquiry?
3. How is venue availability checked?
4. How is pricing determined?
5. How is the quote/invoice sent? (Zoho? QuickBooks?)
6. How is payment tracked?
7. How is the booking confirmed?
8. What happens day-of? (Check-in, setup?)
9. What follow-up happens after?

**Pain Points:**
1. What's frustrating about the current Zoho workflow?
2. What manual steps could be automated?
3. What information is hard to find or report on?

**Business Challenges:**
1. Program Partners must be members to rent — how is this enforced today?
2. How are rental date limits tracked per membership level?

**Deliverable:** Business Process Document

---

#### 3.2 Wix Integration Research
**Estimate:** 2-4 hours

**Determine:**
| Question | Answer |
|----------|--------|
| Does Wix have rental inquiry forms? | ? |
| Can Wix send webhooks on form submission? | ? |
| Does Wix/Stripe handle invoicing? | ? |
| Can Wix send webhooks on payment? | ? |
| What data fields does Wix form include? | ? |

**Deliverable:** Integration specification document

---

#### 3.3 Data Audit: Current Zoho Footprint
**Estimate:** 2-3 hours

```sql
-- Zoho-sourced transactions
SELECT source_system, COUNT(*), MIN(created_at), MAX(created_at)
FROM transactions
WHERE source_system ILIKE '%zoho%'
GROUP BY source_system;

-- Zoho-linked contacts
SELECT COUNT(*) FROM contacts WHERE zoho_id IS NOT NULL;

-- Any events from Zoho?
SELECT COUNT(*) FROM events WHERE source_system ILIKE '%zoho%';
```

**Also needed:**
- Zoho Invoices export (Ed to provide)
- Compare Invoices vs Sales Orders
- Field mapping

**Deliverable:** Data Audit Report

---

#### 3.4 Schema Design
**Estimate:** 2-3 hours

```sql
-- Venues/Spaces
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

-- Booking Inquiries (from Wix webhook)
CREATE TABLE IF NOT EXISTS booking_inquiries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source TEXT DEFAULT 'wix',
  
  -- Contact info (may or may not match existing contact)
  contact_name TEXT,
  contact_email TEXT,
  contact_phone TEXT,
  contact_id UUID REFERENCES contacts(id), -- Linked after staff review
  
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

-- Bookings (staff-managed)
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
  invoice_reference TEXT, -- Wix or QB invoice ID
  payment_received BOOLEAN DEFAULT false,
  payment_received_at TIMESTAMPTZ,
  payment_reference TEXT, -- Stripe payment ID
  
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

-- Triggers
CREATE TRIGGER venues_set_updated_at BEFORE UPDATE ON venues FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER booking_inquiries_set_updated_at BEFORE UPDATE ON booking_inquiries FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER bookings_set_updated_at BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_inquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON venues FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "staff_full_access" ON booking_inquiries FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "staff_full_access" ON bookings FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

#### 3.5 Webhook Receiver
**Estimate:** 2-3 hours

**Build:** Vercel Edge Function to receive Wix webhooks

```typescript
// /api/webhooks/wix/rental-inquiry.ts
import { NextRequest } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const config = { runtime: 'edge' };

export default async function handler(req: NextRequest) {
  const payload = await req.json();
  
  // Validate webhook signature (Wix-specific)
  // ...
  
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
  
  const { error } = await supabase.from('booking_inquiries').insert({
    source: 'wix',
    contact_name: payload.name,
    contact_email: payload.email,
    contact_phone: payload.phone,
    event_name: payload.eventName,
    event_type: payload.eventType,
    venue_requested: payload.venue,
    requested_date: payload.date,
    message: payload.message,
    raw_payload: payload,
    status: 'new'
  });
  
  if (error) {
    console.error('Webhook insert error:', error);
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
  
  return new Response(JSON.stringify({ received: true }), { status: 200 });
}
```

---

#### 3.6 Staff UI Build
**Estimate:** 8-12 hours

**Inquiry Queue:**
- List of new inquiries (from Wix webhook)
- Status badges (new, contacted, converted, declined)
- Click to review details
- Action: Link to existing contact or create new
- Action: Convert to booking or decline

**Booking Management:**
- List of bookings by status
- Filter by date range, status, venue
- Search by contact name
- Calendar view (optional but valuable)

**Booking Detail View:**
- Full booking information
- Contact card link
- Payment status indicators
- Membership verification status (auto-check via `is_current_member()`)
- Timeline/history of status changes
- Staff notes

**Create/Edit Booking:**
- Select contact (or create new)
- Select venue
- Date/time picker
- Auto-calculate pricing based on venue rates
- Membership validation check (warning if not member)
- Save as tentative/confirmed

**Don't build:**
- Invoice generation — Wix or QuickBooks does this
- Payment collection — Stripe via Wix does this
- Email notifications — Wix does this

---

#### 3.7 Membership Validation for Bookings
**Estimate:** 2-3 hours

**Business Rule:** Program Partners must be members to rent

**Implementation:**
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

**UI:** 
- Auto-run validation when contact selected
- Warning banner if not valid
- Override option with required reason

---

#### 3.8 Events KPI Dashboard
**Estimate:** 2-3 hours

**Supabase view:**
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

**UI:** Dashboard widget displaying these metrics

---

#### 3.9 Historical Import (Optional)
**Estimate:** 4-6 hours

**Only after UI is functional:**
- Import Zoho Invoices → bookings table
- Map to contacts via `zoho_id` or email match
- Mark as `status = 'completed'`

**This is optional** — prioritize capturing new data over perfect history.

---

#### 3.10 Zoho Elimination

**Use Platform Elimination Checklist above.**

**Zoho can be turned off when:**
- [ ] Wix inquiry form live and sending webhooks
- [ ] Staff processing inquiries in StarHouse
- [ ] Staff managing bookings in StarHouse
- [ ] Invoices sent via Wix or QuickBooks (not Zoho)
- [ ] Historical data imported (if required)
- [ ] Staff trained on new workflow
- [ ] 2 weeks parallel operation successful

---

**Phase 3 Acceptance Criteria:**
- [ ] Business process documented
- [ ] Wix webhook receiving inquiries
- [ ] Schema implemented
- [ ] Inquiry → Booking workflow functional
- [ ] Booking status management works
- [ ] Membership validation works
- [ ] Calendar view works (if built)
- [ ] KPI dashboard shows metrics
- [ ] Historical import complete (if needed)
- [ ] **Zoho eliminated**

---

### Phase 4: Membership Module
**Timeline:** Week 7-9  
**Build:** Staff UI for membership management  
**Goal:** Centralized membership view, Program Partner enforcement

---

#### 4.1 Business Process Audit
**Estimate:** 2-3 hours

**Key Questions:**
1. How do people sign up for membership today? (Kajabi? Wix?)
2. What membership levels exist?
3. How are Individual vs Program Partner distinguished?
4. How are renewals handled?
5. What happens when membership expires?
6. How is Program Partner rental limit tracked?

---

#### 4.2 Data Source Decision
**Current options:**
- Kajabi — current membership management
- PayPal — subscription payments
- QuickBooks — financial record
- Wix/Stripe — future

**Recommendation for transition:**
1. **Now:** PayPal subscriptions = source of truth for payment status
2. **Future:** Wix/Stripe subscriptions = source of truth
3. **Always:** StarHouse = operational view combining all sources

---

#### 4.3 Membership Levels Schema
**Estimate:** 2 hours

**Review existing `products` table for membership products.**

**Add membership-specific fields if needed:**
```sql
-- Add to products table or create membership_levels table
ALTER TABLE products ADD COLUMN IF NOT EXISTS membership_type TEXT CHECK (membership_type IN ('individual', 'program_partner'));
ALTER TABLE products ADD COLUMN IF NOT EXISTS rental_dates_allowed INT; -- For Program Partners
ALTER TABLE products ADD COLUMN IF NOT EXISTS rental_priority INT; -- Higher = more priority
```

---

#### 4.4 Wix/Stripe Subscription Webhook
**Estimate:** 3-4 hours

**Build:** Webhook receiver for subscription events

```typescript
// /api/webhooks/stripe/subscription.ts
export default async function handler(req: NextRequest) {
  const event = await req.json();
  
  switch (event.type) {
    case 'customer.subscription.created':
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted':
      // Update subscription in Supabase
      break;
  }
}
```

---

#### 4.5 Membership Status View
**Estimate:** 3-4 hours

**Don't build logic — use existing Supabase functions:**
- `is_current_member(uuid)` — already exists
- `get_membership_status(uuid)` — already exists
- `v_active_members` — already exists
- `v_membership_metrics` — already exists

**Build:** UI that displays these

**Member List View:**
- All active members
- Filter by level (Individual, Program Partner)
- Filter by expiring soon (30/60/90 days)
- Search by name/email

**Member Detail (on Contact Card):**
- Current status
- Level
- Start date, renewal date
- Payment history
- Rental dates used (for Program Partners)

---

#### 4.6 Program Partner Rental Tracking
**Estimate:** 3-4 hours

**Business Rule:** Higher Program Partner levels get more rental dates

**Schema:**
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

**UI:**
- Display rentals used vs allowed
- Warning when approaching limit
- Integrate with booking validation

---

#### 4.7 Membership Conversion Challenge
**Estimate:** 2-3 hours

**Business Challenge:** Convert Individual members with rentals to Program Partner

**Build view to identify:**
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

**UI:**
- List view of members needing upgrade
- Quick action to flag/contact
- Track conversion status

---

#### 4.8 Expiring Memberships & Alerts
**Estimate:** 2-3 hours

**Supabase view:**
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

**Vercel Cron:**
```json
{
  "path": "/api/cron/membership-expiry-alerts",
  "schedule": "0 8 * * 1"
}
```

**UI:** Dashboard widget showing expiring memberships

---

#### 4.9 Past Members History
**Estimate:** 2 hours

**Build:** View past members and their history

**Use existing data:**
- `subscriptions` with `status IN ('cancelled', 'expired')`
- `contact_roles` with `ended_at IS NOT NULL`

**UI:**
- Tab or filter for "Past Members"
- Show membership history timeline per contact
- Useful for reactivation campaigns

---

#### 4.10 Membership Dashboard
**Estimate:** 2-3 hours

**Leverage existing views:**
- `v_membership_metrics` (exists)
- `v_active_members` (exists)
- `v_memberships_expiring` (new)
- `v_members_needing_upgrade` (new)

**Dashboard widgets:**
- Total active members by level
- New members this month
- Expiring soon count
- Members needing upgrade count
- Revenue by level (if trackable)

---

**Phase 4 Acceptance Criteria:**
- [ ] Business process documented
- [ ] Webhook receiving subscription events
- [ ] All membership levels defined with rental limits
- [ ] Individual vs Program Partner distinguished
- [ ] Active member list accurate
- [ ] Rental usage tracked for Program Partners
- [ ] Members needing upgrade identified
- [ ] Expiring members flagged
- [ ] Past members viewable
- [ ] Dashboard shows membership KPIs
- [ ] Events module validates membership

---

### Phase 5: School for Souls Module
**Timeline:** Week 9-11  
**Build:** Enrollment tracking and course management UI  
**Goal:** Visibility into courses/workshops, eliminate Ticket Tailor dependency

---

#### 5.1 Business Process Audit
**Estimate:** 2-3 hours

**Key Questions:**
1. What types of offerings exist?
   - In-person workshops (Ticket Tailor)
   - Online courses (Kajabi → Wix)
   - Hybrid?
2. How do people register today?
3. What's tracked per participant?
4. How is attendance recorded (in-person)?
5. What reporting does staff need?
6. What are the pain points?

**Deliverable:** Business Process Document

---

#### 5.2 Data Sources Analysis
**Estimate:** 2-3 hours

**Two distinct sources:**

| Source | Type | Data Available |
|--------|------|----------------|
| **Ticket Tailor** | In-person events | Event details, registrations, attendance |
| **Kajabi → Wix** | Online courses | Course catalog, enrollments, progress |

**Current schema:**
- `products` table — courses exist here
- `contact_products` — enrollment records
- `events` table — Ticket Tailor events
- `event_registrations` — ticket purchases

**Question:** Is existing schema sufficient, or do we need:
- Course-specific fields (duration, modules, completion)?
- Attendance tracking table?
- Certificate/completion records?

---

#### 5.3 Wix Course Integration Research
**Estimate:** 2-3 hours

**Determine:**
| Question | Answer |
|----------|--------|
| Does Wix host online courses? | ? |
| Can Wix send enrollment webhooks? | ? |
| Does Wix track course progress? | ? |
| Can Wix send completion webhooks? | ? |

**Deliverable:** Integration specification

---

#### 5.4 Ticket Tailor Integration Review
**Estimate:** 2 hours

**Current state:** Some Ticket Tailor data imported

**Review:**
- What's already in `events` table?
- What's in `event_registrations`?
- Is webhook integration active?
- What's missing?

---

#### 5.5 Schema Additions (If Needed)
**Estimate:** 2-3 hours

```sql
-- Add course-specific fields to products (if needed)
ALTER TABLE products ADD COLUMN IF NOT EXISTS course_type TEXT CHECK (course_type IN ('in_person', 'online', 'hybrid'));
ALTER TABLE products ADD COLUMN IF NOT EXISTS duration_hours DECIMAL(5,2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS max_participants INT;

-- Course enrollments with progress (if Wix provides this)
CREATE TABLE IF NOT EXISTS course_enrollments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  
  -- Enrollment
  enrolled_at TIMESTAMPTZ DEFAULT NOW(),
  source TEXT, -- 'wix', 'ticket_tailor', 'manual'
  
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

-- Triggers & RLS
CREATE TRIGGER course_enrollments_set_updated_at BEFORE UPDATE ON course_enrollments FOR EACH ROW EXECUTE FUNCTION set_updated_at();
ALTER TABLE course_enrollments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON course_enrollments FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

#### 5.6 Webhook Receivers
**Estimate:** 3-4 hours

**Wix course enrollment:**
```typescript
// /api/webhooks/wix/course-enrollment.ts
export default async function handler(req: NextRequest) {
  const payload = await req.json();
  
  // Find or create contact
  // Create enrollment record
  // Link to product
}
```

**Ticket Tailor registration (if not already active):**
```typescript
// /api/webhooks/tickettailor/registration.ts
export default async function handler(req: NextRequest) {
  const payload = await req.json();
  
  // Find or create contact
  // Create event_registration record
}
```

---

#### 5.7 Staff UI Build
**Estimate:** 6-8 hours

**Course/Workshop List:**
- All products with `product_type = 'course'` or similar
- Filter: in-person vs online
- Filter: upcoming vs past
- Enrollment count per course

**Course Detail View:**
- Course information
- Enrollment list with status
- Attendance tracking (in-person)
- Completion tracking (online)

**Contact's Course History (on Contact Card):**
- Courses enrolled
- Attendance record
- Completions

**Don't build:**
- Course content delivery — Wix does this
- Registration forms — Wix does this
- Payment — Stripe via Wix does this

---

#### 5.8 Attendance Tracking (In-Person)
**Estimate:** 2-3 hours

**Build:** Simple attendance UI for in-person events

**UI:**
- Event detail shows registration list
- Checkbox for attended
- Notes field
- Bulk mark attendance

---

#### 5.9 School for Souls Dashboard
**Estimate:** 2-3 hours

**Supabase views:**
```sql
-- Top products by enrollment
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

-- School for Souls KPIs
CREATE OR REPLACE VIEW v_school_kpi AS
SELECT
  (SELECT COUNT(DISTINCT contact_id) FROM course_enrollments WHERE enrolled_at >= date_trunc('year', NOW())) as ytd_students,
  (SELECT COUNT(*) FROM course_enrollments WHERE enrolled_at >= NOW() - INTERVAL '30 days') as enrollments_30_days,
  (SELECT COUNT(*) FROM course_enrollments WHERE completed AND completed_at >= date_trunc('year', NOW())) as ytd_completions,
  (SELECT COUNT(*) FROM events WHERE start_datetime BETWEEN NOW() AND NOW() + INTERVAL '30 days') as upcoming_events;
```

**Dashboard widgets:**
- Top 5 courses (by enrollment or revenue)
- YTD students
- Upcoming workshops/events
- Recent enrollments

---

#### 5.10 Ticket Tailor Elimination Criteria

**Ticket Tailor can be reduced/eliminated when:**
- [ ] Wix handles event registration
- [ ] Webhooks flowing to StarHouse
- [ ] Staff can view registrations in StarHouse
- [ ] Attendance tracking works
- [ ] Reporting meets needs
- [ ] 2 weeks parallel operation

**Note:** Ticket Tailor may remain for ticket scanning/check-in functionality. Evaluate whether Wix can replace this.

---

**Phase 5 Acceptance Criteria:**
- [ ] Business process documented
- [ ] In-person vs online offerings distinguished
- [ ] Wix enrollment webhook receiving
- [ ] Ticket Tailor integration verified
- [ ] Course list with enrollment counts
- [ ] Attendance tracking for in-person events
- [ ] Course history on contact card
- [ ] Top 5 products on dashboard
- [ ] School for Souls KPIs displayed
- [ ] Ticket Tailor dependency reduced

---

### Phase 6: Donor Module — Advanced Features
**Timeline:** Week 11-13  
**Build:** Campaign management, phone-a-thon, acknowledgments

---

#### 6.1 Campaign Schema
**Estimate:** 1-2 hours

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

-- Triggers & RLS
CREATE TRIGGER campaigns_set_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER campaign_contacts_set_updated_at BEFORE UPDATE ON campaign_contacts FOR EACH ROW EXECUTE FUNCTION set_updated_at();
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_contacts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON campaigns FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "staff_full_access" ON campaign_contacts FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

#### 6.2 Campaign Management UI
**Estimate:** 4-6 hours

**Build:**
- Create/edit campaigns
- Set goal, dates, type
- Add contacts to campaign (from donor filters)
- View campaign progress
- Campaign results dashboard

---

#### 6.3 Phone-a-thon UI
**Estimate:** 4-6 hours

**Build:**
- Call list view (filtered by campaign)
- "Next call" workflow
- Record outcome per attempt
- Pledge entry
- Link pledge to donation when fulfilled

**Call outcomes:**
- No answer
- Left voicemail
- Spoke - not interested
- Spoke - considering
- Spoke - pledged
- Wrong number
- Do not call

---

#### 6.4 Direct Mail Campaign Support
**Estimate:** 2-3 hours

**Build:**
- Select donors by criteria
- Filter by `is_mailing = true` addresses
- Export CSV with mailing addresses
- Track who was mailed (mark in campaign_contacts)

**Don't build:** Mail merge — use external tool

---

#### 6.5 Acknowledgment Tracking
**Estimate:** 3-4 hours

**Schema:**
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
```

**Build:**
- Acknowledgment queue (donations needing thank-you)
- Mark as sent (manual tracking)
- Integration with Wix email (future)

**Don't build:** Email sending — Wix does this

---

#### 6.6 Donor Campaign KPIs
**Estimate:** 2 hours

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

**Phase 6 Acceptance Criteria:**
- [ ] Campaign CRUD works
- [ ] Contacts can be added to campaigns
- [ ] Phone-a-thon workflow functional
- [ ] Call outcomes tracked
- [ ] Pledges tracked and linked to donations
- [ ] Direct mail export works
- [ ] Acknowledgment queue works
- [ ] Campaign KPIs displayed

---

### Phase 7: Dashboard & Polish
**Timeline:** Week 13-14

---

#### 7.1 Main Dashboard Redesign

**From original outline:**
- [ ] Remove mailing list widget
- [ ] Contacts: 2-3 updating stats
- [ ] Membership: simple stats
- [ ] Donors: YTD totals, donor count
- [ ] Events: upcoming, year total
- [ ] School for Souls: top 5 products
- [ ] Staff: keep same

**Widget sources:**

| Widget | Source View |
|--------|-------------|
| Contacts stats | `v_contact_summary` (exists) |
| Donor YTD | `v_donor_classification` |
| Events upcoming | `v_events_kpi` |
| Membership | `v_membership_metrics` (exists) |
| School for Souls | `v_top_courses` |
| Health | `v_database_health` (exists) |

---

#### 7.2 Cross-Module Polish
- [ ] Consistent loading states
- [ ] Error handling
- [ ] Empty states with helpful messages
- [ ] Mobile responsiveness
- [ ] Keyboard navigation
- [ ] Accessibility basics

---

#### 7.3 Documentation
- [ ] Update README
- [ ] Staff user guide
- [ ] Webhook documentation
- [ ] Schema documentation

---

#### 7.4 Staff Management UI
**Estimate:** 4-6 hours

**Build:** Admin interface for managing staff users

**Features:**
- List all staff users (from Supabase Auth)
- Invite new staff (send Supabase Auth invite)
- View last login, activity
- Disable/enable staff accounts
- Role assignment (if roles beyond basic staff are needed)

**Don't build:**
- Auth system — use Supabase Auth
- Password management — Supabase handles via magic links/password reset

**UI:**
- Staff list with status badges (active, disabled)
- "Invite Staff" button → enters email, sends invite
- Click staff row to view details/activity

---

**Phase 7 Acceptance Criteria:**
- [ ] Dashboard shows all module KPIs
- [ ] No mailing list widget
- [ ] Consistent UI across modules
- [ ] Mobile-friendly
- [ ] Documentation complete
- [ ] Staff management UI functional

---

## Definition of Done: Module Summary

| Module | Key Criteria | Platform Eliminated |
|--------|--------------|---------------------|
| **Contacts** | Edit works, multi-field, dedup resolved, 360° view | — |
| **Donors (basic)** | 1,000 imported, 0 duplicates, manual entry works | — |
| **Events** | Webhook receiving, workflow functional, KPIs | **Zoho** |
| **Membership** | Status accurate, Program Partner tracked, expiry alerts | **Kajabi** (for membership) |
| **School for Souls** | Enrollments tracked, attendance works, top 5 on dashboard | **Ticket Tailor** (reduced) |
| **Donors (advanced)** | Campaigns, phone-a-thon, acknowledgments | **JotForm** |
| **Dashboard** | All KPIs visible, polished UI | — |

---

## Summary: Build vs Configure vs Use

| Need | Approach | Platform |
|------|----------|----------|
| Public forms | USE | Wix |
| Payment processing | USE | Stripe via Wix |
| Invoice sending | USE | Wix or QuickBooks |
| Email marketing | USE | Wix |
| Course hosting | USE | Wix |
| User auth | CONFIGURE | Supabase Auth |
| Database | CONFIGURE | Supabase |
| Row-level security | CONFIGURE | Supabase RLS |
| Audit trails | CONFIGURE | Supabase Triggers |
| Business logic | CONFIGURE | Supabase Functions |
| Reporting queries | CONFIGURE | Supabase Views |
| Scheduled jobs | CONFIGURE | Vercel Cron |
| Webhook receivers | BUILD (minimal) | Vercel Edge |
| **Staff UI** | BUILD | Next.js |
| **Workflow screens** | BUILD | Next.js |
| **KPI dashboards** | BUILD | Next.js |

---

## Project Status

**Last Updated:** 2025-11-29

### Current Phase
Phase 1 - Contact Foundation (5 of 8 tasks complete)

### Active To-Do
- [ ] 1.6 Deduplication UI (Kate Kripke test case ready)
- [ ] 1.7 Contact Card Redesign (business_name header, reusable component)
- [ ] 1.8 Review Other Platforms for UI Best Practices

### Up Next (Phase 2: Donor Module)
- [ ] 2.1 Complete Remaining Imports (356 contacts, 17 joint donors)
- [ ] 2.2 Donor List UI
- [ ] 2.3 Donor Classification
- [ ] 2.4 Manual Donation Entry
- [ ] 2.5 Fix "nan" Donor Names
- [ ] 2.6 Prevention Trigger for NULL external_transaction_id

### Blocked / Needs Decision
(none currently)

### Completed
| Task | Date |
|------|------|
| 1.5 Display Purchase History | 2025-11-29 |
| 1.4 Display Kajabi Tags | 2025-11-29 |
| 1.3 Address Strategy | 2025-11-29 |
| 1.2 Multi-Email Display | 2025-11-28 |
| 1.1 Edit Contact Function | 2025-11-28 |
| 0.2 Supabase Auth | 2025-11-28 |
| 0.1 Fix Duplicate Transactions | 2025-11-28 |

### Remaining Phases
- Phase 3: Events Module (10 tasks) — Zoho Replacement
- Phase 4: Membership Module (10 tasks)
- Phase 5: School for Souls (10 tasks)
- Phase 6: Donor Advanced (6 tasks)
- Phase 7: Dashboard & Polish (4 tasks)
- Future Enhancements (4 items)

### Next Session Starts With
```
Follow /docs/ENGINEERING_STANDARDS.md for all code changes.

Current phase: Phase 1 - Contact Foundation
Current task: 1.6 Deduplication UI

Test case: Kate Kripke (3 duplicate contacts identified)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Wix doesn't have needed webhooks | Research before building; may need alternative |
| Over-building in app | Senior Advisor reviews; "can Supabase do this?" first |
| Integration complexity | Start simple; one webhook at a time |
| Wix migration delays | StarHouse can work without Wix; manual entry fallback |
| Scope creep | Stick to plan; defer nice-to-haves |

---

## Metrics: Are We Building Too Much?

**Warning signs we're over-building:**
- Writing validation logic in Next.js (should be DB constraint)
- Writing aggregation queries in API routes (should be Supabase view)
- Building auth flows (should be Supabase Auth)
- Building email sending (should be Wix)
- Building payment forms (should be Wix/Stripe)

**Healthy signs:**
- Most "features" are new Supabase views
- API routes are thin (fetch from Supabase, return to UI)
- Webhooks are simple (validate, insert, done)
- UI is forms + tables + dashboards (no complex logic)

---

**Remember:** StarHouse is a staff UI layer. The less code we write, the less we maintain. Let the platforms do their jobs.

---

## Future Enhancements

*Items identified during development that are valuable but not critical for launch. Track here for future phases.*

### Normalized Phone/Address Tables
**Priority:** Low
**Rationale:** Current column-based storage (phone, paypal_phone, address_line_1, shipping_address_line_1) works for display. Full normalization to `contact_phones` and `contact_addresses` tables would require:
- Migration to create tables (schemas defined in 1.2)
- Data migration script to populate from existing columns
- Update UI to query from new tables
- Decision on column vs table as source of truth

**Trigger:** Consider when staff needs to add/edit multiple phones or addresses per contact.

---

### Backfill NULL external_transaction_id
**Priority:** Medium
**Rationale:** Historical transactions may have NULL `external_transaction_id`, complicating duplicate detection. After implementing 2.6 prevention trigger:
- Audit existing NULL records
- Attempt to match with QuickBooks invoice numbers
- Generate synthetic IDs for unmatched records (e.g., `legacy_YYYYMMDD_amount`)

---

### Fix MailingListStats Permission Error
**Priority:** Low
**Rationale:** Dashboard component `MailingListStats` throws RLS permission error. Current workaround: component hidden. Future fix:
- Review RLS policies on `mailing_list_priority` view
- Ensure authenticated users can read aggregate stats
- Or remove component entirely per Phase 7 dashboard redesign

---

### PayPal Product Name Capture
**Priority:** Medium
**Rationale:** Task 1.5 diagnostics revealed 0% of PayPal transactions (3,982 total) have product info. Update PayPal import script to capture item/product names for transaction display.

**Current state:**
- Kajabi: 50.7% have `quickbooks_memo` with product names
- Ticket Tailor: `raw_source.event_name` available
- PayPal: No product info stored

**Fix:**
- Review PayPal transaction data structure for item_name or description fields
- Update import script to populate `quickbooks_memo` or create `paypal_item_name` column
- Consider storing in `raw_source` JSON for future flexibility

**Trigger:** When staff requests better PayPal transaction labeling in purchase history.

---

### Technical Debt: Supabase Security Advisor Cleanup
**Priority:** P2 (Medium)
**Estimate:** 2-4 hours
**Source:** Supabase Security Advisor (discovered 2025-11-29)

**Issues:**
- 65 errors: Security Definer Views — views using `SECURITY DEFINER` bypass RLS
- 57 warnings: To be assessed

**Affected views (partial list):**
- `public.mailing_list_quality_issues`
- `public.v_failed_webhooks`
- `public.phone_verification_stats`
- `public.mailing_list_stats`
- `public.v_donor_summary`
- `public.name_sync_health`
- `public.recent_webhook_failures`

**Action required:**
- Review each view for RLS bypass necessity
- Convert to `SECURITY INVOKER` where appropriate
- Document any views that legitimately need `SECURITY DEFINER`

**Risk assessment:** Low — staff-only internal tool, all users authenticated

---

### Technical Debt: Contact Edit Modal Enhancements
**Priority:** P2 (Medium)
**Estimate:** 2-3 hours total
**Source:** UI capability assessment (discovered 2025-11-29)

**Current state:**
- ContactEditModal supports editing billing/mailing address only
- Shipping address fields exist in schema but not exposed in edit UI
- No ability to set primary email/phone/address from contact card

**Missing features:**
1. **Shipping address editing** — Add shipping address fields to ContactEditModal (schema fields already exist: `shipping_address_line_1`, `shipping_city`, etc.)
2. **Set primary email** — Allow marking an email as primary from IdentityColumn email list
3. **Set primary phone** — Allow marking a phone as primary from IdentityColumn phone list
4. **Set primary address** — Allow setting `preferred_mailing_address` field (billing vs shipping) from UI

**Files to modify:**
- `starhouse-ui/components/contacts/ContactEditModal.tsx` — Add shipping address section
- `starhouse-ui/components/contacts/contact-card/IdentityColumn.tsx` — Add "Set Primary" actions

**Trigger:** When staff requests ability to edit shipping addresses or set primary contact methods via UI
