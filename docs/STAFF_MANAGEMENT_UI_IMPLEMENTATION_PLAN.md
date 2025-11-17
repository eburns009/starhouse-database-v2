# Staff Management UI - FAANG Standard Implementation Plan

**Date:** 2025-11-17
**Status:** Planning Phase
**Standards:** FAANG-Level Architecture & Security

---

## Executive Summary

Build a comprehensive staff management UI with three-tier access control (Admin, Full User, Read Only) following FAANG best practices for security, scalability, and maintainability.

---

## Current State Analysis

### ✅ Existing Infrastructure

**Database (Already Implemented):**
- ✅ `staff_members` table with role-based access
- ✅ Two roles: `admin`, `staff`
- ✅ RLS policies with `is_verified_staff()` function
- ✅ Audit trail (`created_by`, `updated_by`, `deleted_at`)
- ✅ Helper functions: `add_staff_member()`, `deactivate_staff_member()`, `promote_to_admin()`

**Current Limitations:**
- ❌ Only 2 roles (need 3: Admin, Full User, Read Only)
- ❌ No UI for staff management
- ❌ No TypeScript types generated
- ❌ No frontend validation
- ❌ No activity logging

---

## Requirements

### 1. Three-Tier Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full access + manage users + system settings |
| **Full User** | View/edit contacts, donors, transactions (no user management) |
| **Read Only** | View-only access (no edits, no user management) |

### 2. Core Features

**Staff Management (Admin Only):**
- [x] Add new staff member (email, name, role)
- [x] Edit staff roles
- [x] Deactivate/reactivate staff
- [x] View staff list with status
- [ ] Bulk operations
- [ ] Activity audit log

**User Experience:**
- [ ] Real-time updates (Supabase realtime)
- [ ] Optimistic UI updates
- [ ] Comprehensive error handling
- [ ] Loading states
- [ ] Toast notifications
- [ ] Confirmation dialogs for destructive actions

**Security:**
- [ ] Client-side role verification
- [ ] Server-side RLS enforcement
- [ ] Audit logging
- [ ] Session management
- [ ] CSRF protection (built into Supabase)

---

## Architecture (FAANG Standards)

### Layer 1: Database Schema

```sql
-- ENHANCEMENT: Add 'read_only' role
ALTER TABLE staff_members
DROP CONSTRAINT IF EXISTS staff_members_role_check;

ALTER TABLE staff_members
ADD CONSTRAINT staff_members_role_check
CHECK (role IN ('admin', 'full_user', 'read_only'));

-- ENHANCEMENT: Add display name
ALTER TABLE staff_members
ADD COLUMN IF NOT EXISTS display_name TEXT;

-- ENHANCEMENT: Add last_login tracking
ALTER TABLE staff_members
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- INDEX: Fast lookups
CREATE INDEX IF NOT EXISTS idx_staff_members_last_login
ON staff_members(last_login_at DESC)
WHERE active = true;
```

### Layer 2: RLS Policies (Update for 3 Roles)

```sql
-- Read-only users: SELECT only
CREATE POLICY "read_only_select_contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role IN ('admin', 'full_user', 'read_only')
            AND active = true
        )
    );

-- Full users: SELECT, INSERT, UPDATE (no DELETE)
CREATE POLICY "full_user_modify_contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role IN ('admin', 'full_user')
            AND active = true
        )
    );

-- Admin: Full CRUD
CREATE POLICY "admin_full_access"
    ON contacts FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM staff_members
            WHERE email = auth.jwt()->>'email'
            AND role = 'admin'
            AND active = true
        )
    );
```

### Layer 3: TypeScript Types (Auto-generated)

```typescript
// Generated from Supabase
export type StaffRole = 'admin' | 'full_user' | 'read_only';

export interface StaffMember {
  email: string;
  display_name: string | null;
  role: StaffRole;
  active: boolean;
  added_at: string;
  added_by: string | null;
  deactivated_at: string | null;
  deactivated_by: string | null;
  last_login_at: string | null;
  notes: string | null;
}

export interface Database {
  public: {
    Tables: {
      staff_members: {
        Row: StaffMember;
        Insert: Omit<StaffMember, 'added_at' | 'last_login_at'>;
        Update: Partial<StaffMember>;
      };
    };
    Functions: {
      add_staff_member: {
        Args: {
          p_email: string;
          p_role: StaffRole;
          p_display_name?: string;
          p_notes?: string;
        };
        Returns: Json;
      };
      deactivate_staff_member: {
        Args: { p_email: string };
        Returns: Json;
      };
      promote_to_admin: {
        Args: { p_email: string };
        Returns: Json;
      };
      is_admin: {
        Args: Record<string, never>;
        Returns: boolean;
      };
    };
  };
}
```

