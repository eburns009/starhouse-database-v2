# FAANG Code Review - Comprehensive Action Plan
**Date:** 2025-11-09
**Review Scope:** Complete codebase (Python, SQL, Documentation)
**Total Issues Found:** 250+
**Critical (P0):** 35 issues
**High (P1):** 69 issues
**Medium (P2):** 97 issues
**Low (P3):** 49 issues

---

## 🚨 CRITICAL ISSUES - IMMEDIATE ACTION REQUIRED

### 1. **SECURITY: Hardcoded Production Credentials (P0)**

**Impact:** 10/10 - Production database credentials exposed in version control
**Compliance:** Violates PCI-DSS, SOC2, HIPAA
**Timeline:** Fix TODAY

**Files with hardcoded credentials:**
```
scripts/import_paypal_transactions.py
scripts/import_kajabi_data_v2.py
scripts/weekly_import_kajabi_v2.py
scripts/weekly_import_paypal.py
scripts/duplicate_prevention.py
scripts/enrich_contacts_from_zoho.py
scripts/generate_mailing_list.py
```

**Action:**
```bash
# 1. Remove hardcoded credentials
# 2. Use environment variables only
# 3. Update all scripts to:
DB_CONNECTION = os.environ['DATABASE_URL']  # No fallback!

# 4. Add to .env.example (NOT .env)
echo "DATABASE_URL=postgresql://user:pass@host:port/db" >> .env.example

# 5. Verify .env is in .gitignore
grep ".env" .gitignore
```

**Estimated Time:** 2 hours

---

### 2. **SQL SECURITY: Missing RLS on Core Tables (P0)**

**Impact:** 9/10 - All data exposed to authenticated users
**File:** `schema/starhouse_schema_v2.sql`
**Timeline:** This week

**Tables missing RLS:**
- `contacts` (6,563 records with PII)
- `transactions` (8,077 financial records)
- `subscriptions` (411 subscription records)
- `products`, `tags`

**Action:**
```sql
-- Enable RLS on all core tables
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

-- Service role gets full access
CREATE POLICY "Service role full access" ON contacts
  FOR ALL TO service_role USING (true);

-- Repeat for all tables
```

**Estimated Time:** 4 hours (testing included)

---

### 3. **DATA INTEGRITY: Missing Unique Constraints on External IDs (P0)**

**Impact:** 8/10 - Allows duplicate imports, data corruption
**File:** `schema/starhouse_schema_v2.sql`
**Timeline:** This week

**Missing constraints:**
```sql
-- Add unique constraints on external IDs
CREATE UNIQUE INDEX ux_contacts_kajabi_id
  ON contacts(kajabi_id) WHERE kajabi_id IS NOT NULL;

CREATE UNIQUE INDEX ux_products_kajabi_offer_id
  ON products(kajabi_offer_id) WHERE kajabi_offer_id IS NOT NULL;

-- Already exists for subscriptions/transactions
```

**Estimated Time:** 2 hours

---

### 4. **OPERATIONS: No Rollback Procedures (P0)**

**Impact:** 8/10 - Cannot safely deploy migrations
**Files:** 23 out of 29 migration files
**Timeline:** Next 2 weeks

**Action:** Add rollback sections to all migration files:
```sql
-- Migration: add_feature.sql

-- Forward migration
BEGIN;
ALTER TABLE contacts ADD COLUMN new_field TEXT;
CREATE INDEX idx_contacts_new_field ON contacts(new_field);
COMMIT;

-- Rollback procedure (commented out)
/*
-- To rollback, uncomment and run:
BEGIN;
DROP INDEX IF EXISTS idx_contacts_new_field;
ALTER TABLE contacts DROP COLUMN IF EXISTS new_field;
COMMIT;
*/
```

**Estimated Time:** 8 hours (all files)

---

### 5. **PERFORMANCE: Missing Indexes on Foreign Keys (P0)**

**Impact:** 8/10 - Slow queries, table locks during cascade operations
**Files:** Multiple schema files
**Timeline:** This week

**Missing indexes:**
```sql
-- Foreign keys missing indexes
CREATE INDEX idx_transactions_contact_id ON transactions(contact_id);
CREATE INDEX idx_subscriptions_contact_id ON subscriptions(contact_id);
CREATE INDEX idx_subscriptions_product_id ON subscriptions(product_id);
CREATE INDEX idx_events_kajabi_product_id ON events(kajabi_product_id);
CREATE INDEX idx_contact_tags_contact_id ON contact_tags(contact_id);
CREATE INDEX idx_contact_tags_tag_id ON contact_tags(tag_id);
```

