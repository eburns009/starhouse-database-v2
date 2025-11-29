# UI Research: Contact Card Best Practices

**Task:** 1.8 Review Other Platforms for UI Best Practices
**Date:** 2025-11-29
**Purpose:** Inform Task 1.7 Contact Card Redesign

---

## Platforms Reviewed

| Platform | Focus | Key Strength |
|----------|-------|--------------|
| HubSpot | Marketing/Sales CRM | Customizable sidebar cards |
| Salesforce | Enterprise CRM | Compact layouts, dynamic forms |
| Zoho CRM | SMB CRM | Canvas visual customization |
| Pipedrive | Sales-focused CRM | Focus section for priorities |
| Airtable | Database/workflow | Hierarchical linked records |

---

## Common Patterns (What They All Do)

### 1. Two-Column Layout
All platforms use a **left sidebar + right content area** or **header + two columns** structure:
- **Left/Top:** Contact identity, key fields, quick actions
- **Right/Bottom:** Related records, activity timeline, history

### 2. Compact Header with Primary Fields
Every platform shows 3-5 critical fields at the very top:
- Name (always first)
- Email (clickable to compose)
- Phone (clickable to dial if integrated)
- Organization/Company
- Status or label

### 3. Collapsible Sections
All platforms organize fields into collapsible sections:
- Reduces visual clutter
- Users expand what they need
- Preserves information without overwhelming

### 4. Activity Timeline
Central feature in all CRMs:
- Chronological history of interactions
- Most recent at top (or configurable)
- Icons differentiate activity types (email, call, note, meeting)
- Filterable by type or date range

### 5. Related Records as Cards
Associations shown as preview cards:
- Linked deals, tickets, organizations
- Click to expand or navigate
- Count badges show quantity

### 6. Quick Actions in Header
Action buttons positioned prominently:
- Edit, Log Activity, Email, Call
- Consistent placement across all records

---

## Best Ideas Worth Adopting for StarHouse

### 1. "Focus" Section (from Pipedrive)
**What:** A dedicated section at the top showing the most important actionable items:
- Upcoming activities
- Pinned notes
- Draft communications

**Why for StarHouse:** Staff need to quickly see "what's next" for a contact—upcoming event, expiring membership, pending donation acknowledgment.

### 2. Compact Layout with Key Indicators (from Salesforce)
**What:** Show critical status fields as badges/icons in the header:
- Email opt-out indicator
- Do not call flag
- Membership status badge

**Why for StarHouse:** Membership status and donor level should be visible without scrolling.

### 3. Conditional/Dynamic Sections (from HubSpot, Zoho)
**What:** Show/hide sections based on contact type:
- Donors see donation history section
- Members see membership details
- Event attendees see registration history

**Why for StarHouse:** A contact could be a donor, member, AND event attendee. Show relevant sections only when data exists.

### 4. Business Card Summary (from Zoho)
**What:** A visual "business card" at the top with photo placeholder, name, title, and contact methods in a card format.

**Why for StarHouse:** Professional appearance, scannable at a glance.

### 5. Changelog/Revision History (from Pipedrive, Airtable)
**What:** A collapsible section showing when fields were changed and by whom.

**Why for StarHouse:** Audit trail visibility for staff—especially useful after merges or data corrections.

---

## Anti-Patterns to Avoid

### 1. Too Many Tabs
**Problem:** Hiding important info behind multiple tab clicks
**Solution:** Use collapsible sections on a single scrollable page instead

### 2. Cluttered Headers
**Problem:** Showing 10+ fields in the header area
**Solution:** Limit to 5 primary fields; use sections for the rest

### 3. Inconsistent Button Placement
**Problem:** Edit button in different locations on different records
**Solution:** Always place Edit in the same spot (top-right of header)

### 4. Missing Empty States
**Problem:** Blank sections with no guidance
**Solution:** Show helpful text like "No donations recorded" with action link

### 5. Information Overload
**Problem:** Showing all related records expanded by default
**Solution:** Show counts with expand option; collapse by default

### 6. Buried Primary Contact Methods
**Problem:** Email and phone not immediately clickable
**Solution:** Make email/phone prominent and actionable in header

---

## Recommendations for Task 1.7 Contact Card Redesign

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER BAR                                                    [Edit] [More] │
│ ┌──────────┐                                                                │
│ │  Avatar  │  Full Name                          ┌─────────────────────────┐│
│ │  Initials│  Business Name (if exists)          │ Donor: Major           ││
│ │          │  email@example.com (clickable)      │ Member: Active         ││
│ └──────────┘  (555) 123-4567 (clickable)         │ Staff: No              ││
│                                                   └─────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│ LEFT COLUMN (40%)                │ RIGHT COLUMN (60%)                       │
│──────────────────────────────────│──────────────────────────────────────────│
│                                  │                                          │
│ ▼ Contact Details                │ ▼ Activity Timeline                      │
│   All Emails (with source)       │   [Filter: All | Notes | Donations]     │
│   All Phones (with type)         │   • Nov 29 - Donation $100              │
│   All Addresses (mailing flag)   │   • Nov 15 - Event: Fall Gala           │
│                                  │   • Oct 3 - Membership renewed          │
│ ▼ Tags & Roles                   │   • Sep 1 - Note added by Jane          │
│   Kajabi tags (badges)           │                                          │
│   Roles (with dates)             │ ▼ Donations (3 total, $1,250 lifetime)  │
│                                  │   [View All]                             │
│ ▼ External IDs                   │   • 2024-11-29 $100 General Fund        │
│   QuickBooks, PayPal, etc.       │   • 2024-06-15 $150 Building Campaign   │
│   (collapsible, for debugging)   │   • 2024-01-01 $1,000 Annual Gift       │
│                                  │                                          │
│ ▼ Staff Notes                    │ ▼ Memberships                            │
│   [Add Note]                     │   Current: Program Partner (exp 2025-06)│
│   Note content here...           │   History: Individual 2022-2024         │
│                                  │                                          │
│                                  │ ▼ Events & Courses                       │
│                                  │   Upcoming: Winter Workshop (Dec 15)    │
│                                  │   Past: 5 events attended               │
│                                  │                                          │
│                                  │ ▼ Purchases                              │
│                                  │   Products purchased with dates         │
│                                  │                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Specific Recommendations

