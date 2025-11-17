# Architecture Analysis: Multi-Tenant Staff-Only CRM

**Date**: 2025-11-13
**Context**: Reviewing security model for tag operations

---

## 🔍 Current Database Architecture

### Contacts Table Schema
```sql
CREATE TABLE contacts (
    id uuid PRIMARY KEY,
    email citext NOT NULL,
    first_name text,
    last_name text,
    -- ... other fields ...
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
```

**Key Findings:**
- ❌ **No `created_by` column** - Contacts don't track who created them
- ❌ **No `owner_id` column** - No concept of ownership
- ✅ **Has RLS enabled** - Security is configured
- ✅ **Source tracking exists** - (kajabi_id, zoho_id, etc.)

### Current RLS Policies

**Policy 1: Service Role (Backend)**
```sql
CREATE POLICY "Service role has full access" ON contacts
    FOR ALL TO service_role USING (true);
```
✅ Webhooks and backend operations work

**Policy 2: Authenticated Users (Frontend)**
```sql
CREATE POLICY "Users can view their own contact" ON contacts
    FOR SELECT TO authenticated
    USING (auth.jwt()->>'email' = email);
```

**What this means:**
- Users can only SELECT contacts where `contact.email = their_login_email`
- **No UPDATE policy** - Users can't modify ANY contacts via UI
- **No INSERT policy** - Users can't create contacts via UI
- **No DELETE policy** - Users can't delete contacts

---

## 🚨 THE CRITICAL GAP

### Your Tag RPC Function Will Fail

```sql
-- Your function:
CREATE FUNCTION add_contact_tag(p_contact_id UUID, p_new_tag TEXT)
  RETURNS JSONB SECURITY DEFINER AS $$
BEGIN
  -- This UPDATE will FAIL for authenticated users:
  UPDATE contacts
  SET tags = array_append(tags, p_new_tag)
  WHERE id = p_contact_id;  -- ❌ No RLS policy allows this!
END;
$$;
```

**Why it fails:**
1. Function runs as `SECURITY DEFINER` (bypasses RLS)
2. But the UPDATE statement checks RLS policies
3. There's no RLS policy allowing `UPDATE` for `authenticated` role
4. **Result**: Permission denied error

---

## 🎯 Required Security Model for "Multi-Tenant Staff-Only"

You have **3 options**. Choose based on your business requirements:

### Option 1: All Staff Can Edit All Contacts (Recommended for Small Team)

**Use Case:**
- You have 5-20 staff members
- Everyone is trusted
- It's a shared CRM (like Salesforce for a small company)
- Any staff member should be able to tag/edit any contact

**Implementation:**
```sql
-- Add UPDATE policy for all authenticated staff
CREATE POLICY "Staff can update all contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (true)  -- All staff can update any contact
    WITH CHECK (true);

-- Add INSERT policy (if staff create contacts)
CREATE POLICY "Staff can create contacts"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Update SELECT policy to show all contacts
DROP POLICY "Users can view their own contact" ON contacts;

CREATE POLICY "Staff can view all contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (true);  -- See all contacts
```

**Tag Function (No Auth Check Needed):**
```sql
CREATE FUNCTION add_contact_tag(p_contact_id UUID, p_new_tag TEXT)
  RETURNS JSONB AS $$  -- Remove SECURITY DEFINER
DECLARE
  v_tag TEXT;
BEGIN
  v_tag := LOWER(TRIM(p_new_tag));

  -- Validate
  IF v_tag = '' THEN RAISE EXCEPTION 'Tag cannot be empty'; END IF;
  IF LENGTH(v_tag) > 50 THEN RAISE EXCEPTION 'Tag too long'; END IF;

  -- Update (RLS automatically enforces staff permission)
  UPDATE contacts
  SET tags = CASE
    WHEN tags IS NULL THEN ARRAY[v_tag]
    WHEN v_tag = ANY(tags) THEN tags
    ELSE array_append(tags, v_tag)
  END
  WHERE id = p_contact_id;

  -- Return updated tags
  RETURN jsonb_build_object(
    'success', true,
    'tags', (SELECT tags FROM contacts WHERE id = p_contact_id)
  );
END;
$$ LANGUAGE plpgsql;  -- No SECURITY DEFINER needed!
```

**Pros:**
- ✅ Simple
- ✅ No ownership tracking needed
- ✅ Fast (no auth queries)
- ✅ Natural for small CRM teams

**Cons:**
- ❌ No audit trail of who changed what
- ❌ Can't track "my contacts" vs "team contacts"

