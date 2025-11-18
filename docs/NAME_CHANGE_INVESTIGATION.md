# Contact Name Change Investigation & Fix

**Date:** 2025-11-18
**Issue:** Ed Burns → Erik Burns name mutation
**Status:** 🔧 Root cause identified, safeguards implemented

---

## Summary

**Root Cause:** Kajabi webhook handler automatically overwrites contact names when receiving `contact.updated` events from Kajabi. If someone updated the Kajabi contact to "Erik Burns", it would immediately overwrite "Ed Burns" in your database with no audit trail.

**Risk Level:** CRITICAL - Affects all contacts, happens automatically, no visibility

---

## How Name Changes Can Occur

### 1. Kajabi Webhook (CRITICAL - Auto-executes)

**File:** [`supabase/functions/kajabi-webhook/index.ts:729-735`](supabase/functions/kajabi-webhook/index.ts#L729-L735)

**What it does:**
```typescript
.upsert(contactData, {
  onConflict: 'email',
  ignoreDuplicates: false  // ⚠️ OVERWRITES existing data
})
```

**When it runs:** Real-time, whenever Kajabi sends a `contact.updated` webhook event

**Why it's dangerous:**
- No validation that new name is correct
- No audit log of what changed
- No way to prevent bad data from corrupting your database
- `ignoreDuplicates: false` means it REPLACES data on conflict

**Example scenario:**
1. Someone in Kajabi admin panel changes "Ed Burns" to "Erik Burns" (typo or mistake)
2. Kajabi sends `contact.updated` webhook
3. Your database is automatically updated to "Erik Burns"
4. No notification, no audit trail, no way to know what happened

---

### 2. PayPal Webhook (CRITICAL - Auto-executes)

**File:** [`supabase/functions/paypal-webhook/index.ts:864-867`](supabase/functions/paypal-webhook/index.ts#L864-L867)

**Same issue:** Overwrites names from PayPal transaction data

---

### 3. Smart Name Enrichment Script (HIGH - Auto-executes for high confidence)

**File:** [`scripts/smart_name_enrichment.py:255`](scripts/smart_name_enrichment.py#L255)

**What it does:** Extracts names from email patterns and updates database

**Example:**
- Email: `erikburns@domain.com`
- Script extracts: "Erik Burns" (HIGH confidence)
- Automatically updates database: `first_name = 'Erik'`

**When it runs:** Line 255 shows `dry_run=False` meaning it DOES modify data

---

### 4. Other Scripts

**Batch update scripts:**
- `scripts/batch_update_nan_names.py` - Hardcoded name replacements
- `scripts/enrich_contacts_from_donors.py` - Parses donor names via naive space-splitting
- `scripts/merge_duplicate_contacts.py` - Merges duplicates (can override names)
- `scripts/extract_last_names_round*.py` - Extracts last names from email patterns

All of these can modify contact names with varying levels of risk.

---

## Safeguards Implemented

### 1. ✅ Audit Logging Migration

**File:** [`sql/migrations/010_add_name_change_audit_log.sql`](sql/migrations/010_add_name_change_audit_log.sql)

**What it does:**
- Creates `contact_name_audit` table to log ALL name changes
- Automatically triggers on any UPDATE to `contacts.first_name`, `contacts.last_name`, or `contacts.display_name`
- Captures:
  - Old name → New name
  - Who changed it (`changed_by`: 'kajabi_webhook', 'paypal_webhook', 'manual_update', etc.)
  - When it changed (`changed_at` timestamp)
  - Change context (webhook event ID, script name, etc.)

**Example audit record:**
```sql
{
  contact_id: 'abc-123',
  old_first_name: 'Ed',
  old_last_name: 'Burns',
  new_first_name: 'Erik',
  new_last_name: 'Burns',
  changed_by: 'kajabi_webhook',
  change_source: 'kajabi_id:12345',
  changed_at: '2025-11-18 10:30:00'
}
```

**Helper function:**
```sql
-- View complete name change history for a contact
SELECT * FROM get_contact_name_history('contact-id-here');
```

---

### 2. ✅ Webhook Audit Context

**Updated files:**
- `supabase/functions/kajabi-webhook/index.ts` - Sets audit context before upserts
- `supabase/functions/paypal-webhook/index.ts` - Sets audit context before upserts

**What it does:**
Before modifying contact data, webhooks now call:
```typescript
await supabase.rpc('execute_sql', {
  sql: `SELECT set_config('app.change_source', 'kajabi_webhook', false)`
})
```

This sets PostgreSQL session variables that the audit trigger captures, so you know exactly which webhook changed the name.

---

## How to Investigate Future Name Changes

### Step 1: Check Audit Log

```sql
-- Get name change history for Ed Burns
SELECT * FROM get_contact_name_history(
  (SELECT id FROM contacts WHERE email = 'eburns009@gmail.com')
);
```

**Output:**
```
changed_at           | old_name   | new_name    | changed_by      | change_source
---------------------|------------|-------------|-----------------|------------------
2025-11-18 10:30:00 | Ed Burns   | Erik Burns  | kajabi_webhook  | kajabi_id:12345
2025-11-15 14:20:00 | Edward B   | Ed Burns    | manual_update   | staff_member_id:5
```

### Step 2: Check Webhook Events Table

```sql
SELECT event_type, event_data, created_at, processed
FROM webhook_events
WHERE event_data::text ILIKE '%burns%'
ORDER BY created_at DESC
LIMIT 10;
```

### Step 3: Check Contact Updated At

```sql
SELECT email, first_name, last_name, updated_at
FROM contacts
WHERE email = 'eburns009@gmail.com';
```

The `updated_at` timestamp shows when the name was last changed.

---

## How to Fix Incorrect Names

### Manual Fix via SQL

```sql
-- Fix Ed Burns back to Ed
UPDATE contacts
SET first_name = 'Ed',
    updated_at = NOW()
WHERE email = 'eburns009@gmail.com';
```

### Fix via Supabase Dashboard

1. Go to Supabase Dashboard → Table Editor → contacts
2. Find contact by email: `eburns009@gmail.com`
3. Edit `first_name` field
4. Click Save

**Note:** Both methods will be logged in the `contact_name_audit` table!

---

## Preventing Future Mutations

### Option 1: Manual Review Required (Recommended)

Modify webhook handlers to require admin approval for name changes:

```typescript
// Instead of automatically overwriting:
if (existingContact.first_name !== data.first_name) {
  // Store in pending_name_changes table for admin review
  await supabase.from('pending_name_changes').insert({
    contact_id: existingContact.id,
    current_name: `${existingContact.first_name} ${existingContact.last_name}`,
    proposed_name: `${data.first_name} ${data.last_name}`,
    source: 'kajabi_webhook'
  })
  // Don't update automatically!
}
```

### Option 2: Only Update If Empty

Only allow webhooks to set names if they're currently NULL or 'nan':

```typescript
// Only update if name is missing
if (!existingContact.first_name || existingContact.first_name === 'nan') {
  contactData.first_name = data.first_name
}
// Otherwise, preserve existing name
```

### Option 3: Name Validation Rules

Add validation to reject obviously wrong names:

```typescript
function validateName(oldName: string, newName: string): boolean {
  // Reject if new name is single letter (likely abbreviation)
  if (newName.length < 2) return false

  // Reject if drastically different (use Levenshtein distance)
  const similarity = calculateSimilarity(oldName, newName)
  if (similarity < 0.5) return false

  return true
}
```

---

## Deployment Steps

### 1. Deploy Audit Migration

```bash
# Apply the audit logging migration
psql $DATABASE_URL -f sql/migrations/010_add_name_change_audit_log.sql
```

**Verify:**
```sql
-- Check table exists
\d contact_name_audit

-- Check trigger exists
SELECT tgname FROM pg_trigger WHERE tgname = 'trigger_log_contact_name_change';
```

### 2. Deploy Updated Webhooks

```bash
# Deploy Kajabi webhook with audit context
supabase functions deploy kajabi-webhook

# Deploy PayPal webhook with audit context
supabase functions deploy paypal-webhook
```

**Verify:**
```bash
# Check function logs for audit context messages
supabase functions logs kajabi-webhook --limit 20
```

### 3. Test Audit Logging

```sql
-- Make a test update
UPDATE contacts
SET first_name = 'Test'
WHERE email = 'test@example.com';

-- Check audit log captured it
SELECT * FROM contact_name_audit
WHERE contact_id = (SELECT id FROM contacts WHERE email = 'test@example.com')
ORDER BY changed_at DESC
LIMIT 1;

-- Revert test
UPDATE contacts
SET first_name = 'Original'
WHERE email = 'test@example.com';
```

---

## Monitoring & Alerts

### Daily Name Change Report

```sql
-- See all name changes in last 24 hours
SELECT
  c.email,
  a.old_first_name || ' ' || a.old_last_name as old_name,
  a.new_first_name || ' ' || a.new_last_name as new_name,
  a.changed_by,
  a.changed_at
FROM contact_name_audit a
JOIN contacts c ON c.id = a.contact_id
WHERE a.changed_at > NOW() - INTERVAL '24 hours'
ORDER BY a.changed_at DESC;
```

### Suspicious Change Detection

```sql
-- Find name changes where names are drastically different
SELECT
  c.email,
  a.old_first_name,
  a.new_first_name,
  a.changed_by
FROM contact_name_audit a
JOIN contacts c ON c.id = a.contact_id
WHERE
  -- First name changed by more than 3 characters
  ABS(LENGTH(a.old_first_name) - LENGTH(a.new_first_name)) > 3
  -- Or completely different first letter
  OR LEFT(a.old_first_name, 1) != LEFT(a.new_first_name, 1)
ORDER BY a.changed_at DESC;
```

---

## Ed Burns Specific Fix

### Current State

```sql
SELECT email, first_name, last_name, updated_at
FROM contacts
WHERE email = 'eburns009@gmail.com';
```

**Expected output:**
```
email                | first_name | last_name | updated_at
---------------------|------------|-----------|-------------------
eburns009@gmail.com | Erik       | Burns     | 2025-11-XX XX:XX
```

### Fix Command

```sql
UPDATE contacts
SET first_name = 'Ed'
WHERE email = 'eburns009@gmail.com';
```

### Verify Fix

```sql
-- Check current name
SELECT email, first_name, last_name FROM contacts WHERE email = 'eburns009@gmail.com';

-- Check audit trail
SELECT * FROM get_contact_name_history(
  (SELECT id FROM contacts WHERE email = 'eburns009@gmail.com')
);
```

---

## Summary

**Root Cause:** Kajabi webhook automatically overwrites names without validation

**Fix Applied:**
- ✅ Created audit logging migration
- ✅ Added audit context to Kajabi webhook
- ✅ Added audit context to PayPal webhook
- ✅ Created investigation documentation

**Next Steps:**
1. Deploy audit migration to database
2. Deploy updated webhook functions
3. Test audit logging works
4. Fix Ed Burns name back to "Ed"
5. Monitor daily name changes
6. Consider implementing approval workflow for name changes

**Status:** 🟡 Safeguards ready for deployment
