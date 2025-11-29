# StarHouse Platform - Engineering Standards v2

## Senior Technical Advisor Role

**Identity:** Senior Technical Lead with 20+ years experience, reporting to Ed Burns (Tech Lead/Project Owner)

**Purpose:**
- Engineering advisor — ensure quality and prevent shortcuts
- Review and direct Claude's work (does not write code)
- Enforce platform-first architecture

**Prompt Standards:**

| Task Type | Format |
|-----------|--------|
| Code changes | Full Engineering Standards header + build verification |
| Database writes | Full header + DRY-RUN + verification |
| Deploys | Full header + commit message + promotion check |
| Documentation/planning | Simple direct prompt |
| Diagnostics/questions | Simple direct prompt |

**Mandatory:** Every prompt to Claude must begin with:
```
Follow /docs/ENGINEERING_STANDARDS.md for all code changes.
```

**Before Any Fix:**
- Actual error messages shown
- Root cause identified
- Explanation of WHY bug exists
- Proposed fix with verification plan

**Before Any DB Write:**
- DRY-RUN results shown
- Record counts before and after
- Duplicate check query run
- Ed approval

**Before Any Deploy:**
- npm run build passes
- npx tsc --noEmit passes
- Manual testing completed

**Non-Negotiable Rule:**
When any item is deferred or identified for future work, immediately update the Master Plan. The Master Plan is the single source of truth.

---

## Schema Quick Reference

This section tracks schema changes made during development. Full schema in SCHEMA_SUMMARY_v2.md.

### Tables Modified

| Table | Change | Phase | Date |
|-------|--------|-------|------|
| contacts | Added `business_name` TEXT column | 1.1 | 2025-11-28 |

### Views Created

(none this session)

### Functions Modified

| Function | Change | Phase | Date |
|----------|--------|-------|------|
| is_verified_staff() | Now checks staff_members table instead of just auth.uid() | 0.2 | 2025-11-28 |

---

## Context

- **Project:** Internal CRM+ for StarHouse (spiritual/transformational community)
- **Scale:** <10 staff members (internal tool, not public SaaS)
- **Tech Lead:** Ed Burns
- **Standard:** FAANG-level engineering (we build it right, once)
- **Architecture:** Staff UI layer — build only what we must

---

## Architecture Principles

### Platform-First Philosophy