---

### Option 2: Staff Own Contacts (Sales Team Model)

**Use Case:**
- You have sales reps or account managers
- Each contact has an "owner"
- Staff should only edit their own contacts
- Need to track who's responsible for each contact

**Implementation:**
```sql
-- 1. Add ownership column
ALTER TABLE contacts
  ADD COLUMN owner_id UUID REFERENCES auth.users(id);

-- 2. Backfill existing contacts (assign to first staff member or null)
UPDATE contacts SET owner_id = (
  SELECT id FROM auth.users LIMIT 1
) WHERE owner_id IS NULL;

-- 3. Create RLS policies
CREATE POLICY "Staff can view all contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (true);  -- Can see all, but...

CREATE POLICY "Staff can only update their own contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (owner_id = auth.uid())  -- Can only edit owned contacts
    WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Staff can create contacts (owned by them)"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (owner_id = auth.uid());
```

**Tag Function (With Ownership Check):**
```sql
CREATE FUNCTION add_contact_tag(p_contact_id UUID, p_new_tag TEXT)
  RETURNS JSONB AS $$
DECLARE
  v_tag TEXT;
BEGIN
  v_tag := LOWER(TRIM(p_new_tag));

  -- Validate
  IF v_tag = '' THEN RAISE EXCEPTION 'Tag cannot be empty'; END IF;

  -- Check ownership (explicit check for clarity)
  IF NOT EXISTS (
    SELECT 1 FROM contacts
    WHERE id = p_contact_id
    AND owner_id = auth.uid()
  ) THEN
    RAISE EXCEPTION 'You do not own this contact';
  END IF;

  -- Update
  UPDATE contacts
  SET tags = CASE
    WHEN tags IS NULL THEN ARRAY[v_tag]
    WHEN v_tag = ANY(tags) THEN tags
    ELSE array_append(tags, v_tag)
  END
  WHERE id = p_contact_id;

  RETURN jsonb_build_object('success', true, 'tags', ...);
END;
$$ LANGUAGE plpgsql;
```

**Pros:**
- ✅ Clear ownership
- ✅ Audit trail
- ✅ Isolation between staff members

**Cons:**
- ❌ More complex
- ❌ Need UI to reassign contacts
- ❌ Requires backfilling owner_id

---

### Option 3: Role-Based Access (Admin vs Staff)

**Use Case:**
- You have admins (full access) and regular staff (limited access)
- Admins can edit any contact
- Staff can only view or limited edit

**Implementation:**
```sql
-- 1. Create roles table
CREATE TABLE staff_roles (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id),
  role TEXT NOT NULL CHECK (role IN ('admin', 'staff', 'viewer')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Helper function
CREATE FUNCTION get_user_role()
RETURNS TEXT AS $$
  SELECT role FROM staff_roles WHERE user_id = auth.uid();
$$ LANGUAGE SQL SECURITY DEFINER;

-- 3. RLS policies
CREATE POLICY "All staff can view contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (get_user_role() IN ('admin', 'staff', 'viewer'));

CREATE POLICY "Only admins can update contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (get_user_role() = 'admin')
    WITH CHECK (get_user_role() = 'admin');
```

**Tag Function (Role Check):**
```sql
CREATE FUNCTION add_contact_tag(p_contact_id UUID, p_new_tag TEXT)
  RETURNS JSONB AS $$
BEGIN
  -- Check user is staff or admin
  IF get_user_role() NOT IN ('admin', 'staff') THEN
    RAISE EXCEPTION 'Insufficient permissions';
  END IF;

  -- Rest of function...
END;
$$ LANGUAGE plpgsql;
```

---

## 🎯 MY RECOMMENDATION

**For "Multi-Tenant Staff-Only" → Choose Option 1**

**Reasoning:**
1. You said "staff-only" - implies trusted team
2. No mention of ownership in your schema
3. Simplest to implement
4. Most flexible for small teams
5. Can always add ownership later

**Implementation Steps:**

1. **Add RLS policies** (5 minutes):
```sql
-- File: supabase/migrations/20251113000003_staff_rls_policies.sql

-- Drop old restrictive policy
DROP POLICY IF EXISTS "Users can view their own contact" ON contacts;

-- Allow all staff to see all contacts
CREATE POLICY "staff_select_all_contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (true);

-- Allow all staff to update all contacts
CREATE POLICY "staff_update_all_contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow all staff to insert contacts
CREATE POLICY "staff_insert_contacts"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (true);
```

