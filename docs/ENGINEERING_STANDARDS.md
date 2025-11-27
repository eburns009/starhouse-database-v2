# StarHouse Platform - Engineering Standards

## Context

- **Project:** Internal CRM+ for StarHouse (spiritual/transformational community)
- **Scale:** <10 staff members (internal tool, not public SaaS)
- **Tech Lead:** Ed Burns
- **Standard:** FAANG-level engineering (we build it right, once)

---

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

---

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

### Deployment
- Frontend: Vercel (auto-deploy on push to main)
- Database: Supabase managed

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
Scope: auth, db, ui, api, donors, contacts, imports
```

Examples:
- `fix(donors): Resolve duplicate transactions in import`
- `feat(db): Add email alias matching to contact lookup`
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

---

## Error Handling Standards

### Code Errors
- ✅ Always handle both success and error cases
- ✅ Log errors with context (what operation, what inputs)
- ✅ User-facing errors must be actionable
- ❌ Never swallow errors silently

### Database Errors
```python
try:
    result = db.execute(query, params)
except IntegrityError as e:
    logging.error(f"Row {row_num}: Duplicate key - {record['email']}")
    errors.append(f"Row {row_num}: {e}")
except Exception as e:
    logging.error(f"Row {row_num}: Unexpected error - {e}")
    raise  # Re-raise unexpected errors
```

- ✅ Catch specific exceptions
- ✅ Include row number and record data in error logs
- ✅ Continue processing on recoverable errors (duplicates)
- ✅ Fail fast on unrecoverable errors

---

## Logging Standards

### Log Levels
- **ERROR**: Operation failed, needs attention
- **WARNING**: Unexpected but recoverable (e.g., skipped record)
- **INFO**: Normal operations (import started, counts, completed)
- **DEBUG**: Detailed record-level operations

### Required Format
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/{script_name}_{timestamp}.log"),
        logging.StreamHandler()
    ]
)
```

### Required Log Points
```python
logging.info(f"Operation started: {source}")
logging.info(f"Records to process: {count}")
logging.info(f"Created: {x}, Updated: {y}, Skipped: {z}, Errors: {e}")
logging.info(f"Operation completed in {elapsed}s")
```

- ✅ Log to file in `logs/` directory with timestamp
- ✅ Include source, record counts, timing
- ✅ Log errors with full context (row number, data, reason)
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

### Import Script Tests
```python
# Test validation logic without database
def test_validate_email():
    assert validate_email("user@example.com") == True
    assert validate_email("invalid") == False

def test_parse_amount():
    assert parse_amount("$1,234.56") == 1234.56
```

---

## Deployment Checklist

### Before Push to Main
- [ ] All local checks pass
- [ ] Changes tested manually
- [ ] No console errors
- [ ] Database migrations are idempotent

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
- **Examples:** Can't sign in, can't save data, import failures

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

---

## Prohibited Actions
```
❌ Never DELETE without backup
❌ Never UPDATE without WHERE clause verification
❌ Never deploy without local testing
❌ Never commit with failing builds
❌ Never use production credentials in code
❌ Never skip verification steps
❌ Never guess at root causes
❌ Never make multiple partial fixes
❌ Never re-import without deduplication check
```

---

**Remember:** We're building a small internal tool, but with enterprise-grade quality. Every shortcut creates debt we'll pay later. Do it right, once.