StarHouse is a **staff-facing workflow and reporting layer**, not a full application. We leverage existing platforms for what they do best and build only what we must.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUBLIC LAYER (Wix)                           │
│  Forms • Payments • Courses • Email Marketing                   │
└─────────────────────────────────────────────────────────────────┘
                              │ Webhooks
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                            │
│  Supabase (Data/Auth/Logic)  •  Vercel (Hosting/Cron/Webhooks) │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              STARHOUSE APP (What We Build)                      │
│  Staff UI • Workflows • KPIs • Reporting • Data Quality         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ACCOUNTING LAYER (QuickBooks)                   │
│  Financial Records • Revenue Tracking • Tax Reporting           │
└─────────────────────────────────────────────────────────────────┘
```

### Platform Responsibilities

| Platform | Owns | We Do NOT Build |
|----------|------|-----------------|
| **Wix** | Public forms, Stripe payments, invoicing, courses, email marketing | Public-facing forms, payment processing, email sending |
| **Supabase** | Database, Auth, RLS, Functions, Views, Triggers, Storage | Authentication flows, session management, audit trails |
| **Vercel** | Hosting, Edge Functions, Cron Jobs, Analytics | Deployment, scheduling infrastructure |
| **QuickBooks** | Accounting, financial records | Invoice generation, financial reporting |
| **StarHouse** | Staff UI, workflows, KPIs, reporting, data quality | This is what we build |

### The Golden Rule

> **The less code we write, the less we maintain. Let the platforms do their jobs.**

---

## Before Any New Feature

Before writing any code, ask these questions in order:

### 1. Can Wix Do This?
- Public form? → Wix Forms + webhook
- Payment collection? → Wix/Stripe + webhook
- Invoice? → Wix or QuickBooks
- Email to users? → Wix email marketing
- Course delivery? → Wix courses

**If yes → Configure webhook to receive data. Don't build.**

### 2. Can Supabase Do This?
- Data aggregation? → Create a View
- Business logic? → Create a Function
- Validation? → Add a Constraint
- Computed field? → Add to View
- Audit trail? → Trigger exists
- Authentication? → Supabase Auth

**If yes → Write SQL, not application code.**

### 3. Can Vercel Do This?
- Scheduled task? → Vercel Cron
- Webhook receiver? → Edge Function
- Performance monitoring? → Vercel Analytics

**If yes → Configure, don't build custom.**

### 4. Only Then: Build in App
If none of the above can handle it, and it's staff-facing workflow or KPI display, then build it in Next.js.

**Healthy app code:**
- Thin API routes (fetch from Supabase, return to UI)
- Simple webhooks (validate, insert, done)
- UI components (forms, tables, dashboards)
- No business logic in app layer

---

## Core Principles

### 0. Build Only What We Must
- ❌ Building what platforms provide
- ❌ Business logic in application code
- ❌ Aggregation queries in API routes
- ✅ Supabase views for data aggregation
- ✅ Supabase functions for business logic
- ✅ Wix for public-facing features
- ✅ App code only for staff UI

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
- ✅ Use Supabase Auth (not custom auth)
- ✅ RLS policies on all tables
- ✅ No session hijacking vulnerabilities
- ✅ P0 security bugs block all other work

### 5. Complete Diagnostics
- ❌ Guessing at root causes
- ✅ Show me the actual error messages
- ✅ Show me the actual code sections
- ✅ Show me the verification queries
- ✅ Full diagnostic before attempting fix

---

## Tech Stack

### Public Layer (Wix)
- Website and content
- Public forms (inquiry, donation, registration)
- Stripe payment processing
- Course hosting
- Email marketing
- **Sends webhooks to StarHouse**

### Infrastructure Layer

#### Supabase (Data & Logic)
- PostgreSQL database
- Supabase Auth (email/password)
- Row Level Security (RLS)
- Database Functions (business logic)
- Database Views (reporting, aggregation)
- Database Triggers (audit trails)
- Storage (file uploads if needed)

#### Vercel (Hosting & Operations)
- Next.js hosting (auto-deploy on push to main)
- Edge Functions (webhook receivers)
- Cron Jobs (scheduled tasks)
- Analytics (usage tracking)

### Application Layer (StarHouse - What We Build)
- Next.js 14.1.0 (App Router)
- TypeScript (strict mode)
- Tailwind CSS
- React 18
- **Staff UI only**

### Accounting Layer (QuickBooks)
- Financial records
- Revenue tracking
- Tax reporting
- **Source of truth for finances**

---

## Supabase-First Development

### Prefer Views Over App Queries

**❌ Don't do this in API route:**
```typescript
// BAD: Aggregation in app code
const donors = await supabase.from('contacts').select('*');
const totals = donors.reduce((acc, d) => {
  // Complex aggregation logic
}, {});
```

**✅ Do this instead:**
```sql
-- GOOD: Create a Supabase view
CREATE OR REPLACE VIEW v_donor_summary AS
SELECT 
  c.id,
  c.full_name,
  COALESCE(SUM(t.amount), 0) as lifetime_giving,
  COUNT(t.id) as gift_count,
  MAX(t.transaction_date) as last_gift
FROM contacts c
LEFT JOIN transactions t ON t.contact_id = c.id AND t.is_donation = true
GROUP BY c.id, c.full_name;
```

```typescript
// GOOD: Thin API route
const { data } = await supabase.from('v_donor_summary').select('*');
```

### Prefer Functions Over App Logic

**❌ Don't do this in app:**
```typescript
// BAD: Business logic in app
function checkMembership(contact) {
  const subscription = contact.subscriptions.find(s => s.status === 'active');
  if (!subscription) return false;
  if (subscription.end_date < new Date()) return false;
  return true;
}
```

**✅ Do this instead:**
```sql
-- GOOD: Supabase function (already exists!)
SELECT is_current_member('contact-uuid-here');
SELECT get_membership_status('contact-uuid-here');
```

### Prefer Constraints Over App Validation

**❌ Don't do this in app:**
```typescript
// BAD: Validation in app
if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
  throw new Error('Invalid email');
}
```

**✅ Do this instead:**
```sql
-- GOOD: Database constraint
ALTER TABLE contacts 
ADD CONSTRAINT valid_email 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
```

### Prefer Triggers Over Manual Updates

**❌ Don't do this in app:**
```typescript
// BAD: Manual timestamp
await supabase.from('contacts').update({
  ...data,
  updated_at: new Date().toISOString()
});
```

**✅ Do this instead:**
```sql
-- GOOD: Trigger handles it (already exists!)
-- Just update the data, trigger sets updated_at automatically
```

```typescript
// GOOD: Trigger handles timestamp
await supabase.from('contacts').update(data);
```

---

## Webhook Standards

### Webhook Receiver Pattern

```typescript
// /api/webhooks/wix/[type].ts
import { NextRequest } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const config = { runtime: 'edge' };

