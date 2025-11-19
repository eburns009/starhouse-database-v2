# Migration Deployment Checklist
**Migration:** 20251119000001_add_staff_auth_metadata.sql
**Date:** 2025-11-19
**Status:** Ready for Production Deployment

---

## Pre-Deployment Checklist ✅

### Code Quality
- [x] Migration file created and reviewed
- [x] Updated trigger function (ID matching, no RAISE NOTICE)
- [x] Backfill uses ID matching (not email)
- [x] Performance index added (idx_staff_users_last_sign_in)
- [x] updated_at column added
- [x] Idempotent (safe to run multiple times)
- [x] Includes rollback procedure

### Testing Scripts Created
- [x] Verification script: `scripts/verify-staff-auth-migration.sql`
- [x] Trigger test script: `scripts/test-staff-auth-trigger.sql`

### Build Verification
- [x] Next.js build passes: `npm run build` ✅
- [x] No TypeScript errors
- [x] No ESLint errors

---

## Deployment Steps

### Step 1: Commit Migration
```bash
git add supabase/migrations/20251119000001_add_staff_auth_metadata.sql
git add scripts/verify-staff-auth-migration.sql
git add scripts/test-staff-auth-trigger.sql
git add docs/MIGRATION_20251119000001_CHECKLIST.md
git commit -m "feat(db): Add staff auth metadata sync with auto-update triggers

- Add last_sign_in_at, email_confirmed_at, updated_at columns to staff_users
- Create trigger to auto-sync from auth.users on sign-in/email confirmation
- Backfill existing staff users with current auth data
- Add performance index for last_sign_in_at sorting
- Use ID matching (not email) for reliability

Benefits:
- UI can display login status without admin API calls
- Denormalized for performance (no auth.users queries)
- Auto-syncs on every sign-in event
- Optimized for 'Recent Activity' sorting

FAANG Standards: Idempotent, performant, secure, well-documented

🤖 Generated with Claude Code"
git push origin main
```

### Step 2: Wait for Vercel Deployment
- [ ] Check Vercel dashboard: https://vercel.com/eburns009/starhouse-database-v2
- [ ] Verify deployment completes successfully
- [ ] Status: PENDING

### Step 3: Apply Migration to Production Database

**Important:** This step requires Supabase CLI authentication

```bash
# Option 1: Using Supabase CLI (recommended)
npx supabase db push --linked

# Option 2: Manual execution via Supabase Dashboard
# Go to: https://supabase.com/dashboard/project/lnagadkqejnopgfxwlkb/sql
# Copy/paste migration file contents and execute
```

### Step 4: Verify Production Deployment

Run verification queries from `scripts/verify-staff-auth-migration.sql`:

**a) Check columns exist:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'staff_users'
AND column_name IN ('last_sign_in_at', 'email_confirmed_at', 'updated_at');
```
Expected: 3 rows

**b) Check trigger exists:**
```sql
SELECT trigger_name
FROM information_schema.triggers
WHERE event_object_table = 'users'
AND trigger_name = 'sync_staff_auth_metadata_trigger';
```
Expected: 1 row

**c) Check index exists:**
```sql
SELECT indexname FROM pg_indexes
WHERE tablename = 'staff_users'
AND indexname = 'idx_staff_users_last_sign_in';
```
Expected: 1 row

**d) Verify backfill:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(last_sign_in_at) as with_sign_in_data,
    COUNT(email_confirmed_at) as with_email_confirmed,
    COUNT(updated_at) as with_updated_at
FROM staff_users;
```
Expected: All staff users have updated_at, some have sign-in data

---

## Post-Deployment Verification

### Step 5: Test Trigger Functionality

1. **Sign in as a test staff user** via the UI
2. **Wait 5 seconds** for trigger to fire
3. **Run verification query:**

```sql
SELECT
    id, email, last_sign_in_at, updated_at,
    EXTRACT(EPOCH FROM (NOW() - updated_at)) as seconds_since_update
FROM staff_users
WHERE email = 'YOUR_TEST_EMAIL';
```

**Expected Results:**
- `last_sign_in_at` should be recent (within last minute)
- `updated_at` should match or be very close to `last_sign_in_at`
- `seconds_since_update` should be less than 60

### Step 6: Verify Auth Sync

Run comparison query from `scripts/test-staff-auth-trigger.sql`:

```sql
SELECT
    au.id,
    au.email,
    au.last_sign_in_at as auth_last_sign_in,
    su.last_sign_in_at as staff_last_sign_in,
    CASE
        WHEN au.last_sign_in_at = su.last_sign_in_at THEN '✅ MATCH'
        ELSE '❌ MISMATCH'
    END as sync_status
FROM auth.users au
JOIN staff_users su ON au.id = su.id
WHERE au.email = 'YOUR_TEST_EMAIL';
```

**Expected:** sync_status = '✅ MATCH'

---

## Rollback Procedure (If Needed)

### When to Rollback
- Trigger not firing
- Data not syncing correctly
- Performance issues
- Any critical errors

### Rollback Steps

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

### After Rollback
- [ ] Verify columns removed
- [ ] Verify trigger removed
- [ ] Verify index removed
- [ ] Document reason for rollback
- [ ] Fix issues before re-applying

---

## Final Review Checklist

Before marking deployment as complete:

1. ✅ Migration adds 3 columns: last_sign_in_at, email_confirmed_at, updated_at
2. ✅ Trigger uses ID matching (not email matching)
3. ✅ No RAISE NOTICE in trigger function (only in one-time operations)
4. ✅ Index created for performance: idx_staff_users_last_sign_in
5. [ ] Backfill completed successfully (show row count)
6. [ ] Trigger tested and working (show test results)
7. [ ] Local build passes: npm run build
8. [ ] No TypeScript errors

**GO/NO-GO Decision:**

- ✅ **GO** - All pre-deployment checks passed
- ❌ **NO-GO** - Issues found (document below)

**Issues (if any):**
- None at this time

---

## Next Steps After Deployment

1. **Update UI Components** to display new columns:
   - Show `last_sign_in_at` in staff admin table
   - Show `email_confirmed_at` verification status
   - Use `updated_at` for "Last Modified" column

2. **Remove Admin API Calls**:
   - Replace `auth.admin.getUserById()` calls
   - Use `staff_users` table directly (faster, no admin privileges needed)

3. **Monitor Performance**:
   - Watch for trigger execution time
   - Verify index improves query performance
   - Check for any sync delays

4. **Create Deployment Report**:
   - Document what was deployed
   - Include test results
   - Record any issues encountered

---

**Deployment Status:** ⏳ Ready for Production
**Last Updated:** 2025-11-19
**Next Action:** Commit and push migration to main branch
