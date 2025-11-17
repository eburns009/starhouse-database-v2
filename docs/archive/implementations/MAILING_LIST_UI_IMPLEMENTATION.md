# Mailing List UI Implementation Plan

**Date:** 2025-11-14
**Status:** Implementation Ready

---

## What We're Building

### 1. Protect the List ✅
- RLS policies on mailing list views
- Audit logging for all exports
- Staff-only access

### 2. Add to Contact Card
Show mailing list quality score and recommended address on each contact

### 3. New Mailing List Page
- Preview top 50 contacts
- Filter by confidence level
- Export buttons
- Stats dashboard

### 4. Workflow for 28 "Potential" Contacts
- Tag system to track engagement
- Follow-up workflow
- Score tracking

---

## Implementation Steps

### Step 1: Database Protection (DONE ✅)

Migration: `20251114000001_protect_mailing_list.sql`

**What it does:**
- RLS policies: Only staff can view mailing list
- Audit log: Tracks all exports
- Function: `log_mailing_list_export()` logs every export

### Step 2: Add to Contact Detail Card

**Location:** `starhouse-ui/components/contacts/ContactDetailCard.tsx`

**Add new section after "Addresses" card:**
```tsx
<Card>
  <CardHeader>
    <CardTitle className="flex items-center gap-2 text-base">
      <Mail className="h-4 w-4" />
      Mailing List Quality
    </CardTitle>
  </CardHeader>
  <CardContent>
    <MailingListQuality contactId={contact.id} />
  </CardContent>
</Card>
```

**New component:** `components/contacts/MailingListQuality.tsx`

### Step 3: New Mailing List Page

**Location:** `app/mailing-list/page.tsx`

**Features:**
- Show top 50 contacts by default
- Filter: All / High Confidence / Medium-Low / Very Low
- Export buttons
- Real-time stats

### Step 4: Workflow for 28 Potential Contacts

**Create tags:**
- `mailing-list-potential` (auto-assigned to 28 contacts)
- `address-follow-up-needed`
- `awaiting-purchase`

**Create workflow:**
1. Tag the 28 contacts
2. Email campaign targeting them
3. Track responses
4. Update addresses when confirmed

---

## File Structure

```
starhouse-ui/
├── app/
│   └── mailing-list/
│       └── page.tsx (NEW)
├── components/
│   ├── contacts/
│   │   ├── ContactDetailCard.tsx (MODIFY)
│   │   └── MailingListQuality.tsx (NEW)
│   └── mailing-list/
│       ├── MailingListTable.tsx (NEW)
│       ├── ExportButtons.tsx (NEW)
│       └── PotentialContactsWorkflow.tsx (NEW)
└── lib/
    └── api/
        └── mailing-list.ts (NEW)

supabase/
└── migrations/
    ├── 20251114000001_protect_mailing_list.sql (DONE ✅)
    └── 20251114000002_mailing_list_workflow_tags.sql (NEW)
```

---

## Next: Let's implement these components!
