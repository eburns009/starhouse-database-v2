# CRITICAL SECURITY FIX - Database Credentials Exposure

**Date:** November 17, 2025
**Status:** 🚨 **CRITICAL - IMMEDIATE ACTION REQUIRED**
**Severity:** HIGH

---

## 🔴 Security Issue Discovered

### Problem:
**Hardcoded database credentials found in 45 Python scripts and committed to git history.**

### Impact:
- **Database credentials** (username, password, host) are **publicly visible** in git history
- **5+ commits** contain hardcoded `DATABASE_URL` with full credentials
- Any person with repository access can see database password
- Credentials need to be **rotated immediately**

### Files Affected:
45 Python scripts in `/scripts/` directory containing:
```python
DATABASE_URL = 'postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres'
```

### Git Commits with Exposed Credentials:
- `c6c6623` - feat: Add Phase 3 duplicate detection scripts
- `a3a0774` - feat: Add Phase 2 contact enrichment scripts
- `e540675` - feat: Add Phase 1 contact data enhancement scripts
- `83d403e` - docs: Add Phase 1 execution reports and manual review guide
- `dc2e44d` - feat: Add data enrichment and analysis scripts

---

## ✅ Immediate Fix Applied

### 1. Created Secure Configuration Module
**File:** [scripts/db_config.py](../scripts/db_config.py)

- Loads credentials from environment variables
- Supports `.env` file with python-dotenv
- Validates database URL format
- Provides helpful error messages
- Never exposes credentials in code

### 2. Created Environment Template
**File:** [.env.example](../.env.example)

- Template for developers to copy
- Documents required variables
- Includes setup instructions
- No actual credentials (safe to commit)

### 3. Created Automated Fix Script
**File:** [scripts/fix_hardcoded_credentials.py](../scripts/fix_hardcoded_credentials.py)

- Scans all 210 Python scripts
- Identifies 45 files with hardcoded credentials
- Automatically replaces with secure `get_database_url()` call
- Adds import statements
- Supports dry-run mode

---

## 🚀 Remediation Steps

### Step 1: Fix All Scripts (IMMEDIATE)
```bash
# Preview what will be fixed
python3 scripts/fix_hardcoded_credentials.py

# Apply fixes to all 45 files
python3 scripts/fix_hardcoded_credentials.py --execute
```

**Expected Result:** All 45 files updated to use environment variables

---

### Step 2: Set Up Environment File (IMMEDIATE)
```bash
# Copy template
cp .env.example .env

# Edit .env and add actual credentials
nano .env  # or vim, code, etc.

# Install python-dotenv
pip install python-dotenv
```

**`.env` file should contain:**
```env
DATABASE_URL=postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres
ENVIRONMENT=production
DEBUG=false
```

**VERIFY `.env` is in `.gitignore`:**
```bash
grep -n "^\.env$" .gitignore
# Should show line 138: .env
```

---

### Step 3: Rotate Database Credentials (CRITICAL)
⚠️ **The exposed password MUST be changed immediately**

**In Supabase Dashboard:**
1. Go to Settings → Database
2. Click "Reset database password"
3. Copy new password
4. Update `.env` file with new credentials
5. Update any production deployments
6. Update team members' `.env` files

**OR via psql:**
```sql
ALTER USER "postgres.lnagadkqejnopgfxwlkb" WITH PASSWORD 'NEW_SECURE_PASSWORD_HERE';
```

---

### Step 4: Remove from Git History (CRITICAL)

**Option A: Force Push with Cleaned History (RECOMMENDED for private repos)**
```bash
# WARNING: This rewrites git history - coordinate with team!

# Use git-filter-repo to remove credentials
pip install git-filter-repo

# Create expressions file
cat > /tmp/expressions.txt << 'EOF'
regex:gqelzN6LRew4Cy9H==>***PASSWORD_REMOVED***
regex:postgresql://postgres\.lnagadkqejnopgfxwlkb:[^@]+@==>postgresql://USER:PASSWORD@
EOF

# Clean history
git filter-repo --replace-text /tmp/expressions.txt --force

# Force push to remote
git push origin --force --all
git push origin --force --tags
```

**Option B: Treat Repository as Compromised**
1. Create new repository
2. Copy only necessary files (without git history)
3. Add `.env` to `.gitignore` from start
4. Use new database credentials
5. Deprecate old repository

