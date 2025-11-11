# Primary Email Logic & UI Change Design

**Date:** 2025-11-10
**Purpose:** Document how primary email is determined and design UI workflow for changing it

---

## Current Primary Email Determination

### Database Schema

**Two Places Store Email Data:**

1. **`contacts.email`** (legacy, still used)
   - Single email field
   - Currently the "source of truth" for imports
   - Automatically migrated to `contact_emails` with `is_primary = true`

2. **`contact_emails` table** (modern, normalized)
   - Stores multiple emails per contact
   - Fields:
     - `is_primary` (boolean) - Exactly ONE per contact
     - `is_outreach` (boolean) - Which email to use for outreach
     - `verified` (boolean) - Email verified
     - `deliverable` (boolean) - Email deliverability status

### Enforcement Mechanism

**Unique Partial Index (Constraint):**
```sql
CREATE UNIQUE INDEX ux_contact_emails_one_primary
ON contact_emails(contact_id)
WHERE is_primary = true;

CREATE UNIQUE INDEX ux_contact_emails_one_outreach
ON contact_emails(contact_id)
WHERE is_outreach = true;
```

**What this means:**
- ✅ **Exactly 1** email can have `is_primary = true` per contact
- ✅ **Exactly 1** email can have `is_outreach = true` per contact
- ✅ Database will **reject** any attempt to violate this
- ✅ Atomic operations required to change primary

### Outreach Email Fallback Logic

**View:** `v_contact_outreach_email`

**Priority (in order):**
1. `is_outreach = true` → "explicit_outreach"
2. `is_primary = true` → "primary_fallback"
3. `verified = true` (oldest) → "verified_fallback"
4. Any email (oldest) → "any_email_fallback"
5. `contacts.email` → "legacy_contacts_table"

**Purpose:** Always provide an email for outreach even if is_outreach is not set.

### Current Sync Status ⚠️

**TWO-WAY SYNC MISSING:**
- ❌ No trigger: `contacts.email` → `contact_emails.is_primary`
- ❌ No trigger: `contact_emails.is_primary` → `contacts.email`

**Current behavior:**
- Migration (one-time): `contacts.email` → `contact_emails` with `is_primary = true`
- After migration: **No automatic sync**
- Result: The two tables can drift out of sync

---

## Design: UI Workflow for Changing Primary Email

### User Story

> "As a user viewing a contact detail page, I want to change which email is the primary email so that I can update the contact's preferred communication method."

### UI Mockup (Conceptual)

```
Contact Detail - John Doe
━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 Emails
┌──────────────────────────────────────────────────┐
│ ● john@example.com                    [PRIMARY]  │  ← Current primary
│   • personal • kajabi • verified                 │
│                                                   │
│ ○ john.doe@gmail.com            [Make Primary]   │  ← Click to make primary
│   • personal • manual • verified                 │
│                                                   │
│ ○ jdoe@work.com                 [Make Primary]   │
│   • work • manual • not verified                 │
└──────────────────────────────────────────────────┘

💡 Outreach Email: john@example.com (same as primary)
```

### Required Actions

**When user clicks "Make Primary" on john.doe@gmail.com:**

1. **Atomic Database Operation:**
   ```sql
   -- Option A: Use a database function (RECOMMENDED)
   SELECT set_primary_email(
     p_contact_id := 'uuid-here',
     p_new_primary_email := 'john.doe@gmail.com'
   );

   -- Option B: Two-step update (needs transaction)
   BEGIN;
     -- Step 1: Set new primary
     UPDATE contact_emails
     SET is_primary = true
     WHERE contact_id = 'uuid' AND email = 'john.doe@gmail.com';

     -- Step 2: Unset old primary (automatic via unique constraint violation)
     -- This will fail! Need to unset old first.
   ROLLBACK;
   ```

2. **Update `contacts.email` field** (for backward compatibility)
   ```sql
   UPDATE contacts
   SET email = 'john.doe@gmail.com'
   WHERE id = 'uuid';
   ```