**Estimated Time:** 2 hours

---

## 📊 ORGANIZATION: PROJECT CLEANUP (P1)

### 6. **154+ Files in Root Directory**

**Impact:** 7/10 - Makes project unprofessional, hard to navigate
**Timeline:** Next week

**Files to reorganize:**
- 154 markdown files (session notes, handoffs, deployment docs)
- 11 SQL files
- 7 CSV files

**Action:**
```bash
# Create proper structure
mkdir -p docs/{sessions,deployments,analysis,features,reviews}
mkdir -p docs/sessions/{2025-10,2025-11,prompts,handoffs}
mkdir -p docs/analysis/{duplicates,data-quality,integrations}
mkdir -p sql/queries
mkdir -p data/exports/{mailing_lists,contact_info,donor_lists}

# Move files (use script for automation)
# See: docs/FAANG_CODE_REVIEW_ACTION_PLAN.md Section 6
```

**Quick Win Script:**
```bash
# Move all session docs
mv SESSION_*.md docs/sessions/2025-11/
mv HANDOFF_*.md docs/sessions/handoffs/
mv NEXT_SESSION_*.md docs/sessions/prompts/

# Move SQL files
mv *.sql sql/queries/ 2>/dev/null

# Move CSV files
mv *.csv data/exports/mailing_lists/ 2>/dev/null
```

**Estimated Time:** 3 hours

---

### 7. **Duplicate Scripts with Version Suffixes**

**Impact:** 7/10 - Confusion about which version to use
**Timeline:** Next week

**Duplicates to consolidate:**
```
weekly_import_kajabi.py          DELETE
weekly_import_kajabi_improved.py DELETE
weekly_import_kajabi_simple.py   DELETE
weekly_import_kajabi_v2.py       KEEP → rename to weekly_import_kajabi.py

weekly_import_paypal.py          DELETE
weekly_import_paypal_improved.py KEEP → rename to weekly_import_paypal.py

weekly_import_all.py             DELETE
weekly_import_all_v2.py          KEEP → rename to weekly_import_all.py
```

**Estimated Time:** 2 hours

---

## 🔧 CODE QUALITY IMPROVEMENTS (P1/P2)

### 8. **Missing Type Hints (P1)**

**Impact:** 6/10 - Hard to maintain, refactoring is risky
**Files:** 70% of Python scripts
**Timeline:** Next sprint (2 weeks)

**Action:** Add type hints to all functions
```python
# BAD
def process_contact(contact_data, options):
    ...

# GOOD
def process_contact(
    contact_data: Dict[str, Any],
    options: Optional[ContactOptions] = None
) -> ProcessResult:
    ...
```

**Estimated Time:** 16 hours (use automated tools like `monkeytype`)

---

### 9. **No Automated Tests (P0)**

**Impact:** 10/10 - Cannot safely refactor or deploy
**Current Coverage:** 0%
**Timeline:** Next 2 sprints

**Action:**
```bash
# 1. Set up pytest structure
mkdir -p tests/{unit,integration,e2e}
touch tests/__init__.py
touch tests/conftest.py

# 2. Write tests for critical functions
# - Import scripts (test with sample data)
# - Duplicate detection
# - Data validation
# - Database operations

# 3. Set up CI/CD
# - GitHub Actions workflow (already exists)
# - Run tests on PR
# - Require tests for new code

# Target: 80% coverage for critical paths
```

**Estimated Time:** 40 hours (over 2 sprints)

---

### 10. **Schema Version Tracking (P1)**

**Impact:** 7/10 - Cannot track migration state
**Timeline:** This week

**Action:**
```sql
-- Create migrations tracking table
CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_by TEXT DEFAULT current_user,
    checksum TEXT,
    execution_time_ms INTEGER,
    status TEXT CHECK (status IN ('success', 'failed', 'rolled_back'))
);

-- Track each migration
INSERT INTO schema_migrations (version, name, checksum, status)
VALUES ('001', 'starhouse_schema_v2', 'sha256-hash', 'success');
```

**Estimated Time:** 4 hours

---

## 📈 QUICK WINS (Can do in one afternoon)

### Quick Win 1: Remove Hardcoded Credentials (2 hours)
**Impact:** 10/10 Security improvement
```bash
# Find all files with hardcoded credentials
grep -r "***REMOVED***" scripts/

# Replace with environment variable
# Use find/replace in VS Code
```

