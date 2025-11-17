# Donor Management Module - REVISED PLAN
## With UI Simplifications & Phone-a-Thon Module

**Document Version:** 2.0 (REVISED)
**Created:** 2025-11-15
**Updated:** 2025-11-15 (Incorporating feedback)
**Status:** Planning & Design Complete
**Estimated Timeline:** 5-6 weeks (includes Phone-a-Thon)
**Priority:** High-Value Feature

---

## 🔄 Changes from V1.0

### Major Improvements

1. **Simplified UI/UX** - Tabs instead of dropdowns, better mobile experience
2. **Critical Missing Elements Added** - Empty states, loading states, accessibility
3. **Phone-a-Thon Module** - NEW: Enable 300+ donor outreach calls
4. **Mobile-First Design** - Card views, bottom navigation, touch targets
5. **Keyboard Shortcuts** - Power user features for staff

---

## Table of Contents

### Part 1: Core Donor Module (REVISED)
1. [Executive Summary](#executive-summary)
2. [Revised UI Design](#revised-ui-design)
3. [Critical Missing Elements](#critical-missing-elements)
4. [Simplified Implementation](#simplified-implementation)

### Part 2: Phone-a-Thon Module (NEW)
5. [Phone-a-Thon Overview](#phone-a-thon-overview)
6. [Phone-a-Thon Data Model](#phone-a-thon-data-model)
7. [Phone-a-Thon UI Design](#phone-a-thon-ui-design)
8. [Phone-a-Thon Workflow](#phone-a-thon-workflow)

### Part 3: Implementation
9. [Complete Roadmap (6 Weeks)](#complete-roadmap)
10. [Success Metrics](#success-metrics)
11. [Appendix](#appendix)

---

# PART 1: CORE DONOR MODULE (REVISED)

## Executive Summary

### Purpose
Build a user-friendly Donor Management Module with simplified UI patterns and integrated phone-a-thon capabilities for effective donor stewardship.

### Key Statistics (Unchanged)
- **Current Database:** 11,843 transactions | 3,022 unique customers | $629,437.73 total revenue
- **QuickBooks Donor Data:** 1,056 transactions | 568 donors | $83,521.47 (2024 only)
- **Enrichment Completed:** 342 contacts enriched with $49,733.33 in donations
- **Opportunity:** 241 additional donors + 5 years historical data pending

### What Changed
- ✅ **Simplified navigation** - Tabs instead of complex filters
- ✅ **Better mobile experience** - Card views, touch-friendly
- ✅ **Empty states** - Every list has helpful guidance
- ✅ **Loading states** - Skeleton screens, optimistic updates
- ✅ **Accessibility** - Keyboard shortcuts, ARIA labels
- ✅ **Phone-a-Thon integration** - Track outbound donor calls

---

## Revised UI Design

### 1. `/donors` - Donor List Page (SIMPLIFIED)

**Major Changes:**
- ✅ Tabs instead of filter dropdowns
- ✅ Smart search bar with operators
- ✅ Gmail-style bulk action bar
- ✅ Default sort by total donated

**New Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  DONORS                                   [+ Add] [Export]  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Total       │  │ Active      │  │ YTD         │       │
│  │ Donations   │  │ Donors      │  │ Donations   │       │
│  │ $629,437    │  │ 1,247       │  │ $83,521     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🔍 Search donors (try "donors >$500" or "lapsed")   │ │
│  │                                    [Advanced ▼]      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  [All] [Active] [Lapsed] [Major] [Recurring] [First-Time] │
│  ─────  ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏  ͏ ͏ ͏ ͏ ͏ ͏   ͏ ͏ ͏ ͏ ͏ ͏   ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏   ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏ ͏  │
│                                                            │
│  Showing 256 active donors                                 │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Name              Total    Count   Last Gift          │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Jeff Stein        $2,450   12 ↻   Nov 15, 2024       │ │
│  │ 🥇 Gold · jeff@   Tree Sale                          │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Karen Gallik      $1,850   8      Oct 3, 2024        │ │
│  │ 🥈 Silver         Annual Appeal                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  1-25 of 256                          [1] 2 3 ... 11      │
└────────────────────────────────────────────────────────────┘

[When 3+ donors selected, bottom bar appears:]
┌────────────────────────────────────────────────────────────┐
│  ✓ 3 selected                                              │
│  [Send Thank You] [Generate Receipts] [Export] [Clear]     │
└────────────────────────────────────────────────────────────┘
```

**Smart Search Examples:**
- `"donors >$500"` → Filters to donors with total > $500
- `"lapsed"` → Shows lapsed status donors
- `"jeff"` → Name search
- `"tree sale"` → Donors who gave to Tree Sale campaign
- `"recurring"` → Recurring donors only

**Advanced Filter Panel** (hidden by default):
```
┌──────────────────────────────────────────┐
│ ADVANCED FILTERS                    [×]  │
├──────────────────────────────────────────┤
│ Amount Range:                            │
│ [$ 0    ] to [$ 10,000 ]                 │
│                                          │
│ Last Donation:                           │
│ [Date picker: From] [To]                 │
│                                          │
│ Campaign:                                │
│ [ Select campaign... ▼ ]                 │
│                                          │
│ Tier:                                    │
│ ☐ Bronze ☐ Silver ☐ Gold ☐ Platinum     │
│                                          │
│ [Clear All] [Apply Filters]              │
└──────────────────────────────────────────┘
```

**Empty State:**
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│                    📭                                      │
│                                                            │
│               No lapsed donors found                       │
│                                                            │
│           All your donors are active! 🎉                   │
│                                                            │
│          [View All Donors]  [Create Phone-a-Thon]          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2. `/donors/[id]` - Donor Detail Page (SIMPLIFIED)

**Major Changes:**
- ✅ Sticky header with actions always visible
- ✅ Two-column layout (donations left, stats right)
- ✅ Collapse donation years (current year expanded)
- ✅ Sidebar for notes (not at bottom)
- ✅ One-click copy for email/phone

**New Layout:**

```
┌────────────────────────────────────────────────────────────┐
│ ← Donors  │  Jeff Stein  🥇 Gold · Active  [Sticky Header] │
│                                                            │
│ [Send Thank You] [Generate Receipt] [Add Note] [Edit]      │
├──────────────────────┬─────────────────────────────────────┤
│ DONATION HISTORY     │  DONOR PROFILE                      │
│ (60% width)          │  (40% width - Sidebar)              │
├──────────────────────┼─────────────────────────────────────┤
│                      │  ┌─────────────────────────────────┐│
│ 2024 ($850) [▼]      │  │ jeff@example.com     [Copy 📋] ││
│ ┌──────────────────┐ │  │ (555) 123-4567       [Copy 📋] ││
│ │ Nov 15  $250     │ │  │ Portland, OR                   ││
│ │ Tree Sale        │ │  └─────────────────────────────────┘│
│ │ ✓✓ PayPal        │ │                                     │
│ ├──────────────────┤ │  ┌─────────────────────────────────┐│
│ │ Jun 3   $100     │ │  │ LIFETIME STATS                  ││
│ │ Fire Mitigation  │ │  ├─────────────────────────────────┤│
│ │ ✓- Check #4521   │ │  │ Total Given    $2,450          ││
│ ├──────────────────┤ │  │ Donations      12              ││
│ │ Mar 12  $500     │ │  │ First Gift     May 2020        ││
│ │ Annual Appeal    │ │  │ Latest Gift    Nov 2024        ││
│ │ ✓✓ Credit Card   │ │  │ Largest        $500            ││
│ └──────────────────┘ │  │ Average        $204.17         ││
│                      │  │ Status         Recurring ↻      ││
│ 2023 ($1,200) [▶]    │  │ Campaigns      5               ││
│                      │  └─────────────────────────────────┘│
│ 2022 ($400) [▶]      │                                     │
│                      │  ┌─────────────────────────────────┐│
│                      │  │ NOTES & CALLS                   ││
│                      │  ├─────────────────────────────────┤│
│                      │  │ 📞 Nov 16, 2024                 ││
│                      │  │ Called re: Tree Sale.           ││
│                      │  │ Very engaged!                   ││
│                      │  ├─────────────────────────────────┤│
│                      │  │ 📧 Mar 15, 2024                 ││
│                      │  │ Thank you sent for              ││
│                      │  │ $500 donation.                  ││
│                      │  └─────────────────────────────────┘│
│                      │                                     │
│                      │  [+ Add Note]                       │
└──────────────────────┴─────────────────────────────────────┘
```

**One-Click Copy:**
```typescript
// On click, copy to clipboard + show toast
<button onClick={() => {
  navigator.clipboard.writeText(donor.email)
  toast.success('Email copied!')
}}>
  {donor.email} <Copy className="h-3 w-3" />
</button>
```

### 3. `/campaigns` - Campaign Management (SIMPLIFIED)

**Major Changes:**
- ✅ Large visual progress bar
- ✅ Pace indicator (On Track / Behind / Ahead)
- ✅ Top 5 donors visible immediately
- ✅ Export button always visible

**New Campaign Card:**

```
┌─────────────────────────────────────────────────────────┐
│ Tree Sale 2024                       [View] [Edit]      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ $24,550 raised of $30,000 goal                          │
│ ████████████████░░░░ 82%                                │
│                                                         │
│ 🟢 ON TRACK - 23 days left                              │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 156 donors  |  $157 avg  |  23 days left            ││
│ └─────────────────────────────────────────────────────┘│
│                                                         │
│ TOP DONORS:                                             │
│ 1. Jeff Stein - $500                                    │
│ 2. Karen Gallik - $450                                  │
│ 3. Mark Jones - $400                                    │
│ 4. Susan Chen - $350                                    │
│ 5. David Park - $300                                    │
│                                                         │
│ [View All Donations] [Export Report]                    │
└─────────────────────────────────────────────────────────┘
```

**Pace Indicator Logic:**
```typescript
type PaceStatus = 'ahead' | 'on_track' | 'behind'

function calculatePace(campaign: Campaign): PaceStatus {
  const totalDays = daysBetween(campaign.start_date, campaign.end_date)
  const elapsedDays = daysBetween(campaign.start_date, new Date())
  const daysRemaining = totalDays - elapsedDays

  const targetPace = (elapsedDays / totalDays) * campaign.goal_amount
  const actualRaised = campaign.total_raised

  const percentDifference = (actualRaised - targetPace) / targetPace

  if (percentDifference > 0.1) return 'ahead'      // 10%+ ahead
  if (percentDifference < -0.1) return 'behind'    // 10%+ behind
  return 'on_track'
}

// Display:
// 🟢 ON TRACK
// 🟡 BEHIND PACE - Need $2,000 more to hit goal
// 🔵 AHEAD OF PACE - Exceeding expectations!
```

---

## Critical Missing Elements

### 1. Empty States (EVERY LIST)

**Philosophy:** Every empty list should guide the user to the next action.

**Donor List - No Results:**
```jsx
<EmptyState
  icon={<Search />}
  title="No donors found"
  description="Try adjusting your filters or search terms"
  actions={[
    { label: 'Clear Filters', onClick: clearFilters },
    { label: 'View All Donors', onClick: resetView }
  ]}
/>
```

**Donor List - No Donors At All:**
```jsx
<EmptyState
  icon={<Users />}
  title="No donors yet"
  description="Import donor data from QuickBooks to get started"
  actions={[
    { label: 'Import from QuickBooks', onClick: openImport, primary: true },
    { label: 'Add Donor Manually', onClick: openNewDonorForm }
  ]}
/>
```

**Donation History - First Time Donor:**
```jsx
<EmptyState
  icon={<Gift />}
  title="First donation!"
  description="This is Jeff's first donation to All Seasons Chalice Church. Make sure to send a warm welcome!"
  actions={[
    { label: 'Send Thank You Email', onClick: sendThankYou, primary: true }
  ]}
/>
```

**Lapsed Donors - All Active:**
```jsx
<EmptyState
  icon={<CheckCircle />}
  title="All donors active! 🎉"
  description="Every donor has given in the last 12 months. Great job!"
  actions={[
    { label: 'View Active Donors', onClick: viewActive }
  ]}
/>
```

**Campaign List - No Campaigns:**
```jsx
<EmptyState
  icon={<Target />}
  title="No campaigns yet"
  description="Create your first fundraising campaign to start tracking goals and progress"
  actions={[
    { label: 'Create First Campaign', onClick: createCampaign, primary: true },
    { label: 'Learn About Campaigns', onClick: openDocs }
  ]}
/>
```

### 2. Mobile Design (Card View)

**Mobile Donor List:**
```jsx
// Desktop: Table
// Mobile: Cards

{isMobile ? (
  <div className="space-y-3">
    {donors.map(donor => (
      <DonorCard
        key={donor.id}
        donor={donor}
        onClick={() => navigate(`/donors/${donor.id}`)}
      />
    ))}
  </div>
) : (
  <DonorTable donors={donors} />
)}

// DonorCard component
<Card className="p-4">
  <div className="flex items-start justify-between">
    <div>
      <h3 className="font-semibold">{donor.name}</h3>
      <p className="text-sm text-muted-foreground">{donor.email}</p>
    </div>
    <TierBadge tier={donor.tier} />
  </div>

  <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
    <div>
      <div className="text-muted-foreground">Total</div>
      <div className="font-medium">{formatCurrency(donor.total)}</div>
    </div>
    <div>
      <div className="text-muted-foreground">Gifts</div>
      <div className="font-medium">{donor.count}</div>
    </div>
    <div>
      <div className="text-muted-foreground">Status</div>
      <div><StatusBadge status={donor.status} /></div>
    </div>
  </div>

  <div className="mt-3 text-xs text-muted-foreground">
    Last: {formatDate(donor.last_donation_date)}
  </div>
</Card>
```

**Mobile Filters - Single Dropdown:**
```jsx
<Select onValueChange={setFilter}>
  <SelectTrigger>
    <SelectValue placeholder="Filter donors" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">All Donors</SelectItem>
    <SelectItem value="active">Active Only</SelectItem>
    <SelectItem value="lapsed">Lapsed Only</SelectItem>
    <SelectItem value="major">Major Donors (>$1k)</SelectItem>
    <SelectItem value="recurring">Recurring</SelectItem>
    <SelectItem value="first_time">First-Time</SelectItem>
  </SelectContent>
</Select>
```

**Mobile Bottom Navigation:**
```jsx
<nav className="fixed bottom-0 left-0 right-0 bg-background border-t md:hidden">
  <div className="flex justify-around py-2">
    <NavButton icon={<Users />} label="Donors" active />
    <NavButton icon={<DollarSign />} label="Donations" />
    <NavButton icon={<Target />} label="Campaigns" />
    <NavButton icon={<BarChart />} label="Analytics" />
    <NavButton icon={<Phone />} label="Calls" />
  </div>
</nav>
```

**44px Touch Targets (Mobile):**
```css
/* All interactive elements on mobile */
.mobile-touch-target {
  min-height: 44px;
  min-width: 44px;
  padding: 12px;
}

/* Buttons */
button {
  @apply mobile-touch-target;
}

/* List items */
.list-item {
  @apply mobile-touch-target;
}
```

### 3. Loading & Error States

**Skeleton Screens (While Loading):**
```jsx
{loading ? (
  <div className="space-y-3">
    {[1,2,3,4,5].map(i => (
      <div key={i} className="border rounded-lg p-4">
        <Skeleton className="h-6 w-48 mb-2" />
        <Skeleton className="h-4 w-32 mb-3" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      </div>
    ))}
  </div>
) : (
  <DonorList donors={donors} />
)}
```

**Optimistic Updates (Instant Feedback):**
```typescript
// When marking thank-you as sent
async function markThankYouSent(donationId: string) {
  // 1. Update UI immediately (optimistic)
  setDonations(prev => prev.map(d =>
    d.id === donationId
      ? { ...d, thank_you_sent: true, thank_you_sent_date: new Date() }
      : d
  ))

  // 2. Show instant feedback
  toast.success('Thank you marked as sent')

  // 3. Update database in background
  try {
    await supabase
      .from('donations')
      .update({ thank_you_sent: true, thank_you_sent_date: new Date() })
      .eq('id', donationId)
  } catch (error) {
    // 4. Revert on error
    setDonations(prev => prev.map(d =>
      d.id === donationId
        ? { ...d, thank_you_sent: false, thank_you_sent_date: null }
        : d
    ))
    toast.error('Failed to update. Please try again.')
  }
}
```

**Toast Notifications:**
```typescript
// Success: 3 seconds, auto-dismiss
toast.success('Donor updated successfully', { duration: 3000 })

// Error: 5 seconds, manual dismiss
toast.error('Failed to generate receipt. Please try again.', {
  duration: 5000,
  action: { label: 'Retry', onClick: retryReceipt }
})

// Info: 4 seconds
toast.info('Exporting 250 donors...', { duration: 4000 })

// Loading: Manual dismiss when complete
const toastId = toast.loading('Importing donations...')
// ... later
toast.success('Imported 150 donations!', { id: toastId })
```

**Error Boundaries (Graceful Failure):**
```jsx
<ErrorBoundary
  fallback={
    <div className="p-8 text-center">
      <AlertTriangle className="h-12 w-12 mx-auto text-destructive mb-4" />
      <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
      <p className="text-muted-foreground mb-4">
        We encountered an error loading this page.
      </p>
      <div className="space-x-2">
        <Button onClick={() => window.location.reload()}>
          Reload Page
        </Button>
        <Button variant="outline" onClick={() => navigate('/donors')}>
          Back to Donors
        </Button>
      </div>
    </div>
  }
>
  <DonorDetailPage />
</ErrorBoundary>
```

### 4. Accessibility (WCAG 2.1 AA)

**Keyboard Shortcuts:**
```typescript
// Global shortcuts
useKeyboardShortcut('/', () => focusSearch())           // Focus search
useKeyboardShortcut('n', () => openNewDonor())          // New donor
useKeyboardShortcut('e', () => exportDonors())          // Export
useKeyboardShortcut('?', () => showShortcuts())         // Show help
useKeyboardShortcut('Escape', () => closeModal())       // Close modal

// List navigation
useKeyboardShortcut('j', () => selectNext())            // Next item
useKeyboardShortcut('k', () => selectPrevious())        // Previous item
useKeyboardShortcut('Enter', () => openSelected())      // Open selected

// Shortcuts help modal
<ShortcutsDialog>
  <table>
    <tr><td>/</td><td>Focus search</td></tr>
    <tr><td>N</td><td>New donor</td></tr>
    <tr><td>E</td><td>Export</td></tr>
    <tr><td>J/K</td><td>Navigate list</td></tr>
    <tr><td>Enter</td><td>Open selected</td></tr>
    <tr><td>?</td><td>Show shortcuts</td></tr>
  </table>
</ShortcutsDialog>
```

**ARIA Labels (Icon-Only Buttons):**
```jsx
// Bad: No context for screen readers
<button><Copy /></button>

// Good: Accessible label
<button aria-label="Copy email address">
  <Copy className="h-4 w-4" />
  <span className="sr-only">Copy email address</span>
</button>

// Better: Tooltip + ARIA
<Tooltip content="Copy email address">
  <button aria-label="Copy email address">
    <Copy className="h-4 w-4" />
  </button>
</Tooltip>
```

**Visible Focus Indicators:**
```css
/* All interactive elements */
*:focus-visible {
  outline: 2px solid hsl(var(--primary));
  outline-offset: 2px;
  border-radius: 4px;
}

/* Custom focus for buttons */
button:focus-visible {
  ring: 2px solid hsl(var(--ring));
  ring-offset: 2px;
}

/* Table rows */
tr:focus-within {
  background: hsl(var(--accent));
  outline: 2px solid hsl(var(--primary));
}
```

**Skip to Content Links:**
```jsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground"
>
  Skip to main content
</a>

<main id="main-content" tabIndex={-1}>
  {/* Page content */}
</main>
```

**Screen Reader Announcements:**
```jsx
// Announce dynamic updates
<div role="status" aria-live="polite" className="sr-only">
  {donors.length} donors found
</div>

// Announce errors
<div role="alert" aria-live="assertive" className="sr-only">
  {error && `Error: ${error.message}`}
</div>
```

---

# PART 2: PHONE-A-THON MODULE (NEW)

## Phone-a-Thon Overview

### Purpose
Enable 3-5 staff members to make 300+ donor outreach calls over 2 weeks, track outcomes, capture pledges, and convert to donations.

### Business Value
- **Re-engage lapsed donors** - Personal touch increases retention
- **Secure pledges** - $7,500+ additional revenue per campaign
- **Update contact info** - Verify phone, email, address
- **Build relationships** - Notes capture donor interests and preferences
- **Data-driven follow-up** - Track what works, iterate

### Key Metrics Goal
- **300 calls** in 2 weeks (15 calls/hour average)
- **60% contact rate** (180 reached vs. voicemail/no answer)
- **10% pledge rate** (30 pledges from 300 calls)
- **$7,500 raised** ($250 average pledge)
- **80% fulfillment** (24 pledges paid within 30 days)

---

## Phone-a-Thon Data Model

### New Tables

**1. `call_campaigns` Table**

```sql
CREATE TABLE call_campaigns (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign Details
    name TEXT NOT NULL,
    description TEXT,

    -- Targeting
    target_segment TEXT, -- 'lapsed', 'major', 'active', 'custom'
    target_filters JSONB, -- Stored filter criteria

    -- Timeline
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Goals
    goal_calls INTEGER NOT NULL,
    goal_pledges INTEGER,
    goal_amount DECIMAL(12,2),

    -- Progress (computed by trigger)
    total_calls INTEGER DEFAULT 0,
    reached_count INTEGER DEFAULT 0,
    pledge_count INTEGER DEFAULT 0,
    pledge_amount DECIMAL(12,2) DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'active', -- 'active', 'completed', 'paused'

    -- Call Script
    call_script TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_by TEXT,

    CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'paused'))
);

-- Indexes
CREATE INDEX idx_call_campaigns_status ON call_campaigns(status);
CREATE INDEX idx_call_campaigns_dates ON call_campaigns(start_date, end_date);
```

**2. `call_logs` Table**

```sql
CREATE TABLE call_logs (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    call_campaign_id UUID NOT NULL REFERENCES call_campaigns(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

    -- Call Details
    call_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    caller_name TEXT NOT NULL,

    -- Outcome
    outcome TEXT NOT NULL,
    -- 'reached', 'voicemail', 'no_answer', 'wrong_number', 'do_not_call', 'busy', 'disconnected'

    -- Notes
    notes TEXT,

    -- Pledge Capture
    pledge_amount DECIMAL(12,2),
    pledge_payment_method TEXT, -- 'check', 'credit_card', 'cash', 'paypal'
    pledge_status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'cancelled'

    -- Follow-Up
    follow_up_needed BOOLEAN DEFAULT false,
    follow_up_date DATE,
    follow_up_reason TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,

    CONSTRAINT valid_outcome CHECK (
        outcome IN ('reached', 'voicemail', 'no_answer', 'wrong_number', 'do_not_call', 'busy', 'disconnected')
    ),
    CONSTRAINT valid_pledge_status CHECK (
        pledge_status IN ('pending', 'paid', 'cancelled')
    )
);

-- Indexes
CREATE INDEX idx_call_logs_campaign ON call_logs(call_campaign_id);
CREATE INDEX idx_call_logs_contact ON call_logs(contact_id);
CREATE INDEX idx_call_logs_date ON call_logs(call_date DESC);
CREATE INDEX idx_call_logs_outcome ON call_logs(outcome);
CREATE INDEX idx_call_logs_follow_up ON call_logs(follow_up_needed) WHERE follow_up_needed = true;
CREATE INDEX idx_call_logs_pledge_status ON call_logs(pledge_status) WHERE pledge_amount IS NOT NULL;

-- Unique constraint: One call per contact per campaign per day
CREATE UNIQUE INDEX ux_call_logs_contact_campaign_date
    ON call_logs(contact_id, call_campaign_id, DATE(call_date));
```

**3. `call_campaign_contacts` Table (Join Table)**

```sql
CREATE TABLE call_campaign_contacts (
    -- Relationships
    call_campaign_id UUID NOT NULL REFERENCES call_campaigns(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,

    -- Order for calling
    call_order INTEGER,

    -- Status
    status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'skipped'

    -- Metadata
    added_at TIMESTAMPTZ DEFAULT now() NOT NULL,

    PRIMARY KEY (call_campaign_id, contact_id),

    CONSTRAINT valid_status CHECK (status IN ('pending', 'completed', 'skipped'))
);

-- Indexes
CREATE INDEX idx_call_campaign_contacts_campaign ON call_campaign_contacts(call_campaign_id);
CREATE INDEX idx_call_campaign_contacts_status ON call_campaign_contacts(call_campaign_id, status);
CREATE INDEX idx_call_campaign_contacts_order ON call_campaign_contacts(call_campaign_id, call_order);
```

### Enhanced `contacts` Table

```sql
-- Add phone-a-thon related fields
ALTER TABLE contacts ADD COLUMN do_not_call BOOLEAN DEFAULT false;
ALTER TABLE contacts ADD COLUMN last_called_date DATE;
ALTER TABLE contacts ADD COLUMN call_notes TEXT;

-- Index
CREATE INDEX idx_contacts_do_not_call ON contacts(do_not_call) WHERE do_not_call = true;
CREATE INDEX idx_contacts_last_called ON contacts(last_called_date DESC) WHERE last_called_date IS NOT NULL;
```

### Database Triggers

**Update Campaign Totals:**

```sql
CREATE OR REPLACE FUNCTION update_call_campaign_totals()
RETURNS TRIGGER AS $$
DECLARE
    v_campaign_id UUID;
BEGIN
    -- Determine which campaign to update
    IF TG_OP = 'DELETE' THEN
        v_campaign_id := OLD.call_campaign_id;
    ELSE
        v_campaign_id := NEW.call_campaign_id;
    END IF;

    -- Recalculate campaign totals
    UPDATE call_campaigns
    SET
        total_calls = (
            SELECT COUNT(*)
            FROM call_logs
            WHERE call_campaign_id = v_campaign_id
        ),
        reached_count = (
            SELECT COUNT(*)
            FROM call_logs
            WHERE call_campaign_id = v_campaign_id
              AND outcome = 'reached'
        ),
        pledge_count = (
            SELECT COUNT(*)
            FROM call_logs
            WHERE call_campaign_id = v_campaign_id
              AND pledge_amount IS NOT NULL
        ),
        pledge_amount = COALESCE((
            SELECT SUM(pledge_amount)
            FROM call_logs
            WHERE call_campaign_id = v_campaign_id
              AND pledge_amount IS NOT NULL
        ), 0),
        updated_at = now()
    WHERE id = v_campaign_id;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER call_logs_update_campaign_totals
    AFTER INSERT OR UPDATE OR DELETE ON call_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_call_campaign_totals();
```

**Update Contact Last Called:**

```sql
CREATE OR REPLACE FUNCTION update_contact_last_called()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE contacts
    SET
        last_called_date = CURRENT_DATE,
        do_not_call = CASE WHEN NEW.outcome = 'do_not_call' THEN true ELSE do_not_call END,
        updated_at = now()
    WHERE id = NEW.contact_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER call_logs_update_contact
    AFTER INSERT ON call_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_contact_last_called();
```

---

## Phone-a-Thon UI Design

### 1. `/campaigns/calls` - Campaign List

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  PHONE-A-THON CAMPAIGNS                   [+ New Campaign] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Active Campaigns (1)                                      │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Spring 2025 Lapsed Donor Outreach      [Open] [Edit]│  │
│  │ Mar 1 - Mar 14, 2025                                │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ Progress: 127 / 300 calls (42%)                     │  │
│  │ ███████████░░░░░░░░░░░░░░░░░░                       │  │
│  │                                                      │  │
│  │ Reached: 85 (67%)  |  Pledges: 15 ($4,200)          │  │
│  │ Today: 23 calls    |  Your calls: 8                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  Past Campaigns (3) [View All ▼]                           │
│  • Fall 2024 Major Donor Call - 150 calls, $8,500 raised  │
│  • Summer 2024 Tree Sale Follow-up - 200 calls, 45 pledges│
└────────────────────────────────────────────────────────────┘
```

### 2. `/campaigns/calls/new` - Create Campaign

**Wizard-Style Form:**

```
┌────────────────────────────────────────────────────────────┐
│  CREATE PHONE-A-THON CAMPAIGN                      [Cancel]│
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [1. Details] → [2. Select Donors] → [3. Review]           │
│   ═══════                                                  │
│                                                            │
│  Campaign Name:                                            │
│  [Spring 2025 Lapsed Donor Outreach                     ]  │
│                                                            │
│  Description (optional):                                   │
│  [Re-engage donors who haven't given in 12+ months      ]  │
│                                                            │
│  Timeline:                                                 │
│  Start: [03/01/2025 ▼]   End: [03/14/2025 ▼]              │
│                                                            │
│  Goals:                                                    │
│  Calls: [300    ]                                          │
│  Pledges: [30     ] (optional)                             │
│  Amount: [$7,500   ] (optional)                            │
│                                                            │
│  Call Script:                                              │
│  [                                                       ]  │
│  │ Hi {name}, this is {caller} from All Seasons          │
│  │ Chalice Church. I'm calling to thank you for          │
│  │ your past support...                                  │
│  [                                                       ]  │
│                                                            │
│  [Cancel] [Next: Select Donors →]                          │
└────────────────────────────────────────────────────────────┘

[Step 2: Select Donors]

┌────────────────────────────────────────────────────────────┐
│  SELECT DONORS TO CALL                                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [Quick Select ▼] or [Build Custom List]                   │
│                                                            │
│  Quick Select Options:                                     │
│  ○ All Lapsed Donors (172 contacts)                       │
│  ○ All Major Donors (85 contacts)                         │
│  ○ All First-Time Donors (42 contacts)                    │
│  ○ All Recurring Donors (48 contacts)                     │
│  ● Custom Selection                                        │
│                                                            │
│  [If Custom Selected]                                      │
│                                                            │
│  Start with: [Lapsed Donors ▼] (172 contacts)              │
│                                                            │
│  Then add:                                                 │
│  ☑ Major Donors (>$1,000) - adds 30 contacts               │
│  ☐ Active Donors (random sample)                           │
│                                                            │
│  Or manually select:                                       │
│  [Search donors...                                      ]  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ ☐ Jeff Stein        $2,450    Last: Nov 2024        │ │
│  │ ☐ Karen Gallik      $1,850    Last: Oct 2024        │ │
│  │ ☑ Mark Jones        $450      Last: Jan 2023 ← Added│ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Total selected: 203 contacts                              │
│  Estimated calls needed: 300 (with follow-ups)             │
│                                                            │
│  [← Back] [Next: Review →]                                 │
└────────────────────────────────────────────────────────────┘

[Step 3: Review]

┌────────────────────────────────────────────────────────────┐
│  REVIEW & LAUNCH                                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Campaign: Spring 2025 Lapsed Donor Outreach               │
│  Timeline: Mar 1 - Mar 14, 2025 (14 days)                  │
│  Goals: 300 calls, 30 pledges, $7,500                      │
│                                                            │
│  Donor List:                                               │
│  • 172 Lapsed Donors                                       │
│  • 30 Major Donors                                         │
│  • 1 Custom Selected                                       │
│  ───────────                                               │
│  Total: 203 contacts                                       │
│                                                            │
│  Call Script: [View Script ▼]                              │
│                                                            │
│  Ready to launch? Staff can start calling immediately.     │
│                                                            │
│  [← Back] [Save Draft] [Launch Campaign]                   │
└────────────────────────────────────────────────────────────┘
```

### 3. `/campaigns/calls/[id]` - Caller Interface (MAIN PAGE)

**This is the PRIMARY interface where staff spend their time.**

**Full Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  ← Back  │  Spring 2025 Lapsed Donor Outreach              │
├────────────────────────────────────────────────────────────┤
│  PROGRESS DASHBOARD                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ Calls    │ Reached  │ Pledges  │ Today    │ Your     │ │
│  │ 127/300  │ 85 (67%) │ 15 ($4.2k│ 23 calls │ 8 calls  │ │
│  │ 42%      │          │          │          │          │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  CONTACT CARD (Left 40%)        │  CALL ACTION (Right 60%)│
├─────────────────────────────────┼─────────────────────────┤
│ ┌─────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ Jeff Stein                  │ │ │ CALL SCRIPT         │ │
│ │ 🥇 Gold Donor              │ │ ├─────────────────────┤ │
│ ├─────────────────────────────┤ │ │                     │ │
│ │ 📞 (555) 123-4567  [Copy]  │ │ │ "Hi Jeff, this is   │ │
│ │ 📧 jeff@ex... [Copy]       │ │ │  {Your Name} from   │ │
│ ├─────────────────────────────┤ │ │  All Seasons Chalice│ │
│ │ GIVING HISTORY              │ │ │  Church.            │ │
│ │ Total: $2,450 (12 gifts)   │ │ │                     │ │
│ │ Last: Nov 2024 - Tree Sale │ │ │  I'm calling to     │ │
│ │ Avg: $204                  │ │ │  thank you for your │ │
│ │ Status: Active - Recurring │ │ │  generous support   │ │
│ ├─────────────────────────────┤ │ │  over the years..." │ │
│ │ RECENT DONATIONS            │ │ │                     │ │
│ │ • Nov 2024: $250 Tree Sale │ │ │ [Expand Full Script]│ │
│ │ • Jun 2024: $100 Fire Mit. │ │ └─────────────────────┘ │
│ │ • Mar 2024: $500 Annual    │ │                         │
│ ├─────────────────────────────┤ │ ┌─────────────────────┐ │
│ │ LAST CALL                   │ │ │ CALL OUTCOME        │ │
│ │ None yet                    │ │ ├─────────────────────┤ │
│ └─────────────────────────────┘ │ │                     │ │
│                                 │ │ [✅ Reached]        │ │
│                                 │ │ [📧 Voicemail]      │ │
│                                 │ │ [❌ No Answer]      │ │
│                                 │ │ [📵 Wrong Number]   │ │
│                                 │ │ [🛑 Do Not Call]    │ │
│                                 │ │ [📞 Busy]           │ │
│                                 │ │ [🔌 Disconnected]   │ │
│                                 │ │                     │ │
│                                 │ └─────────────────────┘ │
│                                 │                         │
│                                 │ ┌─────────────────────┐ │
│                                 │ │ NOTES               │ │
│                                 │ ├─────────────────────┤ │
│                                 │ │                     │ │
│                                 │ │ [Large text area]   │ │
│                                 │ │                     │ │
│                                 │ │                     │ │
│                                 │ │                     │ │
│                                 │ └─────────────────────┘ │
│                                 │                         │
│                                 │ ┌─────────────────────┐ │
│                                 │ │ PLEDGE (optional)   │ │
│                                 │ ├─────────────────────┤ │
│                                 │ │ Amount: $           │ │
│                                 │ │ Method: [Check ▼]   │ │
│                                 │ └─────────────────────┘ │
│                                 │                         │
│                                 │ ┌─────────────────────┐ │
│                                 │ │ FOLLOW-UP           │ │
│                                 │ ├─────────────────────┤ │
│                                 │ │ ☐ Needs follow-up   │ │
│                                 │ │ Date: [Select ▼]    │ │
│                                 │ │ Reason: [         ] │ │
│                                 │ └─────────────────────┘ │
│                                 │                         │
│                                 │ [Skip] [Save & Next →] │
│                                 │                         │
├─────────────────────────────────┴─────────────────────────┤
│  CALL QUEUE                                                │
├────────────────────────────────────────────────────────────┤
│  [Not Called (173)] [Needs Follow-up (12)] [Completed (115│
│   ─────────────────                                        │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Name              Last Gift       Status   Outcome   │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Karen Gallik      Oct 2024        Lapsed  -         │ │
│  │ Mark Jones        Jan 2023        Lapsed  -         │ │
│  │ Susan Chen        Dec 2022        Lapsed  -         │ │
│  │ David Park        Nov 2024        Active  -         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Click any donor to call them next                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Outcome Button Actions:**

```typescript
// When outcome clicked
async function handleOutcome(outcome: CallOutcome) {
  // Create call log
  const callLog = await supabase.from('call_logs').insert({
    call_campaign_id: campaignId,
    contact_id: currentContact.id,
    caller_name: currentUser.name,
    outcome,
    notes: notes,
    pledge_amount: pledgeAmount || null,
    pledge_payment_method: pledgeMethod || null,
    follow_up_needed: needsFollowUp,
    follow_up_date: followUpDate || null,
    follow_up_reason: followUpReason || null
  })

  // Update contact if do not call
  if (outcome === 'do_not_call') {
    await supabase.from('contacts').update({
      do_not_call: true
    }).eq('id', currentContact.id)
  }

  // Show toast
  toast.success(`Call logged: ${outcomeLabels[outcome]}`)

  // Advance to next contact
  loadNextContact()

  // Clear form
  resetForm()
}
```

**Smart Next Contact Logic:**

```typescript
function loadNextContact() {
  // Priority order:
  // 1. Follow-ups due today
  // 2. Not called yet (by call_order)
  // 3. Voicemails from 2+ days ago (second attempt)
  // 4. No answers from 2+ days ago (second attempt)

  const nextContact = await supabase
    .from('call_campaign_contacts')
    .select(`
      contact_id,
      contacts (
        *,
        call_logs!inner (
          outcome,
          call_date,
          follow_up_needed,
          follow_up_date
        )
      )
    `)
    .eq('call_campaign_id', campaignId)
    .eq('status', 'pending')
    .order('call_order', { ascending: true })
    .limit(1)
    .single()

  setCurrentContact(nextContact.contacts)
}
```

### 4. `/campaigns/calls/[id]/reports` - Campaign Reports

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│  Spring 2025 Lapsed Donor Outreach - REPORTS               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  CAMPAIGN SUMMARY                                          │
│                                                            │
│  Timeline: Mar 1 - Mar 14, 2025 (14 days)                  │
│  Status: Active (7 days remaining)                         │
│                                                            │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐│
│  │ Total Calls  │ Contact Rate │ Pledges      │ $ Raised ││
│  │ 127 / 300    │ 85 / 127     │ 15           │ $4,200   ││
│  │ 42%          │ 67%          │ 12%          │ $280 avg ││
│  └──────────────┴──────────────┴──────────────┴──────────┘│
│                                                            │
│  CALL OUTCOMES                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ ✅ Reached:          85 (67%)                         │ │
│  │ 📧 Voicemail:        25 (20%)                         │ │
│  │ ❌ No Answer:        12 (9%)                          │ │
│  │ 📵 Wrong Number:     3 (2%)                           │ │
│  │ 🛑 Do Not Call:      2 (2%)                           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  PLEDGE FOLLOW-UP                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Pledges Secured:     15                               │ │
│  │ Pledges Paid:        8 ($2,100)                       │ │
│  │ Pledges Pending:     7 ($2,100)                       │ │
│  │ Fulfillment Rate:    53% (target: 80%)                │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  [Export Pledge List] [Export All Call Logs]               │
│                                                            │
│  CALLER LEADERBOARD                                        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Caller        Calls   Reached   Pledges   Amount     │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Sarah J.      45      32 (71%)  7         $1,850     │ │
│  │ Mike R.       38      25 (66%)  5         $1,400     │ │
│  │ Lisa K.       28      19 (68%)  2         $600       │ │
│  │ Tom B.        16      9 (56%)   1         $350       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  CONTACT UPDATES                                           │
│  • 2 "Do Not Call" flags added                             │
│  • 3 Wrong numbers corrected                               │
│  • 12 Email addresses updated                              │
│  • 24 Notes added to donor profiles                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Phone-a-Thon Workflow

### Setup Phase (10 minutes)

**1. Create Campaign**
```
Navigate to: Campaigns → Phone-a-Thon → New Campaign

Fill in:
✓ Name: "Spring 2025 Lapsed Donor Outreach"
✓ Dates: Mar 1-14, 2025
✓ Goals: 300 calls, 30 pledges, $7,500

Select donors:
✓ Start with: Lapsed Donors (172 contacts)
✓ Add: Major Donors >$1k (30 contacts)
✓ Manually add: 98 random active donors
✓ Total: 300 contacts

Add call script:
✓ Paste template or write custom

Launch Campaign
```

**2. Staff Training (30 minutes)**
- Walk through caller interface
- Practice call script
- Demonstrate outcome logging
- Show pledge capture process
- Review follow-up workflow

### Daily Calling (2-3 hours)

**Caller Workflow:**

```
1. Open campaign caller interface
   /campaigns/calls/[id]

2. System shows next contact automatically
   - Jeff Stein
   - Giving history visible
   - Phone number ready to dial

3. Make call (using your phone/headset)
   - Read script from screen
   - Personalize based on giving history

4. Log outcome (click button)
   ✅ Reached
   📧 Voicemail
   ❌ No Answer
   etc.

5. If reached:
   - Type notes in text area
   - Capture pledge if made (amount + method)
   - Mark follow-up if needed

6. Click "Save & Next"
   - Saves call log
   - Loads next contact
   - Form resets

7. Repeat 15-20 times (1 hour session)

8. Take break, resume later
```

**Sample Call Flow:**

```
[Caller clicks "Jeff Stein" in queue]

[Screen loads Jeff's info:]
- Phone: (555) 123-4567
- Total donated: $2,450 (12 gifts)
- Last gift: Nov 2024 - $250 to Tree Sale
- Status: Active, Recurring

[Caller dials phone number]

Ring... ring... ring...

Jeff: "Hello?"

Caller (reading script):
"Hi Jeff, this is Sarah from All Seasons Chalice Church.
I'm calling to thank you for your incredible support over
the years. I see you've been a loyal supporter since 2020,
and your recent $250 donation to the Tree Sale made such
a difference. How are you doing today?"

Jeff: "I'm doing well, thanks for calling!"

Caller: "That's wonderful. I wanted to let you know about
our Spring Appeal to support [program]. Would you consider
making a gift to help us reach our goal of $30,000?"

Jeff: "Sure, I can send a check for $300."

Caller: "That's amazing, thank you so much! I'll send you
a reminder email with the mailing address."

[Clicks "✅ Reached"]
[Types notes: "Very enthusiastic, pledged $300 by check"]
[Enters pledge: $300, Check]
[Clicks "Save & Next"]

[Next contact loads immediately]
```

### End of Campaign (1 hour)

**1. View Summary Dashboard**
- Total calls: 300 ✓
- Reached: 185 (62%)
- Pledges: 38 ($9,400)
- Do not call: 5

**2. Export Pledge List**
```csv
Name,Phone,Email,Pledge Amount,Payment Method,Call Date,Status
Jeff Stein,(555) 123-4567,jeff@ex.com,300,Check,2025-03-05,Pending
Karen Gallik,(555) 234-5678,karen@ex.com,250,Credit Card,2025-03-06,Paid
...
```

**3. Send Pledge Reminders**
- Day after call: "Thanks for pledging $300..."
- 1 week: Gentle reminder
- 2 weeks: Final reminder

**4. Create Donations for Paid Pledges**
```typescript
// When check arrives or payment processed
async function convertPledgeToDonation(callLogId: string) {
  const callLog = await getCallLog(callLogId)

  // Create donation record
  await supabase.from('donations').insert({
    contact_id: callLog.contact_id,
    donation_date: new Date(),
    amount: callLog.pledge_amount,
    payment_method: callLog.pledge_payment_method,
    source_system: 'phone_athon',
    external_id: `call-${callLogId}`,
    campaign_name: callLog.call_campaign.name,
    memo: `Pledge from ${formatDate(callLog.call_date)} phone call`
  })

  // Mark pledge as paid
  await supabase.from('call_logs').update({
    pledge_status: 'paid'
  }).eq('id', callLogId)

  toast.success('Pledge converted to donation!')
}
```

**5. Mark Campaign Complete**
- Changes status to 'completed'
- Archives from active campaigns
- Preserves all data for reporting

---

## Complete Roadmap (6 Weeks)

### Week 1: Core Donor Module - Database
- Create donations table
- Create campaigns table
- Add donor fields to contacts
- Database functions and triggers
- Import historical QuickBooks data
- Verify data quality

### Week 2: Core Donor Module - UI (Simplified)
- Build /donors page with tabs
- Build /donors/[id] detail page
- Build /donations list page
- Implement smart search
- Add empty states
- Mobile card views

### Week 3: Campaign Management
- Build /campaigns list
- Build campaign detail pages
- Campaign CRUD operations
- Visual progress bars
- Pace indicators
- Export reports

### Week 4: Automation & Stewardship
- Thank-you email templates
- Tax receipt generation
- Bulk operations
- Communication logging
- Loading states
- Optimistic updates

### Week 5: Phone-a-Thon Module
- Create call_campaigns table
- Create call_logs table
- Build campaign creation wizard
- Build caller interface (split screen)
- Outcome logging + pledge capture
- Reports and exports

### Week 6: Polish & Launch
- Keyboard shortcuts
- Accessibility (ARIA labels, focus)
- Error boundaries
- Performance optimization
- Staff training
- Production deployment

---

## Success Metrics

### Donor Module
**Phase 1 (Database):**
- ✅ 500+ donors with 5 years history
- ✅ 90%+ QuickBooks match rate
- ✅ All aggregates calculating correctly

**Phase 2 (Core UI):**
- ✅ Page load <2 seconds
- ✅ Search results <500ms
- ✅ Mobile responsive

**Phase 3-4 (Campaigns + Automation):**
- ✅ 80%+ thank-you delivery rate
- ✅ Receipts generate <5 seconds each
- ✅ 50% reduction in admin time

### Phone-a-Thon Module
**Per Campaign:**
- ✅ 300 calls in 2 weeks
- ✅ 60% contact rate (180 reached)
- ✅ 10% pledge rate from reached (30 pledges)
- ✅ $7,500 raised ($250 avg pledge)
- ✅ 80% fulfillment within 30 days

**User Experience:**
- ✅ 15 calls/hour average
- ✅ All outcomes logged same day
- ✅ Zero data entry errors
- ✅ Staff satisfaction >90%

**Business Impact:**
- ✅ Re-engage 50+ lapsed donors
- ✅ Update 100+ contact records
- ✅ Identify 20+ major donor prospects
- ✅ Build foundation for annual phone-a-thons

---

## Appendix

### A. UI Component Library

**Simplified Components:**

1. **TabNav** - Horizontal tabs for filtering
2. **SmartSearch** - Search with operator support
3. **BulkActionBar** - Fixed bottom bar (Gmail-style)
4. **EmptyState** - Helpful guidance for empty lists
5. **SkeletonCard** - Loading placeholder
6. **Toast** - Bottom-right notifications
7. **MobileCard** - Card view for mobile
8. **CopyButton** - One-click copy with feedback
9. **PaceIndicator** - Campaign pace status
10. **OutcomeButton** - Large touch-friendly outcome buttons

### B. Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `/` | Focus search |
| `N` | New donor |
| `E` | Export |
| `J` | Next item |
| `K` | Previous item |
| `Enter` | Open selected |
| `?` | Show shortcuts |
| `Esc` | Close modal |

### C. Mobile Breakpoints

```css
/* Tailwind breakpoints */
sm: 640px  /* Small tablets */
md: 768px  /* Tablets */
lg: 1024px /* Small desktops */
xl: 1280px /* Desktops */

/* Mobile-first approach */
- Default: Mobile layout
- md+: Tablet layout
- lg+: Desktop layout
```

### D. Phone-a-Thon Call Script Template

```
"Hi {donor_name}, this is {caller_name} from All Seasons Chalice Church.

How are you doing today?

[PAUSE - Listen]

I'm calling to thank you for your generous support over the years.
I see you've donated {total_donated} since {first_donation_year},
and your most recent gift of {last_amount} to {last_campaign} made
a real difference.

[PAUSE - Let them respond]

I wanted to let you know about our {current_campaign}. We're working
to raise {campaign_goal} to {campaign_purpose}.

Would you consider making a gift to help us reach our goal?

[PAUSE - Listen for response]

[IF YES]
That's wonderful, thank you so much! What amount works for you?

[Record pledge amount]

And how would you like to make your donation? Check, credit card,
or online?

[Record payment method]

Perfect. I'll send you a reminder email with instructions. Thank you
again for your continued support!

[IF NO]
I understand. Is there anything preventing you from giving right now?

[Listen - may reveal address change, financial hardship, dissatisfaction]

[Record notes]

Thank you for your time today. We appreciate all you've done for
All Seasons Chalice Church.

[IF VOICEMAIL]
Hi {donor_name}, this is {caller_name} from All Seasons Chalice Church.
I'm calling to thank you for your support and share an exciting
opportunity to make an impact with our {campaign_name}. I'll try
calling back another time. You can also reach us at {org_phone} or
visit {website}. Thanks!
```

### E. Email Templates for Pledge Follow-Up

**Day After Call:**
```
Subject: Thank you for your pledge!

Hi {donor_name},

Thank you so much for your generous pledge of {pledge_amount} during
our call yesterday!

Your support means the world to us and will help [impact statement].

To fulfill your pledge, you can:

• Mail a check to: [Mailing address]
• Donate online: [Online donation link]
• Call us: [Phone number]

Payment Method: {pledge_method}

We're grateful for supporters like you who make our work possible.

With gratitude,
{Caller name}
All Seasons Chalice Church
```

**1 Week Later (If Unpaid):**
```
Subject: Friendly reminder: Your pledge of {amount}

Hi {donor_name},

I wanted to follow up on the pledge you made during our phone call
last week.

Your pledge: {pledge_amount}
Payment method: {pledge_method}

If you've already sent your donation, thank you! Please disregard
this reminder.

If you haven't had a chance yet, we'd love to receive your gift soon:

• Mail: [Address]
• Online: [Link]
• Questions? Call [Phone]

Thank you for your continued support!

Best regards,
{Caller name}
```

---

**End of Revised Plan**

**Total Timeline:** 6 weeks

**Phase 1-4:** Core Donor Module (4 weeks)
**Phase 5:** Phone-a-Thon Module (1 week)
**Phase 6:** Polish & Launch (1 week)

**Recommendation:** Approve and proceed with phased implementation.