3. **Refresh UI** to show new primary

---

## Solution: Database Function for Changing Primary

### Function: `set_primary_email()`

```sql
CREATE OR REPLACE FUNCTION set_primary_email(
  p_contact_id UUID,
  p_new_primary_email TEXT
)
RETURNS TABLE(
  success BOOLEAN,
  message TEXT,
  old_primary_email TEXT,
  new_primary_email TEXT
) AS $$
DECLARE
  v_old_primary_email TEXT;
  v_email_exists BOOLEAN;
BEGIN
  -- Validate: Check if email exists for this contact
  SELECT EXISTS(
    SELECT 1 FROM contact_emails
    WHERE contact_id = p_contact_id
      AND email = p_new_primary_email
  ) INTO v_email_exists;

  IF NOT v_email_exists THEN
    RETURN QUERY SELECT
      false,
      'Email not found for this contact',
      NULL::TEXT,
      NULL::TEXT;
    RETURN;
  END IF;

  -- Get current primary email
  SELECT email INTO v_old_primary_email
  FROM contact_emails
  WHERE contact_id = p_contact_id
    AND is_primary = true;

  -- Check if already primary
  IF v_old_primary_email = p_new_primary_email THEN
    RETURN QUERY SELECT
      true,
      'Email is already primary',
      v_old_primary_email,
      p_new_primary_email;
    RETURN;
  END IF;

  -- ATOMIC OPERATION: Change primary email
  -- Step 1: Unset old primary
  UPDATE contact_emails
  SET is_primary = false
  WHERE contact_id = p_contact_id
    AND is_primary = true;

  -- Step 2: Set new primary
  UPDATE contact_emails
  SET is_primary = true
  WHERE contact_id = p_contact_id
    AND email = p_new_primary_email;

  -- Step 3: Update contacts.email for backward compatibility
  UPDATE contacts
  SET email = p_new_primary_email
  WHERE id = p_contact_id;

  -- Return success
  RETURN QUERY SELECT
    true,
    'Primary email changed successfully',
    v_old_primary_email,
    p_new_primary_email;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
SELECT * FROM set_primary_email(
  'contact-uuid-here',
  'john.doe@gmail.com'
);
```

### Function: `set_outreach_email()`

Similar pattern for changing outreach email:

```sql
CREATE OR REPLACE FUNCTION set_outreach_email(
  p_contact_id UUID,
  p_new_outreach_email TEXT
)
RETURNS TABLE(
  success BOOLEAN,
  message TEXT,
  old_outreach_email TEXT,
  new_outreach_email TEXT
) AS $$
DECLARE
  v_old_outreach_email TEXT;
  v_email_exists BOOLEAN;
BEGIN
  -- Validate email exists
  SELECT EXISTS(
    SELECT 1 FROM contact_emails
    WHERE contact_id = p_contact_id
      AND email = p_new_outreach_email
  ) INTO v_email_exists;

  IF NOT v_email_exists THEN
    RETURN QUERY SELECT
      false,
      'Email not found for this contact',
      NULL::TEXT,
      NULL::TEXT;
    RETURN;
  END IF;

  -- Get current outreach email
  SELECT email INTO v_old_outreach_email
  FROM contact_emails
  WHERE contact_id = p_contact_id
    AND is_outreach = true;

  -- Check if already outreach
  IF v_old_outreach_email = p_new_outreach_email THEN
    RETURN QUERY SELECT
      true,
      'Email is already set for outreach',
      v_old_outreach_email,
      p_new_outreach_email;
    RETURN;
  END IF;

  -- ATOMIC OPERATION
  -- Step 1: Unset old outreach
  UPDATE contact_emails
  SET is_outreach = false
  WHERE contact_id = p_contact_id
    AND is_outreach = true;

  -- Step 2: Set new outreach
  UPDATE contact_emails
  SET is_outreach = true
  WHERE contact_id = p_contact_id
    AND email = p_new_outreach_email;

  RETURN QUERY SELECT
    true,
    'Outreach email changed successfully',
    v_old_outreach_email,
    p_new_outreach_email;
END;
$$ LANGUAGE plpgsql;
```

