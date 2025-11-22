# StarHouse Platform - Engineering Standards

## Context
- **Project:** Internal CRM+ for StarHouse (spiritual/transformational community)
- **Scale:** <10 staff members (internal tool, not public SaaS)
- **Tech Lead:** Ed Burns
- **Standard:** FAANG-level engineering (we build it right, once)

## Core Principles

### 1. Fix Root Causes, Not Symptoms
- ❌ Quick patches that create tech debt
- ✅ Understand the problem fully before coding
- ✅ One comprehensive fix, not multiple partial fixes

### 2. Verify Before Deploy
- ❌ "It should work" assumptions
- ✅ Local build must pass: `npm run build`
- ✅ TypeScript must pass: `npx tsc --noEmit`
- ✅ Show verification output before committing

### 3. Zero Failed Deploys
- ❌ "Try it and see" deployments
- ✅ Test locally first, always
- ✅ One successful deploy per fix
- ✅ No more than 1 failed deploy per issue

### 4. Security First
- ✅ Session management must be explicit
- ✅ No session hijacking vulnerabilities
- ✅ Clear existing state before creating new state
- ✅ P0 security bugs block all other work

### 5. Complete Diagnostics
- ❌ Guessing at root causes
- ✅ Show me the actual error messages
- ✅ Show me the actual code sections
- ✅ Show me the verification queries
- ✅ Full diagnostic before attempting fix

## Tech Stack

### Frontend
- Next.js 14.1.0 (App Router)
- TypeScript (strict mode)
- Tailwind CSS
- React 18

### Backend
- Supabase (PostgreSQL + Auth + Edge Functions)
- Database: PostgreSQL with RLS
- Auth: Supabase Auth (email/password)
- Edge Functions: Deno runtime

### Deployment
- Frontend: Vercel (auto-deploy on push to main)
- Edge Functions: GitHub Actions
- Database: Supabase managed

## Database Standards

### Schema Rules
- ✅ Use UUID as primary key (immutable)
- ❌ Never use mutable fields (email) as PK
- ✅ Foreign keys with CASCADE delete
- ✅ Timestamps: created_at, updated_at
- ✅ Idempotent migrations (IF NOT EXISTS)

### Current Schema
- **staff_members:** id (UUID PK), email (UNIQUE), role, last_sign_in_at, email_confirmed_at, updated_at
- **Primary roles:** super_admin, admin, staff

## Code Quality Standards

### Before Every Commit
```bash
# Must pass all three:
npm run build          # ✅ Next.js build
npx tsc --noEmit       # ✅ TypeScript check
npm run lint           # ✅ ESLint check
```

### Git Commit Format
```
type(scope): description

Types: feat, fix, refactor, docs, test, chore
Scope: auth, db, ui, api, edge-functions
```

Examples:
- `fix(auth): Clear existing sessions on invite callback`
- `feat(db): Add UUID primary key to staff_members`
- `refactor(ui): Extract StaffTable into separate component`

### TypeScript Standards
- ✅ Strict mode enabled
- ✅ No `any` types without justification
- ✅ Explicit return types on exported functions
- ✅ Interface over type for object shapes

### Error Handling
- ✅ Always handle both success and error cases
- ✅ Log errors with context (what operation, what inputs)
- ✅ User-facing errors must be actionable
- ❌ Never swallow errors silently

## Testing Standards

### Local Testing Checklist
1. Build passes: `npm run build`
2. TypeScript passes: `npx tsc --noEmit`
3. Lint passes: `npm run lint`
4. Manual test the specific feature
5. Check browser console for errors
6. Verify database state after operations

### Database Verification
```sql
-- Always verify state changes
SELECT id, email, role, email_confirmed_at, last_sign_in_at
FROM staff_members
WHERE email = 'user@example.com';
```

## Deployment Checklist

### Before Push to Main
- [ ] All local checks pass
- [ ] Changes tested manually
- [ ] No console errors
- [ ] Database migrations are idempotent
- [ ] Environment variables documented

### After Deploy
- [ ] Verify Vercel deployment succeeded
- [ ] Check Vercel function logs for errors
- [ ] Test feature in production
- [ ] Monitor for 5 minutes post-deploy

## Security Standards

### Authentication
- ✅ Use Supabase Auth exclusively
- ✅ Clear sessions before creating new ones
- ✅ Validate session on every protected route
- ✅ Handle invite flow vs normal sign-in separately

### Row Level Security (RLS)
- ✅ Enable RLS on all tables
- ✅ Policies based on auth.uid()
- ✅ Test policies with different user roles
- ❌ Never disable RLS in production

### Sensitive Data
- ✅ Never log passwords or tokens
- ✅ Use environment variables for secrets
- ✅ Rotate credentials on suspected compromise

## Incident Response

### P0 (Critical) - Security Bugs
- **Response time:** Immediate
- **Action:** Stop all other work, fix immediately
- **Examples:** Session hijacking, auth bypass, data exposure

### P1 (High) - Feature Breaking
- **Response time:** Same day
- **Action:** Fix before any new features
- **Examples:** Can't sign in, can't save data

### P2 (Medium) - Degraded Experience
- **Response time:** This week
- **Examples:** Slow queries, UI glitches

### P3 (Low) - Nice to Have
- **Response time:** When convenient
- **Examples:** Code cleanup, minor improvements

## Documentation Requirements

### Code Comments
- ✅ Why, not what (code shows what)
- ✅ Document non-obvious business logic
- ✅ Link to relevant docs/issues
- ❌ Don't comment obvious code

### README Updates
- ✅ Update setup instructions when dependencies change
- ✅ Document environment variables
- ✅ Keep architecture diagrams current

## Review Checklist

Before requesting review:
- [ ] Self-reviewed the diff
- [ ] All checks pass locally
- [ ] No commented-out code
- [ ] No console.log statements (except intentional logging)
- [ ] No TODO comments without issue links
- [ ] Commit messages follow format

---

**Remember:** We're building a small internal tool, but with enterprise-grade quality. Every shortcut creates debt we'll pay later. Do it right, once.