### Quick Win 2: Move Session Docs (1 hour)
**Impact:** Makes project 10x more navigable
```bash
mkdir -p docs/sessions/2025-11
mv SESSION_*.md HANDOFF_*.md NEXT_SESSION_*.md docs/sessions/2025-11/
```

### Quick Win 3: Add Missing Indexes (2 hours)
**Impact:** Immediate query performance improvement
```bash
./db.sh -f schema/add_missing_foreign_key_indexes.sql
```

### Quick Win 4: Enable RLS on Core Tables (3 hours)
**Impact:** Major security improvement
```bash
./db.sh -f schema/enable_rls_core_tables.sql
```

### Quick Win 5: Consolidate Import Scripts (2 hours)
**Impact:** Eliminates confusion
```bash
# Rename v2 versions to canonical names
# Delete old versions
# Update documentation
```

**Total Quick Wins Time:** 10 hours = One full day
**Total Quick Wins Impact:** Massive improvement in security & organization

---

## 📅 RECOMMENDED TIMELINE (8-Week Plan)

### Week 1: CRITICAL SECURITY
- [ ] Remove hardcoded credentials (2h)
- [ ] Enable RLS on core tables (4h)
- [ ] Add unique constraints on external IDs (2h)
- [ ] Add missing foreign key indexes (2h)
- [ ] **Total: 10 hours**
- **Impact:** Security score 8.8/10 → 9.5/10

### Week 2: OPERATIONS & SAFETY
- [ ] Add rollback procedures to migrations (8h)
- [ ] Implement schema version tracking (4h)
- [ ] Create deployment checklist (2h)
- [ ] **Total: 14 hours**
- **Impact:** Safe deployments, rollback capability

### Week 3: PROJECT ORGANIZATION
- [ ] Move all documentation to proper folders (3h)
- [ ] Consolidate duplicate scripts (2h)
- [ ] Reorganize schema/ and scripts/ folders (4h)
- [ ] Add README files to all directories (3h)
- [ ] **Total: 12 hours**
- **Impact:** Professional project structure

### Week 4: CODE QUALITY - Part 1
- [ ] Add type hints to top 20 functions (8h)
- [ ] Fix bare except clauses (3h)
- [ ] Add input validation (5h)
- [ ] **Total: 16 hours**
- **Impact:** More maintainable code

### Week 5: TESTING INFRASTRUCTURE
- [ ] Set up pytest framework (4h)
- [ ] Write tests for duplicate_prevention (6h)
- [ ] Write tests for critical import functions (8h)
- [ ] **Total: 18 hours**
- **Impact:** Can safely refactor

### Week 6: CODE QUALITY - Part 2
- [ ] Add type hints to remaining functions (12h)
- [ ] Fix SQL injection issues (4h)
- [ ] Standardize error handling (6h)
- [ ] **Total: 22 hours**
- **Impact:** Production-ready code

### Week 7: TESTING & COVERAGE
- [ ] Write integration tests (10h)
- [ ] Achieve 60%+ test coverage (10h)
- [ ] Set up GitHub Actions CI (2h)
- [ ] **Total: 22 hours**
- **Impact:** Automated quality checks

### Week 8: POLISH & DOCUMENTATION
- [ ] Add comprehensive docstrings (8h)
- [ ] Create architecture diagrams (4h)
- [ ] Write deployment runbook (4h)
- [ ] Final code review (4h)
- [ ] **Total: 20 hours**
- **Impact:** Team-ready, well-documented

**TOTAL EFFORT:** 134 hours (~17 working days)
**TIMELINE:** 8 weeks at 16-20 hours/week
**FINAL GRADE:** C+ → A- (FAANG-ready)

---

## 🎯 PRIORITIES BY IMPACT

### Priority 1: SECURITY (MUST DO IMMEDIATELY)
1. Remove hardcoded credentials (2h) - **DO TODAY**
2. Enable RLS on core tables (4h) - **THIS WEEK**
3. Add unique constraints (2h) - **THIS WEEK**
4. Fix SQL injection issues (4h) - **THIS WEEK**

**Total: 12 hours - CRITICAL**

### Priority 2: STABILITY (MUST DO SOON)
1. Add rollback procedures (8h)
2. Schema version tracking (4h)
3. Add missing indexes (2h)
4. Testing framework (18h)