### Layer 4: React Hooks (Custom Hooks Pattern)

```typescript
// hooks/useStaffMembers.ts
export function useStaffMembers() {
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Real-time subscription
  useEffect(() => {
    const subscription = supabase
      .channel('staff_members_changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'staff_members'
      }, handleChange)
      .subscribe();

    return () => subscription.unsubscribe();
  }, []);

  return { staff, loading, error, refetch };
}

// hooks/useCurrentUser.ts
export function useCurrentUser() {
  const { data: session } = useSession();
  const { data: staffMember } = useQuery({
    queryKey: ['currentStaff', session?.user?.email],
    queryFn: async () => {
      const { data } = await supabase
        .from('staff_members')
        .select('*')
        .eq('email', session?.user?.email)
        .single();
      return data;
    },
    enabled: !!session?.user?.email
  });

  return {
    isAdmin: staffMember?.role === 'admin',
    isFullUser: staffMember?.role === 'full_user',
    isReadOnly: staffMember?.role === 'read_only',
    role: staffMember?.role,
    ...staffMember
  };
}
```

### Layer 5: UI Components (Shadcn/UI + Tailwind)

**File Structure:**
```
starhouse-ui/
├── app/
│   └── (authenticated)/
│       └── staff/
│           ├── page.tsx                 # Staff list page
│           ├── [email]/
│           │   └── page.tsx             # Staff detail/edit page
│           └── new/
│               └── page.tsx             # Add new staff
├── components/
│   └── staff/
│       ├── StaffTable.tsx               # Main table component
│       ├── StaffTableRow.tsx            # Table row with actions
│       ├── AddStaffDialog.tsx           # Modal for adding staff
│       ├── EditStaffDialog.tsx          # Modal for editing
│       ├── DeactivateStaffDialog.tsx    # Confirmation dialog
│       ├── RoleBadge.tsx                # Visual role indicator
│       └── StaffActivityLog.tsx         # Activity history
├── lib/
│   ├── supabase/
│   │   ├── client.ts                    # Supabase client
│   │   ├── types.ts                     # Generated types
│   │   └── staff-api.ts                 # Staff API methods
│   └── hooks/
│       ├── useStaffMembers.ts
│       ├── useCurrentUser.ts
│       └── useStaffActions.ts
└── types/
    └── staff.ts                         # Additional types
```

---

## Implementation Phases

### Phase 1: Database Schema Enhancement (30 min)

**Tasks:**
1. Add `read_only` role to enum
2. Add `display_name` column
3. Add `last_login_at` column
4. Update RLS policies for 3-tier access
5. Create helper function `is_admin()`
6. Create activity log table
7. Test with SQL scripts

**Files to Create:**
- `/supabase/migrations/20251117000001_three_tier_staff_roles.sql`

**Acceptance Criteria:**
- All 3 roles work in database
- RLS policies enforce correct permissions
- Helper functions return correct results
- Migration is idempotent

---

### Phase 2: TypeScript Types & API Layer (45 min)

**Tasks:**
1. Generate TypeScript types from Supabase
2. Create Supabase client utilities
3. Build staff API methods with error handling
4. Create custom React hooks
5. Add Zod validation schemas
6. Write unit tests for API layer

**Files to Create:**
- `starhouse-ui/lib/supabase/types.ts`
- `starhouse-ui/lib/supabase/staff-api.ts`
- `starhouse-ui/lib/hooks/useStaffMembers.ts`
- `starhouse-ui/lib/hooks/useCurrentUser.ts`
- `starhouse-ui/lib/hooks/useStaffActions.ts`
- `starhouse-ui/lib/validations/staff.ts`

**Acceptance Criteria:**
- Types are generated and accurate
- API methods handle all error cases
- Hooks provide real-time updates
- Validation catches invalid inputs
- 100% test coverage on critical paths

---

### Phase 3: UI Components (2 hours)

**Tasks:**
1. Build StaffTable with sorting/filtering
2. Create Add/Edit/Delete dialogs
3. Implement role badge component
4. Add loading states
5. Add error boundaries
6. Implement optimistic updates
7. Add toast notifications
8. Style with Tailwind + Shadcn

**Files to Create:**
- `starhouse-ui/app/(authenticated)/staff/page.tsx`
- `starhouse-ui/components/staff/StaffTable.tsx`
- `starhouse-ui/components/staff/AddStaffDialog.tsx`
- `starhouse-ui/components/staff/EditStaffDialog.tsx`
- `starhouse-ui/components/staff/DeactivateStaffDialog.tsx`
- `starhouse-ui/components/staff/RoleBadge.tsx`

