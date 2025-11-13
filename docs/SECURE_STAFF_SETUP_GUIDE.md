# Secure Staff Access Control - Setup Guide

**Date**: 2025-11-13
**Security Model**: Explicit Allowlist + Role-Based Access
**Status**: Ready for review - DO NOT DEPLOY without completing setup

---

## 🎯 What This Implements

### Security Model
- **Allowlist-based**: Only emails in `staff_members` table can access contacts
- **Role-based**: Admin vs Staff permissions
- **Audit trail**: Tracks who created/modified contacts
- **Defense in depth**: Verifies users even with invite-only auth

### Permissions

| Action | Staff | Admin |
|--------|-------|-------|
| View contacts | ✅ | ✅ |
| Create contacts | ✅ | ✅ |
| Update contacts | ✅ | ✅ |
| Delete contacts | ❌ | ✅ |
| View staff list | ✅ | ✅ |
| Add staff member | ❌ | ✅ |
| Promote to admin | ❌ | ✅ |
| Deactivate staff | ❌ | ✅ |

---

## ⚠️ CRITICAL: Before Running Migration

### Step 1: Update Your Email in Migration

**MUST DO**: Edit migration file before running!

File: `supabase/migrations/20251113000004_secure_staff_access_control.sql`

Find line ~50:
```sql
INSERT INTO staff_members (email, role, added_by, notes)
VALUES (
    'your.email@thestarhouse.org',  -- ⚠️ CHANGE THIS!
    'admin',
    'system',
    'Initial admin - created during migration'
)
```

**Replace** `'your.email@thestarhouse.org'` with **your actual email**.

**Critical**: This must be the EXACT email you use to log into Supabase. Otherwise, you'll lock yourself out!

To verify your email:
1. Go to Supabase Dashboard
2. Authentication → Users
3. Find your account
4. Copy the email exactly as shown

---

## 🚀 Running the Migration

### Method 1: Via Supabase Dashboard (Recommended)

1. Go to Supabase Dashboard
2. SQL Editor → New Query
3. Copy entire content of `20251113000004_secure_staff_access_control.sql`
4. **Verify your email is correct** (line ~50)
5. Run query
6. Check for errors

### Method 2: Via Script

**IMPORTANT**: First verify your email in the migration file!

```bash
# Make sure DATABASE_URL is set
echo $DATABASE_URL

# Run the secure migration
psql "$DATABASE_URL" -f supabase/migrations/20251113000004_secure_staff_access_control.sql
```

---

## ✅ Post-Migration Verification

### Test 1: Verify You're Admin

```sql
-- Should return YOUR email with role='admin'
SELECT * FROM staff_members WHERE role = 'admin';
```

Expected output:
```
email                          | role  | added_at            | added_by
-------------------------------|-------|---------------------|----------
your.email@thestarhouse.org   | admin | 2025-11-13 ...      | system
```

If this is **empty** or shows wrong email → **You locked yourself out!**
See "Recovery" section below.

---

### Test 2: Verify RLS Policies

```sql
-- Should show 4 new policies
SELECT policyname, cmd
FROM pg_policies
WHERE tablename = 'contacts'
ORDER BY policyname;
```

Expected output:
```
policyname                        | cmd
----------------------------------|--------
verified_staff_select_contacts    | SELECT
verified_staff_update_contacts    | UPDATE
verified_staff_insert_contacts    | INSERT
admin_delete_contacts             | DELETE
```

---

### Test 3: Verify Staff Verification Function

Log into your UI with your admin email, then in SQL Editor:

```sql
-- Should return true (you're in staff_members)
SELECT is_verified_staff();
```

Expected: `true`

If `false` → Your email doesn't match staff_members table.

---

### Test 4: Test Contacts Access

```sql
-- Should work (return count of contacts)
SELECT COUNT(*) FROM contacts;

-- Should work (return tags)
SELECT tags FROM contacts WHERE tags IS NOT NULL LIMIT 3;
```

