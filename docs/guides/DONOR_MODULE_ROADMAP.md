# Donor Module - Future Implementation Roadmap

**Created:** 2025-11-15
**Context:** QuickBooks donor enrichment completed
**Status:** Planning document for future implementation

---

## Background

We successfully enriched 342 contacts with $49,733.33 in donation data from QuickBooks. However, several limitations were discovered that should be addressed in a dedicated donor management module.

**Current State:**
- ✅ 342 contacts enriched with donation data
- ✅ $49,733.33 in donations tracked
- ⚠️ Donations mixed with product purchases in `total_spent` field
- ⚠️ 241 new donors couldn't be imported (no email addresses)
- ⚠️ Only 2024 transaction data included (missing 2019-2023)
- ⚠️ No transaction-level detail preserved

---

## Phase 2: Separate Donation Fields

### Add Donation-Specific Fields to Contacts Table

```sql
-- Migration: Add donation tracking fields
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS total_donated DECIMAL(10,2) DEFAULT 0;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS donation_count INTEGER DEFAULT 0;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS first_donation_date DATE;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_donation_date DATE;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS largest_donation DECIMAL(10,2) DEFAULT 0;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS average_donation DECIMAL(10,2) DEFAULT 0;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS donor_status TEXT; -- 'active', 'lapsed', 'major', 'recurring'
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS quickbooks_donor_id TEXT;
```

### Data Migration

**Migrate QuickBooks donation data from `total_spent` to `total_donated`:**

```python
# Script: migrate_donation_data.py
# 1. Identify contacts enriched from QuickBooks (updated_at around 2025-11-15 14:19)
# 2. Calculate donation amounts to migrate
# 3. Move to new donation fields
# 4. Subtract from total_spent (to avoid double-counting)
# 5. Update donor_status based on recency and amount
```

### Benefits
- Clean separation of donations vs. purchases
- Donor-specific analytics and segmentation
- Proper fundraising reporting
- Better donor engagement tracking

---

## Phase 3: Full Donation Management System

### Create Dedicated Donations Table

```sql
CREATE TABLE donations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,

    -- Transaction details
    donation_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',

    -- Source tracking
    source_system TEXT, -- 'quickbooks', 'stripe', 'paypal', 'check', 'cash'
    external_id TEXT, -- QuickBooks receipt number, Stripe charge ID, etc.
    transaction_type TEXT, -- 'invoice', 'sales_receipt', 'deposit', 'journal_entry'

    -- Categorization
    campaign TEXT, -- 'Tree Sale 2024', 'Fire Mitigation', '30K in 30', 'Annual Appeal'
    category TEXT, -- 'fundraising', 'sponsorship', 'membership', 'grant'
    payment_method TEXT, -- 'paypal', 'check', 'cash', 'credit_card', 'bank_transfer'

    -- Details
    memo TEXT,
    is_recurring BOOLEAN DEFAULT false,
    is_pledge BOOLEAN DEFAULT false,
    pledge_fulfilled_date DATE,

    -- Acknowledgment
    thank_you_sent BOOLEAN DEFAULT false,
    thank_you_sent_date DATE,
    tax_receipt_sent BOOLEAN DEFAULT false,
    tax_receipt_number TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID REFERENCES auth.users(id),

    -- Indexes
    INDEX idx_donations_contact (contact_id),
    INDEX idx_donations_date (donation_date),
    INDEX idx_donations_campaign (campaign),
    INDEX idx_donations_amount (amount DESC)
);

-- Row Level Security
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Staff can view all donations"
    ON donations FOR SELECT
    TO authenticated
    USING (true); -- Add staff check

CREATE POLICY "Staff can manage donations"
    ON donations FOR ALL
    TO authenticated
    USING (true) -- Add staff check
    WITH CHECK (true);
```

### Import Script

**Re-import QuickBooks data with full transaction detail:**

```python
# Script: import_donations_full.py
#
# Features:
# 1. Load complete QuickBooks transaction history (2019-2024)
# 2. Parse each transaction into donations table
# 3. Extract campaign from "Class full name" field
# 4. Map transaction types (Invoice, Sales Receipt, etc.)
# 5. Link to contacts by name matching
# 6. Calculate contact-level aggregates
# 7. Update donor_status based on recency
```

### Benefits
- Transaction-level detail preserved
- Rich fundraising analytics
- Campaign tracking and ROI
- Donation trends over time
- Better donor engagement

---

## Handle 241 New Donors (No Emails)

### Strategy 1: Cross-Reference with QuickBooks Contacts

Many skipped donors may already be in the QuickBooks Contacts import (which has emails).

```python
# Script: match_donors_to_contacts.py
#
# 1. Load 241 skipped donors
# 2. Load QuickBooks Contacts import data
# 3. Match by name
# 4. Extract email addresses
# 5. Create contacts with emails
# 6. Import donation data
```

**Expected recovery:** 40-60% of skipped donors (~100-150)

### Strategy 2: Manual Research for High-Value Donors

Top 20 skipped donors represent $10,000+ in donations. Worth researching manually.

