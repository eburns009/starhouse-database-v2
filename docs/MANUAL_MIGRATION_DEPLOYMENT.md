# Manual Migration Deployment Guide
**Migration:** 20251119000001_add_staff_auth_metadata
**Date:** 2025-11-19
**Status:** Ready for Manual Deployment

---

## Why Manual Deployment?

The development environment doesn't have direct network access to the production database. This is a security feature. Therefore, we'll deploy the migration manually via the Supabase Dashboard.

---

## Step-by-Step Deployment

### STEP 1: Open Supabase SQL Editor

1. Go to: https://supabase.com/dashboard/project/lnagadkqejnopgfxwlkb/sql
2. Click "New Query"

---

### STEP 2: Copy Migration SQL

Open the migration file and copy its entire contents:

**File:** `/workspaces/starhouse-database-v2/supabase/migrations/20251119000001_add_staff_auth_metadata.sql`

Or use this command to view it:
```bash
cat supabase/migrations/20251119000001_add_staff_auth_metadata.sql
```

---

### STEP 3: Paste and Execute

1. Paste the entire migration SQL into the Supabase SQL Editor
2. Click **"Run"** button
3. Wait for execution to complete (~10-30 seconds)

**Expected Output:**
```
NOTICE: Backfill complete: X of Y staff users have auth metadata
NOTICE: ✅ Migration 20251119000001_add_staff_auth_metadata completed successfully
NOTICE:    - Added last_sign_in_at column to staff_users
NOTICE:    - Added email_confirmed_at column to staff_users
NOTICE:    - Added updated_at column to staff_users
NOTICE:    - Created sync_staff_auth_metadata() trigger function
NOTICE:    - Created trigger on auth.users table
NOTICE:    - Backfilled existing staff users with auth data
NOTICE:    - Created performance index: idx_staff_users_last_sign_in
```

---

### STEP 4: Verify Migration

Run these verification queries in the SQL Editor:

#### a) Verify Columns Were Added
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'staff_users'
AND column_name IN ('last_sign_in_at', 'email_confirmed_at', 'updated_at');
```

**Expected:** 3 rows returned

#### b) Verify Trigger Was Created
```sql
SELECT trigger_name, event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'auth'
  AND event_object_table = 'users'
  AND trigger_name = 'sync_staff_auth_metadata_trigger';
```

**Expected:** 1 row returned

#### c) Verify Index Was Created
```sql
SELECT indexname FROM pg_indexes
WHERE tablename = 'staff_users'
AND indexname = 'idx_staff_users_last_sign_in';
```

**Expected:** 1 row returned

#### d) Verify Backfill Worked
```sql
SELECT
    COUNT(*) as total,
    COUNT(last_sign_in_at) as with_sign_in_data,
    COUNT(email_confirmed_at) as with_email_confirmed,
    COUNT(updated_at) as with_updated_at
FROM staff_users;
```

**Expected:** All staff users should have `updated_at`, some may have `last_sign_in_at`

---

### STEP 5: Test Trigger Functionality

#### Before Sign-In: Capture Current State

Run this query and save the results:

```sql
SELECT
    id,
    email,
    last_sign_in_at,
    email_confirmed_at,
    updated_at,
    created_at
FROM staff_users
ORDER BY email;
```

**Save these results** - we'll compare after sign-in.

---

#### Perform Sign-In Test

1. Go to: https://starhouse-database-v2.vercel.app/login
2. Sign in with your staff account
3. **Wait 10 seconds** (give trigger time to fire)

---

#### After Sign-In: Check If Trigger Fired

Run the same query again:

```sql
SELECT
    id,
    email,
    last_sign_in_at,
    email_confirmed_at,
    updated_at,
    created_at
FROM staff_users
ORDER BY email;
```

**Compare with "Before" results:**
- Your `last_sign_in_at` should be updated to NOW (within last minute)
- Your `updated_at` should match `last_sign_in_at` (or very close)

---

#### Cross-Check with auth.users

Verify the data synced correctly:

```sql
SELECT
    au.email,
    au.last_sign_in_at as auth_last_sign_in,
    su.last_sign_in_at as staff_last_sign_in,
    au.email_confirmed_at as auth_confirmed,
    su.email_confirmed_at as staff_confirmed,
    CASE
        WHEN au.last_sign_in_at IS NOT DISTINCT FROM su.last_sign_in_at
         AND au.email_confirmed_at IS NOT DISTINCT FROM su.email_confirmed_at
        THEN '✅ SYNCED'
        ELSE '❌ OUT OF SYNC'
    END as sync_status