**Total: 32 hours - HIGH PRIORITY**

### Priority 3: MAINTAINABILITY (SHOULD DO)
1. Type hints (20h)
2. Error handling (9h)
3. Project organization (12h)
4. Documentation (8h)

**Total: 49 hours - MEDIUM PRIORITY**

### Priority 4: POLISH (NICE TO HAVE)
1. Code style (8h)
2. Performance optimization (12h)
3. Monitoring improvements (8h)

**Total: 28 hours - LOW PRIORITY**

---

## 📋 CHECKLIST FORMAT (Copy to tracking doc)

```markdown
## WEEK 1: CRITICAL SECURITY
- [ ] Remove hardcoded DB credentials from 7 scripts (2h)
  - [ ] import_paypal_transactions.py
  - [ ] import_kajabi_data_v2.py
  - [ ] weekly_import_kajabi_v2.py
  - [ ] weekly_import_paypal.py
  - [ ] duplicate_prevention.py
  - [ ] enrich_contacts_from_zoho.py
  - [ ] generate_mailing_list.py
  - [ ] Update .env.example
  - [ ] Verify .env in .gitignore

- [ ] Enable RLS on core tables (4h)
  - [ ] Create enable_rls_core_tables.sql
  - [ ] Test with service_role
  - [ ] Test with authenticated user (should fail)
  - [ ] Deploy to production
  - [ ] Verify with health check

- [ ] Add unique constraints on external IDs (2h)
  - [ ] Add ux_contacts_kajabi_id
  - [ ] Add ux_products_kajabi_offer_id
  - [ ] Test duplicate prevention
  - [ ] Deploy to production

- [ ] Add missing foreign key indexes (2h)
  - [ ] Create add_missing_fk_indexes.sql
  - [ ] Test query performance before/after
  - [ ] Deploy to production
  - [ ] Verify with EXPLAIN ANALYZE
```

---

## 🔍 DETECTION: How to Find These Issues in Future

### Automated Checks (Add to CI/CD)

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Checks

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Check for hardcoded credentials
      - name: Scan for secrets
        run: |
          if grep -r "***REMOVED***" .; then
            echo "ERROR: Hardcoded credentials found!"
            exit 1
          fi

      # Check for SQL injection patterns
      - name: Check for SQL injection
        run: |
          if grep -r "f\".*UPDATE.*{" scripts/; then
            echo "WARNING: Potential SQL injection via f-strings"
          fi

  type-checking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run mypy
        run: |
          pip install mypy
          mypy scripts/ --ignore-missing-imports

  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install pytest pytest-cov
          pytest tests/ --cov=scripts --cov-report=html
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=120]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## 📚 RESOURCES

### Tools to Use:
- **bandit**: Security linter for Python
- **mypy**: Static type checker
- **pytest**: Testing framework
- **black**: Code formatter
- **sqlfluff**: SQL linter
- **pre-commit**: Git hook framework

### Install All Tools:
```bash
pip install bandit mypy pytest pytest-cov black sqlfluff pre-commit
```

### Example Commands:
```bash
# Security scan
bandit -r scripts/

# Type check
mypy scripts/ --ignore-missing-imports

# Format code
black scripts/

# Lint SQL
sqlfluff lint schema/

# Run tests with coverage
pytest tests/ --cov=scripts --cov-report=html
```

---

## 🎯 SUCCESS METRICS

### Current State (Baseline):
- **Security Score:** 8.8/10 (hardcoded creds bring it down)
- **Code Quality:** C+
- **Test Coverage:** 0%
- **Documentation:** 6/10
- **Organization:** 3/10
- **Maintainability:** C

### Target State (8 weeks):
- **Security Score:** 9.5/10 (FAANG-level)
- **Code Quality:** A-
- **Test Coverage:** 80%+ (critical paths)
- **Documentation:** 9/10
- **Organization:** 9/10
- **Maintainability:** A

### Measurement:
```bash
# Track progress weekly
echo "Week 1 Progress:" >> PROGRESS.md
echo "- [ ] Security fixes: 3/4 complete" >> PROGRESS.md
echo "- [ ] Test coverage: 5%" >> PROGRESS.md
echo "- [ ] Type hints: 15%" >> PROGRESS.md
```

---

**Created:** 2025-11-09
**Status:** Ready for implementation
**Priority:** HIGH - Security issues require immediate attention
**Estimated ROI:** High (prevents data breaches, enables safe refactoring, improves team velocity)