#### 1. Header Design
- **Avatar:** Circle with initials (first letter of first + last name)
- **Name:** Large, bold—`full_name` as primary
- **Business Name:** Smaller, gray, directly below name (if exists)
- **Contact Methods:** Email and phone as clickable links with icons
- **Status Badges:** Right side of header showing:
  - Donor level (Major/Mid-Level/Standard) if donor
  - Membership status (Active/Expired/None)
  - Any special flags (Do Not Contact, VIP, etc.)

#### 2. Left Column: Identity & Reference
- **Contact Details:** Expandable list of all emails, phones, addresses
  - Show source system as subtle badge (Kajabi, PayPal, etc.)
  - Highlight `is_primary` with star icon
  - Show `is_mailing` flag for addresses
- **Tags & Roles:** Visual badges, grouped by source
- **External IDs:** Collapsed by default (admin/debug info)
- **Staff Notes:** Always visible, easy to add

#### 3. Right Column: Relationships & History
- **Activity Timeline:** Combined view of all interactions
  - Filter tabs: All | Notes | Donations | Events
  - Each entry: date, type icon, brief description
  - Click to expand details
- **Donations:** Summary card with lifetime total + count
  - Show 3 most recent
  - "View All" link to full history
- **Memberships:** Current status prominent, history collapsible
- **Events & Courses:** Upcoming first, then past count
- **Purchases:** Product names from all sources

#### 4. Actions
- **Edit Button:** Top-right, opens modal or inline edit
- **More Menu (...):** Merge, Export, Delete, View Changelog
- **Quick Actions:** Log Note, Log Call, Send Email (if email exists)

#### 5. Empty States
Each section should handle missing data gracefully:
- "No donations recorded" with "Log First Donation" link
- "No membership history" with "Add Membership" link
- "No events attended" (no action needed)

#### 6. Mobile Responsiveness
- Single column on mobile
- Header stacks vertically
- Sections become accordion-style

---

## Implementation Priority

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Header with badges | P0 | Low | High |
| Two-column layout | P0 | Medium | High |
| Collapsible sections | P1 | Low | Medium |
| Activity timeline | P1 | Medium | High |
| Empty states | P1 | Low | Medium |
| Status badges in header | P1 | Low | High |
| Changelog view | P2 | Medium | Low |
| Quick actions | P2 | Medium | Medium |

---

## Sources

### HubSpot
- [Understand and use the record page layout](https://knowledge.hubspot.com/records/work-with-records)
- [Create cards to display data on records](https://knowledge.hubspot.com/object-settings/create-cards-on-records)
- [Customizing the Contact Record View](https://umbrex.com/resources/how-to-set-up-and-use-hubspot-crm/customizing-the-contact-record-view/)
- [View and customize record overviews](https://knowledge.hubspot.com/crm-setup/view-and-customize-record-overviews)

### Salesforce
- [Page Layout Tips](https://help.salesforce.com/s/articleView?id=layouts_tips.htm&language=en_US&type=5)
- [5 Tips to Maximise Your Salesforce Page Layouts](https://www.salesforceben.com/5-tips-to-maximise-your-salesforce-page-layouts-improve-your-ux-ui/)
- [Boost Salesforce Record Page Customization](https://trailhead.salesforce.com/content/learn/modules/lex_customization/lex_customization_page_layouts)

### Zoho CRM
- [Create Page Layouts](https://help.zoho.com/portal/en/kb/crm/customize-crm-account/customizing-page-layouts/articles/create-page-layouts)
- [Online CRM Software With Custom Page Layouts](https://www.zoho.com/crm/page-layouts.html)
- [Customizing Record's Detail Page](https://help.zoho.com/portal/en/kb/crm/customize-crm-account/record-level-customization/articles/page-level-customization)
- [Creating Canvas Detail Pages](https://www.zosuccess.com/blog/create-canvas-detail-pages-and-mobile-pages-in-zoho-crm/)

### Pipedrive
- [Detail view sidebar](https://support.pipedrive.com/en/article/detail-view-sidebar)
- [Detail view](https://support.pipedrive.com/en/article/detail-view)
- [Contact detail view](https://support.pipedrive.com/en/article/contact-detail-view)

### Airtable
- [Interface layout: Record detail](https://support.airtable.com/docs/airtable-interface-layout-record-detail)
- [Interface layout: Record review](https://support.airtable.com/docs/interface-layout-record-review)
- [Getting started with Interface Designer](https://support.airtable.com/docs/getting-started-with-airtable-interface-designer)

### General CRM Best Practices
- [CRM Best Practices for Contacts Management](https://www.nimble.com/blog/crm-best-practices-for-contacts-management-for-small-business/)
- [The ultimate guide to CRM contact management](https://capsulecrm.com/blog/contact-management-best-practices/)
- [8 CRM Best Practices For Your Business](https://www.salesforce.com/crm/best-practices/)