export default async function handler(req: NextRequest) {
  // 1. Parse payload
  const payload = await req.json();
  
  // 2. Validate webhook (signature verification)
  const signature = req.headers.get('x-wix-signature');
  if (!validateSignature(payload, signature)) {
    return new Response('Invalid signature', { status: 401 });
  }
  
  // 3. Create Supabase client with service role
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
  
  // 4. Insert data (simple, no business logic)
  const { error } = await supabase.from('table_name').insert({
    source: 'wix',
    ...mapPayloadToSchema(payload),
    raw_payload: payload, // Always store raw for debugging
    status: 'new'
  });
  
  // 5. Handle errors
  if (error) {
    console.error('Webhook insert error:', error);
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
  
  // 6. Return success
  return new Response(JSON.stringify({ received: true }), { status: 200 });
}
```

### Webhook Requirements

- ✅ Use Edge runtime for speed
- ✅ Validate signatures
- ✅ Store raw payload for debugging
- ✅ Use service role key (webhooks bypass RLS)
- ✅ Return quickly (no long processing)
- ✅ Log errors with context
- ❌ Don't put business logic in webhooks
- ❌ Don't call external APIs from webhooks

---

## Vercel Cron Standards

### Configuration

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/daily-health-check",
      "schedule": "0 6 * * *"
    },
    {
      "path": "/api/cron/membership-expiry-alerts",
      "schedule": "0 8 * * 1"
    },
    {
      "path": "/api/cron/cleanup-old-webhooks",
      "schedule": "0 0 * * 0"
    }
  ]
}
```

### Cron Handler Pattern

```typescript
// /api/cron/daily-health-check.ts
import { NextRequest } from 'next/server';

export default async function handler(req: NextRequest) {
  // 1. Verify cron secret (prevent unauthorized calls)
  const authHeader = req.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return new Response('Unauthorized', { status: 401 });
  }
  
  // 2. Call Supabase function (logic lives in DB)
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
  
  const { data, error } = await supabase.rpc('daily_health_check');
  
  // 3. Log results
  console.log('Health check completed:', data);
  
  // 4. Return status
  return new Response(JSON.stringify({ success: !error, data }), { 
    status: error ? 500 : 200 
  });
}
```

### Cron Requirements

- ✅ Verify authorization
- ✅ Call Supabase functions (logic in DB)
- ✅ Log results
- ✅ Keep handlers thin
- ❌ Don't put business logic in cron handlers

---

## Code Quality Standards

### Before Every Commit
```bash
npm run build          # ✅ Next.js build must pass
npx tsc --noEmit       # ✅ TypeScript check must pass
npm run lint           # ✅ ESLint check must pass
```

### Git Commit Format
```
type(scope): description

Types: feat, fix, refactor, docs, test, chore
Scope: auth, db, ui, api, donors, contacts, events, membership, webhooks
```

Examples:
- `fix(donors): Resolve duplicate transactions in import`
- `feat(db): Add v_donor_classification view`
- `feat(webhooks): Add Wix inquiry receiver`
- `refactor(ui): Extract DonorCard into separate component`

### TypeScript Standards
- ✅ Strict mode enabled
- ✅ No `any` types without justification
- ✅ Explicit return types on exported functions
- ✅ Interface over type for object shapes

---

## Database Standards

### Schema Rules
- ✅ Use UUID as primary key (immutable)
- ❌ Never use mutable fields (email) as PK
- ✅ Foreign keys with appropriate CASCADE behavior
- ✅ Timestamps: created_at, updated_at
- ✅ Idempotent migrations (IF NOT EXISTS)
- ✅ Soft-delete (deleted_at) over hard delete

### Query Standards
- ✅ Always include `WHERE deleted_at IS NULL` unless investigating deleted records
- ✅ Use `LOWER(TRIM())` for string comparisons
- ✅ Limit results during investigation (`LIMIT 20`)
- ✅ Show `COUNT(*)` before showing details

### Write Standards
- ✅ Default to DRY-RUN mode for bulk operations
- ✅ Require explicit `--execute` flag for writes
- ✅ Use savepoints for batch operations
- ✅ Verify counts before AND after writes
- ✅ Create backup records for destructive operations

### Row Level Security (RLS)
- ✅ Enable RLS on all tables
- ✅ Policies based on auth.uid()
- ✅ Test policies with different user roles
- ❌ Never disable RLS in production

### New Table Checklist
```sql
-- Every new table needs:
CREATE TABLE new_table (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- ... columns ...
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger for updated_at
CREATE TRIGGER new_table_set_updated_at
  BEFORE UPDATE ON new_table
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
CREATE POLICY "staff_full_access" ON new_table
  FOR ALL TO authenticated USING (true) WITH CHECK (true);
```

---

## Error Handling Standards

### Code Errors
- ✅ Always handle both success and error cases
- ✅ Log errors with context (what operation, what inputs)
- ✅ User-facing errors must be actionable
- ❌ Never swallow errors silently

### Database Errors
```typescript
try {
  const { data, error } = await supabase.from('table').insert(record);
  if (error) throw error;
  return data;
} catch (e) {
  console.error(`Insert failed for ${record.id}:`, e);
  throw e;
}
```

---

## Logging Standards

### Log Levels
- **ERROR**: Operation failed, needs attention
- **WARNING**: Unexpected but recoverable (e.g., skipped record)
- **INFO**: Normal operations (import started, counts, completed)
- **DEBUG**: Detailed record-level operations

### Required Log Points
```typescript
console.log(`Operation started: ${source}`);
console.log(`Records to process: ${count}`);
console.log(`Created: ${x}, Updated: ${y}, Skipped: ${z}, Errors: ${e}`);
console.log(`Operation completed in ${elapsed}ms`);
```

- ✅ Include source, record counts, timing
- ✅ Log errors with full context
- ❌ Never log passwords or tokens

---

## Testing Standards

### Before Every Commit
1. Build passes: `npm run build`
2. TypeScript passes: `npx tsc --noEmit`
3. Lint passes: `npm run lint`
4. Manual test the specific feature
5. Check browser console for errors
6. Verify database state after operations

### Database Verification
```sql
-- Always verify state changes with queries
-- Check counts before and after operations
-- Verify no unintended side effects
```

---

## Deployment Checklist

### Before Push to Main
- [ ] All local checks pass
- [ ] Changes tested manually
- [ ] No console errors
- [ ] Database migrations are idempotent
- [ ] Webhooks tested (if applicable)

### After Deploy
- [ ] Verify Vercel deployment succeeded
- [ ] Check Vercel function logs for errors
- [ ] Test feature in production
- [ ] Monitor for 5 minutes post-deploy

---

## Incident Response

### P0 (Critical) - Security/Data Integrity
- **Response time:** Immediate
- **Action:** Stop all other work, fix immediately
- **Examples:** Session hijacking, auth bypass, data exposure, duplicate data corruption

### P1 (High) - Feature Breaking
- **Response time:** Same day
- **Action:** Fix before any new features
- **Examples:** Can't sign in, can't save data, webhook failures

### P2 (Medium) - Degraded Experience
- **Response time:** This week
- **Examples:** Slow queries, UI glitches

### P3 (Low) - Nice to Have
- **Response time:** When convenient
- **Examples:** Code cleanup, minor improvements

---

## Data Import Standards (Python Scripts)

### Required Flags
```python
parser.add_argument('--dry-run', action='store_true', default=True)
parser.add_argument('--execute', action='store_true')
parser.add_argument('--force', action='store_true')
```

- ✅ Default to dry-run (require explicit `--execute` to write)
- ✅ Log all operations that would occur
- ✅ Show record counts and sample data

### Idempotency
- ✅ Running the same import twice produces the same result
- ✅ Use upsert patterns (INSERT ... ON CONFLICT)
- ✅ Check for existing records before creating
- ❌ Never duplicate data on re-run

### Validation Before Write
```python
errors = validate_all_records(records)
if errors:
    log_errors(errors)
    sys.exit(1)
# Only after validation passes:
write_to_database(records)
```

- ✅ Validate entire dataset before first write
- ✅ Fail fast on validation errors
- ✅ Log specific validation failures with row numbers

### Transaction Safety
```python
for record in records:
    try:
        cur.execute("SAVEPOINT record_import")
        import_record(record)
        cur.execute("RELEASE SAVEPOINT record_import")
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT record_import")
        logging.error(f"Failed: {record} - {e}")
        continue
conn.commit()
```

- ✅ Use savepoints for batch operations
- ✅ One failure doesn't rollback all
- ✅ Log errors and continue processing

### Verification After Import
```python
def verify_import():
    expected = len(records_to_import)
    actual = db.query("SELECT COUNT(*) FROM table WHERE source = 'import'")
    logging.info(f"Verification: Expected {expected}, Actual {actual}")
```

- ✅ Run verification after import completes
- ✅ Compare expected vs actual counts
- ✅ Sample data integrity checks

---

## Duplicate Prevention Standards

### 1. Define Unique Key
```python
# Every import must define what makes a record unique
UNIQUE_KEY_FIELDS = ['source_id', 'contact_id', 'transaction_date', 'amount']
```

### 2. Check Before Insert
```python
existing = db.query("""
    SELECT id FROM transactions 
    WHERE quickbooks_invoice_num = %s 
      AND contact_id = %s
      AND amount = %s
""", [invoice_num, contact_id, amount])

if existing:
    logging.warning(f"Skipping duplicate: {invoice_num}")
    skip_count += 1
    continue
```

### 3. Use Upsert Pattern
```sql
INSERT INTO transactions (...)
VALUES (...)
ON CONFLICT (quickbooks_invoice_num, contact_id) 
DO UPDATE SET updated_at = NOW()
```

### 4. Post-Import Duplicate Check
```sql
-- Required: Check for duplicates after every import
SELECT source_id, contact_id, COUNT(*) 
FROM transactions 
WHERE source_system = 'quickbooks'
GROUP BY source_id, contact_id
HAVING COUNT(*) > 1;
```

- ✅ If duplicates found: STOP and investigate
- ❌ Never assume "it will just update"

---

## Contact Matching Standards

### Priority Order (Highest to Lowest Confidence)
1. Exact email match (case-insensitive) - includes `contact_emails` aliases
2. External ID match (QuickBooks ID, PayPal ID, etc.)
3. Exact full name match + phone match
4. Exact full name match + address match
5. Fuzzy name match (>90% similarity)

### Name Normalization
```python
def normalize_name(name):
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name)     # Collapse whitespace
    # Strip business suffixes
    for suffix in [' ug', ' llc', ' inc', ' corp', ' ltd', ' foundation']:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name
```

### Required Logging
```python
logging.info(f"Matched '{csv_name}' to contact {contact_id} via {match_method}")
```

- ✅ Log the matching method used for each record
- ✅ Flag low-confidence matches for review
- ✅ Check `contact_emails` table for email aliases
- ❌ Never auto-merge without high confidence match
- ❌ Never create duplicates without checking

---

## Documentation Requirements

### Code Comments
- ✅ Why, not what (code shows what)
- ✅ Document non-obvious business logic
- ❌ Don't comment obvious code

### README Updates
- ✅ Update setup instructions when dependencies change
- ✅ Document environment variables
- ✅ Document webhook endpoints

---

## Prohibited Actions

### Data Safety
```
❌ Never DELETE without backup
❌ Never UPDATE without WHERE clause verification
❌ Never re-import without deduplication check
```

### Code Quality
```
❌ Never deploy without local testing
❌ Never commit with failing builds
❌ Never use production credentials in code
❌ Never skip verification steps
❌ Never guess at root causes
❌ Never make multiple partial fixes
```

### Platform Violations
```
❌ Never build public forms (use Wix)
❌ Never build payment processing (use Stripe via Wix)
❌ Never build email sending (use Wix)
❌ Never build custom authentication (use Supabase Auth)
❌ Never build invoice generation (use Wix or QuickBooks)
❌ Never write aggregation logic in app code (use Supabase views)
❌ Never write business logic in app code (use Supabase functions)
❌ Never write validation in app code (use database constraints)
```

---

## Warning Signs: Are We Over-Building?

If you see these patterns, stop and reconsider:

| Warning Sign | Should Be |
|--------------|-----------|
| Validation logic in Next.js | Database constraint |
| Aggregation queries in API routes | Supabase view |
| Business logic in components | Supabase function |
| Auth/session code | Supabase Auth |
| Email sending code | Wix integration |
| Payment form | Wix/Stripe |
| Complex API route (>50 lines) | Probably too much logic |

## Healthy Signs: We're On Track

| Healthy Pattern | Why It's Good |
|-----------------|---------------|
| New feature = new Supabase view | Logic in database |
| API routes are <30 lines | Thin layer |
| Webhooks just validate + insert | No business logic |
| UI is forms + tables + charts | Display only |
| Most SQL is in migrations | Version controlled |

---

## Reference Documents

- **STARHOUSE_MASTER_PLAN_v3.1.md** — Current phases and priorities
- **STARHOUSE_SENIOR_ADVISOR_v2.txt** — Review and approval process
- **SCHEMA_SUMMARY.md** — Database structure reference

---

**Remember:** StarHouse is a staff UI layer. We build workflows, KPIs, and reporting. Everything else — forms, payments, auth, business logic — belongs in the platforms. The less code we write, the less we maintain. Do it right, once.
