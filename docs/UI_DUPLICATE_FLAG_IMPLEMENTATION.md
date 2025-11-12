# UI Duplicate Flag Implementation Guide

**Date**: 2025-11-12
**Purpose**: Show potential duplicate contacts in the UI for manual review

---

## Overview

The duplicate flagging system adds 3 new fields to the `contacts` table:
- `potential_duplicate_group` - Group ID linking related duplicates
- `potential_duplicate_reason` - Human-readable reason (e.g., "Same name + phone")
- `potential_duplicate_flagged_at` - When the flag was added

---

## Database Schema

```sql
-- Added to contacts table
ALTER TABLE contacts
ADD COLUMN potential_duplicate_group TEXT,
ADD COLUMN potential_duplicate_reason TEXT,
ADD COLUMN potential_duplicate_flagged_at TIMESTAMPTZ;

-- Index for performance
CREATE INDEX idx_contacts_duplicate_group
ON contacts(potential_duplicate_group)
WHERE potential_duplicate_group IS NOT NULL;
```

---

## UI Implementation

### 1. Contact List - Show Badge

**File**: `starhouse-ui/components/contacts/ContactList.tsx`

```typescript
interface Contact {
  id: string
  email: string
  first_name: string
  last_name: string
  // ... other fields ...
  potential_duplicate_group?: string | null
  potential_duplicate_reason?: string | null
}

function ContactRow({ contact }: { contact: Contact }) {
  return (
    <div className="flex items-center gap-2">
      <div>
        {contact.first_name} {contact.last_name}
        <div className="text-sm text-gray-500">{contact.email}</div>
      </div>

      {/* Duplicate Warning Badge */}
      {contact.potential_duplicate_group && (
        <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
          ⚠️ Potential Duplicate
        </span>
      )}
    </div>
  )
}
```

---

### 2. Contact Detail - Show Duplicate Group

**File**: `starhouse-ui/components/contacts/ContactDetail.tsx`

```typescript
'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

export function ContactDetail({ contactId }: { contactId: string }) {
  const [contact, setContact] = useState<Contact | null>(null)
  const [duplicates, setDuplicates] = useState<Contact[]>([])
  const supabase = createClient()

  useEffect(() => {
    async function loadContact() {
      // Load main contact
      const { data } = await supabase
        .from('contacts')
        .select('*')
        .eq('id', contactId)
        .single()

      setContact(data)

      // If contact has duplicate flag, load the duplicate group
      if (data?.potential_duplicate_group) {
        const { data: dupes } = await supabase
          .from('contacts')
          .select('*')
          .eq('potential_duplicate_group', data.potential_duplicate_group)
          .neq('id', contactId)
          .is('deleted_at', null)

        setDuplicates(dupes || [])
      }
    }

    loadContact()
  }, [contactId])

  if (!contact) return <div>Loading...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">
          {contact.first_name} {contact.last_name}
        </h1>
        <p className="text-gray-600">{contact.email}</p>
      </div>

      {/* Duplicate Warning */}
      {contact.potential_duplicate_group && (
        <div className="border border-yellow-300 bg-yellow-50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="text-yellow-600 text-xl">⚠️</div>
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900">
                Potential Duplicate Detected
              </h3>
              <p className="text-sm text-yellow-800 mt-1">
                {contact.potential_duplicate_reason}
              </p>

              {/* Show duplicate contacts */}
              {duplicates.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-yellow-900 mb-2">
                    Possible duplicate accounts:
                  </p>
                  <div className="space-y-2">
                    {duplicates.map((dup) => (
                      <div
                        key={dup.id}
                        className="bg-white rounded border border-yellow-200 p-3"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">
                              {dup.first_name} {dup.last_name}
                            </div>
                            <div className="text-sm text-gray-600">
                              {dup.email}
                            </div>
                            {dup.phone && (
                              <div className="text-sm text-gray-500">
                                📞 {dup.phone}
                              </div>
                            )}
                          </div>
                          <a
                            href={`/contacts/${dup.id}`}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            View →
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Merge button */}
                  <button
                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    onClick={() => {
                      // TODO: Implement merge modal
                      alert('Merge functionality coming soon!')
                    }}
                  >
                    Merge Contacts
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Rest of contact details */}
      <div>
        {/* ... existing contact details ... */}
      </div>
    </div>
  )
}
```

---

### 3. Admin Page - Review All Duplicates

**File**: `starhouse-ui/app/admin/duplicates/page.tsx`