---

### Step 5: Verify Fix (IMMEDIATE)
```bash
# Test secure configuration
python3 scripts/db_config.py

# Should show:
# ✓ DATABASE_URL: postgresql://postgres.***@aws-1-us-east-2.pooler.supabase.com:5432/postgres
# ✓ Environment: production
# ✓ Debug: False
```

---

### Step 6: Security Audit (NEXT 24 HOURS)

1. **Check Database Logs**
   - Review Supabase logs for unauthorized access
   - Check for suspicious queries
   - Verify no data exfiltration

2. **Review Access Control**
   - List all database users: `\du` in psql
   - Remove any unauthorized users
   - Verify row-level security policies

3. **Enable Monitoring**
   - Set up database connection alerts
   - Monitor for unusual query patterns
   - Enable failed login attempt alerts

4. **Update Documentation**
   - Document credential rotation procedure
   - Create security incident response plan
   - Train team on secure credential handling

---

## 📊 Current Status

### ✅ Completed:
- [x] Created secure config module (`db_config.py`)
- [x] Created environment template (`.env.example`)
- [x] Created automated fix script (`fix_hardcoded_credentials.py`)
- [x] Verified `.env` is in `.gitignore`
- [x] Documented security issue

### ⏳ Pending (DO BEFORE COMMITTING):
- [ ] Run `fix_hardcoded_credentials.py --execute`
- [ ] Create `.env` file with credentials
- [ ] Install python-dotenv
- [ ] Test scripts with new config
- [ ] Rotate database password in Supabase
- [ ] Update `.env` with new password
- [ ] Remove credentials from git history
- [ ] Verify no credentials in code

---

## 🔒 Prevention Measures

### For This Repository:
1. **Pre-commit Hook** - Reject commits with credentials
2. **Code Review** - Require review for all scripts
3. **CI/CD Check** - Scan for secrets in pipeline
4. **Documentation** - Security best practices guide

### For Team:
1. **Training** - Never hardcode credentials
2. **Tools** - Use password managers (1Password, LastPass)
3. **Secrets Management** - AWS Secrets Manager, HashiCorp Vault
4. **Code Review** - Always review for hardcoded secrets

---

## 📝 Files Created for Fix

1. **[scripts/db_config.py](../scripts/db_config.py)** - Secure database config (100 lines)
2. **[.env.example](../.env.example)** - Environment template (20 lines)
3. **[scripts/fix_hardcoded_credentials.py](../scripts/fix_hardcoded_credentials.py)** - Auto-fix tool (200+ lines)
4. **[docs/SECURITY_FIX_CRITICAL_2025_11_17.md](SECURITY_FIX_CRITICAL_2025_11_17.md)** - This document

---

## ⚠️ BEFORE ANY GIT COMMIT

**RUN THIS CHECKLIST:**

```bash
# 1. Fix all scripts
python3 scripts/fix_hardcoded_credentials.py --execute

# 2. Verify no hardcoded credentials remain
grep -r "gqelzN6LRew4Cy9H" scripts/
# Should return: No results

# 3. Verify .env not committed
git status | grep ".env"
# Should return: Nothing (only .env.example)

# 4. Test a script
python3 scripts/db_config.py
# Should work and show masked password

# 5. Then and ONLY then, commit
git add .
git commit -m "security: Remove hardcoded database credentials

- Replace all hardcoded DATABASE_URL with environment variables
- Add db_config.py for secure credential loading
- Add .env.example template
- Add automated fix script
- All 45 affected scripts updated

BREAKING CHANGE: Scripts now require DATABASE_URL in .env file
"
```

---

## 🆘 If Credentials Already Leaked

**Assume the database is compromised. Follow incident response:**

1. **Immediate** - Rotate password (within 1 hour)
2. **Immediate** - Review recent database access logs
3. **Within 24h** - Audit all data for unauthorized changes
4. **Within 24h** - Review all database users and permissions
5. **Within 48h** - Complete security audit
6. **Within 1 week** - Implement monitoring and alerting

---

**Created By:** Security Audit
**Date:** November 17, 2025
**Priority:** 🚨 CRITICAL
**Status:** Fix Available - Awaiting Execution

**DO NOT COMMIT ANY CODE UNTIL THIS IS RESOLVED**