If these **fail with permission denied** → RLS is blocking you. Check staff_members table.

---

## 👥 Adding Staff Members

### Option 1: Via SQL (As Admin)

```sql
-- Add regular staff member
SELECT add_staff_member(
    'newstaff@gmail.com',      -- Email (any domain)
    'staff',                    -- Role (staff or admin)
    'Marketing team member'     -- Notes
);

-- Add another admin
SELECT add_staff_member(
    'trusted@thestarhouse.org',
    'admin',
    'Co-founder - can manage staff'
);
```

### Option 2: Direct INSERT (As Admin)

```sql
INSERT INTO staff_members (email, role, added_by, notes)
VALUES
    ('contractor@freelance.com', 'staff', 'you@thestarhouse.org', 'Temp contractor - expires 2026-01'),
    ('partner@example.com', 'staff', 'you@thestarhouse.org', 'Partner organization');
```

### Option 3: Via UI (Future)

You can build a UI panel later that calls `add_staff_member()` function.

---

## 🔐 Admin Operations

### Promote Staff to Admin

```sql
-- Allow another admin to manage staff
SELECT promote_to_admin('trusted@thestarhouse.org');
```

**Result**: That person can now add/remove staff members.

---

### Deactivate Staff Member (Soft Delete)

```sql
-- Immediate access revocation
SELECT deactivate_staff_member('exstaff@example.com');
```

**What happens:**
- `active` set to `false`
- `deactivated_at` set to NOW()
- `deactivated_by` set to your email
- User **immediately** loses access (even if still logged in)
- Audit trail preserved

**To reactivate:**
```sql
UPDATE staff_members
SET active = true,
    deactivated_at = NULL,
    deactivated_by = NULL
WHERE email = 'returning@example.com';
```

---

### View All Staff

```sql
-- See all active staff
SELECT email, role, added_at, added_by
FROM staff_members
WHERE active = true
ORDER BY role DESC, added_at;

-- See deactivated staff (audit trail)
SELECT email, role, deactivated_at, deactivated_by
FROM staff_members
WHERE active = false
ORDER BY deactivated_at DESC;
```

---

## 🔍 Audit Trail

### See Who Modified Contacts

```sql
-- Recent contact modifications
SELECT
    id,
    CONCAT(first_name, ' ', last_name) AS contact_name,
    created_by,
    updated_by,
    updated_at
FROM contacts
ORDER BY updated_at DESC
LIMIT 10;

-- Find all contacts modified by specific staff
SELECT COUNT(*)
FROM contacts
WHERE updated_by = 'staff@example.com';
```

### See Who Added Staff Members

```sql
-- Staff addition history
SELECT
    email AS new_staff,
    role,
    added_by,
    added_at,
    notes
FROM staff_members
ORDER BY added_at DESC;
```

---

## 🚨 Recovery Procedures

### Scenario 1: Locked Yourself Out (Wrong Email)

If you can't access contacts because your email isn't in `staff_members`:

```sql
-- As service_role (has full access), add yourself:
INSERT INTO staff_members (email, role, added_by, notes)
VALUES
    ('your.actual.email@example.com', 'admin', 'recovery', 'Fixed lockout')
ON CONFLICT (email) DO UPDATE
SET role = 'admin', active = true;
```

Run this in Supabase Dashboard SQL Editor (uses service_role automatically).

---

### Scenario 2: No Admins Left

If all admins were deactivated:

```sql
-- Promote someone to admin
UPDATE staff_members
SET role = 'admin',
    active = true
WHERE email = 'trusted@thestarhouse.org';
```

---

### Scenario 3: Need to Bypass RLS (Emergency)

If RLS is completely broken:

```sql
-- Temporarily disable RLS (DANGER!)
ALTER TABLE contacts DISABLE ROW LEVEL SECURITY;

-- Do emergency fix...

-- Re-enable RLS (CRITICAL!)
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
```

**⚠️ Only use in absolute emergency!**

