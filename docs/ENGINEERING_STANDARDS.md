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

## Data Import Standards (Python Scripts)

### Core Requirements

All data import scripts must implement:

#### 1. Dry-Run Mode
```python
# Required: --dry-run flag that shows what would happen without writing
parser.add_argument('--dry-run', action='store_true',
                    help='Show what would be imported without writing to database')
```
- ✅ Default to dry-run (require explicit `--execute` to write)
- ✅ Log all operations that would occur
- ✅ Show record counts and sample data

#### 2. Idempotency
- ✅ Running the same import twice produces the same result
- ✅ Use upsert patterns (INSERT ... ON CONFLICT)
- ✅ Check for existing records before creating
- ❌ Never duplicate data on re-run

#### 3. Validation Before Write
```python
# Validate all records before any database writes
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

#### 4. Transaction Safety
```python
# Wrap bulk operations in transactions
with connection.begin():
    for record in records:
        upsert_record(record)
    # Commit only if all succeed
```
- ✅ Use database transactions for atomicity
- ✅ All-or-nothing for bulk operations
- ✅ Automatic rollback on error

#### 5. Audit Logging
```python
# Required log format
logging.info(f"Import started: {csv_file}")
logging.info(f"Records to process: {len(records)}")
logging.info(f"Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}")
logging.info(f"Import completed in {elapsed_time}s")
```
- ✅ Log to file in `logs/` directory with timestamp
- ✅ Include source file, record counts, timing
- ✅ Log individual record actions at DEBUG level
- ✅ Log errors with full context (row number, data, reason)

#### 6. Verification Queries
```python
# After import, verify database state
def verify_import():
    """Run verification queries and log results."""
    count = db.execute("SELECT COUNT(*) FROM donors WHERE source = 'quickbooks'")
    logging.info(f"Verification: {count} QuickBooks donors in database")
```
- ✅ Run verification after import completes
- ✅ Compare expected vs actual counts
- ✅ Sample data integrity checks

### Import Script Structure

```python
#!/usr/bin/env python3
"""
Import [source] data into [target table].

Usage:
    python import_source.py --dry-run           # Preview changes
    python import_source.py --execute           # Apply changes
    python import_source.py --execute --force   # Skip confirmations
"""

import argparse
import logging
from datetime import datetime

def setup_logging(script_name: str) -> None:
    """Configure logging to file and console."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/{script_name}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', default=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--force', action='store_true')
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging('import_source')

    # 1. Load and validate data
    records = load_csv(CSV_PATH)
    errors = validate_records(records)
    if errors:
        for error in errors:
            logging.error(error)
        sys.exit(1)

    # 2. Preview or execute
    if args.execute:
        if not args.force:
            confirm = input(f"Import {len(records)} records? [y/N] ")
            if confirm.lower() != 'y':
                sys.exit(0)
        import_records(records)
        verify_import()
    else:
        preview_import(records)
        logging.info("Dry run complete. Use --execute to apply changes.")

if __name__ == '__main__':
    main()
```

### CSV Handling Standards

```python
# Required: Explicit encoding and error handling
import pandas as pd

df = pd.read_csv(
    filepath,
    encoding='utf-8',
    dtype=str,  # Read all as strings, convert explicitly
    na_values=['', 'NULL', 'null', 'None'],
    keep_default_na=False
)

# Required: Column validation
expected_columns = ['Name', 'Date', 'Amount', ...]
missing = set(expected_columns) - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")
```

### Contact Matching Standards

When matching CSV records to existing contacts:

```python
# Priority order for matching (highest to lowest confidence)
1. Exact email match (case-insensitive)
2. Exact full name match + phone match
3. Exact full name match + address match
4. Fuzzy name match (>90% similarity) + email domain match

# Required: Log match confidence
logging.info(f"Matched '{csv_name}' to contact {contact_id} via {match_method}")
```

- ✅ Log the matching method used for each record
- ✅ Flag low-confidence matches for review
- ✅ Never auto-merge without high confidence match
- ❌ Never create duplicates without checking

### Error Handling

```python
# Specific exception handling with context
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

## Automated Testing Standards

### Minimum Requirements

Even for a small team, automated tests prevent regressions:

#### 1. Critical Path Tests
```bash
# tests/ directory structure
tests/
  test_auth.py           # Login, logout, session management
  test_data_import.py    # Import script validation logic
  test_api_endpoints.py  # Core API functionality
```

- ✅ Test authentication flows
- ✅ Test import validation functions (unit tests)
- ✅ Test critical database operations

#### 2. Running Tests
```bash
# Add to package.json scripts
"test": "pytest tests/ -v",
"test:watch": "pytest tests/ -v --watch"

# Run before commit
pytest tests/ -v
```

#### 3. Import Script Tests
```python
# Test validation logic without database
def test_validate_email():
    assert validate_email("user@example.com") == True
    assert validate_email("invalid") == False

def test_parse_amount():
    assert parse_amount("$1,234.56") == 1234.56
    assert parse_amount("1234") == 1234.0

def test_match_contact():
    # Test matching logic with mock data
    contacts = [{"id": 1, "email": "test@example.com"}]
    result = find_matching_contact("test@example.com", contacts)
    assert result["id"] == 1
```

### CI Pipeline (Future)

When ready, add GitHub Actions:
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest tests/ -v
```

## Observability Standards

### Structured Logging

Use consistent log format for easy parsing:

```python
import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "script": record.name,
        }
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        return json.dumps(log_data)
```

### Log Levels
- **ERROR**: Operation failed, needs attention
- **WARNING**: Unexpected but recoverable (e.g., skipped record)
- **INFO**: Normal operations (import started, counts, completed)
- **DEBUG**: Detailed record-level operations

### Key Metrics to Log

For every import script:
```python
logging.info("Import summary", extra={
    "source": "quickbooks",
    "file": csv_path,
    "total_records": len(records),
    "created": created_count,
    "updated": updated_count,
    "skipped": skipped_count,
    "errors": error_count,
    "duration_seconds": elapsed
})
```

---

**Remember:** We're building a small internal tool, but with enterprise-grade quality. Every shortcut creates debt we'll pay later. Do it right, once.
