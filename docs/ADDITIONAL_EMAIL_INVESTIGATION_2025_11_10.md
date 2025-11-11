# Additional Email Investigation - 2025-11-10

## Problem Statement

User reported that 2nd emails (alternate emails) are not showing in the Next.js UI for contacts.

**Example:** Corin Blanchard has `corinblanchard@gmail.com` as her additional_email, but it doesn't appear in the UI.

## Investigation Results

### Root Cause ✅ IDENTIFIED

**The `contacts.additional_email` field was never migrated to the `contact_emails` table.**

### Data Analysis

```sql
-- Contacts with additional_email field populated
SELECT COUNT(*) FROM contacts
WHERE additional_email IS NOT NULL
  AND additional_email <> ''
  AND deleted_at IS NULL;
-- Result: 373 contacts

-- Records in contact_emails table
SELECT COUNT(*) FROM contact_emails;
-- Result: 5,601 records

-- Unique contacts in contact_emails
SELECT COUNT(DISTINCT contact_id) FROM contact_emails;
-- Result: 5,600 contacts

-- Additional emails MISSING from contact_emails table
SELECT COUNT(*)
FROM contacts c
LEFT JOIN contact_emails ce ON c.id = ce.contact_id AND ce.email = c.additional_email
WHERE c.additional_email IS NOT NULL
  AND c.additional_email <> ''
  AND c.deleted_at IS NULL
  AND ce.email IS NULL;
-- Result: 372 contacts (99.7% missing!)
```

### Migration File Analysis

**File:** `supabase/migrations/20251102000004_contact_module_migration.sql`

The migration includes:
- ✅ **Step 1:** Migrates `contacts.email` → `contact_emails` (primary email)
- ✅ **Step 2:** Migrates `contacts.paypal_email` → `contact_emails` (if different from primary)
- ❌ **MISSING:** No migration for `contacts.additional_email`

**Evidence from migration file (lines 82-130):**
```sql
-- STEP 2: Migrate contacts.paypal_email → contact_emails
INSERT INTO contact_emails (...)
SELECT ...
FROM contacts c
WHERE c.paypal_email IS NOT NULL
  AND c.paypal_email != c.email
```

**No corresponding step for `additional_email`.**

### UI Code Analysis

**File:** `starhouse-ui/components/contacts/ContactDetailCard.tsx:254-260`

```typescript
// Fetch alternate emails
const { data: emailsData, error: emailsError } = await supabase
  .from('contact_emails')
  .select('id, email, email_type, is_primary, is_outreach, source, verified')
  .eq('contact_id', contactId)
  .order('is_primary', { ascending: false })
  .order('created_at', { ascending: false })
```

**The UI correctly queries `contact_emails` table.** The issue is the data is missing from that table.

### Example Contact: Corin Blanchard

```sql
SELECT
  id,
  email,
  paypal_email,
  additional_email,
  additional_email_source
FROM contacts
WHERE id = '3a961edf-7b2b-4d26-89b2-be784b735dbc';
```

| Field | Value |
|-------|-------|
| email | corin@thestarhouse.org |
| paypal_email | corin@thestarhouse.org |
| additional_email | **corinblanchard@gmail.com** |
| additional_email_source | NULL |

```sql
SELECT email, email_type, is_primary, source
FROM contact_emails
WHERE contact_id = '3a961edf-7b2b-4d26-89b2-be784b735dbc';
```

| email | email_type | is_primary | source |
|-------|------------|------------|--------|
| corin@thestarhouse.org | personal | true | kajabi |

**Missing:** `corinblanchard@gmail.com` ❌

### Additional Email Data Quality

Sample additional_email values (all valid Gmail addresses):
```
corinblanchard@gmail.com
glendaluck@gmail.com
nelghossain@gmail.com
connelsar@gmail.com
zenithrising@gmail.com
mary.christine.obrien@gmail.com
```

Some contacts have multiple emails in the field:
```
aewatson9@gmail.com, ann@annwatson.us
houseofmartin@comcast.net, zenithrising@gmail.com
```

## Impact

- **372 contacts** (373 total with additional_email) have alternate email addresses that are not visible in the UI
- These emails are likely important for outreach and communication
- Gmail addresses appear to be common secondary emails
- Data exists in the database but is not accessible through the modern schema

## Solution

### Option 1: Migration Script (RECOMMENDED)

Create a migration to move `contacts.additional_email` → `contact_emails` table.

**Complexity:** Medium
- Must handle comma-separated emails (some have multiple)
- Must deduplicate against existing emails
- Must set appropriate metadata (source, email_type, is_outreach)

**Migration file:** `sql/migrations/006_migrate_additional_emails.sql`

### Option 2: One-time Data Fix Script

Create a Python script to migrate the data.

**Complexity:** Low
- Can be run once and verified
- Easier to handle edge cases
- Can provide detailed logging

**Script:** `scripts/migrate_additional_emails_to_contact_emails.py`

### Option 3: Modify UI to Show Both

Update UI to query both `contact_emails` AND `contacts.additional_email`.

**Complexity:** Low for short-term
**Not Recommended:** Maintains technical debt, doesn't solve root cause

## Recommendation

**Implement Option 1: SQL Migration Script**

Benefits:
- Fixes the root cause
- Makes data available through proper schema
- Maintains FAANG standards (normalize data)
- One-time operation with verification
- Can be rolled back if needed

Create migration file: `sql/migrations/006_migrate_additional_emails.sql`

The migration should:
1. Split comma-separated emails in `additional_email` field
2. Insert each email into `contact_emails` table
3. Mark as `is_primary = false`, `is_outreach = true`
4. Set `source = additional_email_source` (or 'manual' if NULL)
5. Skip duplicates (emails already in contact_emails)
6. Provide verification counts

## Next Steps

1. Create migration SQL script
2. Test on sample data (10 contacts)
3. Verify results in database
4. Test in UI (should see additional emails)
5. Run full migration
6. Update `contacts.additional_email` column with deprecation comment
7. Document in handoff for future cleanup

## Files Reviewed

- ✅ `supabase/migrations/20251102000004_contact_module_migration.sql` - No additional_email migration
- ✅ `starhouse-ui/components/contacts/ContactDetailCard.tsx:254-260` - UI queries contact_emails correctly
- ✅ Database schema - `contact_emails` table structure supports additional emails
- ✅ Sample data - 372 contacts with valid additional_email values

---

**Investigation completed by:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-10
**Status:** Root cause identified, solution recommended

🤖 Generated with [Claude Code](https://claude.com/claude-code)