**Process:**
1. Export top 50 skipped donors
2. Search QuickBooks customer records for emails
3. Google search for foundations/organizations
4. Manually add contacts with verified emails
5. Import donation data

### Strategy 3: Allow Contacts Without Emails (Schema Change)

**Modify contacts table constraint:**

```sql
-- Make email optional
ALTER TABLE contacts ALTER COLUMN email DROP NOT NULL;

-- Add check: must have email OR phone OR address
ALTER TABLE contacts ADD CONSTRAINT contacts_must_have_contact_info
    CHECK (
        email IS NOT NULL OR
        phone IS NOT NULL OR
        (address_line_1 IS NOT NULL AND city IS NOT NULL)
    );
```

**Then re-run import:**
- 241 donors can be added
- Mark as `donor_only = true`
- Flag for email lookup later

---

## Request Full Historical Data from QuickBooks

**Current limitation:** Only 2024 transactions included (01/01/2024 to 12/31/2024)

**Missing:** 5 years of donation history (2019-2023)

### Action Items

1. **Export complete transaction history:**
   - All Dates (not just 2024)
   - Same format: Statement of Activity Detail
   - Include all income categories

2. **Expected impact:**
   - 5,000+ additional transactions
   - 2,000+ total donors
   - $400,000+ in historical donations
   - Better donor recency analysis

3. **Re-run analysis:**
   ```bash
   python3 scripts/analyze_donors_quickbooks.py --file historical_donors.csv
   ```

4. **Re-import donations:**
   - If using Phase 2: Update totals
   - If using Phase 3: Import all transactions to donations table

---

## Build Donor Analytics Dashboard

### Key Metrics to Display

**Overview:**
- Total donations (all time)
- Total donations (YTD)
- Total donors
- Average donation size
- Donation trends (monthly/yearly)

**Donor Segmentation:**
- Major donors (>$1,000)
- Active donors (donated in last 12 months)
- Lapsed donors (no donation in 18+ months)
- Recurring donors (3+ donations)
- First-time donors (1 donation ever)

**Campaign Performance:**
- Tree Sale revenue by year
- Fire Mitigation campaign total
- 30K in 30 campaign results
- Top performing campaigns

**Donor Retention:**
- Year-over-year retention rate
- Average donor lifetime
- Reactivation rate (lapsed → active)

### UI Components

**Pages to Build:**

1. **`/donors`** - Main donor list
   - Filterable by status, amount, recency
   - Sortable by total donated, last donation
   - Export to CSV

2. **`/donors/[id]`** - Donor detail page
   - Donation history timeline
   - Total/average/largest donation
   - Campaign participation
   - Thank you letter status
   - Notes and communication history

3. **`/donations`** - Transaction list
   - All donations with filters
   - Search by campaign, amount, date
   - Bulk actions (mark thank you sent, etc.)

4. **`/campaigns`** - Campaign tracking
   - List of all fundraising campaigns
   - Revenue by campaign
   - Donor participation
   - Year-over-year comparison

5. **`/analytics/donors`** - Donor analytics
   - Charts and visualizations
   - Retention metrics
   - Segmentation breakdown
   - Export reports

---

## QuickBooks Integration (Long-Term)

### Automated Sync

**Option 1: QuickBooks API Integration**
- Connect to QuickBooks Online API
- Sync donations nightly
- Real-time donor updates
- Requires QuickBooks developer account

**Option 2: Scheduled CSV Import**
- Export from QuickBooks monthly
- Upload to import endpoint
- Process in background job
- Lower technical complexity

**Option 3: Zapier/Make Integration**
- QuickBooks → Webhook → Database
- No custom API code needed
- Pay-per-transaction model

### Sync Strategy

```python
# Script: sync_quickbooks_donations.py
#
# 1. Fetch new transactions since last sync
# 2. Match to existing contacts
# 3. Create new donations records
# 4. Update contact aggregates
# 5. Flag new donors for email lookup
# 6. Send notification of new donations
# 7. Update sync timestamp
```

---

## Tax Receipt Generation

### Requirements

**IRS compliance for 501(c)(3):**
- Donor name and address
- Donation date and amount
- Organization EIN
- Tax-exempt status statement
- Goods/services disclosure

### Implementation

**Generate receipt PDFs:**

```typescript
// API: /api/donations/receipt/[donation_id]
//
// 1. Fetch donation details
// 2. Fetch contact info
// 3. Generate PDF with receipt template
// 4. Mark tax_receipt_sent = true
// 5. Send via email
// 6. Store PDF in Supabase Storage
```

**Bulk year-end receipts:**
- Generate for all donations in tax year
- Group by contact
- Email batch or print for mailing

---

## Thank You Letter Automation

### Workflow

**When donation received:**
1. Create donation record
2. Trigger thank you workflow
3. Select template based on amount:
   - >$1,000: Personal letter from director
   - $250-$999: Standard thank you
   - <$250: Email thank you

**Template variables:**
- {donor_name}
- {donation_amount}
- {donation_date}
- {campaign_name}
- {total_lifetime_donations}

**Delivery:**
- Email for small donations
- Print/mail for major donors
- Personal phone call for >$5,000

---

## Donor Communication