---

## UI Implementation (Next.js)

### Server Action: `actions/emails.ts`

```typescript
'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function setPrimaryEmail(
  contactId: string,
  newPrimaryEmail: string
) {
  const supabase = createClient()

  // Call database function
  const { data, error } = await supabase.rpc('set_primary_email', {
    p_contact_id: contactId,
    p_new_primary_email: newPrimaryEmail,
  })

  if (error) {
    return { success: false, error: error.message }
  }

  // Revalidate the contact page to show updated data
  revalidatePath(`/contacts/${contactId}`)

  return { success: data[0].success, message: data[0].message }
}

export async function setOutreachEmail(
  contactId: string,
  newOutreachEmail: string
) {
  const supabase = createClient()

  const { data, error } = await supabase.rpc('set_outreach_email', {
    p_contact_id: contactId,
    p_new_outreach_email: newOutreachEmail,
  })

  if (error) {
    return { success: false, error: error.message }
  }

  revalidatePath(`/contacts/${contactId}`)

  return { success: data[0].success, message: data[0].message }
}
```

### Component: `EmailListItem.tsx`

```typescript
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { setPrimaryEmail, setOutreachEmail } from '@/app/actions/emails'
import { useToast } from '@/hooks/use-toast'

interface EmailListItemProps {
  contactId: string
  email: string
  emailType: string
  isPrimary: boolean
  isOutreach: boolean
  source: string
  verified: boolean
}

export function EmailListItem({
  contactId,
  email,
  emailType,
  isPrimary,
  isOutreach,
  source,
  verified,
}: EmailListItemProps) {
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  async function handleSetPrimary() {
    setLoading(true)
    try {
      const result = await setPrimaryEmail(contactId, email)

      if (result.success) {
        toast({
          title: 'Success',
          description: result.message,
        })
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to set primary email',
          variant: 'destructive',
        })
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An unexpected error occurred',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleSetOutreach() {
    setLoading(true)
    try {
      const result = await setOutreachEmail(contactId, email)

      if (result.success) {
        toast({
          title: 'Success',
          description: result.message,
        })
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to set outreach email',
          variant: 'destructive',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-between rounded-lg bg-muted/30 p-3">
      <div>
        <div className="flex items-center gap-2">
          <a href={`mailto:${email}`} className="font-medium hover:text-primary">
            {email}
          </a>
          {isPrimary && <Badge>Primary</Badge>}
          {isOutreach && <Badge variant="secondary">Outreach</Badge>}
          {verified && <Badge variant="outline">✓ Verified</Badge>}
        </div>
        <p className="text-xs text-muted-foreground">
          {emailType} • {source}
        </p>
      </div>

      <div className="flex gap-2">
        {!isPrimary && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleSetPrimary}
            disabled={loading}
          >
            Make Primary
          </Button>
        )}
        {!isOutreach && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSetOutreach}
            disabled={loading}
          >
            Use for Outreach
          </Button>
        )}
      </div>
    </div>
  )
}
```

---

## Summary

### Current State
- **Primary email** = `contacts.email` (migrated to `contact_emails.is_primary = true`)
- **Unique constraint** enforced via partial unique index
- **No automatic sync** between `contacts.email` and `contact_emails`

### Recommended Solution
1. **Create database functions:**
   - `set_primary_email(contact_id, new_email)` - Atomic operation
   - `set_outreach_email(contact_id, new_email)` - Atomic operation

2. **UI Implementation:**
   - Server Actions in Next.js
   - "Make Primary" button on each email
   - Optimistic UI updates
   - Toast notifications

3. **Maintain backward compatibility:**
   - Keep `contacts.email` in sync with primary email
   - Functions update both tables atomically

### Migration Required
Create: `sql/migrations/007_email_management_functions.sql`

---

**Created by:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-10

🤖 Generated with [Claude Code](https://claude.com/claude-code)
