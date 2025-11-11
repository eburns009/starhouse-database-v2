# Future RLS Migration Guide

**Created:** 2025-11-09
**Status:** Reference Only - DO NOT IMPLEMENT NOW
**Review Date:** 2025-05-09 (6 months from now)

---

## When to Migrate to Role-Based RLS

Current simple model (authenticated = full access) will need to change when:

### Triggers for Migration

1. **Staff Growth:** More than 5-7 active staff members
2. **Permission Requirements:** Different staff need different access levels
3. **Audit Requirements:** Need to track who changed what
4. **External Access:** Contractors/partners need limited access
5. **Data Sensitivity:** Need to hide financial details from some staff
6. **Territory Management:** Staff should only see their assigned contacts

### Signs Current Model is Breaking

- Multiple requests for "can you hide X from person Y?"
- Audit questions you can't answer ("who changed this contact?")
- Onboarding new staff feels risky (they see everything)
- Someone accidentally deleted important data (no guardrails)

---

## Migration Path: Simple → Role-Based

### Phase 1: Add User Roles Table

```sql
-- Create roles table
CREATE TABLE user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('admin', 'coordinator', 'volunteer', 'readonly')),
  granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  granted_by UUID REFERENCES auth.users(id),
  notes TEXT,

  -- Prevent duplicate role assignments
  UNIQUE(user_id, role)
);

-- Index for fast role lookups (critical for RLS performance)
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role);

-- RLS on user_roles table itself
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Admins can manage roles
CREATE POLICY "admins_manage_roles" ON user_roles
  FOR ALL TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid()
      AND role = 'admin'
    )
  );

-- Everyone can see their own roles
CREATE POLICY "users_view_own_roles" ON user_roles
  FOR SELECT TO authenticated
  USING (user_id = auth.uid());
```

### Phase 2: Create Helper Function

```sql
-- Helper function to check user role
-- This makes policies more readable and maintainable
CREATE OR REPLACE FUNCTION has_role(required_role TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM user_roles
    WHERE user_id = auth.uid()
    AND role = required_role
  );
$$;

-- Alternative: Check for ANY of multiple roles
CREATE OR REPLACE FUNCTION has_any_role(required_roles TEXT[])
RETURNS BOOLEAN
LANGUAGE SQL
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM user_roles
    WHERE user_id = auth.uid()
    AND role = ANY(required_roles)
  );
$$;
```

### Phase 3: Migrate Contacts Table (Example)

```sql
BEGIN;

-- STEP 1: Drop current simple policies
DROP POLICY IF EXISTS "staff_full_access" ON contacts;
DROP POLICY IF EXISTS "service_role_full_access" ON contacts;

-- STEP 2: Create role-based policies

-- Admins: Full access (same as before)
CREATE POLICY "admins_full_access" ON contacts
  FOR ALL TO authenticated
  USING (has_role('admin'))
  WITH CHECK (has_role('admin'));

-- Coordinators: Can view all, edit most fields (not delete)
CREATE POLICY "coordinators_view_all" ON contacts
  FOR SELECT TO authenticated
  USING (has_role('coordinator'));

CREATE POLICY "coordinators_edit_limited" ON contacts
  FOR UPDATE TO authenticated
  USING (has_role('coordinator'))
  WITH CHECK (has_role('coordinator'));
  -- Note: No DELETE or INSERT for coordinators

-- Volunteers: Read-only access
CREATE POLICY "volunteers_readonly" ON contacts
  FOR SELECT TO authenticated
  USING (has_role('volunteer'));

-- Service role: Still full access for backend
CREATE POLICY "service_role_full_access" ON contacts
  FOR ALL TO service_role
  USING (true)
  WITH CHECK (true);

COMMIT;
```

### Phase 4: Territory-Based Access (Optional)

If you need staff to only see specific contacts:

```sql
-- Add territory field to contacts
ALTER TABLE contacts ADD COLUMN territory TEXT;
CREATE INDEX idx_contacts_territory ON contacts(territory);

-- Add territory assignments to user_roles
ALTER TABLE user_roles ADD COLUMN territories TEXT[];

-- Update policy for territory filtering
CREATE POLICY "coordinators_own_territory" ON contacts
  FOR SELECT TO authenticated
  USING (
    has_role('coordinator')
    AND (
      -- Can see contacts in their territories
      territory = ANY(
        SELECT unnest(territories)
        FROM user_roles
        WHERE user_id = auth.uid()
      )
      OR
      -- Or contacts with no territory assigned
      territory IS NULL
    )
  );
```

---

## Role Definitions

### Recommended Role Hierarchy

| Role | Access Level | Use Case |
|------|--------------|----------|
| **admin** | Full access (read/write/delete all tables) | Executive director, database admin |
| **coordinator** | Read all, edit contacts/notes, no delete | Program coordinators, staff leads |
| **volunteer** | Read-only (filtered by territory if needed) | Event volunteers, part-time staff |
| **readonly** | Read-only basic info (hides sensitive fields) | Contractors, external partners |

### Permission Matrix Example

| Action | admin | coordinator | volunteer | readonly |
|--------|-------|-------------|-----------|----------|
| View contacts | ✅ All | ✅ All | ✅ Territory only | ✅ Basic info |
| Edit contacts | ✅ | ✅ Limited fields | ❌ | ❌ |
| Delete contacts | ✅ | ❌ | ❌ | ❌ |
| View subscriptions | ✅ Full details | ✅ No amounts | ✅ Count only | ❌ |
| Edit subscriptions | ✅ | ❌ | ❌ | ❌ |
| View transactions | ✅ Full | ✅ No amounts | ❌ | ❌ |
| Manage user roles | ✅ | ❌ | ❌ | ❌ |