**Acceptance Criteria:**
- All CRUD operations work
- Real-time updates visible
- Optimistic UI feels instant
- Errors are handled gracefully
- Mobile responsive
- Accessibility (WCAG 2.1 AA)

---

### Phase 4: Testing & Documentation (1 hour)

**Tasks:**
1. Write integration tests
2. Write E2E tests with Playwright
3. Test all 3 roles
4. Document API usage
5. Create user guide
6. Add JSDoc comments

**Files to Create:**
- `starhouse-ui/tests/staff-management.test.ts`
- `starhouse-ui/tests/e2e/staff-flow.spec.ts`
- `docs/STAFF_MANAGEMENT_USER_GUIDE.md`
- `docs/STAFF_MANAGEMENT_API.md`

**Acceptance Criteria:**
- 90%+ test coverage
- All user flows tested
- Documentation complete
- Code reviewed

---

## FAANG Standards Checklist

### Security
- [x] RLS policies enforce all access control
- [ ] Client-side validation (Zod)
- [ ] Server-side validation (database constraints)
- [ ] Audit logging for all admin actions
- [ ] CSRF protection (Supabase built-in)
- [ ] Rate limiting on sensitive operations
- [ ] No credentials in frontend code
- [ ] Secure session management

### Performance
- [ ] Optimistic UI updates (instant feedback)
- [ ] Real-time subscriptions (Supabase Realtime)
- [ ] Efficient database queries (indexes)
- [ ] Lazy loading for large lists
- [ ] Memoization for expensive computations
- [ ] Debounced search inputs
- [ ] Virtual scrolling for 100+ items

### Reliability
- [ ] Error boundaries catch React errors
- [ ] Graceful degradation (network failures)
- [ ] Retry logic for transient failures
- [ ] Loading states for all async operations
- [ ] Empty states for no data
- [ ] Confirmation dialogs for destructive actions
- [ ] Transaction rollback on errors

### Scalability
- [ ] Database indexes on all foreign keys
- [ ] Pagination for large datasets
- [ ] Efficient bulk operations
- [ ] Database connection pooling
- [ ] Caching for frequently accessed data
- [ ] CDN for static assets

### Maintainability
- [ ] TypeScript strict mode
- [ ] ESLint + Prettier configured
- [ ] Component library (Shadcn/UI)
- [ ] Consistent naming conventions
- [ ] Comprehensive JSDoc comments
- [ ] Clear file structure
- [ ] Reusable hooks and utilities

### Observability
- [ ] Error tracking (Sentry/similar)
- [ ] Analytics events for key actions
- [ ] Performance monitoring
- [ ] Audit logs in database
- [ ] User activity tracking
- [ ] Debug logging (development only)

---

## Migration Strategy

### Step 1: Database Migration (Zero Downtime)
```sql
BEGIN;
-- Add new columns (nullable first)
ALTER TABLE staff_members ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE staff_members ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- Update constraint to include new role
ALTER TABLE staff_members DROP CONSTRAINT IF EXISTS staff_members_role_check;
ALTER TABLE staff_members ADD CONSTRAINT staff_members_role_check
  CHECK (role IN ('admin', 'full_user', 'read_only'));

-- Migrate existing 'staff' role to 'full_user'
UPDATE staff_members SET role = 'full_user' WHERE role = 'staff';

COMMIT;
```

### Step 2: Deploy Backend (API/Functions)
- Deploy new Supabase functions
- Update RLS policies
- Test with existing frontend

### Step 3: Deploy Frontend (Feature Flag)
- Deploy UI behind feature flag
- Enable for admin users only
- Monitor for errors
- Gradual rollout to all users

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Data loss during migration | HIGH | Full database backup before migration |
| Privilege escalation bug | HIGH | Comprehensive RLS testing, code review |
| UI breaking changes | MEDIUM | Feature flags, gradual rollout |
| Performance degradation | MEDIUM | Load testing, database indexes |
| User confusion | LOW | In-app help, documentation |

---

## Success Metrics

1. **Functionality:** All 3 roles work as expected
2. **Performance:** Page load <500ms, actions <200ms
3. **Reliability:** 99.9% uptime, <0.1% error rate
4. **Security:** Zero privilege escalation bugs
5. **UX:** <5 clicks to common actions
6. **Accessibility:** WCAG 2.1 AA compliance

---

## Timeline

- **Phase 1 (Database):** 30 minutes
- **Phase 2 (API Layer):** 45 minutes
- **Phase 3 (UI):** 2 hours
- **Phase 4 (Testing/Docs):** 1 hour

**Total Estimated Time:** 4 hours 15 minutes

---

## Next Steps

1. Review and approve this plan
2. Create database migration
3. Generate TypeScript types
4. Build UI components
5. Test thoroughly
6. Deploy to production

**Ready to proceed?**