2. **Simplify tag function** (remove SECURITY DEFINER):
```sql
-- File: supabase/migrations/20251113000004_simplify_tag_functions.sql

DROP FUNCTION IF EXISTS add_contact_tag;
DROP FUNCTION IF EXISTS remove_contact_tag;

-- Simplified (RLS handles permissions)
CREATE FUNCTION add_contact_tag(p_contact_id UUID, p_new_tag TEXT)
  RETURNS JSONB AS $$
DECLARE
  v_tag TEXT;
  v_result JSONB;
BEGIN
  -- Normalize
  v_tag := LOWER(TRIM(p_new_tag));

  -- Validate
  IF v_tag = '' THEN
    RAISE EXCEPTION 'Tag cannot be empty';
  END IF;

  IF LENGTH(v_tag) > 50 THEN
    RAISE EXCEPTION 'Tag cannot exceed 50 characters';
  END IF;

  -- Max tags limit
  IF (SELECT array_length(tags, 1) FROM contacts WHERE id = p_contact_id) >= 50 THEN
    RAISE EXCEPTION 'Maximum 50 tags per contact';
  END IF;

  -- Atomic update (RLS enforces permissions automatically)
  UPDATE contacts
  SET
    tags = CASE
      WHEN tags IS NULL THEN ARRAY[v_tag]
      WHEN v_tag = ANY(tags) THEN tags  -- Already exists
      ELSE array_append(tags, v_tag)
    END,
    updated_at = NOW()
  WHERE id = p_contact_id
  RETURNING jsonb_build_object(
    'success', true,
    'tags', tags
  ) INTO v_result;

  -- Check if contact exists and user has permission
  IF v_result IS NULL THEN
    RAISE EXCEPTION 'Contact not found or permission denied';
  END IF;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql;  -- No SECURITY DEFINER!

-- Same for remove
CREATE FUNCTION remove_contact_tag(p_contact_id UUID, p_tag TEXT)
  RETURNS JSONB AS $$
DECLARE
  v_tag TEXT;
  v_result JSONB;
BEGIN
  v_tag := LOWER(TRIM(p_tag));

  UPDATE contacts
  SET
    tags = array_remove(tags, v_tag),
    updated_at = NOW()
  WHERE id = p_contact_id
  RETURNING jsonb_build_object(
    'success', true,
    'tags', tags
  ) INTO v_result;

  IF v_result IS NULL THEN
    RAISE EXCEPTION 'Contact not found or permission denied';
  END IF;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION add_contact_tag TO authenticated;
GRANT EXECUTE ON FUNCTION remove_contact_tag TO authenticated;
```

---

## ✅ REVISED PRIORITY LIST

### MUST FIX BEFORE DEPLOYMENT:

1. **Add staff RLS policies** (blocks tag functionality)
   - Risk: HIGH - Tags don't work at all
   - Effort: 5 minutes
   - File: `20251113000003_staff_rls_policies.sql`

2. **Remove SECURITY DEFINER from tag functions**
   - Risk: MEDIUM - Creates confusion
   - Effort: 2 minutes
   - File: `20251113000004_simplify_tag_functions.sql`

3. **Add loading state to auth check**
   - Risk: MEDIUM - Brief flash of content
   - Effort: 5 minutes
   - File: `app/(dashboard)/layout.tsx`

### SHOULD FIX THIS WEEK:

4. Replace alert() with toast notifications
5. Add TypeScript types for RPC responses
6. Add loading states to tag operations
7. Add max tags limit (already in new function above)

### NICE TO HAVE:

8. Add ARIA attributes
9. Keyboard shortcuts
10. Error boundaries
11. Monitoring

---

## 🚫 IGNORE FROM ORIGINAL REVIEW

These don't apply to your architecture:

- ❌ Authorization checks for `created_by` column (doesn't exist)
- ❌ `admin_users` table checks (not needed for Option 1)
- ❌ Complex rate limiting (simple max tags limit is enough)
- ❌ Middleware auth (client component is fine for staff app)

---

## Questions to Confirm:

1. **Are all authenticated users staff?** (Yes/No)
   - If YES → Use Option 1
   - If NO → How do you differentiate staff from non-staff?

2. **Should staff see all contacts or only their own?**
   - All contacts → Option 1
   - Only their own → Option 2

3. **Do you need to track who created/modified contacts?**
   - No → Option 1 (current)
   - Yes → Add audit columns later

**My assumption**: All authenticated = staff, all should see/edit all contacts.

If that's correct, I'll implement the Option 1 fixes now.