---

## Migration Checklist

When you're ready to implement role-based RLS:

### Pre-Migration
- [ ] Document current staff members and their needed permissions
- [ ] Create permission matrix (who needs what access)
- [ ] Design role hierarchy (keep it simple - 3-4 roles max)
- [ ] Create test Supabase project
- [ ] Test role-based policies thoroughly

### Migration Day
- [ ] Backup database (pg_dump)
- [ ] Create user_roles table
- [ ] Assign roles to all current staff (everyone = 'admin' initially)
- [ ] Update policies table by table
- [ ] Test each role with real user accounts
- [ ] Verify service_role still works for backend
- [ ] Test import scripts still work
- [ ] Monitor for policy violations in logs

### Post-Migration
- [ ] Document new role assignment process
- [ ] Update staff onboarding guide
- [ ] Train staff on new permission model
- [ ] Set up audit logging (track role changes)
- [ ] Schedule review in 3 months

---

## Common Pitfalls to Avoid

### 1. Over-Engineering Roles

**Bad:** admin, super_admin, coordinator, senior_coordinator, junior_coordinator, volunteer_lead, volunteer, readonly, limited_readonly

**Good:** admin, staff, volunteer

Start simple. You can always add roles later.

### 2. Forgetting service_role

**Problem:** Backend scripts break because you removed service_role policies

**Fix:** ALWAYS keep service_role policies with full access:
```sql
CREATE POLICY "service_role_full_access" ON tablename
  FOR ALL TO service_role USING (true) WITH CHECK (true);
```

### 3. Performance Issues

**Problem:** Policy checks `SELECT * FROM user_roles` on every query

**Fix:**
- Index user_roles.user_id (done in Phase 1)
- Use helper functions (done in Phase 2)
- Monitor query performance
- Consider caching role in JWT claims if needed

### 4. Locking Yourself Out

**Problem:** Changed admin policy, now nobody (including you) can access data

**Fix:**
- Always test policies with REAL user accounts first
- Keep postgres superuser access (bypasses RLS)
- Have rollback script ready
- Start with one table, verify, then migrate others

---

## Rollback Plan

If role-based RLS causes problems:

```sql
BEGIN;

-- Drop all role-based policies
DROP POLICY IF EXISTS "admins_full_access" ON contacts;
DROP POLICY IF EXISTS "coordinators_view_all" ON contacts;
DROP POLICY IF EXISTS "coordinators_edit_limited" ON contacts;
DROP POLICY IF EXISTS "volunteers_readonly" ON contacts;
-- ... repeat for all tables

-- Restore simple staff_full_access policies
CREATE POLICY "staff_full_access" ON contacts
  FOR ALL TO authenticated
  USING (true) WITH CHECK (true);
-- ... repeat for all tables

-- Keep service_role policies (don't touch these)

COMMIT;
```

---

## Testing Role-Based Policies

### Test Script Template

```sql
-- Test as admin
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "admin-user-uuid", "role": "authenticated"}';

-- Should work (admin has full access)
SELECT COUNT(*) FROM contacts;
INSERT INTO contacts (first_name, last_name, email, source)
VALUES ('Test', 'Admin', 'test-admin@example.com', 'test');
DELETE FROM contacts WHERE email = 'test-admin@example.com';

RESET ROLE;

-- Test as coordinator
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "coordinator-user-uuid", "role": "authenticated"}';

-- Should work (coordinator can view)
SELECT COUNT(*) FROM contacts;

-- Should work (coordinator can edit)
UPDATE contacts SET notes = 'test' WHERE id = 'some-contact-id';

-- Should FAIL (coordinator cannot delete)
DELETE FROM contacts WHERE email = 'some-email@example.com';

RESET ROLE;

-- Test as volunteer
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "volunteer-user-uuid", "role": "authenticated"}';

-- Should work (volunteer can view)
SELECT COUNT(*) FROM contacts;

-- Should FAIL (volunteer cannot edit)
UPDATE contacts SET notes = 'test' WHERE id = 'some-contact-id';

RESET ROLE;
```

---

## Audit Logging (Bonus)

If you need to track who changed what:

```sql
-- Create audit log table
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  old_values JSONB,
  new_values JSONB,
  changed_by UUID REFERENCES auth.users(id),
  changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log (table_name, record_id, action, new_values, changed_by)
    VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), auth.uid());
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_by)
    VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), auth.uid());
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log (table_name, record_id, action, old_values, changed_by)
    VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), auth.uid());
    RETURN OLD;
  END IF;
END;
$$;

-- Add audit trigger to contacts table
CREATE TRIGGER audit_contacts
  AFTER INSERT OR UPDATE OR DELETE ON contacts
  FOR EACH ROW EXECUTE FUNCTION audit_trigger();
```

---

## Summary

**Current State (2025-11-09):**
- Simple model: authenticated = full access
- Works for 3-5 trusted staff
- Easy to understand and maintain

**Future State (when needed):**
- Role-based model: admin/coordinator/volunteer
- Granular permissions per table
- Territory filtering if needed
- Audit logging for compliance

**DO NOT migrate until:**
- You have more than 5-7 staff, OR
- Someone asks for different permission levels, OR
- You need audit trails for compliance

**When you do migrate:**
1. Follow this guide step-by-step
2. Test thoroughly in staging first
3. Start with one table and verify
4. Keep it simple (3-4 roles max)
5. Have rollback plan ready

---

**Review this document in May 2025** and decide if migration is needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