```typescript
'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

interface DuplicateGroup {
  group_id: string
  reason: string
  contact_count: number
  contacts: Contact[]
}

export default function DuplicatesPage() {
  const [groups, setGroups] = useState<DuplicateGroup[]>([])
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const supabase = createClient()

  useEffect(() => {
    async function loadDuplicates() {
      // Get all contacts with duplicate flags
      const { data: contacts } = await supabase
        .from('contacts')
        .select('*')
        .not('potential_duplicate_group', 'is', null)
        .is('deleted_at', null)
        .order('potential_duplicate_group')

      if (!contacts) return

      // Group by duplicate_group
      const groupMap = new Map<string, DuplicateGroup>()

      contacts.forEach((contact) => {
        const groupId = contact.potential_duplicate_group!
        if (!groupMap.has(groupId)) {
          groupMap.set(groupId, {
            group_id: groupId,
            reason: contact.potential_duplicate_reason || 'Unknown',
            contact_count: 0,
            contacts: [],
          })
        }
        const group = groupMap.get(groupId)!
        group.contacts.push(contact)
        group.contact_count++
      })

      setGroups(Array.from(groupMap.values()))
    }

    loadDuplicates()
  }, [])

  // Filter groups by confidence level
  const filteredGroups = groups.filter((group) => {
    if (filter === 'all') return true
    if (filter === 'high') return group.reason.includes('phone') || group.reason.includes('address')
    if (filter === 'medium') return group.reason.includes('address') && !group.reason.includes('phone')
    if (filter === 'low') return !group.reason.includes('phone') && !group.reason.includes('address')
    return true
  })

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Duplicate Contacts</h1>
        <p className="text-gray-600 mt-2">
          Review and merge potential duplicate contacts
        </p>
      </div>

      {/* Filter buttons */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded ${
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          All ({groups.length})
        </button>
        <button
          onClick={() => setFilter('high')}
          className={`px-4 py-2 rounded ${
            filter === 'high'
              ? 'bg-red-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          🔴 High Confidence
        </button>
        <button
          onClick={() => setFilter('medium')}
          className={`px-4 py-2 rounded ${
            filter === 'medium'
              ? 'bg-yellow-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          🟡 Medium Confidence
        </button>
        <button
          onClick={() => setFilter('low')}
          className={`px-4 py-2 rounded ${
            filter === 'low'
              ? 'bg-green-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          🟢 Low Confidence
        </button>
      </div>

      {/* Duplicate groups */}
      <div className="space-y-4">
        {filteredGroups.map((group) => (
          <div
            key={group.group_id}
            className="border rounded-lg p-4 bg-white shadow-sm"
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-lg">
                  {group.contacts[0]?.first_name} {group.contacts[0]?.last_name}
                </h3>
                <p className="text-sm text-gray-600">
                  {group.contact_count} accounts • {group.reason}
                </p>
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Merge
              </button>
            </div>

            {/* Contact cards */}
            <div className="grid gap-3 md:grid-cols-2">
              {group.contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="border rounded p-3 bg-gray-50"
                >
                  <div className="font-medium">{contact.email}</div>
                  {contact.phone && (
                    <div className="text-sm text-gray-600">📞 {contact.phone}</div>
                  )}
                  {contact.address_line_1 && (
                    <div className="text-sm text-gray-600">
                      📍 {contact.address_line_1}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 mt-2">
                    Created: {new Date(contact.created_at).toLocaleDateString()}
                  </div>
                  <a
                    href={`/contacts/${contact.id}`}
                    className="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block"
                  >
                    View details →
                  </a>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {filteredGroups.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No duplicates found in this category
        </div>
      )}
    </div>
  )
}
```

---

## Running the Flagging Script

### Step 1: Dry-Run (Review)
```bash
cd /workspaces/starhouse-database-v2
set -a && source .env && set +a
python3 scripts/flag_potential_duplicates.py --dry-run
```

### Step 2: Execute (Apply Flags)
```bash
python3 scripts/flag_potential_duplicates.py --execute
```

### Step 3: Clear Flags (Optional)
```bash
python3 scripts/flag_potential_duplicates.py --clear
```

---

## Confidence Levels

**🔴 High Confidence** (137 groups)
- Same first_name + last_name + phone
- Same first_name + last_name + address
- **Action**: Likely safe to merge automatically

**🟡 Medium Confidence** (25 groups)
- Same first_name + last_name + address (but different phones)
- **Action**: Review before merging

**🟢 Low Confidence** (42 groups)
- Same first_name + last_name only
- **Action**: Manual review required (could be different people)

---

## Example Queries

### Get all duplicate groups
```sql
SELECT
  potential_duplicate_group,
  potential_duplicate_reason,
  COUNT(*) as contact_count,
  STRING_AGG(email, ', ') as emails
FROM contacts
WHERE potential_duplicate_group IS NOT NULL
  AND deleted_at IS NULL
GROUP BY potential_duplicate_group, potential_duplicate_reason
ORDER BY COUNT(*) DESC;
```

### Get duplicates for a specific contact
```sql
SELECT *
FROM contacts
WHERE potential_duplicate_group = (
  SELECT potential_duplicate_group
  FROM contacts
  WHERE id = 'CONTACT_ID_HERE'
)
AND deleted_at IS NULL;
```

### Count duplicates by confidence
```sql
SELECT
  CASE
    WHEN potential_duplicate_reason LIKE '%phone%' THEN 'High'
    WHEN potential_duplicate_reason LIKE '%address%' THEN 'Medium'
    ELSE 'Low'
  END as confidence,
  COUNT(DISTINCT potential_duplicate_group) as groups,
  COUNT(*) as contacts
FROM contacts
WHERE potential_duplicate_group IS NOT NULL
  AND deleted_at IS NULL
GROUP BY confidence;
```

---

## Next Steps

1. **Run the flagging script** to add flags to database
2. **Update UI queries** to include duplicate fields
3. **Add duplicate badge** to contact list
4. **Create admin page** for reviewing duplicates
5. **Build merge functionality** (future enhancement)

---

## Benefits

✅ **Non-destructive** - Flags don't change original data
✅ **Reversible** - Can clear flags and re-run
✅ **User-controlled** - Staff decides which to merge
✅ **Confidence levels** - High/medium/low guidance
✅ **Transparent** - Shows reason for each flag

---

**Created**: 2025-11-12
**Status**: Ready to implement