### Email Campaigns

**Segmented lists:**
- Active donors (reactivation)
- Lapsed donors (re-engagement)
- Major donors (VIP updates)
- Tree Sale participants (annual reminder)

**Templates:**
- Thank you after donation
- Year-end appeal
- Campaign launch
- Impact report
- Event invitation

### Notes and History

**Track interactions:**
- Phone calls
- Emails sent
- Meetings
- Events attended
- Preferences (communication frequency, interests)

---

## Quick Start (When Ready)

### Step 1: Choose Implementation Phase

**Quick Win (Phase 2):**
```bash
# 1. Add donation fields to contacts
psql -f migrations/add_donation_fields.sql

# 2. Migrate existing data
python3 scripts/migrate_donation_data.py

# 3. Update UI to show donations separately
# (Edit contact detail page)
```

**Full System (Phase 3):**
```bash
# 1. Create donations table
psql -f migrations/create_donations_table.sql

# 2. Request full historical data from QuickBooks
# (Export 2019-2024)

# 3. Import all transactions
python3 scripts/import_donations_full.py --file historical_donors.csv

# 4. Build donor dashboard
cd starhouse-ui
# Create pages: /donors, /donations, /campaigns
```

### Step 2: Test Data Quality

```sql
-- Verify migration
SELECT
    COUNT(*) as donor_count,
    SUM(total_donated) as total_donations,
    AVG(total_donated) as avg_donation
FROM contacts
WHERE total_donated > 0;

-- Check for duplicates
SELECT first_name, last_name, COUNT(*)
FROM contacts
WHERE total_donated > 0
GROUP BY first_name, last_name
HAVING COUNT(*) > 1;

-- Verify top donors
SELECT first_name, last_name, total_donated, donation_count
FROM contacts
ORDER BY total_donated DESC
LIMIT 20;
```

### Step 3: Build UI

**Priority order:**
1. Donor list page (filterable, sortable)
2. Donor detail page (donation history)
3. Export functionality
4. Basic analytics dashboard
5. Campaign tracking
6. Thank you automation

---

## Data Files Available

**For when you're ready:**

1. **`kajabi 3 files review/Donors_Quickbooks.csv`**
   - 1,056 transactions (2024 only)
   - 568 unique donors
   - $83,521.47 total

2. **Analysis Scripts:**
   - `scripts/analyze_donors_quickbooks.py`
   - `scripts/enrich_contacts_from_donors.py`
   - `scripts/check_enrichment_status.py`

3. **Documentation:**
   - `docs/DONORS_ENRICHMENT_SUMMARY.md` (30+ pages)
   - `docs/DONORS_ENRICHMENT_COMPLETE.md` (execution results)
   - This roadmap

4. **Logs:**
   - `logs/donor_analysis_20251115_141308.log`
   - `logs/donor_enrichment_20251115_141913.log`

---

## Estimated Effort

### Phase 2: Separate Donation Fields
- **Development:** 1-2 days
- **Migration:** 2-4 hours
- **Testing:** 1 day
- **Total:** 3-5 days

### Phase 3: Full Donation System
- **Schema & Migration:** 2-3 days
- **Import Scripts:** 3-5 days
- **UI Development:** 5-7 days
- **Analytics Dashboard:** 3-5 days
- **Testing:** 2-3 days
- **Total:** 15-23 days (3-4 weeks)

### QuickBooks Integration
- **API Setup:** 2-3 days
- **Sync Logic:** 3-5 days
- **Testing:** 2-3 days
- **Total:** 7-11 days (1.5-2 weeks)

---

## Success Metrics

**When donor module is complete:**

- ✅ Donations separated from purchases in database
- ✅ Transaction-level detail preserved (5+ years)
- ✅ 500+ donors tracked with complete history
- ✅ $500,000+ in total donations tracked
- ✅ Donor segmentation (active/lapsed/major)
- ✅ Campaign performance tracking
- ✅ Automated thank you letters
- ✅ Tax receipt generation
- ✅ QuickBooks sync (manual or automated)
- ✅ Donor analytics dashboard

---

## Questions to Answer Before Starting

1. **Data strategy:**
   - Phase 2 (fields) or Phase 3 (table)?
   - Migrate existing data or start fresh?

2. **Historical data:**
   - Can you export 2019-2024 from QuickBooks?
   - How often will you sync (monthly/weekly/realtime)?

3. **Email constraint:**
   - Make email optional for donor-only contacts?
   - Or require manual email lookup?

4. **QuickBooks integration:**
   - API integration or manual CSV import?
   - Who manages QuickBooks exports?

5. **Tax receipts:**
   - Need automated generation?
   - Or handle outside the system?

6. **Priority:**
   - When do you want to build this?
   - What's the driver (reporting, compliance, engagement)?

---

**Save this document for when you're ready to build the donor module.**

All the analysis, scripts, and recommendations are ready. Just follow the Quick Start guide and you'll have a complete donor management system.

**Estimated Timeline:** 3-4 weeks for full Phase 3 implementation
**Prerequisites:** Full QuickBooks historical export (2019-2024)
**Resources:** All scripts and analysis already complete ✅
