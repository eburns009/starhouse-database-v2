# Donor Management Module - Comprehensive Implementation Plan

**Document Version:** 1.0
**Created:** 2025-11-15
**Status:** Planning & Design Complete
**Estimated Timeline:** 4-5 weeks
**Priority:** High-Value Feature

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Context & Objectives](#business-context--objectives)
3. [Current State Analysis](#current-state-analysis)
4. [Technical Architecture](#technical-architecture)
5. [Data Model Design](#data-model-design)
6. [User Interface Design](#user-interface-design)
7. [Core Features & Functionality](#core-features--functionality)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Data Migration Strategy](#data-migration-strategy)
10. [Integration Points](#integration-points)
11. [Success Metrics & KPIs](#success-metrics--kpis)
12. [Risk Assessment & Mitigation](#risk-assessment--mitigation)
13. [Open Questions & Decisions](#open-questions--decisions)
14. [Appendix](#appendix)

---

## Executive Summary

### Purpose
Build a dedicated Donor Management Module that separates charitable donations from product purchases, provides comprehensive donor analytics, and enables effective donor stewardship and engagement.

### Business Value
- **Financial Clarity:** Separate donation tracking from e-commerce revenue
- **Donor Insights:** Segment and analyze donor behavior for targeted engagement
- **Operational Efficiency:** Automate thank-you letters and tax receipt generation
- **Fundraising Intelligence:** Track campaign performance and donor retention
- **Compliance:** Proper IRS-compliant donation records and receipting

### Key Statistics
- **Current Database:** 11,843 transactions | 3,022 unique customers | $629,437.73 total revenue
- **QuickBooks Donor Data:** 1,056 transactions | 568 donors | $83,521.47 (2024 only)
- **Enrichment Completed:** 342 contacts enriched with $49,733.33 in donations
- **Opportunity:** 241 additional donors + 5 years historical data pending

### High-Level Approach
Create a new `donations` table for transaction-level tracking, enhance `contacts` with donor-specific fields, build comprehensive UI for donor management, and implement automation for stewardship activities.

---

## Business Context & Objectives

### Current Pain Points

**1. Data Confusion**
- Donations mixed with product purchases in `total_spent` field
- Cannot differentiate between donors and customers
- Fundraising reports require manual QuickBooks exports

**2. Limited Donor Intelligence**
- No donor segmentation (active/lapsed/major)
- No campaign tracking or performance analytics
- Cannot identify at-risk donors for reactivation

**3. Manual Processes**
- Thank-you letters handled manually
- Tax receipts generated outside the system
- No automated donor communication workflows

**4. Missing Historical Context**
- Only 2024 QuickBooks data imported
- 5 years of donation history (2019-2023) not in system
- 241 donors excluded due to missing email addresses

### Business Objectives

**Primary Goals:**
1. **Separate Financial Reporting:** Distinguish donations from product sales
2. **Donor Stewardship:** Enable personalized, timely donor acknowledgment
3. **Campaign Management:** Track and optimize fundraising campaigns
4. **Retention Analytics:** Identify and re-engage lapsed donors
5. **Compliance:** Generate IRS-compliant tax receipts

**Success Criteria:**
- 500+ donors tracked with complete 5-year history
- 90%+ donor records matched to contact profiles
- <1 hour to generate year-end tax receipts for all donors
- 80%+ automated thank-you email delivery rate
- Real-time campaign performance dashboards

---

## Current State Analysis

### Database Schema (Existing)

**Contacts Table:**
- 129 fields including financial aggregates (`total_spent`, `transaction_count`)
- Source system tracking (Kajabi, PayPal, QuickBooks, TicketTailor, etc.)
- Email subscription and consent management
- Address validation and USPS enrichment
- Tags, notes, and household management

**Transactions Table:**
- Transaction types: `purchase`, `subscription_payment`, `refund`
- Links to: `contacts`, `products`, `subscriptions`
- Source systems: Kajabi, PayPal, TicketTailor
- **Gap:** No donation-specific fields (campaign, donor acknowledgment, etc.)

**Products Table:**
- Name, type, Kajabi offer ID
- **Gap:** No distinction between products vs. donation funds

### Data Sources

**1. QuickBooks Donor Export (Primary)**
```
Format: Statement of Activity Detail
Structure:
- Transaction date
- Transaction type (Invoice, Sales Receipt, Deposit)
- Num (Receipt/Invoice number)
- Name (Donor name)
- Class full name (Campaign: "Fundraising", "Tree Sale", etc.)
- Memo/Description
- Item split account (PayPal Bank, A/R, etc.)
- Amount
- Running Balance
```

**2. Existing Database Transactions**
- 11,843 transactions spanning 2020-2025
- Already linked to contacts
- Mix of purchases, subscriptions, and donations

### Current Limitations

**Data Quality Issues:**
1. **241 donors without emails** - Cannot import to contact-required system
2. **Name matching ambiguity** - "Christine Hibbard (C)" vs "Christine Hibbard"
3. **Duplicate donors** - Same person may have multiple QuickBooks entries
4. **Historical gap** - Only 2024 data imported (missing 2019-2023)

**Functional Gaps:**
1. No campaign attribution for donations
2. No donor segmentation or lifecycle tracking
3. No thank-you or tax receipt workflow
4. No donor communication preferences
5. No recurring donation tracking

---

## Technical Architecture

### System Design Principles

**FAANG Standards Applied:**
- ✅ **Data Normalization:** Separate `donations` table for transaction details
- ✅ **Computed Fields:** Aggregate calculations stored on `contacts` for performance
- ✅ **Referential Integrity:** Foreign keys with proper cascade rules
- ✅ **Audit Trail:** `created_at`, `updated_at`, `created_by` on all tables
- ✅ **Soft Deletes:** `deleted_at` for data retention
- ✅ **Row-Level Security:** Supabase RLS policies for staff access control
- ✅ **Indexing Strategy:** Optimized indexes for common queries
- ✅ **Type Safety:** Full TypeScript types generated from database schema

### Technology Stack

**Database:** PostgreSQL (Supabase)
**Backend:** Supabase Edge Functions (TypeScript)
**Frontend:** Next.js 14 (App Router, Server Components)
**UI Library:** React, shadcn/ui, TailwindCSS
**Charts:** Recharts or Chart.js
**PDF Generation:** jsPDF or Puppeteer for tax receipts
**Email:** Resend or SendGrid for thank-you automation

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ Donors   │  │Donations │  │Campaigns │  │Analytics││
│  │  List    │  │   List   │  │  Mgmt    │  │Dashboard││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ Supabase Client SDK
                       │
┌──────────────────────▼──────────────────────────────────┐
│                Supabase Backend                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Row-Level Security (RLS)                │   │
│  │  - Staff-only access to financial data          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────┬──────────────┬─────────────────────┐  │
│  │  contacts   │  donations   │  campaigns          │  │
│  │  (enhanced) │  (new)       │  (new)              │  │
│  └─────────────┴──────────────┴─────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Database Functions/Triggers             │   │
│  │  - update_donor_aggregates()                    │   │
│  │  - calculate_donor_status()                     │   │
│  │  - update_campaign_totals()                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ Import Scripts
                       │
┌──────────────────────▼──────────────────────────────────┐
│              External Data Sources                      │
│                                                         │
│  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │   QuickBooks     │  │   Stripe/PayPal             │ │
│  │   CSV Export     │  │   (Future Integration)      │ │
│  └──────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Data Model Design

### 1. New Table: `donations`

**Purpose:** Store individual donation transactions with full detail

```sql
CREATE TABLE donations (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,

    -- Transaction Core Fields
    donation_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    currency TEXT DEFAULT 'USD' CHECK (currency ~* '^[A-Z]{3}$'),

    -- Source System Tracking
    source_system TEXT NOT NULL DEFAULT 'manual',
    external_id TEXT,
    transaction_type TEXT, -- 'invoice', 'sales_receipt', 'deposit', 'journal_entry', 'online'

    -- QuickBooks-Specific Fields
    qb_receipt_number TEXT,
    qb_class TEXT, -- Original QuickBooks class for reference
    qb_account TEXT, -- Split account (PayPal Bank, Cash, etc.)

    -- Categorization
    campaign_name TEXT, -- Denormalized for reporting (e.g., "Tree Sale 2024")
    category TEXT, -- 'fundraising', 'sponsorship', 'grant', 'membership_fee'
    payment_method TEXT, -- 'paypal', 'check', 'cash', 'credit_card', 'bank_transfer', 'venmo'

    -- Details
    memo TEXT,
    description TEXT,

    -- Recurring Donations
    is_recurring BOOLEAN DEFAULT false,
    recurring_frequency TEXT, -- 'monthly', 'quarterly', 'annual'

    -- Pledges
    is_pledge BOOLEAN DEFAULT false,
    pledge_fulfilled_date DATE,

    -- Donor Acknowledgment
    thank_you_sent BOOLEAN DEFAULT false,
    thank_you_sent_date DATE,
    thank_you_method TEXT, -- 'email', 'mail', 'phone', 'in_person'

    -- Tax Receipt
    tax_receipt_sent BOOLEAN DEFAULT false,
    tax_receipt_sent_date DATE,
    tax_receipt_number TEXT UNIQUE,
    tax_year INTEGER, -- Fiscal year for reporting

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_by TEXT,
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_source_system CHECK (
        source_system IN ('quickbooks', 'stripe', 'paypal', 'manual', 'check', 'cash')
    ),
    CONSTRAINT unique_external_id UNIQUE (source_system, external_id)
        WHERE external_id IS NOT NULL
);

-- Indexes for Performance
CREATE INDEX idx_donations_contact ON donations(contact_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_donations_date ON donations(donation_date DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_donations_campaign ON donations(campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX idx_donations_amount ON donations(amount DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_donations_source ON donations(source_system, external_id) WHERE external_id IS NOT NULL;
CREATE INDEX idx_donations_tax_year ON donations(tax_year) WHERE tax_year IS NOT NULL;
CREATE INDEX idx_donations_acknowledgment ON donations(thank_you_sent, tax_receipt_sent);

-- Row-Level Security
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Staff can view all donations"
    ON donations FOR SELECT
    TO authenticated
    USING (is_verified_staff());

CREATE POLICY "Staff can insert donations"
    ON donations FOR INSERT
    TO authenticated
    WITH CHECK (is_verified_staff());

CREATE POLICY "Staff can update donations"
    ON donations FOR UPDATE
    TO authenticated
    USING (is_verified_staff())
    WITH CHECK (is_verified_staff());

-- Service role full access
CREATE POLICY "service_role_full_access"
    ON donations
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Trigger to update contact aggregates
CREATE TRIGGER donations_update_contact_aggregates
    AFTER INSERT OR UPDATE OR DELETE ON donations
    FOR EACH ROW
    EXECUTE FUNCTION update_donor_aggregates();
```

### 2. New Table: `campaigns`

**Purpose:** Track fundraising campaigns for attribution and reporting

```sql
CREATE TABLE campaigns (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign Details
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL, -- URL-friendly name
    description TEXT,
    campaign_type TEXT, -- 'annual_appeal', 'tree_sale', 'event', 'grant', 'emergency', 'capital'

    -- Timeline
    start_date DATE,
    end_date DATE,
    fiscal_year INTEGER,

    -- Goals
    goal_amount DECIMAL(12,2),
    goal_donor_count INTEGER,

    -- Computed Totals (updated by trigger)
    total_raised DECIMAL(12,2) DEFAULT 0,
    donor_count INTEGER DEFAULT 0,
    donation_count INTEGER DEFAULT 0,
    average_donation DECIMAL(12,2) DEFAULT 0,

    -- Status
    active BOOLEAN DEFAULT true,
    archived_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_by TEXT,

    -- Constraints
    CONSTRAINT valid_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT valid_campaign_type CHECK (
        campaign_type IN ('annual_appeal', 'tree_sale', 'event', 'grant', 'emergency', 'capital', 'other')
    )
);

-- Indexes
CREATE INDEX idx_campaigns_active ON campaigns(active) WHERE active = true;
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);
CREATE INDEX idx_campaigns_fiscal_year ON campaigns(fiscal_year);

-- RLS
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Staff can view campaigns"
    ON campaigns FOR SELECT
    TO authenticated
    USING (is_verified_staff());

CREATE POLICY "Staff can manage campaigns"
    ON campaigns FOR ALL
    TO authenticated
    USING (is_verified_staff())
    WITH CHECK (is_verified_staff());

-- Trigger to recalculate totals
CREATE TRIGGER campaigns_set_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
```

### 3. Enhanced `contacts` Table

**New Donor-Specific Fields:**

```sql
-- Add donor aggregate fields
ALTER TABLE contacts ADD COLUMN total_donated DECIMAL(12,2) DEFAULT 0;
ALTER TABLE contacts ADD COLUMN donation_count INTEGER DEFAULT 0;
ALTER TABLE contacts ADD COLUMN first_donation_date DATE;
ALTER TABLE contacts ADD COLUMN last_donation_date DATE;
ALTER TABLE contacts ADD COLUMN largest_donation DECIMAL(12,2);
ALTER TABLE contacts ADD COLUMN average_donation DECIMAL(12,2);

-- Donor segmentation
ALTER TABLE contacts ADD COLUMN donor_status TEXT;
ALTER TABLE contacts ADD COLUMN donor_tier TEXT;
ALTER TABLE contacts ADD COLUMN is_recurring_donor BOOLEAN DEFAULT false;

-- QuickBooks matching
ALTER TABLE contacts ADD COLUMN quickbooks_donor_name TEXT;

-- Communication preferences
ALTER TABLE contacts ADD COLUMN thank_you_preference TEXT DEFAULT 'email';
ALTER TABLE contacts ADD COLUMN communication_frequency TEXT DEFAULT 'quarterly';

-- Constraints
ALTER TABLE contacts ADD CONSTRAINT valid_donor_status CHECK (
    donor_status IS NULL OR donor_status IN ('active', 'lapsed', 'major', 'recurring', 'first_time', 'inactive')
);

ALTER TABLE contacts ADD CONSTRAINT valid_donor_tier CHECK (
    donor_tier IS NULL OR donor_tier IN ('bronze', 'silver', 'gold', 'platinum')
);

ALTER TABLE contacts ADD CONSTRAINT valid_thank_you_preference CHECK (
    thank_you_preference IN ('email', 'mail', 'phone', 'none')
);

-- Indexes
CREATE INDEX idx_contacts_donor_status ON contacts(donor_status) WHERE donor_status IS NOT NULL;
CREATE INDEX idx_contacts_total_donated ON contacts(total_donated DESC) WHERE total_donated > 0;
CREATE INDEX idx_contacts_last_donation ON contacts(last_donation_date DESC) WHERE last_donation_date IS NOT NULL;
CREATE INDEX idx_contacts_recurring_donors ON contacts(is_recurring_donor) WHERE is_recurring_donor = true;
```

### 4. Database Functions

**Function: `update_donor_aggregates()`**

```sql
CREATE OR REPLACE FUNCTION update_donor_aggregates()
RETURNS TRIGGER AS $$
DECLARE
    v_contact_id UUID;
BEGIN
    -- Determine which contact to update
    IF TG_OP = 'DELETE' THEN
        v_contact_id := OLD.contact_id;
    ELSE
        v_contact_id := NEW.contact_id;
    END IF;

    -- Recalculate aggregates for this contact
    UPDATE contacts
    SET
        total_donated = COALESCE(stats.total, 0),
        donation_count = COALESCE(stats.count, 0),
        first_donation_date = stats.first_date,
        last_donation_date = stats.last_date,
        largest_donation = stats.max_amount,
        average_donation = COALESCE(stats.avg_amount, 0),
        updated_at = now()
    FROM (
        SELECT
            SUM(amount) as total,
            COUNT(*) as count,
            MIN(donation_date) as first_date,
            MAX(donation_date) as last_date,
            MAX(amount) as max_amount,
            AVG(amount) as avg_amount
        FROM donations
        WHERE contact_id = v_contact_id
          AND deleted_at IS NULL
    ) as stats
    WHERE contacts.id = v_contact_id;

    -- Calculate donor status
    PERFORM calculate_donor_status(v_contact_id);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

**Function: `calculate_donor_status()`**

```sql
CREATE OR REPLACE FUNCTION calculate_donor_status(p_contact_id UUID)
RETURNS VOID AS $$
DECLARE
    v_donation_count INTEGER;
    v_last_donation_date DATE;
    v_total_donated DECIMAL(12,2);
    v_has_recurring BOOLEAN;
    v_days_since_last INTEGER;
    v_status TEXT;
    v_tier TEXT;
BEGIN
    -- Get contact donation data
    SELECT
        donation_count,
        last_donation_date,
        total_donated,
        EXISTS(SELECT 1 FROM donations WHERE contact_id = p_contact_id AND is_recurring = true)
    INTO
        v_donation_count,
        v_last_donation_date,
        v_total_donated,
        v_has_recurring
    FROM contacts
    WHERE id = p_contact_id;

    -- Calculate days since last donation
    v_days_since_last := CURRENT_DATE - v_last_donation_date;

    -- Determine donor status
    IF v_donation_count = 0 THEN
        v_status := NULL;
    ELSIF v_donation_count = 1 THEN
        v_status := 'first_time';
    ELSIF v_has_recurring THEN
        v_status := 'recurring';
    ELSIF v_total_donated >= 1000 THEN
        v_status := 'major';
    ELSIF v_days_since_last <= 365 THEN
        v_status := 'active';
    ELSIF v_days_since_last <= 730 THEN
        v_status := 'lapsed';
    ELSE
        v_status := 'inactive';
    END IF;

    -- Determine donor tier
    IF v_total_donated >= 10000 THEN
        v_tier := 'platinum';
    ELSIF v_total_donated >= 5000 THEN
        v_tier := 'gold';
    ELSIF v_total_donated >= 1000 THEN
        v_tier := 'silver';
    ELSIF v_total_donated > 0 THEN
        v_tier := 'bronze';
    ELSE
        v_tier := NULL;
    END IF;

    -- Update contact
    UPDATE contacts
    SET
        donor_status = v_status,
        donor_tier = v_tier,
        is_recurring_donor = v_has_recurring,
        updated_at = now()
    WHERE id = p_contact_id;
END;
$$ LANGUAGE plpgsql;
```

**Function: `update_campaign_totals()`**

```sql
CREATE OR REPLACE FUNCTION update_campaign_totals()
RETURNS TRIGGER AS $$
DECLARE
    v_campaign_id UUID;
BEGIN
    -- Determine which campaign to update
    IF TG_OP = 'DELETE' THEN
        v_campaign_id := OLD.campaign_id;
    ELSE
        v_campaign_id := NEW.campaign_id;
    END IF;

    -- Skip if no campaign
    IF v_campaign_id IS NULL THEN
        RETURN NULL;
    END IF;

    -- Recalculate campaign totals
    UPDATE campaigns
    SET
        total_raised = COALESCE(stats.total, 0),
        donor_count = COALESCE(stats.donors, 0),
        donation_count = COALESCE(stats.count, 0),
        average_donation = COALESCE(stats.avg, 0),
        updated_at = now()
    FROM (
        SELECT
            SUM(amount) as total,
            COUNT(DISTINCT contact_id) as donors,
            COUNT(*) as count,
            AVG(amount) as avg
        FROM donations
        WHERE campaign_id = v_campaign_id
          AND deleted_at IS NULL
    ) as stats
    WHERE campaigns.id = v_campaign_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to donations table
CREATE TRIGGER donations_update_campaign_totals
    AFTER INSERT OR UPDATE OR DELETE ON donations
    FOR EACH ROW
    EXECUTE FUNCTION update_campaign_totals();
```

---

## User Interface Design

### Design Principles

**FAANG UI Standards:**
- ✅ **Performance:** Server-side rendering, optimistic updates, pagination
- ✅ **Accessibility:** WCAG 2.1 AA compliance, keyboard navigation
- ✅ **Responsive:** Mobile-first design, tablet/desktop optimization
- ✅ **Consistency:** Reuse existing component library (shadcn/ui)
- ✅ **Data Density:** Information-rich tables with smart filtering
- ✅ **Visual Hierarchy:** Clear typography, spacing, and color usage

### Page Specifications

#### 1. `/donors` - Donor Dashboard & List

**Purpose:** Main entry point for donor management with overview + searchable list

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  DONORS                                          [+ Add]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Total       │  │ Active      │  │ YTD         │       │
│  │ Donations   │  │ Donors      │  │ Donations   │       │
│  │ $629,437    │  │ 1,247       │  │ $83,521     │       │
│  │ ↑ 12% YoY   │  │ 41% of all  │  │ ↑ 8% vs LY  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Filters: [All Statuses ▼] [Amount ▼] [Last Gift ▼] │ │
│  │  Search: [Search by name, email...]                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Donor List (Sortable Table)                          │ │
│  ├─────┬──────────────┬────────┬────────┬──────────────┤ │
│  │ ☐   │ Name         │ Total  │ Count  │ Last Gift    │ │
│  ├─────┼──────────────┼────────┼────────┼──────────────┤ │
│  │ ☐   │ Jeff Stein   │$2,450  │ 12 ↻   │ Nov 15, 2024 │ │
│  │     │ jeff@...     │ 🥇Gold │        │ Tree Sale    │ │
│  ├─────┼──────────────┼────────┼────────┼──────────────┤ │
│  │ ☐   │ Karen Gallik │$1,850  │ 8      │ Oct 3, 2024  │ │
│  │     │ karen@...    │🥈Silver│        │ Annual Appeal│ │
│  ├─────┼──────────────┼────────┼────────┼──────────────┤ │
│  │ ... │ ...          │ ...    │ ...    │ ...          │ │
│  └─────┴──────────────┴────────┴────────┴──────────────┘ │
│                                                            │
│  Showing 1-25 of 568          [1] 2 3 4 ... 23 [Next]     │
│                                                            │
│  Bulk Actions: ✓ 3 selected                               │
│  [Export CSV] [Send Thank You] [Generate Receipts]        │
└────────────────────────────────────────────────────────────┘
```

**Key Components:**

1. **Metrics Cards** (Top Row)
   - Total Donations (all-time) with YoY trend
   - Active Donors count + percentage
   - YTD Donations with comparison to last year
   - Average Donation amount

2. **Filters & Search**
   - Status: All / Active / Lapsed / Major / First-time / Recurring
   - Amount Range: <$100 / $100-500 / $500-1000 / $1,000+
   - Last Donation: Last 6mo / Last year / 1-2 years / 2+ years ago
   - Campaign: All campaigns or specific
   - Search: Real-time search by name, email

3. **Donor Table Columns**
   - Checkbox for bulk selection
   - Name + Email (stacked)
   - Total Donated + Tier Badge (Bronze/Silver/Gold/Platinum)
   - Donation Count + Recurring indicator
   - Last Donation Date + Campaign name
   - Actions: View Details, Send Thank You, Generate Receipt

4. **Bulk Actions** (appears when items selected)
   - Export selected to CSV
   - Mark thank-yous sent
   - Generate tax receipts
   - Add to email campaign

**Technical Implementation:**
```typescript
// app/donors/page.tsx
export default async function DonorsPage({
  searchParams
}: {
  searchParams: { status?: string; amount?: string; search?: string }
}) {
  const supabase = createClient()

  // Build query with filters
  let query = supabase
    .from('contacts')
    .select(`
      id,
      first_name,
      last_name,
      email,
      total_donated,
      donation_count,
      last_donation_date,
      donor_status,
      donor_tier,
      is_recurring_donor
    `)
    .gt('total_donated', 0)
    .order('total_donated', { ascending: false })

  // Apply filters from searchParams
  if (searchParams.status) {
    query = query.eq('donor_status', searchParams.status)
  }

  const { data: donors } = await query

  // Fetch aggregate metrics
  const metrics = await getDonorMetrics()

  return (
    <DonorDashboard donors={donors} metrics={metrics} />
  )
}
```

#### 2. `/donors/[id]` - Donor Detail Page

**Purpose:** Comprehensive donor profile with full donation history

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  ← Back to Donors                                    [Edit] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──┐  Jeff Stein                          🥇 Gold Donor  │
│  │JS│  jeff@example.com          ✓ Active                 │
│  └──┘  (555) 123-4567                                     │
│        Portland, OR                                        │
│                                                            │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐│
│  │ Total Given  │ Donations    │ First Gift   │ Latest   ││
│  │ $2,450.00    │ 12           │ May 2020     │ Nov 2024 ││
│  ├──────────────┼──────────────┼──────────────┼──────────┤│
│  │ Largest      │ Average      │ Status       │ Campaigns││
│  │ $500.00      │ $204.17      │ Recurring ↻  │ 5        ││
│  └──────────────┴──────────────┴──────────────┴──────────┘│
│                                                            │
│  Quick Actions:                                            │
│  [Send Thank You] [Generate Receipt] [Add Note] [Email]   │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  DONATION HISTORY                              [Export]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  2024 ($850.00)                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Nov 15, 2024         $250.00          Tree Sale 2024  │ │
│  │ Receipt #2024-1523   ✓ Thanks sent    ✓ Receipt sent │ │
│  │ PayPal                                                │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Jun 3, 2024          $100.00          Fire Mitigation │ │
│  │ Receipt #2024-0892   ✓ Thanks sent    - Receipt      │ │
│  │ Check #4521                                           │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Mar 12, 2024         $500.00          Annual Appeal   │ │
│  │ Receipt #2024-0334   ✓ Thanks sent    ✓ Receipt sent │ │
│  │ Credit Card                                           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  2023 ($1,200.00) [Expand ▼]                               │
│                                                            │
│  2022 ($400.00) [Expand ▼]                                 │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  CAMPAIGNS SUPPORTED                                       │
├────────────────────────────────────────────────────────────┤
│  • Tree Sale (4 donations, $800)                           │
│  • Fire Mitigation (3 donations, $450)                     │
│  • Annual Appeal (2 donations, $700)                       │
│  • Emergency Fund (2 donations, $300)                      │
│  • Capital Campaign (1 donation, $200)                     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  NOTES & COMMUNICATION                          [+ Note]   │
├────────────────────────────────────────────────────────────┤
│  Nov 16, 2024 - Staff Note                                 │
│  Called to thank for Tree Sale donation. Very engaged,     │
│  interested in volunteer opportunities.                    │
│                                                            │
│  Mar 15, 2024 - Email Sent                                 │
│  Thank you letter sent for $500 Annual Appeal donation.    │
└────────────────────────────────────────────────────────────┘
```

**Key Components:**

1. **Donor Profile Header**
   - Avatar with initials
   - Name, email, phone, address
   - Donor tier badge (visual hierarchy)
   - Donor status (Active, Lapsed, etc.)

2. **Summary Stats Grid**
   - Total donated, donation count
   - First/last donation dates
   - Largest donation, average
   - Status (with recurring indicator)
   - Campaigns supported count

3. **Quick Actions Bar**
   - Send thank you email
   - Generate tax receipt
   - Add note
   - Send email
   - Edit contact

4. **Donation Timeline**
   - Grouped by year (expandable)
   - Each donation shows:
     - Date + amount
     - Campaign name
     - Payment method
     - Receipt number
     - Acknowledgment status (✓ thanks sent, ✓ receipt sent)
   - Click to edit/view details

5. **Campaign Support Summary**
   - List of campaigns with totals
   - Shows donor's giving patterns

6. **Notes & Communications**
   - Chronological log of interactions
   - Types: Staff notes, emails sent, phone calls, meetings
   - Add new note functionality

**Technical Implementation:**
```typescript
// app/donors/[id]/page.tsx
export default async function DonorDetailPage({
  params
}: {
  params: { id: string }
}) {
  const supabase = createClient()

  // Fetch donor with all donations
  const { data: donor } = await supabase
    .from('contacts')
    .select(`
      *,
      donations (
        *,
        campaigns (name, slug)
      )
    `)
    .eq('id', params.id)
    .single()

  // Group donations by year
  const donationsByYear = groupBy(donor.donations, d =>
    new Date(d.donation_date).getFullYear()
  )

  return <DonorDetailView donor={donor} donationsByYear={donationsByYear} />
}
```

#### 3. `/donations` - Transactions List

**Purpose:** View and manage all donation transactions

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  DONATIONS                                      [+ Manual]  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Filters:                                                  │
│  [Date Range: Last 12 months ▼]  [Campaign: All ▼]        │
│  [Amount: All ▼]  [Status: All ▼]  [Payment: All ▼]       │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Date       │ Donor        │ Amount │ Campaign   │ ✓  │ │
│  ├────────────┼──────────────┼────────┼────────────┼────┤ │
│  │ Nov 15 '24 │ Jeff Stein   │ $250   │ Tree Sale  │ ✓✓ │ │
│  │            │ PayPal       │        │            │    │ │
│  ├────────────┼──────────────┼────────┼────────────┼────┤ │
│  │ Nov 14 '24 │ Karen Gallik │ $100   │ Annual     │ ✓- │ │
│  │            │ Check #4892  │        │            │    │ │
│  ├────────────┼──────────────┼────────┼────────────┼────┤ │
│  │ Nov 12 '24 │ Mark Jones   │ $500   │ Capital    │ -- │ │
│  │            │ Credit Card  │        │            │    │ │
│  └────────────┴──────────────┴────────┴────────────┴────┘ │
│                                                            │
│  ✓✓ = Thanks + Receipt sent  |  ✓- = Thanks only         │
│  -- = Neither sent                                         │
│                                                            │
│  Bulk Actions: ✓ 5 selected                               │
│  [Mark Thanks Sent] [Generate Receipts] [Export CSV]      │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Filter by date range, campaign, amount, status
- Sort by any column
- Click row to view/edit donation details
- Bulk mark thank-yous sent
- Bulk generate tax receipts
- Export filtered results to CSV

#### 4. `/campaigns` - Campaign Management

**Purpose:** Track and analyze fundraising campaigns

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  CAMPAIGNS                                    [+ New]       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Active Campaigns (3)                                      │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Tree Sale 2024                          [View] [Edit]│  │
│  │ ──────────────────────────────────────              │  │
│  │ Goal: $30,000  |  End: Dec 31, 2024                 │  │
│  │                                                      │  │
│  │ Raised: $24,550                                      │  │
│  │ ████████████████░░░░ 82%                            │  │
│  │                                                      │  │
│  │ 156 donors  |  $157.37 avg  |  23 days left         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Fire Mitigation Fund                    [View] [Edit]│  │
│  │ ──────────────────────────────────────              │  │
│  │ Goal: $15,000  |  End: Jun 30, 2025                 │  │
│  │                                                      │  │
│  │ Raised: $8,240                                       │  │
│  │ ██████████░░░░░░░░░░ 55%                            │  │
│  │                                                      │  │
│  │ 67 donors  |  $123.28 avg  |  197 days left         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  Past Campaigns (12) [View All ▼]                          │
│                                                            │
│  • Annual Appeal 2023 - $45,200 / $40,000 (113% ✓)        │
│  • Tree Sale 2023 - $28,900 / $25,000 (116% ✓)            │
│  • Emergency Fund 2022 - $12,450 / $10,000 (125% ✓)       │
└────────────────────────────────────────────────────────────┘
```

**Campaign Detail Page:**
```
┌────────────────────────────────────────────────────────────┐
│  ← Campaigns  /  Tree Sale 2024                    [Edit]  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Tree Sale 2024                                            │
│  Annual tree fundraiser supporting land stewardship        │
│  Dec 1, 2024 - Dec 31, 2024                                │
│                                                            │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐│
│  │ Goal         │ Raised       │ Donors       │ Progress ││
│  │ $30,000      │ $24,550      │ 156          │ 82%      ││
│  └──────────────┴──────────────┴──────────────┴──────────┘│
│                                                            │
│  ████████████████░░░░                                      │
│                                                            │
│  DONATION TRENDS                                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  $                                                    │ │
│  │  8k                              ●                    │ │
│  │  6k                    ●         │                    │ │
│  │  4k          ●         │    ●    │                    │ │
│  │  2k     ●    │    ●    │    │    │                    │ │
│  │  0  ────┴────┴────┴────┴────┴────                    │ │
│  │     Wk1 Wk2 Wk3 Wk4 Wk5 Wk6                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  TOP DONORS                                                │
│  1. Jeff Stein - $500                                      │
│  2. Karen Gallik - $450                                    │
│  3. Mark Jones - $400                                      │
│  4. Susan Chen - $350                                      │
│  5. David Park - $300                                      │
│                                                            │
│  NEW VS. REPEAT DONORS                                     │
│  New: 45 (29%)  |  Repeat: 111 (71%)                       │
│                                                            │
│  [Export Campaign Report] [View All Donations]             │
└────────────────────────────────────────────────────────────┘
```

#### 5. `/analytics/donors` - Analytics Dashboard

**Purpose:** Advanced donor insights and reporting

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  DONOR ANALYTICS                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  DONATION TRENDS                                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Revenue                                              │ │
│  │  $100k                                                │ │
│  │   80k                           ╱╲                    │ │
│  │   60k              ╱╲          ╱  ╲      ╱╲          │ │
│  │   40k     ╱╲      ╱  ╲        ╱    ╲    ╱  ╲         │ │
│  │   20k    ╱  ╲____╱    ╲______╱      ╲__╱    ╲        │ │
│  │    0  ──┴────┴────┴────┴────┴────┴────┴────          │ │
│  │      2019 2020 2021 2022 2023 2024 (proj)            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  DONOR SEGMENTATION                                        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Active (45%)                                  │ │
│  │         Lapsed (30%)                                  │ │
│  │         Major (15%)                                   │ │
│  │         Recurring (8%)                                │ │
│  │         First-time (2%)                               │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  RETENTION ANALYSIS                                        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Year-over-Year Retention Rate                        │ │
│  │  2020→2021: 68%  ████████████████░░░░                │ │
│  │  2021→2022: 72%  ██████████████████░░                │ │
│  │  2022→2023: 65%  ██████████████░░░░░                 │ │
│  │  2023→2024: 71%  █████████████████░░░                │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  GIVING LEVELS                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  <$100:      284 donors (50%)                         │ │
│  │  $100-500:   198 donors (35%)                         │ │
│  │  $500-1000:   56 donors (10%)                         │ │
│  │  $1000+:      30 donors (5%)                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ACTIONABLE REPORTS                                        │
│  [Lapsed Donors (172)] [Major Donors (85)]                │
│  [First-Time Donors (42)] [Recurring Donors (48)]         │
│                                                            │
│  [Export All Reports to PDF]                               │
└────────────────────────────────────────────────────────────┘
```

**Key Reports:**
1. **Lapsed Donors** - Donors who haven't given in 18+ months
2. **Major Donors** - Donors who've given $1,000+
3. **First-Time Donors** - New donors needing cultivation
4. **Recurring Donors** - Loyal supporters for recognition
5. **Campaign Comparison** - Side-by-side campaign performance

---

## Core Features & Functionality

### 1. Donor Segmentation (Automated)

**Business Logic:**

```typescript
type DonorStatus = 'first_time' | 'active' | 'lapsed' | 'inactive' | 'recurring' | 'major'

function calculateDonorStatus(contact: Contact): DonorStatus {
  const donationCount = contact.donation_count
  const totalDonated = contact.total_donated
  const lastDonationDate = contact.last_donation_date
  const isRecurring = contact.is_recurring_donor

  // No donations
  if (donationCount === 0) return null

  // First-time donor
  if (donationCount === 1) return 'first_time'

  // Recurring donor (3+ donations with pattern)
  if (isRecurring) return 'recurring'

  // Major donor (lifetime total)
  if (totalDonated >= 1000) return 'major'

  // Calculate recency
  const daysSinceLastDonation = daysBetween(lastDonationDate, new Date())

  if (daysSinceLastDonation <= 365) return 'active'
  if (daysSinceLastDonation <= 730) return 'lapsed'
  return 'inactive'
}

type DonorTier = 'bronze' | 'silver' | 'gold' | 'platinum'

function calculateDonorTier(totalDonated: number): DonorTier | null {
  if (totalDonated >= 10000) return 'platinum'
  if (totalDonated >= 5000) return 'gold'
  if (totalDonated >= 1000) return 'silver'
  if (totalDonated > 0) return 'bronze'
  return null
}
```

**Tier Definitions:**
- **Platinum:** $10,000+ lifetime giving
- **Gold:** $5,000 - $9,999
- **Silver:** $1,000 - $4,999
- **Bronze:** $1 - $999

### 2. Thank You Automation

**Workflow:**

1. **Trigger:** New donation created or imported
2. **Template Selection:**
   - Amount > $1,000: Flag for personal outreach
   - Amount $250-$999: Standard thank-you email
   - Amount < $250: Quick acknowledgment email
3. **Personalization:**
   - Merge fields: {donor_name}, {amount}, {date}, {campaign}
   - Custom message based on donor status (first-time vs. recurring)
4. **Delivery:**
   - Email via Resend/SendGrid
   - Log in communication history
   - Mark `thank_you_sent = true`

**Email Templates:**

```typescript
// templates/thank-you-standard.tsx
export function StandardThankYouEmail({
  donorName,
  amount,
  date,
  campaignName,
  lifetimeTotal
}: ThankYouEmailProps) {
  return (
    <Email>
      <Heading>Thank you for your generous gift!</Heading>

      <Text>Dear {donorName},</Text>

      <Text>
        Thank you for your donation of {formatCurrency(amount)} to support {campaignName}.
        Your generosity makes a real difference in our community.
      </Text>

      {lifetimeTotal >= 1000 && (
        <Text>
          Your total contributions of {formatCurrency(lifetimeTotal)} have been
          instrumental in helping us achieve our mission.
        </Text>
      )}

      <Text>With gratitude,<br/>All Seasons Chalice Church</Text>

      <Footer>
        Tax-deductible receipt available in your donor portal.
        EIN: XX-XXXXXXX
      </Footer>
    </Email>
  )
}
```

**Implementation:**

```typescript
// app/api/donations/send-thank-you/route.ts
export async function POST(request: Request) {
  const { donationId } = await request.json()

  // Fetch donation with contact
  const donation = await getDonationWithContact(donationId)

  // Select template based on amount
  const template = selectThankYouTemplate(donation.amount)

  // Send email
  await sendEmail({
    to: donation.contact.email,
    subject: `Thank you for your donation to ${donation.campaign_name}`,
    react: template({
      donorName: formatName(donation.contact.first_name, donation.contact.last_name),
      amount: donation.amount,
      date: donation.donation_date,
      campaignName: donation.campaign_name,
      lifetimeTotal: donation.contact.total_donated
    })
  })

  // Mark thank you sent
  await supabase
    .from('donations')
    .update({
      thank_you_sent: true,
      thank_you_sent_date: new Date().toISOString(),
      thank_you_method: 'email'
    })
    .eq('id', donationId)

  return Response.json({ success: true })
}
```

### 3. Tax Receipt Generation

**Requirements (IRS 501(c)(3) Compliance):**
- Organization name, address, EIN
- Tax-exempt status statement
- Donor name and address
- Donation date and amount
- "No goods or services received" statement (or value if applicable)
- Unique receipt number

**PDF Template:**

```typescript
// lib/pdf/tax-receipt.ts
import { jsPDF } from 'jspdf'

export function generateTaxReceipt(donation: Donation, contact: Contact): Blob {
  const doc = new jsPDF()

  // Header
  doc.setFontSize(16)
  doc.text('All Seasons Chalice Church', 105, 20, { align: 'center' })
  doc.setFontSize(10)
  doc.text('Tax-Deductible Donation Receipt', 105, 28, { align: 'center' })

  // Receipt number
  doc.setFontSize(12)
  doc.text(`Receipt #${donation.tax_receipt_number}`, 20, 45)

  // Donor information
  doc.setFontSize(11)
  doc.text('Donor:', 20, 60)
  doc.text(formatName(contact.first_name, contact.last_name), 20, 68)
  if (contact.address_line_1) {
    doc.text(contact.address_line_1, 20, 76)
    doc.text(`${contact.city}, ${contact.state} ${contact.postal_code}`, 20, 84)
  }

  // Donation details
  doc.text('Donation Date:', 20, 100)
  doc.text(formatDate(donation.donation_date), 70, 100)

  doc.text('Amount:', 20, 108)
  doc.setFontSize(14)
  doc.text(formatCurrency(donation.amount), 70, 108)

  doc.setFontSize(11)
  doc.text('Payment Method:', 20, 116)
  doc.text(donation.payment_method, 70, 116)

  if (donation.campaign_name) {
    doc.text('Campaign:', 20, 124)
    doc.text(donation.campaign_name, 70, 124)
  }

  // Tax statement
  doc.setFontSize(10)
  doc.text('All Seasons Chalice Church is a 501(c)(3) tax-exempt organization.', 20, 145)
  doc.text('EIN: XX-XXXXXXX', 20, 152)
  doc.text('No goods or services were provided in exchange for this donation.', 20, 159)

  // Footer
  doc.text('Thank you for your generous support!', 105, 180, { align: 'center' })
  doc.text(formatDate(new Date()), 105, 270, { align: 'center' })

  return doc.output('blob')
}
```

**Implementation:**

```typescript
// app/api/donations/receipt/[id]/route.ts
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const donation = await getDonationWithContact(params.id)

  // Generate unique receipt number if not exists
  if (!donation.tax_receipt_number) {
    const receiptNumber = generateReceiptNumber(donation)
    await supabase
      .from('donations')
      .update({ tax_receipt_number: receiptNumber })
      .eq('id', donation.id)
    donation.tax_receipt_number = receiptNumber
  }

  // Generate PDF
  const pdfBlob = generateTaxReceipt(donation, donation.contact)

  // Upload to Supabase Storage
  const fileName = `receipts/${donation.tax_year}/${donation.tax_receipt_number}.pdf`
  await supabase.storage
    .from('tax-receipts')
    .upload(fileName, pdfBlob)

  // Mark receipt sent
  await supabase
    .from('donations')
    .update({
      tax_receipt_sent: true,
      tax_receipt_sent_date: new Date().toISOString()
    })
    .eq('id', donation.id)

  // Return PDF
  return new Response(pdfBlob, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="${donation.tax_receipt_number}.pdf"`
    }
  })
}
```

**Bulk Year-End Receipts:**

```typescript
// app/api/donations/receipts/bulk/route.ts
export async function POST(request: Request) {
  const { taxYear } = await request.json()

  // Get all donations for tax year
  const donations = await supabase
    .from('donations')
    .select('*, contacts(*)')
    .eq('tax_year', taxYear)
    .order('contact_id', { ascending: true })

  // Group by contact
  const donationsByContact = groupBy(donations, d => d.contact_id)

  // Generate receipts
  for (const [contactId, donations] of Object.entries(donationsByContact)) {
    const contact = donations[0].contact
    const totalAmount = donations.reduce((sum, d) => sum + d.amount, 0)

    // Generate consolidated receipt
    const pdf = generateYearEndReceipt(contact, donations, totalAmount)

    // Upload and email
    await uploadAndEmailReceipt(contact, pdf, taxYear)
  }

  return Response.json({ success: true, count: Object.keys(donationsByContact).length })
}
```

### 4. QuickBooks Import

**Enhanced Import Script:**

```python
# scripts/import_quickbooks_donations.py
"""
FAANG-Quality QuickBooks Donation Import
Handles complex QB format, name matching, campaign attribution
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def parse_quickbooks_export(filepath):
    """
    Parse QuickBooks Statement of Activity Detail export

    Format:
    - First 3 rows: Header (org name, report type, date range)
    - Row 4: Column headers
    - Rows 5+: Transaction data
    - Totals and subtotals interspersed
    """
    # Find header row
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if 'Transaction date' in line:
            header_idx = i
            break

    if not header_idx:
        raise ValueError("Could not find header row")

    # Load data
    df = pd.read_csv(filepath, skiprows=header_idx, encoding='utf-8', on_bad_lines='skip')

    # Filter to valid transactions
    df = df[df['Transaction date'].notna()].copy()
    df = df[df['Name'].notna()].copy()

    # Parse amounts
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df[df['Amount'] > 0].copy()  # Only income (donations)

    return df

def normalize_donor_name(name):
    """Normalize donor names for matching"""
    if pd.isna(name):
        return None

    # Remove special markers: (C), {c}, etc.
    name = re.sub(r'\s*[\(\{][^\)\}]*[\)\}]\s*', ' ', str(name))

    # Remove extra whitespace
    name = ' '.join(name.split())

    return name.strip()

def extract_campaign(class_name, memo):
    """
    Extract campaign name from QuickBooks class and memo

    Examples:
    - "FUNDRAISING:Auction Fundraiser" → "Auction Fundraiser"
    - "Tree Sale" → "Tree Sale"
    - "DEVELOPMENT:30K in 30" → "30K in 30"
    """
    if pd.isna(class_name) and pd.isna(memo):
        return 'General Fund'

    # Try class first
    if not pd.isna(class_name):
        # Remove category prefix
        campaign = re.sub(r'^[A-Z\s]+:', '', str(class_name))
        if campaign and campaign != str(class_name):
            return campaign.strip()

    # Fall back to memo
    if not pd.isna(memo):
        return str(memo).strip()[:100]

    return 'General Fund'

def match_donor_to_contact(donor_name, conn):
    """
    Find contact by name matching
    Returns contact_id or None
    """
    normalized = normalize_donor_name(donor_name)
    if not normalized:
        return None

    query = """
        SELECT id, first_name, last_name, email
        FROM contacts
        WHERE
            deleted_at IS NULL
            AND LOWER(CONCAT(first_name, ' ', last_name)) = LOWER(%s)
        LIMIT 1
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (normalized,))
        result = cursor.fetchone()
        return result['id'] if result else None

def get_or_create_campaign(campaign_name, conn):
    """Get campaign ID or create new campaign"""
    # Check if exists
    query = "SELECT id FROM campaigns WHERE name = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (campaign_name,))
        result = cursor.fetchone()

        if result:
            return result['id']

    # Create new campaign
    slug = campaign_name.lower().replace(' ', '-').replace('_', '-')
    insert_query = """
        INSERT INTO campaigns (name, slug, campaign_type, active)
        VALUES (%s, %s, 'other', true)
        RETURNING id
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(insert_query, (campaign_name, slug))
        result = cursor.fetchone()
        conn.commit()
        return result['id']

def import_donations(df, conn):
    """
    Import donations to database

    Returns:
        - matched_count: Donations linked to existing contacts
        - skipped_count: Donations without contact match
        - new_campaigns: Campaigns created
    """
    matched = 0
    skipped = 0
    new_campaigns = set()

    donations_to_insert = []

    for _, row in df.iterrows():
        # Extract fields
        donor_name = row['Name']
        donation_date = pd.to_datetime(row['Transaction date']).date()
        amount = float(row['Amount'])
        transaction_type = row['Transaction type']
        receipt_num = row['Num'] if pd.notna(row['Num']) else None
        class_name = row['Class full name'] if 'Class full name' in row else None
        memo = row['Memo/Description'] if 'Memo/Description' in row else None
        account = row['Item split account'] if 'Item split account' in row else None

        # Match to contact
        contact_id = match_donor_to_contact(donor_name, conn)

        if not contact_id:
            logger.warning(f"No contact match for donor: {donor_name}")
            skipped += 1
            continue

        # Extract campaign
        campaign_name = extract_campaign(class_name, memo)
        campaign_id = get_or_create_campaign(campaign_name, conn)

        if campaign_name not in new_campaigns and campaign_name != 'General Fund':
            new_campaigns.add(campaign_name)

        # Prepare donation record
        donations_to_insert.append({
            'contact_id': contact_id,
            'campaign_id': campaign_id,
            'donation_date': donation_date,
            'amount': amount,
            'currency': 'USD',
            'source_system': 'quickbooks',
            'external_id': receipt_num,
            'transaction_type': transaction_type.lower().replace(' ', '_'),
            'qb_receipt_number': receipt_num,
            'qb_class': class_name,
            'qb_account': account,
            'campaign_name': campaign_name,
            'payment_method': parse_payment_method(account),
            'memo': memo,
            'tax_year': donation_date.year
        })

        matched += 1

    # Batch insert donations
    insert_query = """
        INSERT INTO donations (
            contact_id, campaign_id, donation_date, amount, currency,
            source_system, external_id, transaction_type,
            qb_receipt_number, qb_class, qb_account,
            campaign_name, payment_method, memo, tax_year
        ) VALUES (
            %(contact_id)s, %(campaign_id)s, %(donation_date)s, %(amount)s, %(currency)s,
            %(source_system)s, %(external_id)s, %(transaction_type)s,
            %(qb_receipt_number)s, %(qb_class)s, %(qb_account)s,
            %(campaign_name)s, %(payment_method)s, %(memo)s, %(tax_year)s
        )
        ON CONFLICT (source_system, external_id) DO NOTHING
    """

    with conn.cursor() as cursor:
        execute_batch(cursor, insert_query, donations_to_insert, page_size=100)

    conn.commit()

    logger.info(f"✅ Imported {matched} donations")
    logger.info(f"⚠️  Skipped {skipped} donations (no contact match)")
    logger.info(f"📊 Created {len(new_campaigns)} new campaigns")

    return {
        'matched': matched,
        'skipped': skipped,
        'new_campaigns': list(new_campaigns)
    }

def parse_payment_method(account_name):
    """Parse payment method from QB account name"""
    if pd.isna(account_name):
        return 'unknown'

    account = account_name.lower()

    if 'paypal' in account:
        return 'paypal'
    elif 'check' in account or 'checking' in account:
        return 'check'
    elif 'cash' in account:
        return 'cash'
    elif 'credit' in account or 'card' in account:
        return 'credit_card'
    elif 'bank' in account:
        return 'bank_transfer'
    else:
        return 'other'

def main():
    logger.info("=" * 80)
    logger.info("QUICKBOOKS DONATION IMPORT")
    logger.info("=" * 80)

    # Parse file
    df = parse_quickbooks_export('data/Donors_Quickbooks.csv')
    logger.info(f"Loaded {len(df)} transactions")

    # Connect to database
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))

    # Import
    results = import_donations(df, conn)

    # Close
    conn.close()

    logger.info("✅ Import complete!")
    return results

if __name__ == '__main__':
    main()
```

### 5. Donor Communication System

**Email Campaign Workflow:**

1. **Create Segment:**
   - Select donor status: Active / Lapsed / Major / First-time
   - Filter by date range, amount, campaign
   - Preview recipient count

2. **Choose Template:**
   - Thank you
   - Year-end appeal
   - Campaign launch
   - Impact report
   - Event invitation

3. **Personalize:**
   - Merge fields: name, total donated, last donation, etc.
   - Preview for sample donors

4. **Send:**
   - Schedule or send immediately
   - Track opens/clicks (if using email service)
   - Log in communication history

**Notes System:**

```typescript
// Database: Use existing contact_notes table
CREATE TABLE contact_notes (
  id UUID PRIMARY KEY,
  contact_id UUID REFERENCES contacts(id),
  note_type TEXT, -- 'phone_call', 'email', 'meeting', 'general'
  subject TEXT,
  content TEXT,
  author_name TEXT,
  is_pinned BOOLEAN,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);

// UI: Add note form in donor detail page
<AddNoteForm
  contactId={donorId}
  onSave={async (note) => {
    await supabase.from('contact_notes').insert({
      contact_id: donorId,
      note_type: note.type,
      subject: note.subject,
      content: note.content,
      author_name: currentUser.name
    })
  }}
/>
```

---

## Implementation Roadmap

### Phase 1: Database Foundation (Week 1)

**Goal:** Set up complete data model and migrate existing data

**Tasks:**
1. Create `donations` table with full schema ✓
2. Create `campaigns` table ✓
3. Add donor fields to `contacts` table ✓
4. Create database functions (triggers, aggregates) ✓
5. Set up Row-Level Security policies ✓
6. Generate TypeScript types from schema ✓

**Migration Steps:**
1. Request full historical QuickBooks data (2019-2024)
2. Write enhanced import script with campaign extraction
3. Run import for all years
4. Validate data quality (match rates, duplicates)
5. Calculate donor aggregates and status

**Deliverables:**
- Complete donation database with 5+ years of history
- All 568 QuickBooks donors matched to contacts
- Donor status and tier calculated for all
- 10-15 campaigns automatically created

**Testing:**
- Verify trigger updates (add donation → contact totals update)
- Check donor status calculations
- Validate campaign totals
- Test data integrity constraints

### Phase 2: Core UI - Donor Management (Week 2)

**Goal:** Build essential donor browsing and management pages

**Tasks:**
1. Build `/donors` dashboard page
   - Metrics cards (total donations, active donors, YTD)
   - Donor list table with sorting/filtering
   - Pagination
   - Export to CSV
2. Build `/donors/[id]` detail page
   - Donor profile header with stats
   - Donation timeline (grouped by year)
   - Campaign support summary
   - Notes section
   - Quick actions
3. Build `/donations` transaction list
   - Filterable table
   - Search functionality
   - Bulk operations UI
4. Implement search and filtering
   - Real-time search
   - Filter by status, amount, date, campaign
   - URL state management (searchParams)

**Components to Build:**
- `DonorListTable` - Reusable sortable table
- `DonorCard` - Profile summary card
- `DonationTimeline` - Chronological donation list
- `CampaignBadge` - Campaign display component
- `DonorStatusBadge` - Status indicator
- `TierBadge` - Tier display (Bronze/Silver/Gold/Platinum)

**API Routes:**
- `GET /api/donors` - List with filters
- `GET /api/donors/[id]` - Detail with donations
- `GET /api/donations` - Transaction list
- `GET /api/donors/export` - CSV export

**Deliverables:**
- Functional donor browsing interface
- Staff can view donor profiles and history
- Export donor lists to CSV
- Search and filter donors by multiple criteria

**Testing:**
- Test pagination with 500+ donors
- Verify filtering combinations
- Test export with large datasets
- Check responsive design (mobile/tablet)

### Phase 3: Campaign Management (Week 3)

**Goal:** Enable campaign tracking and performance analytics

**Tasks:**
1. Build `/campaigns` list page
   - Active campaigns with progress bars
   - Past campaigns list
   - Create new campaign form
2. Build `/campaigns/[slug]` detail page
   - Campaign stats and progress
   - Donation trends chart
   - Top donors list
   - New vs. repeat donors breakdown
   - Export campaign report
3. Campaign CRUD operations
   - Create campaign
   - Edit campaign (name, goals, dates)
   - Archive campaign
4. Link donations to campaigns
   - Auto-assign during import
   - Manual re-assignment UI
5. Campaign analytics
   - Progress toward goal
   - Donation timeline chart
   - Donor acquisition metrics

**Components:**
- `CampaignCard` - Campaign summary with progress
- `CampaignProgressBar` - Visual goal progress
- `DonationTrendChart` - Line/bar chart (Recharts)
- `TopDonorsList` - Leaderboard component
- `CampaignForm` - Create/edit form

**API Routes:**
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/[slug]` - Campaign detail
- `POST /api/campaigns` - Create campaign
- `PUT /api/campaigns/[id]` - Update campaign
- `GET /api/campaigns/[slug]/donations` - Campaign donations
- `GET /api/campaigns/[slug]/report` - Export report

**Deliverables:**
- Campaign management interface
- Real-time campaign performance tracking
- Visual progress indicators
- Campaign reports (PDF/CSV export)

**Testing:**
- Test campaign creation and editing
- Verify totals update when donations added
- Test chart rendering with various data
- Validate goal progress calculations

### Phase 4: Automation & Stewardship (Week 4)

**Goal:** Automate donor acknowledgment and communication

**Tasks:**
1. Thank-you email system
   - Email templates (React Email)
   - Template selection logic (by amount)
   - Personalization engine
   - Send API integration (Resend/SendGrid)
   - Bulk send functionality
2. Tax receipt generation
   - PDF generation (jsPDF)
   - Receipt template (IRS-compliant)
   - Unique receipt number generation
   - Supabase Storage upload
   - Email delivery
   - Bulk year-end receipt generation
3. Bulk operations
   - Mark thank-yous sent
   - Generate receipts for selection
   - Export to CSV
   - Update campaigns
4. Communication logging
   - Track emails sent
   - Store in contact notes
   - Display in donor timeline

**Email Templates:**
- Standard thank you (<$250)
- Premium thank you ($250-$999)
- Major donor alert (>$1,000)
- First-time donor welcome
- Year-end recap

**API Routes:**
- `POST /api/donations/send-thank-you` - Send thank you
- `GET /api/donations/receipt/[id]` - Generate single receipt
- `POST /api/donations/receipts/bulk` - Bulk year-end receipts
- `POST /api/donations/bulk-update` - Bulk operations

**Deliverables:**
- Automated thank-you email system
- On-demand tax receipt generation
- Bulk year-end receipt generation
- Communication tracking in donor profiles

**Testing:**
- Test email delivery and formatting
- Verify PDF generation and storage
- Test bulk operations with 100+ records
- Validate receipt number uniqueness

### Phase 5: Analytics & Reporting (Week 5)

**Goal:** Provide data-driven insights for fundraising decisions

**Tasks:**
1. Build `/analytics/donors` dashboard
   - Donation trends chart (multi-year)
   - Donor segmentation pie chart
   - Retention analysis
   - Giving level distribution
   - Campaign comparison
2. Actionable reports
   - Lapsed donors list (for reactivation)
   - Major donors list (for stewardship)
   - First-time donors (for cultivation)
   - Recurring donors (for recognition)
3. Export functionality
   - Export reports to PDF
   - Export data to CSV
   - Custom date ranges
   - Filtered exports
4. Advanced analytics
   - Year-over-year comparison
   - Donor lifetime value
   - Average donation by segment
   - Monthly giving patterns

**Charts & Visualizations:**
- Line chart: Donation trends over time
- Pie chart: Donor segmentation
- Bar chart: Retention rates by year
- Histogram: Giving level distribution
- Stacked bar: Campaign comparison

**API Routes:**
- `GET /api/analytics/trends` - Donation trends data
- `GET /api/analytics/segmentation` - Donor breakdown
- `GET /api/analytics/retention` - Retention metrics
- `GET /api/reports/lapsed-donors` - Lapsed donor report
- `GET /api/reports/major-donors` - Major donor report
- `POST /api/reports/export` - Export to PDF

**Deliverables:**
- Comprehensive analytics dashboard
- Visual charts and graphs
- Downloadable reports (PDF/CSV)
- Actionable donor lists for outreach

**Testing:**
- Test chart rendering with real data
- Verify calculations (retention, averages)
- Test report generation performance
- Validate export file formats

---

## Data Migration Strategy

### Step 1: Prepare Historical Data

**Action Items:**
1. **Request full QuickBooks export (2019-2024)**
   - Format: Statement of Activity Detail
   - Date range: All dates (not just 2024)
   - Include all income categories
   - Export to CSV

2. **Validate export file**
   - Check format matches existing export
   - Verify transaction count (expect 5,000+)
   - Confirm date range coverage

### Step 2: Pre-Migration Analysis

**Run analysis script:**
```bash
python3 scripts/analyze_donors_quickbooks.py \
  --file historical_donors_2019_2024.csv \
  --output analysis_report.json
```

**Review:**
- Total unique donors
- Total donation amount
- Match rate to existing contacts
- New donors to create
- Campaigns to extract
- Potential duplicates

### Step 3: Contact Matching & Creation

**Approach 1: Match to Existing Contacts**
```python
# For each QuickBooks donor:
# 1. Normalize name
# 2. Search for contact by name
# 3. If match found, link donation
# 4. If no match, flag for review
```

**Approach 2: Handle Unmatched Donors (241 currently)**

**Option A:** Cross-reference with QuickBooks Contacts export
- Load QuickBooks Contacts CSV
- Match by name
- Extract email addresses
- Create contacts with emails
- Import donations

**Option B:** Make email optional (schema change)
```sql
ALTER TABLE contacts ALTER COLUMN email DROP NOT NULL;

ALTER TABLE contacts ADD CONSTRAINT contacts_must_have_contact_info
  CHECK (
    email IS NOT NULL OR
    phone IS NOT NULL OR
    address_line_1 IS NOT NULL
  );
```

**Recommendation:** Use Option A first, then Option B for remaining

### Step 4: Campaign Extraction

**Mapping QuickBooks Classes to Campaigns:**

```python
# Automated extraction from "Class full name" field
class_mappings = {
    'FUNDRAISING': {
        'Auction Fundraiser': 'Auction Fundraiser',
        'Tree Sale': 'Tree Sale {year}',
        '30K in 30': '30K in 30 Campaign',
        'Fire Mitigation': 'Fire Mitigation Fund'
    },
    'DEVELOPMENT': {
        'Annual Appeal': 'Annual Appeal {year}',
        'Capital Campaign': 'Capital Campaign'
    }
}

# Extract year from transaction date
# Create campaign if not exists
# Link donation to campaign
```

**Expected Campaigns (15-20):**
- Tree Sale (2019, 2020, 2021, 2022, 2023, 2024)
- Annual Appeal (by year)
- Fire Mitigation Fund
- Auction Fundraiser (by year)
- 30K in 30 Campaign
- Capital Campaign
- Emergency Fund
- General Fund (catchall)

### Step 5: Import Execution

**Run import script:**
```bash
python3 scripts/import_quickbooks_donations.py \
  --file historical_donors_2019_2024.csv \
  --dry-run  # First run to preview

# After validation:
python3 scripts/import_quickbooks_donations.py \
  --file historical_donors_2019_2024.csv \
  --commit
```

**Import Process:**
1. Parse QuickBooks export
2. Normalize donor names
3. Match to contacts
4. Extract campaigns
5. Create campaign records
6. Insert donations (batch)
7. Trigger aggregate updates
8. Calculate donor status/tier
9. Generate summary report

**Expected Results:**
- 5,000+ donation records created
- 500-600 donors matched to contacts
- 15-20 campaigns created
- All donor aggregates updated
- All donor statuses calculated

### Step 6: Data Validation

**Run validation queries:**

```sql
-- Total donations by year
SELECT
  EXTRACT(YEAR FROM donation_date) as year,
  COUNT(*) as count,
  SUM(amount) as total
FROM donations
GROUP BY year
ORDER BY year;

-- Donor counts by status
SELECT
  donor_status,
  COUNT(*) as count,
  SUM(total_donated) as total
FROM contacts
WHERE total_donated > 0
GROUP BY donor_status;

-- Campaign performance
SELECT
  name,
  total_raised,
  donor_count,
  donation_count
FROM campaigns
ORDER BY total_raised DESC;

-- Verify triggers working
SELECT
  c.first_name,
  c.last_name,
  c.total_donated,
  c.donation_count,
  COALESCE(SUM(d.amount), 0) as calculated_total,
  COUNT(d.id) as calculated_count
FROM contacts c
LEFT JOIN donations d ON d.contact_id = c.id AND d.deleted_at IS NULL
WHERE c.total_donated > 0
GROUP BY c.id
HAVING c.total_donated != COALESCE(SUM(d.amount), 0)
  OR c.donation_count != COUNT(d.id);
-- Should return 0 rows (no mismatches)
```

### Step 7: Handle Edge Cases

**Duplicate Donors:**
- Flag potential duplicates (same name, different contact IDs)
- Provide merge tool in UI
- Transfer donations to primary contact
- Soft delete duplicate contact

**Missing Data:**
- Donations without campaign → assign to "General Fund"
- Donations without payment method → mark as "unknown"
- Donors without email → flag for lookup

**Data Conflicts:**
- QuickBooks total != database total → investigate individual transactions
- Contact has both purchase and donation data → verify separation

---

## Integration Points

### QuickBooks Integration (Current: Manual CSV)

**Current Process:**
1. Export from QuickBooks: Reports > Statement of Activity Detail
2. Date range: Select period (monthly/quarterly/annual)
3. Save as CSV
4. Upload to import script
5. Run import
6. Review summary report

**Future Enhancement: API Integration**

**QuickBooks Online API:**
- OAuth 2.0 authentication
- Query transactions by date
- Real-time sync (nightly batch)
- Webhook for new donations

**Implementation:**
```typescript
// lib/integrations/quickbooks.ts
import { QuickBooksAPI } from 'quickbooks-sdk'

export async function syncQuickBooksDonations(since: Date) {
  const qb = new QuickBooksAPI({
    clientId: process.env.QB_CLIENT_ID,
    clientSecret: process.env.QB_CLIENT_SECRET,
    realmId: process.env.QB_REALM_ID
  })

  // Query new income transactions
  const transactions = await qb.query(`
    SELECT * FROM Invoice
    WHERE TxnDate > '${since.toISOString()}'
      AND PrivateNote LIKE '%donation%'
  `)

  // Import each transaction
  for (const txn of transactions) {
    await importDonation({
      donorName: txn.CustomerRef.name,
      amount: txn.TotalAmt,
      date: txn.TxnDate,
      externalId: txn.Id,
      campaign: extractCampaign(txn.ClassRef),
      paymentMethod: txn.PaymentMethodRef.name
    })
  }
}
```

**Pros:**
- Real-time data sync
- No manual export
- Webhook notifications

**Cons:**
- Requires QuickBooks developer account
- OAuth setup complexity
- Ongoing maintenance

**Recommendation:** Start with manual CSV import (Phase 1-5), evaluate API integration later based on volume and frequency needs.

### Email Service Integration

**Options:**

**1. Resend (Recommended)**
- Modern API
- React Email templates
- Analytics included
- Generous free tier
- Simple setup

```typescript
import { Resend } from 'resend'

const resend = new Resend(process.env.RESEND_API_KEY)

await resend.emails.send({
  from: 'All Seasons Chalice Church <donations@allseasonschurch.org>',
  to: donor.email,
  subject: 'Thank you for your donation',
  react: ThankYouEmail({ donorName, amount, campaignName })
})
```

**2. SendGrid**
- Enterprise-grade
- Advanced analytics
- A/B testing
- Template versioning

**3. Mailchimp**
- Campaign builder
- Segmentation
- Automation workflows
- CRM features

**Recommendation:** Resend for thank-you automation, consider Mailchimp for broader donor communication campaigns.

### PDF Generation

**Options:**

**1. jsPDF (Client-side)**
- Lightweight
- No external dependencies
- Good for simple receipts
- Limited styling

**2. Puppeteer (Server-side)**
- Full HTML/CSS support
- Perfect rendering
- Can use React components
- Requires headless Chrome

**3. PDFKit (Node.js)**
- Server-side
- Fine-grained control
- Good performance
- Steeper learning curve

**Recommendation:** Start with jsPDF for simplicity, migrate to Puppeteer if need advanced formatting.

### Storage Integration

**Supabase Storage:**
- Built-in to Supabase
- S3-compatible
- Access control via RLS
- CDN included

**Structure:**
```
tax-receipts/
  2024/
    2024-0001.pdf
    2024-0002.pdf
  2023/
    2023-0001.pdf
```

**Access Pattern:**
```typescript
// Upload receipt
const { data } = await supabase.storage
  .from('tax-receipts')
  .upload(`${taxYear}/${receiptNumber}.pdf`, pdfBlob)

// Generate signed URL (1 hour expiry)
const { data: { signedUrl } } = await supabase.storage
  .from('tax-receipts')
  .createSignedUrl(`${taxYear}/${receiptNumber}.pdf`, 3600)

// Email link to donor
await sendEmail({
  to: donor.email,
  subject: 'Your tax receipt',
  html: `Download your receipt: <a href="${signedUrl}">Download PDF</a>`
})
```

---

## Success Metrics & KPIs

### Phase 1 Success Criteria (Database)

**Metrics:**
- ✅ 500+ donors imported with complete history
- ✅ $500,000+ in total donations tracked
- ✅ 90%+ contact match rate from QuickBooks
- ✅ 5 years of historical data (2019-2024)
- ✅ 15+ campaigns auto-created and linked
- ✅ All donor aggregates calculated correctly
- ✅ Database triggers functional (test: add donation → totals update)

**Validation Queries:**
```sql
-- Check match rate
SELECT
  (SELECT COUNT(DISTINCT contact_id) FROM donations) * 100.0 /
  (SELECT COUNT(DISTINCT name) FROM quickbooks_import)
  AS match_rate_percent;
-- Target: >90%

-- Verify data completeness
SELECT COUNT(*) FROM donations WHERE donation_date < '2020-01-01';
-- Target: >0 (has 2019 data)

-- Check donor status distribution
SELECT donor_status, COUNT(*) FROM contacts WHERE total_donated > 0 GROUP BY donor_status;
-- Should show: active, lapsed, major, recurring, first_time
```

### Phase 2 Success Criteria (Core UI)

**Metrics:**
- ✅ Load donor list <2 seconds (500+ donors)
- ✅ Search results <500ms
- ✅ Donor detail page load <1 second
- ✅ Export 500 donors to CSV <5 seconds
- ✅ Mobile responsive on all pages
- ✅ Accessibility: WCAG 2.1 AA compliant

**User Acceptance:**
- Staff can find any donor in <10 seconds
- Donation history clearly displayed and accurate
- Export functionality works reliably

### Phase 3 Success Criteria (Campaigns)

**Metrics:**
- ✅ 15+ campaigns created and tracked
- ✅ Campaign totals match donation sums (100% accuracy)
- ✅ Charts render <1 second
- ✅ Campaign reports generate <3 seconds

**Business Value:**
- Staff can see real-time campaign progress
- Top donors for each campaign identified
- Historical campaign comparison available

### Phase 4 Success Criteria (Automation)

**Metrics:**
- ✅ 80%+ thank-you email delivery rate
- ✅ Tax receipts generate in <5 seconds each
- ✅ Bulk year-end receipts (500 donors) <2 minutes
- ✅ Email tracking: open rates >40%

**Operational Impact:**
- <1 hour to send thank-yous for 100 donations (vs. 5 hours manual)
- <1 hour to generate year-end receipts for all donors (vs. 10 hours manual)
- 90% reduction in manual donor admin time

### Phase 5 Success Criteria (Analytics)

**Metrics:**
- ✅ Dashboard loads <2 seconds
- ✅ Charts accurate and match raw data
- ✅ Reports export successfully
- ✅ Retention calculations match manual audit

**Decision Support:**
- Lapsed donor list used for reactivation campaign
- Major donor stewardship plan created from report
- Year-over-year trends inform goal setting

### Overall Success Criteria

**6 Months Post-Launch:**
- 90% staff satisfaction with donor module
- 25% increase in donor retention (identified and re-engaged lapsed donors)
- 50% reduction in time spent on donor administration
- 100% tax receipts issued on-time
- Zero compliance issues (IRS, data accuracy)

**12 Months Post-Launch:**
- 1,000+ total donors tracked
- $750,000+ total donations in system
- 5 successful fundraising campaigns managed through system
- 80% donor communication automated
- Data-driven fundraising strategy implemented

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk 1: Data Migration Errors**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Dry-run imports with validation
  - Manual QA on sample of 50 records
  - Rollback plan (database backup before import)
  - Reconciliation report (QB totals vs. database totals)

**Risk 2: Performance Issues with Large Datasets**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Proper database indexing
  - Pagination on all list views
  - Server-side filtering
  - Database query optimization
  - Load testing with 10,000+ records

**Risk 3: QuickBooks Format Changes**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Flexible parsing logic
  - Version detection in import script
  - Error handling and logging
  - Documentation of expected format

**Risk 4: Email Delivery Failures**
- **Probability:** Low
- **Impact:** Low
- **Mitigation:**
  - Use reputable email service (Resend/SendGrid)
  - Retry logic for failures
  - Queue system for bulk sends
  - Monitor bounce/complaint rates
  - Fallback: manual email from records

### Data Quality Risks

**Risk 1: Duplicate Donors**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Name normalization (remove special characters)
  - Fuzzy matching for similar names
  - Duplicate detection UI
  - Manual review workflow
  - Merge tool for confirmed duplicates

**Risk 2: Missing/Incomplete Data**
- **Probability:** Medium
- **Impact:** Low
- **Mitigation:**
  - Validation rules on import
  - Default values for optional fields
  - Data quality dashboard
  - Regular audits
  - Staff training on data entry

**Risk 3: Contact Matching Errors**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Conservative matching (exact name only)
  - Manual review of unmatched donors
  - Re-match tool in UI
  - Audit log of all matches

### Business Risks

**Risk 1: Staff Adoption**
- **Probability:** Low
- **Impact:** High
- **Mitigation:**
  - User training sessions
  - Video tutorials
  - Clear documentation
  - Gradual rollout (read-only first)
  - Collect feedback early

**Risk 2: Historical Data Unavailable**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Request data export early
  - Work with QB administrator
  - Alternative: manual data entry for high-value donors
  - Fallback: start with 2024 data only

**Risk 3: Compliance Issues (Tax Receipts)**
- **Probability:** Low
- **Impact:** High
- **Mitigation:**
  - IRS guidelines review
  - Template approved by accountant/lawyer
  - Audit all receipts before year-end
  - Professional review of first batch

### Security Risks

**Risk 1: Unauthorized Access to Donor Data**
- **Probability:** Low
- **Impact:** High
- **Mitigation:**
  - Row-Level Security (RLS) on all tables
  - Staff-only access (verified_staff check)
  - Audit logging of all access
  - Regular security reviews
  - MFA for staff accounts

**Risk 2: Data Breach**
- **Probability:** Very Low
- **Impact:** Very High
- **Mitigation:**
  - Supabase enterprise security
  - Encryption at rest and in transit
  - Regular backups
  - Incident response plan
  - GDPR/CCPA compliance

---

## Open Questions & Decisions

### Critical Decisions Needed

**1. Email Requirement for Donor Records**
- **Question:** Should we allow contacts without email addresses?
- **Context:** 241 donors in QuickBooks have no email
- **Options:**
  - A) Make email optional (schema change), allow donor-only records
  - B) Require email, skip donors without emails
  - C) Manual email lookup for high-value donors, skip rest
- **Recommendation:** Option C (hybrid approach)
- **Decision Needed By:** Before Phase 1 migration

**2. Historical Data Scope**
- **Question:** Import full 2019-2024 data or start with recent years?
- **Context:** 2019-2021 data may have lower quality, older donors may be inactive
- **Options:**
  - A) Import all 5 years (2019-2024)
  - B) Import recent 3 years (2022-2024)
  - C) Import 2024 only (current state)
- **Recommendation:** Option A (full history for lifetime value calculations)
- **Decision Needed By:** Before Phase 1 migration

**3. QuickBooks Sync Frequency**
- **Question:** How often should we import QuickBooks data?
- **Options:**
  - A) Manual CSV import monthly
  - B) Manual CSV import quarterly
  - C) Automated API sync (future Phase 6)
- **Recommendation:** Option A for first year, evaluate API in Year 2
- **Decision Needed By:** Before Phase 1 launch

**4. Thank You Automation Scope**
- **Question:** Fully automate or require manual approval?
- **Options:**
  - A) Fully automated for all donations
  - B) Automated for <$250, manual for larger
  - C) Draft emails, require staff approval before send
- **Recommendation:** Option B (balances automation with personal touch)
- **Decision Needed By:** Before Phase 4 implementation

**5. Tax Receipt Timing**
- **Question:** When to generate tax receipts?
- **Options:**
  - A) Immediately after each donation
  - B) Quarterly batches
  - C) Year-end only
- **Recommendation:** Option A (immediate), with bulk year-end recap
- **Decision Needed By:** Before Phase 4 implementation

### Information Needed

**From Organization:**
1. Can you provide full QuickBooks export (2019-2024)?
2. Do you have QuickBooks Contacts export with email addresses?
3. Who will manage the donor module (staff roles)?
4. What email address should thank-yous come from?
5. What is your EIN for tax receipts?
6. Do you have existing email templates to adapt?
7. What are your donor tier thresholds? (currently proposing: Bronze <$1k, Silver $1-5k, Gold $5-10k, Platinum $10k+)

**From Technical Team:**
8. Email service preference: Resend vs. SendGrid vs. Mailchimp?
9. PDF generation: jsPDF vs. Puppeteer?
10. Hosting: Supabase sufficient or need separate infrastructure?

### Assumptions to Validate

**Data Assumptions:**
1. QuickBooks "Name" field contains donor name (validated ✓)
2. "Class full name" contains campaign name (validated ✓)
3. Positive amounts = donations, negative = refunds (validated ✓)
4. Receipt numbers are unique within year (to validate)
5. Most donors can be matched by name to existing contacts (241/568 = 42% unmatched currently)

**Business Assumptions:**
1. Staff will dedicate time for training and adoption
2. Donor communication will shift from manual to automated
3. Historical data is valuable for retention analysis
4. QuickBooks will remain primary financial system
5. Donor privacy is paramount (no sharing data externally)

---

## Appendix

### A. QuickBooks Export Format

**File:** `Donors_Quickbooks.csv`

**Header Rows:**
```
Row 1: Statement of Activity Detail
Row 2: All Seasons Chalice Church
Row 3: All Dates
Row 4: (blank)
Row 5: Transaction date,Transaction type,Num,Name,Location,Class full name,Memo/Description,Item split account,Amount,Balance
```

**Sample Data Row:**
```
05/08/2019,Invoice,486,Jeff Stein,,COST OF DOING BUSINESS,ASC Fundraiser,ACCOUNTS RECEIVABLE,22.00,22.00
```

**Field Descriptions:**
- **Transaction date:** Date of donation (MM/DD/YYYY)
- **Transaction type:** Invoice, Sales Receipt, Deposit, Journal Entry
- **Num:** Receipt/Invoice number
- **Name:** Donor name (may contain "(C)" or "{c}" markers)
- **Location:** Usually blank
- **Class full name:** Campaign category (e.g., "FUNDRAISING:Tree Sale")
- **Memo/Description:** Additional notes
- **Item split account:** Payment account (PayPal Bank, Cash, etc.)
- **Amount:** Donation amount (positive for income)
- **Balance:** Running total (ignore)

### B. Donor Status Definitions

**Status Categories:**

1. **First-Time Donor**
   - Definition: Has made exactly 1 donation
   - Purpose: Identify for cultivation and conversion to recurring
   - Example: New donor from 2024 Tree Sale

2. **Active Donor**
   - Definition: 2+ donations, last donation within 12 months
   - Purpose: Regular supporters, maintain engagement
   - Example: Donated Nov 2024 and previously in 2023

3. **Lapsed Donor**
   - Definition: 2+ donations, last donation 12-24 months ago
   - Purpose: Re-engagement opportunity
   - Example: Last donation was Jan 2023

4. **Inactive Donor**
   - Definition: 2+ donations, last donation 24+ months ago
   - Purpose: Archive or long-term reactivation
   - Example: Last donation was 2021

5. **Recurring Donor**
   - Definition: 3+ donations showing yearly or regular pattern
   - Purpose: Loyal base, VIP stewardship
   - Example: Donated annually for Tree Sale 2020-2024

6. **Major Donor**
   - Definition: Lifetime total ≥ $1,000
   - Purpose: Premium stewardship, personal outreach
   - Example: Total donated = $2,450 across 12 donations

### C. Database Schema Diagrams

**Entity Relationship Diagram:**

```
┌─────────────────┐
│    contacts     │
├─────────────────┤
│ id (PK)         │
│ email           │
│ first_name      │
│ last_name       │
│ ...             │
│ total_donated   │◄──┐
│ donation_count  │   │ Computed by trigger
│ donor_status    │   │
│ donor_tier      │   │
└─────────────────┘   │
         △            │
         │            │
         │ 1:N        │
         │            │
┌─────────────────┐   │
│   donations     │───┘
├─────────────────┤
│ id (PK)         │
│ contact_id (FK) │
│ campaign_id (FK)│──┐
│ donation_date   │  │
│ amount          │  │ 1:N
│ source_system   │  │
│ thank_you_sent  │  │
│ tax_receipt_sent│  │
└─────────────────┘  │
                     │
                     ▼
              ┌─────────────────┐
              │   campaigns     │
              ├─────────────────┤
              │ id (PK)         │
              │ name            │
              │ goal_amount     │
              │ total_raised    │◄── Computed by trigger
              │ donor_count     │
              └─────────────────┘
```

### D. API Endpoints Summary

**Donors:**
- `GET /api/donors` - List donors with filters
- `GET /api/donors/[id]` - Donor detail
- `GET /api/donors/export` - Export to CSV
- `GET /api/donors/stats` - Dashboard metrics

**Donations:**
- `GET /api/donations` - List donations
- `POST /api/donations` - Create donation (manual entry)
- `PUT /api/donations/[id]` - Update donation
- `DELETE /api/donations/[id]` - Delete donation
- `POST /api/donations/import` - Import from CSV
- `POST /api/donations/send-thank-you` - Send thank you
- `GET /api/donations/receipt/[id]` - Generate receipt
- `POST /api/donations/receipts/bulk` - Bulk receipts
- `POST /api/donations/bulk-update` - Bulk operations

**Campaigns:**
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/[slug]` - Campaign detail
- `POST /api/campaigns` - Create campaign
- `PUT /api/campaigns/[id]` - Update campaign
- `DELETE /api/campaigns/[id]` - Archive campaign
- `GET /api/campaigns/[slug]/donations` - Campaign donations
- `GET /api/campaigns/[slug]/report` - Export report

**Analytics:**
- `GET /api/analytics/trends` - Donation trends
- `GET /api/analytics/segmentation` - Donor breakdown
- `GET /api/analytics/retention` - Retention metrics
- `GET /api/reports/lapsed-donors` - Lapsed donor report
- `GET /api/reports/major-donors` - Major donor report
- `POST /api/reports/export` - Export to PDF

### E. Component Library

**Reusable Components:**

1. **Data Display:**
   - `DonorListTable` - Sortable, filterable table
   - `DonationTimeline` - Chronological donation list
   - `CampaignCard` - Campaign summary card
   - `MetricsCard` - Stats card with trend indicator

2. **Status Indicators:**
   - `DonorStatusBadge` - Color-coded status
   - `TierBadge` - Bronze/Silver/Gold/Platinum
   - `CampaignProgressBar` - Goal progress
   - `AcknowledgmentStatus` - Thank you/receipt icons

3. **Charts:**
   - `DonationTrendChart` - Line chart (Recharts)
   - `SegmentationPieChart` - Donor breakdown
   - `RetentionBarChart` - YoY retention
   - `GivingLevelHistogram` - Amount distribution

4. **Forms:**
   - `DonationForm` - Create/edit donation
   - `CampaignForm` - Create/edit campaign
   - `FilterPanel` - Advanced filtering
   - `BulkActionBar` - Bulk operations

5. **Utilities:**
   - `ExportButton` - CSV/PDF export
   - `SearchInput` - Debounced search
   - `DateRangePicker` - Date filtering
   - `AmountFilter` - Range slider

### F. Testing Plan

**Unit Tests:**
- Donor status calculation logic
- Donor tier assignment
- Campaign total calculations
- Receipt number generation
- Name normalization
- Email template rendering

**Integration Tests:**
- Donation creation → contact totals update
- Campaign assignment → campaign totals update
- Thank you send → communication log created
- Receipt generation → storage upload
- Import script → database records created

**End-to-End Tests:**
- Complete donor journey (view → detail → export)
- Donation import flow
- Thank you workflow
- Receipt generation workflow
- Campaign management flow

**Performance Tests:**
- Load 1,000 donors in <2 seconds
- Search 1,000 donors in <500ms
- Export 1,000 donors in <10 seconds
- Generate 100 receipts in <60 seconds
- Bulk update 500 records in <30 seconds

**Accessibility Tests:**
- Keyboard navigation on all pages
- Screen reader compatibility
- Color contrast (WCAG AA)
- Focus indicators
- ARIA labels

### G. Deployment Checklist

**Pre-Deployment:**
- [ ] Database migration tested on staging
- [ ] All TypeScript types generated
- [ ] Environment variables configured
- [ ] RLS policies tested
- [ ] Staff accounts created
- [ ] Email service configured
- [ ] Storage buckets created
- [ ] PDF templates tested
- [ ] Import scripts validated
- [ ] Data backup created

**Deployment:**
- [ ] Run database migrations
- [ ] Deploy frontend (Vercel)
- [ ] Configure environment variables
- [ ] Test authentication
- [ ] Verify RLS policies
- [ ] Run smoke tests
- [ ] Import historical data
- [ ] Validate data integrity
- [ ] Test email sending
- [ ] Test PDF generation

**Post-Deployment:**
- [ ] Staff training session
- [ ] Documentation provided
- [ ] Monitor error logs
- [ ] Verify performance metrics
- [ ] Collect user feedback
- [ ] Schedule first data sync
- [ ] Plan iteration 1 improvements

### H. Resources & References

**Documentation:**
- QuickBooks: [QuickBooks Online API Docs](https://developer.intuit.com/app/developer/qbo/docs/get-started)
- Supabase: [Database Functions](https://supabase.com/docs/guides/database/functions)
- React Email: [Email Templates](https://react.email/docs/introduction)
- Recharts: [Chart Library](https://recharts.org/en-US/)

**Best Practices:**
- [IRS Publication 1771](https://www.irs.gov/pub/irs-pdf/p1771.pdf) - Charitable Contributions
- [Nonprofit Donor Management](https://www.councilofnonprofits.org/tools-resources/donor-management)
- [GDPR Compliance for Nonprofits](https://gdpr.eu/compliance/)

**Design References:**
- Bloomerang (Donor CRM)
- DonorPerfect
- Little Green Light
- Salesforce Nonprofit Cloud

---

## Document Control

**Version History:**

| Version | Date       | Author  | Changes                          |
|---------|------------|---------|----------------------------------|
| 1.0     | 2025-11-15 | Claude  | Initial comprehensive plan       |

**Review & Approval:**

| Role            | Name | Date | Signature |
|-----------------|------|------|-----------|
| Technical Lead  |      |      |           |
| Product Owner   |      |      |           |
| Finance/Admin   |      |      |           |

**Next Steps:**

1. **Review this document** with key stakeholders
2. **Answer open questions** (Section 13)
3. **Get approval** to proceed
4. **Schedule Phase 1** kick-off
5. **Request QuickBooks data** (2019-2024 export)

---

**Document Status:** ✅ Ready for Review

**Estimated Effort:** 4-5 weeks (Phases 1-5)

**Prerequisites:** Full QuickBooks historical data export

**Business Value:** High - Separates donations from sales, enables data-driven fundraising, automates donor stewardship

**Technical Risk:** Low - Builds on existing infrastructure, proven patterns

**Recommendation:** Proceed with phased implementation starting with Phase 1 (Database Foundation)

---

*End of Document*
