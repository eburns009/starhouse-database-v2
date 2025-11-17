# Deploy Staff Roles Migration - Quick Guide

**Migration:** `20251117000001_three_tier_staff_roles`
**Status:** Ready to deploy
**Estimated Time:** 2 minutes

---

## Quick Deploy Steps

### Step 1: Open Supabase SQL Editor (30 seconds)

1. Go to [https://supabase.com](https://supabase.com)
2. Select your project: `starhouse-database-v2`
3. Click **SQL Editor** in left sidebar
4. Click **New Query**

### Step 2: Run Migration (30 seconds)

Copy and paste the entire contents of:
```
supabase/migrations/20251117000001_three_tier_staff_roles.sql
```

Click **Run** (or press Cmd/Ctrl + Enter)

**Expected Result:**
```
Success. No rows returned.
```

### Step 3: Verify Migration (30 seconds)

In SQL Editor, run the verification script:
```
tests/test_three_tier_roles.sql
```

Click **Run**

**Expected Results:**
- ✅ Test 1: `display_name` and `last_login_at` columns exist
- ✅ Test 2: Role constraint includes all 4 roles
- ✅ Test 3: No 'staff' roles (all migrated to 'full_user')
- ✅ Test 4: All helper functions exist
- ✅ Test 5-6: RLS policies updated
- ✅ Test 7: Performance indexes created
- ✅ Test 8-10: Functions return correct values

### Step 4: Test Access (30 seconds)

Still in SQL Editor, test the new functions:

```sql
-- Check your role
SELECT get_user_role();
-- Should return: 'admin', 'full_user', or 'read_only'

-- Check if you can edit
SELECT can_edit();
-- Should return: true (if admin or full_user), false (if read_only)

-- Check if you're admin
SELECT is_admin();
-- Should return: true (if admin), false (otherwise)

-- View all staff
SELECT email, role, display_name, active, last_login_at
FROM staff_members
ORDER BY role, email;
```

---

## What This Migration Does

### Schema Changes:
- ✅ Adds `display_name` column (friendly UI names)
- ✅ Adds `last_login_at` column (security audit)
- ✅ Adds `read_only` role to constraint
- ✅ Migrates all 'staff' roles → 'full_user'

### Access Control:
- ✅ **Read-only users**: Can view all data, cannot edit
- ✅ **Full users**: Can view/edit contacts, products, transactions
- ✅ **Admins**: Full access + user management

### Helper Functions:
- ✅ `is_admin()` - Check if current user is admin
- ✅ `can_edit()` - Check if current user can edit data
- ✅ `get_user_role()` - Get current user's role
- ✅ `change_staff_role()` - Change user role (admin only)

---

## Troubleshooting

### Issue: "relation staff_members does not exist"
**Solution:** You need to run migration `20251113000004_secure_staff_access_control.sql` first.

### Issue: "role 'admin' already exists in constraint"
**Solution:** Migration is idempotent. Safe to run again.

### Issue: Functions don't return correct values
**Solution:** Check that `auth.jwt()->>'email'` matches your email in `staff_members` table:
```sql
SELECT * FROM staff_members WHERE email = auth.jwt()->>'email';
```

---

## Rollback (If Needed)

If something goes wrong, run the rollback commands at the bottom of:
```
supabase/migrations/20251117000001_three_tier_staff_roles.sql
```

This will:
- Restore 2-tier role system (admin/staff)
- Revert all 'full_user' → 'staff'
- Remove new functions
- Restore old RLS policies

---

## Next Steps

After migration is verified:

1. ✅ Generate TypeScript types: `npx supabase gen types typescript`
2. ✅ Build staff management UI components
3. ✅ Test all 3 roles in production
4. ✅ Train staff on new access levels

---

## Success Criteria

- [ ] Migration runs without errors
- [ ] All tests pass in verification script
- [ ] No 'staff' roles remain (all migrated to 'full_user')
- [ ] Helper functions return expected values
- [ ] RLS policies enforce correct permissions
- [ ] Can add new staff members with `add_staff_member()`
- [ ] Can change roles with `change_staff_role()`

**Estimated Total Time:** 2 minutes
**Risk Level:** Low (zero-downtime, backward compatible, rollback available)

---

**Questions?** Check the migration file for detailed comments.