FROM auth.users au
JOIN staff_users su ON au.id = su.id
WHERE au.email = 'YOUR_EMAIL_HERE'  -- Replace with your email
LIMIT 1;
```

**Expected:** `sync_status` = '✅ SYNCED'

---

## Troubleshooting

### If Trigger Didn't Fire

1. **Check if trigger exists:**
   ```sql
   SELECT * FROM information_schema.triggers
   WHERE trigger_name = 'sync_staff_auth_metadata_trigger';
   ```

2. **Check if function exists:**
   ```sql
   SELECT routine_name FROM information_schema.routines
   WHERE routine_name = 'sync_staff_auth_metadata';
   ```

3. **Manually test the function:**
   ```sql
   -- This should update your staff record
   UPDATE auth.users
   SET last_sign_in_at = NOW()
   WHERE email = 'YOUR_EMAIL_HERE';

   -- Then check if staff_users was updated
   SELECT last_sign_in_at, updated_at
   FROM staff_users
   WHERE email = 'YOUR_EMAIL_HERE';
   ```

### If Data Is Out of Sync

1. **Manual sync (one-time fix):**
   ```sql
   UPDATE staff_users su
   SET
       last_sign_in_at = au.last_sign_in_at,
       email_confirmed_at = au.email_confirmed_at,
       updated_at = NOW()
   FROM auth.users au
   WHERE su.id = au.id;
   ```

2. **Verify sync:**
   ```sql
   SELECT COUNT(*) FROM staff_users su
   JOIN auth.users au ON su.id = au.id
   WHERE su.last_sign_in_at IS DISTINCT FROM au.last_sign_in_at;
   ```
   **Expected:** 0 (all synced)

---

## Rollback Procedure (If Needed)

If you need to rollback the migration:

```sql
-- Drop trigger
DROP TRIGGER IF EXISTS sync_staff_auth_metadata_trigger ON auth.users;

-- Drop function
DROP FUNCTION IF EXISTS sync_staff_auth_metadata() CASCADE;

-- Drop index
DROP INDEX IF EXISTS public.idx_staff_users_last_sign_in;

-- Remove columns
ALTER TABLE public.staff_users DROP COLUMN IF EXISTS last_sign_in_at;
ALTER TABLE public.staff_users DROP COLUMN IF EXISTS email_confirmed_at;
ALTER TABLE public.staff_users DROP COLUMN IF EXISTS updated_at;
```

---

## Success Criteria

✅ **Migration Successful If:**
1. All 3 columns added to `staff_users` table
2. Trigger `sync_staff_auth_metadata_trigger` exists on `auth.users`
3. Function `sync_staff_auth_metadata()` exists
4. Index `idx_staff_users_last_sign_in` exists
5. Backfill completed (all staff have `updated_at`)
6. Trigger test passed (your sign-in updated `last_sign_in_at`)
7. Sync verification passed (auth.users matches staff_users)

---

## Next Steps After Successful Migration

1. **Update UI Components** to display:
   - `last_sign_in_at` - "Last seen: 2 hours ago"
   - `email_confirmed_at` - "Email verified ✓"
   - Sort by recent activity

2. **Remove Admin API Calls:**
   - Replace `auth.admin.getUserById()` calls
   - Use `staff_users` table directly (faster, no admin privileges)

3. **Monitor Performance:**
   - Watch query times with new index
   - Verify trigger doesn't slow down sign-ins
   - Check for any sync delays

---

## Contact & Support

**Migration File:** `supabase/migrations/20251119000001_add_staff_auth_metadata.sql`
**Verification Scripts:** `scripts/verify-staff-auth-migration.sql`
**Trigger Tests:** `scripts/test-staff-auth-trigger.sql`
**This Guide:** `docs/MANUAL_MIGRATION_DEPLOYMENT.md`

**Deployment Checklist:** `docs/MIGRATION_20251119000001_CHECKLIST.md`

---

**Last Updated:** 2025-11-19
**Status:** ⏳ Ready for Manual Deployment via Supabase Dashboard