---

## 🧪 Security Testing Checklist

Before going to production, verify:

- [ ] ✅ Your admin email is in staff_members table
- [ ] ✅ `is_verified_staff()` returns true when logged in
- [ ] ✅ You can view contacts in UI
- [ ] ✅ You can add/remove tags
- [ ] ✅ Non-staff emails CANNOT access contacts
- [ ] ✅ Regular staff CANNOT add other staff
- [ ] ✅ Admins CAN add other staff
- [ ] ✅ Deactivated staff lose access immediately
- [ ] ✅ Audit trail shows who modified contacts

### Test Non-Staff Access

1. Create test user: `test@notstaff.com`
2. Do NOT add to staff_members
3. Log in as that user
4. Try to view contacts → Should fail with permission denied
5. Verify RLS is working

---

## 📊 Monitoring Queries

### Daily Audit Report

```sql
-- Today's contact modifications
SELECT
    updated_by AS staff_email,
    COUNT(*) AS modifications,
    COUNT(DISTINCT id) AS unique_contacts
FROM contacts
WHERE updated_at::date = CURRENT_DATE
GROUP BY updated_by
ORDER BY modifications DESC;
```

### Active Staff Report

```sql
-- Current staff list
SELECT
    role,
    COUNT(*) AS count,
    string_agg(email, ', ' ORDER BY email) AS emails
FROM staff_members
WHERE active = true
GROUP BY role
ORDER BY role DESC;
```

### Access Anomalies

```sql
-- Find auth.users NOT in staff_members (potential security issue)
SELECT
    u.email,
    u.created_at
FROM auth.users u
LEFT JOIN staff_members sm ON u.email = sm.email
WHERE sm.email IS NULL
ORDER BY u.created_at DESC;
```

If this returns results → Those users authenticated but aren't staff. Investigate!

---

## 🔄 Migration Rollback (If Needed)

If something goes wrong:

```sql
-- Drop new policies
DROP POLICY IF EXISTS "verified_staff_select_contacts" ON contacts;
DROP POLICY IF EXISTS "verified_staff_update_contacts" ON contacts;
DROP POLICY IF EXISTS "verified_staff_insert_contacts" ON contacts;
DROP POLICY IF EXISTS "admin_delete_contacts" ON contacts;

-- Drop staff policies
DROP POLICY IF EXISTS "staff_view_staff_list" ON staff_members;
DROP POLICY IF EXISTS "admin_add_staff" ON staff_members;
DROP POLICY IF EXISTS "admin_update_staff" ON staff_members;
DROP POLICY IF EXISTS "admin_delete_staff" ON staff_members;

-- Optionally drop staff_members table
DROP TABLE IF EXISTS staff_members CASCADE;

-- Restore old insecure policies (temporary, until fixed)
CREATE POLICY "temp_service_role_only" ON contacts
    FOR ALL TO service_role USING (true);
```

---

## 📝 Next Steps After Migration

1. ✅ Verify you can log in and access contacts
2. ✅ Add other staff members via `add_staff_member()`
3. ✅ Test tag functionality works
4. ✅ Promote at least one other person to admin (backup)
5. ✅ Document staff list somewhere safe
6. ✅ Set up monitoring for new auth.users entries

---

## 🎯 Summary

**What changed:**
- ❌ Removed `USING (true)` policies (zero security)
- ✅ Added `staff_members` allowlist table
- ✅ Added `is_verified_staff()` verification function
- ✅ Added RLS policies checking allowlist
- ✅ Added admin role system
- ✅ Added audit trail to contacts
- ✅ Added staff management functions

**Security posture:**
- Before: Anyone authenticated = full access
- After: Only verified staff in allowlist = access

**Future-proof:**
- Role system ready for admin/staff differentiation
- Audit trail for compliance
- Soft deletes for data retention

---

**Questions?** Review sections above or check SQL comments in migration file.
**Ready to deploy?** Complete checklist above first.
