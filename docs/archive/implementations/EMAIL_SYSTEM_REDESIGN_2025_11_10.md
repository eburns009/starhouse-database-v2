# Email System Redesign - Show All Emails & Search by Additional Emails

**Date:** 2025-11-10
**Purpose:** Fix email display and search to handle multiple emails per contact

---

## Problem Statement

**User Requirements:**
1. ✅ See ALL emails associated with a contact (not just primary)
2. ✅ Search should work across ALL emails (not just primary)
3. ✅ Some contacts have 3-4 emails - all need to be visible and searchable
4. ✅ Need ability to change which email is primary in UI
5. ✅ "Outreach" terminology is confusing - should be "additional emails"

**Current Issues:**
- ❌ 373 contacts have `additional_email` field with 404 total emails
- ❌ These additional emails are NOT in `contact_emails` table
- ❌ UI only shows emails from `contact_emails` table
- ❌ Search only queries `contacts.email` (not `contact_emails`)
- ❌ Cannot search by additional emails (e.g., "dralafly@gmail.com" won't find Katherine Kripke)

---

## Data Analysis

### Current Email Distribution

**In `contact_emails` table:**
```
Email Count | Contacts | Percentage
------------|----------|------------
1 email     | 5,599    | 99.98%
2 emails    | 1        | 0.02%
3+ emails   | 0        | 0%
```

**In `contacts.additional_email` field:**
```
Contacts with additional_email: 373
Total additional emails: 404
Max emails in one contact: 3
```

**Example Contacts with Multiple Additional Emails:**

| Contact | Primary Email | Additional Emails (comma-separated) |
|---------|---------------|-------------------------------------|
| Katherine Kripke | kate@katekripke.com | dralafly@gmail.com, kartaelise@gmail.com, katekripke@gmail.com |
| Andrea Dragonfly | andrea@dragonflypassages.com | andrea.dragonfly3@gmail.com, dragonflypassages@gmail.com, andrea.drag0nfly4@gmail.com |
| Catherine Boerder | catherine.boerder@gmail.com | cboerder.toolkit@gmail.com, cboerder.nature@gmail.com, cboerder@hotmail.com |

### Current Search Logic

**File:** `starhouse-ui/components/contacts/ContactSearchResults.tsx:40-47`

```typescript
let query = supabase
  .from('contacts')           // ⚠️ Only queries contacts table
  .select('*')
  .is('deleted_at', null)

query = query.or(
  `first_name.ilike.%${word}%,last_name.ilike.%${word}%,email.ilike.%${word}%,phone.ilike.%${word}%`
  // ⚠️ Only searches contacts.email, NOT contact_emails or additional_email
)
```

**Problem:** Searching for "dralafly@gmail.com" returns ZERO results (should find Katherine Kripke)

---

## Solution Design

### Architecture: Normalize All Emails to `contact_emails` Table

**Single Source of Truth:** `contact_emails` table

**Structure:**
```sql
contact_emails
├── id (uuid, PK)
├── contact_id (uuid, FK → contacts.id)
├── email (text, unique per contact)
├── email_type ('personal' | 'work' | 'other')
├── is_primary (boolean) - Exactly 1 per contact
├── is_outreach (boolean) - DEPRECATED, keep for compatibility
├── source (text) - Where email came from
└── verified (boolean)
```

**Constraints:**
- `ux_contact_emails_one_primary` - Ensures exactly 1 primary per contact
- `ux_contact_emails_unique_per_contact` - No duplicate emails per contact

### Migration Strategy

**STEP 1: Parse and Insert Additional Emails**

```sql
-- Split comma-separated additional_email into individual rows
INSERT INTO contact_emails (
  contact_id,
  email,
  email_type,
  is_primary,
  is_outreach,
  source,
  verified,
  created_at
)
SELECT
  c.id,
  TRIM(email_part) as email,  -- Trim whitespace
  'personal' as email_type,
  false as is_primary,  -- Never primary (primary already set)
  false as is_outreach,
  COALESCE(c.additional_email_source, 'manual') as source,
  false as verified,  -- Assume not verified
  c.created_at
FROM contacts c
CROSS JOIN LATERAL unnest(string_to_array(c.additional_email, ',')) as email_part
WHERE c.additional_email IS NOT NULL
  AND c.additional_email <> ''
  AND c.deleted_at IS NULL
  AND TRIM(email_part) ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'  -- Valid email format
ON CONFLICT (contact_id, email) DO NOTHING;  -- Skip if already exists
```

**Expected Result:**
- Insert ~404 additional emails
- Katherine Kripke will have 4 total emails (1 primary + 3 additional)
- All emails searchable

**STEP 2: Verify Migration**

```sql
-- Check results
SELECT
  'Contacts with 1 email' as metric,
  COUNT(*)
FROM (
  SELECT contact_id
  FROM contact_emails
  GROUP BY contact_id
  HAVING COUNT(*) = 1
) x
UNION ALL
SELECT
  'Contacts with 2 emails',
  COUNT(*)
FROM (
  SELECT contact_id
  FROM contact_emails
  GROUP BY contact_id
  HAVING COUNT(*) = 2
) x
UNION ALL
SELECT
  'Contacts with 3+ emails',
  COUNT(*)
FROM (
  SELECT contact_id
  FROM contact_emails
  GROUP BY contact_id
  HAVING COUNT(*) >= 3
) x;
```

### UI Design: Email Display

**Contact Detail Page - All Emails Section:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Email Addresses (4)

┌──────────────────────────────────────────────┐
│ ● kate@katekripke.com          [PRIMARY]     │
│   personal • kajabi • verified               │
│   [Use for Email Campaigns]                  │
│                                              │
│ ○ dralafly@gmail.com       [Make Primary]    │
│   personal • manual • not verified           │
│   [Verify Email] [Remove]                    │
│                                              │
│ ○ kartaelise@gmail.com     [Make Primary]    │
│   personal • manual • not verified           │
│   [Verify Email] [Remove]                    │
│                                              │
│ ○ katekripke@gmail.com     [Make Primary]    │
│   personal • manual • not verified           │
│   [Verify Email] [Remove]                    │
└──────────────────────────────────────────────┘
```

**Key Features:**
- ✅ Shows ALL emails from `contact_emails` table
- ✅ Primary email clearly marked
- ✅ Can click "Make Primary" on any email
- ✅ Email type, source, verification status shown
- ✅ Actions: Verify, Remove (soft delete)

### Search Redesign

**Current Approach (WRONG):**
```typescript
// Searches only contacts.email
query = query.or(`email.ilike.%${searchQuery}%`)
```

**New Approach (CORRECT):**

**Option 1: Join with contact_emails**
```typescript
// Search across all emails in contact_emails
const { data, error } = await supabase
  .from('contacts')
  .select(`
    *,
    contact_emails!inner(email)
  `)
  .or(`
    first_name.ilike.%${searchQuery}%,
    last_name.ilike.%${searchQuery}%,
    phone.ilike.%${searchQuery}%,
    contact_emails.email.ilike.%${searchQuery}%
  `)
  .is('deleted_at', null)
  .limit(20)
```

**Option 2: Use Database Function (RECOMMENDED)**

Already exists: `search_contacts(p_query text)` function

**Check if it searches contact_emails:**

```sql
-- View function definition
\df+ search_contacts
```

**If function doesn't search contact_emails, update it:**

```sql
CREATE OR REPLACE FUNCTION search_contacts(
  p_query TEXT,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  contact_id UUID,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  total_spent NUMERIC,
  is_member BOOLEAN,
  is_donor BOOLEAN,
  match_score REAL,
  match_type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ON (c.id)
    c.id,
    CONCAT_WS(' ', c.first_name, c.last_name) as full_name,
    c.email,
    c.phone,
    c.total_spent,
    c.has_active_subscription as is_member,
    (c.total_spent > 0) as is_donor,
    1.0::REAL as match_score,
    'exact'::TEXT as match_type
  FROM contacts c
  LEFT JOIN contact_emails ce ON c.id = ce.contact_id
  WHERE c.deleted_at IS NULL
    AND (
      c.first_name ILIKE '%' || p_query || '%'
      OR c.last_name ILIKE '%' || p_query || '%'
      OR c.phone ILIKE '%' || p_query || '%'
      OR c.email ILIKE '%' || p_query || '%'
      OR ce.email ILIKE '%' || p_query || '%'  -- ✅ SEARCH ADDITIONAL EMAILS
    )
  ORDER BY c.id, c.created_at DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
```

**Update UI to use function:**

```typescript
// Use database function for search
const { data, error } = await supabase
  .rpc('search_contacts', {
    p_query: searchQuery,
    p_limit: 20,
    p_offset: 0
  })
```

---

## Terminology Changes

**OLD (Confusing):**
- "Primary Email" ✅ Keep
- "Outreach Email" ❌ Remove
- `is_outreach` field ❌ Deprecate (keep for compatibility)

**NEW (Clear):**
- **Primary Email** - Main contact email (exactly 1 per contact)
- **Additional Emails** - All other emails
- **All Emails** - Primary + Additional

**Database Changes:**
```sql
-- Deprecate is_outreach column (keep for backward compatibility)
COMMENT ON COLUMN contact_emails.is_outreach IS
'⚠️ DEPRECATED: No longer used. All non-primary emails are "additional emails".
Use is_primary to identify the main email.';

-- Drop the unique constraint on outreach (no longer needed)
DROP INDEX IF EXISTS ux_contact_emails_one_outreach;
DROP INDEX IF EXISTS idx_contact_emails_outreach;

-- Drop view that uses outreach
DROP VIEW IF EXISTS v_contact_outreach_email;
```

---

## Implementation Checklist

### Database Changes

**File:** `sql/migrations/008_normalize_all_emails.sql`

- [ ] **Step 1:** Backup `contact_emails` table
- [ ] **Step 2:** Parse comma-separated `additional_email` into rows
- [ ] **Step 3:** Insert all additional emails into `contact_emails`
- [ ] **Step 4:** Verify email count distribution
- [ ] **Step 5:** Update `search_contacts()` function to search all emails
- [ ] **Step 6:** Deprecate `is_outreach` field (add comment)
- [ ] **Step 7:** Drop `ux_contact_emails_one_outreach` constraint
- [ ] **Step 8:** Drop `v_contact_outreach_email` view (if exists)
- [ ] **Step 9:** Create monitoring view for email health

### UI Changes

**File:** `starhouse-ui/components/contacts/ContactDetailCard.tsx`

- [ ] Display ALL emails from `contact_emails` table
- [ ] Show email count in header (e.g., "Email Addresses (4)")
- [ ] Mark primary email clearly
- [ ] Add "Make Primary" button for each email
- [ ] Remove "outreach" terminology
- [ ] Show email type, source, verification status

**File:** `starhouse-ui/components/contacts/ContactSearchResults.tsx`

- [ ] Update search to use `search_contacts()` function
- [ ] Ensure search works across all emails
- [ ] Test: Search for "dralafly@gmail.com" should find Katherine Kripke

**File:** `starhouse-ui/app/actions/emails.ts` (NEW)

- [ ] Create `setPrimaryEmail(contactId, email)` server action
- [ ] Create `removeEmail(contactId, email)` server action
- [ ] Create `addEmail(contactId, email, emailType)` server action

---

## Testing Plan

### Database Tests

```sql
-- Test 1: Katherine Kripke should have 4 emails
SELECT
  c.first_name,
  c.last_name,
  COUNT(ce.email) as email_count,
  string_agg(ce.email, ', ' ORDER BY ce.is_primary DESC) as all_emails
FROM contacts c
INNER JOIN contact_emails ce ON c.id = ce.contact_id
WHERE c.last_name = 'Kripke'
GROUP BY c.id, c.first_name, c.last_name;
-- Expected: 4 emails

-- Test 2: Search for additional email should work
SELECT * FROM search_contacts('dralafly@gmail.com', 10, 0);
-- Expected: Returns Katherine Kripke

-- Test 3: All contacts should have at least 1 email
SELECT COUNT(*) FROM contacts c
WHERE c.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM contact_emails ce WHERE ce.contact_id = c.id
  );
-- Expected: 0 (after backfill)
```

### UI Tests

1. **View Contact with Multiple Emails**
   - Navigate to Katherine Kripke
   - Should see 4 email addresses
   - Primary should be marked clearly

2. **Search by Additional Email**
   - Search for "dralafly@gmail.com"
   - Should find Katherine Kripke
   - Should highlight matching email

3. **Change Primary Email**
   - Click "Make Primary" on "dralafly@gmail.com"
   - Should update immediately
   - Database should reflect change

---

## Migration SQL

**File:** `sql/migrations/008_normalize_all_emails.sql`

```sql
-- ============================================
-- NORMALIZE ALL EMAILS TO contact_emails TABLE
-- ============================================

BEGIN;

-- STEP 1: Backup
CREATE TABLE IF NOT EXISTS contact_emails_backup_20251110 AS
SELECT * FROM contact_emails;

-- STEP 2: Parse and insert additional emails
INSERT INTO contact_emails (
  contact_id,
  email,
  email_type,
  is_primary,
  is_outreach,
  source,
  verified,
  created_at
)
SELECT
  c.id,
  TRIM(email_part)::TEXT as email,
  'personal'::TEXT as email_type,
  false as is_primary,
  false as is_outreach,
  COALESCE(c.additional_email_source, 'manual')::TEXT as source,
  false as verified,
  c.created_at
FROM contacts c
CROSS JOIN LATERAL unnest(string_to_array(c.additional_email, ',')) as email_part
WHERE c.additional_email IS NOT NULL
  AND c.additional_email <> ''
  AND c.deleted_at IS NULL
  AND TRIM(email_part) ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'
ON CONFLICT (contact_id, email) DO NOTHING;

-- STEP 3: Verify
DO $$
DECLARE
  v_inserted_count INTEGER;
  v_expected_count INTEGER := 404;
BEGIN
  SELECT COUNT(*) INTO v_inserted_count
  FROM contact_emails
  WHERE source = 'manual'
    AND is_primary = false
    AND created_at >= NOW() - INTERVAL '1 minute';

  RAISE NOTICE 'Inserted % additional emails (expected ~%)',
    v_inserted_count, v_expected_count;

  IF v_inserted_count < (v_expected_count * 0.9) THEN
    RAISE WARNING 'Only inserted % emails, expected ~%',
      v_inserted_count, v_expected_count;
  END IF;
END $$;

-- STEP 4: Update search function
CREATE OR REPLACE FUNCTION search_contacts(
  p_query TEXT,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  contact_id UUID,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  total_spent NUMERIC,
  is_member BOOLEAN,
  is_donor BOOLEAN,
  match_score REAL,
  match_type TEXT
) AS $func$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ON (c.id)
    c.id,
    CONCAT_WS(' ', c.first_name, c.last_name) as full_name,
    c.email,
    c.phone,
    c.total_spent,
    c.has_active_subscription as is_member,
    (c.total_spent > 0) as is_donor,
    1.0::REAL as match_score,
    'exact'::TEXT as match_type
  FROM contacts c
  LEFT JOIN contact_emails ce ON c.id = ce.contact_id
  WHERE c.deleted_at IS NULL
    AND (
      c.first_name ILIKE '%' || p_query || '%'
      OR c.last_name ILIKE '%' || p_query || '%'
      OR c.phone ILIKE '%' || p_query || '%'
      OR c.email ILIKE '%' || p_query || '%'
      OR ce.email ILIKE '%' || p_query || '%'
    )
  ORDER BY c.id, c.created_at DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$func$ LANGUAGE plpgsql;

-- STEP 5: Deprecate is_outreach
COMMENT ON COLUMN contact_emails.is_outreach IS
'⚠️ DEPRECATED: Use is_primary instead. All non-primary emails are additional emails.';

COMMIT;

-- Verification queries
SELECT 'Migration complete!' as status;

-- Show email distribution
SELECT
  email_count,
  COUNT(*) as contacts_with_this_many
FROM (
  SELECT contact_id, COUNT(*) as email_count
  FROM contact_emails
  GROUP BY contact_id
) counts
GROUP BY email_count
ORDER BY email_count;
```

---

## Summary

**Changes:**
1. ✅ Migrate all `additional_email` → `contact_emails` table (split comma-separated)
2. ✅ Update search to query ALL emails in `contact_emails`
3. ✅ UI shows ALL emails per contact (not just primary)
4. ✅ Deprecate "outreach" terminology → "additional emails"
5. ✅ Add "Make Primary" functionality

**Impact:**
- Katherine Kripke will have 4 emails (was 1)
- Searching "dralafly@gmail.com" will find her (currently doesn't)
- 373 contacts get their additional emails migrated (~404 total emails)
- Clear terminology: Primary vs Additional

---

**Created by:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-10

🤖 Generated with [Claude Code](https://claude.com/claude-code)
