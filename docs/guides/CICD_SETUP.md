# CI/CD Pipeline Setup Guide

**Priority:** 🟠 P1 (High)
**Last Updated:** October 30, 2025
**Estimated Time:** 1 day

---

## Overview

**Current State:** Manual deployments ⚠️
**Target State:** Automated CI/CD with quality gates

### Why CI/CD Matters

Without CI/CD:
- ❌ Manual deployments (error-prone)
- ❌ No automated testing before deploy
- ❌ Inconsistent environments
- ❌ Risky deployments

With CI/CD:
- ✅ Automated testing on every commit
- ✅ Consistent deployments
- ✅ Fast feedback loop
- ✅ Easy rollbacks

---

## Pipeline Overview

```
┌─────────┐    ┌──────────┐    ┌────────┐    ┌─────────┐
│  Commit │ -> │ Run Tests│ -> │  Lint  │ -> │ Deploy  │
│ to main │    │ (required│    │  Check │    │to Prod  │
└─────────┘    └──────────┘    └────────┘    └─────────┘
                     │
                     ▼
                ┌──────────┐
                │  If Fail │
                │Block Merge│
                └──────────┘
```

---

## GitHub Actions Setup

### Step 1: Create Workflow Files

**Create: `.github/workflows/ci.yml`**

```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-webhooks:
    name: Test Webhook Functions
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Deno
        uses: denoland/setup-deno@v1
        with:
          deno-version: v1.x

      - name: Run webhook tests
        run: |
          cd supabase/functions
          deno test --allow-env --allow-net --coverage=coverage

      - name: Generate coverage report
        run: |
          cd supabase/functions
          deno coverage coverage --lcov > coverage.lcov

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./supabase/functions/coverage.lcov
          flags: webhooks

  test-python:
    name: Test Python Scripts
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov requests

      - name: Run Python tests
        run: |
          pytest scripts/ -v --cov=scripts --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: python-scripts

  test-web-app:
    name: Test Web Application
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: web-app/package-lock.json

      - name: Install dependencies
        run: |
          cd web-app
          npm ci

      - name: Run tests
        run: |
          cd web-app
          npm test -- --run --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./web-app/coverage/coverage-final.json
          flags: web-app

  lint:
    name: Lint Code
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Lint web app
        run: |
          cd web-app
          npm ci
          npm run lint

      - name: Lint Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: |
          pip install pylint
          pylint scripts/*.py || true  # Don't fail on warnings yet

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run npm audit
        run: |
          cd web-app
          npm audit --audit-level=high

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'

  build-check:
    name: Build Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: web-app/package-lock.json

      - name: Build web app
        run: |
          cd web-app
          npm ci
          npm run build

      - name: Check bundle size
        run: |
          cd web-app
          npm run build
          # Fail if bundle > 500KB
          du -sh dist | awk '{if ($1 > "500K") exit 1}'
```

---

### Step 2: Deployment Workflow

**Create: `.github/workflows/deploy.yml`**

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch: # Allow manual trigger

jobs:
  # Run all tests first
  test:
    uses: ./.github/workflows/ci.yml

  deploy-webhooks:
    name: Deploy Webhook Functions
    needs: test
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Supabase CLI
        uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Deploy Kajabi webhook
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          PROJECT_ID: lnagadkqejnopgfxwlkb
        run: |
          supabase functions deploy kajabi-webhook \
            --project-ref $PROJECT_ID \
            --no-verify-jwt

      - name: Deploy PayPal webhook
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          PROJECT_ID: lnagadkqejnopgfxwlkb
        run: |
          supabase functions deploy paypal-webhook \
            --project-ref $PROJECT_ID \
            --no-verify-jwt

      - name: Deploy Ticket Tailor webhook
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
          PROJECT_ID: lnagadkqejnopgfxwlkb
        run: |
          supabase functions deploy ticket-tailor-webhook \
            --project-ref $PROJECT_ID \
            --no-verify-jwt

      - name: Smoke test webhooks
        run: |
          # Test health endpoint
          curl -f https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/health || exit 1

      - name: Notify deployment
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Webhooks deployed to production ✅'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

  deploy-web-app:
    name: Deploy Web Application
    needs: test
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build
        run: |
          cd web-app
          npm ci
          npm run build
        env:
          VITE_SUPABASE_URL: ${{ secrets.VITE_SUPABASE_URL }}
          VITE_SUPABASE_ANON_KEY: ${{ secrets.VITE_SUPABASE_ANON_KEY }}

      - name: Deploy to Vercel/Netlify
        # Configure based on your hosting choice
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./web-app
```

---

### Step 3: Add GitHub Secrets

1. Go to: https://github.com/your-org/starhouse-database-v2/settings/secrets/actions

2. Add secrets:
   ```
   SUPABASE_ACCESS_TOKEN=<from-supabase-dashboard>
   VITE_SUPABASE_URL=https://lnagadkqejnopgfxwlkb.supabase.co
   VITE_SUPABASE_ANON_KEY=<from-supabase-dashboard>
   SLACK_WEBHOOK=<slack-webhook-url>
   VERCEL_TOKEN=<if-using-vercel>
   ```

---

## Pre-commit Hooks

### Setup Husky

**Install:**
```bash
cd web-app
npm install --save-dev husky lint-staged
npx husky install
```

**Create: `.husky/pre-commit`**
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

echo "🔍 Running pre-commit checks..."

# Run tests
cd web-app && npm test -- --run --bail || exit 1

# Run linter
npm run lint || exit 1

# Format check
npm run format:check || exit 1

echo "✅ Pre-commit checks passed!"
```

**Update `package.json`:**
```json
{
  "scripts": {
    "prepare": "husky install",
    "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx}\"",
    "format:check": "prettier --check \"src/**/*.{js,jsx,ts,tsx}\""
  },
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

---

## Branch Protection Rules

### Configure in GitHub

1. Go to: Settings → Branches → Add rule

2. Branch name pattern: `main`

3. Enable:
   - ✅ Require pull request reviews (1 approval)
   - ✅ Require status checks to pass:
     - `test-webhooks`
     - `test-python`
     - `test-web-app`
     - `lint`
     - `security-scan`
   - ✅ Require branches to be up to date
   - ✅ Do not allow bypassing (even admins)

---

## Deployment Strategy

### Environment Strategy

```
develop → staging → main → production
   ↓          ↓         ↓
   auto      auto   manual (with approval)
```

### Rollback Procedure

**If deployment fails:**

```bash
# Option 1: Revert git commit
git revert HEAD
git push origin main
# CI/CD automatically deploys previous version

# Option 2: Manual rollback
supabase functions deploy kajabi-webhook --version <previous-version>

# Option 3: Roll forward (fix + deploy)
# Fix the issue, commit, push (fastest)
```

---

## Quality Gates

### Must Pass Before Merge

1. ✅ All tests passing (80%+ coverage)
2. ✅ No linting errors
3. ✅ No security vulnerabilities (high/critical)
4. ✅ Bundle size < 500KB
5. ✅ At least 1 code review approval

### Performance Budgets

```json
{
  "budgets": [
    {
      "resourceSizes": [
        { "maxSize": "500kb", "type": "bundle" },
        { "maxSize": "100kb", "type": "initial" }
      ],
      "resourceCounts": [
        { "maxCount": 20, "type": "script" }
      ]
    }
  ]
}
```

---

## Monitoring Deployments

### Add Deployment Tracking

**Notify Sentry:**
```bash
# In deploy workflow
- name: Create Sentry release
  run: |
    curl https://sentry.io/api/0/organizations/$SENTRY_ORG/releases/ \
      -X POST \
      -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
      -H 'Content-Type: application/json' \
      -d "{
        \"version\": \"$GITHUB_SHA\",
        \"projects\": [\"starhouse\"]
      }"
```

**Track in DataDog:**
```bash
- name: Mark deployment in DataDog
  run: |
    curl -X POST "https://api.datadoghq.com/api/v1/events" \
      -H "DD-API-KEY: $DATADOG_API_KEY" \
      -d @- << EOF
    {
      "title": "Deployment to Production",
      "text": "Deployed commit $GITHUB_SHA",
      "tags": ["environment:production", "service:starhouse"]
    }
    EOF
```

---

## Testing the Pipeline

### Test Locally

**Run the same checks CI runs:**

```bash
# Run all checks locally before pushing
./scripts/ci-local.sh
```

**Create: `scripts/ci-local.sh`**
```bash
#!/bin/bash
set -e

echo "🧪 Running local CI checks..."

echo "\n📦 Testing webhooks..."
cd supabase/functions
deno test --allow-env --allow-net

echo "\n🐍 Testing Python..."
cd ../../
pytest scripts/ -v --cov=scripts

echo "\n⚛️  Testing web app..."
cd web-app
npm test -- --run

echo "\n🔍 Linting..."
npm run lint

echo "\n🔒 Security scan..."
npm audit

echo "\n✅ All checks passed! Safe to push."
```

---

## Checklist

### Initial Setup
- [ ] Create `.github/workflows/ci.yml`
- [ ] Create `.github/workflows/deploy.yml`
- [ ] Add GitHub secrets
- [ ] Configure branch protection
- [ ] Set up pre-commit hooks
- [ ] Test pipeline with dummy commit

### Ongoing
- [ ] Monitor CI/CD success rate
- [ ] Keep actions up to date
- [ ] Review failed builds daily
- [ ] Optimize slow tests

---

## Troubleshooting

### Build Fails in CI but Passes Locally

**Cause:** Environment differences

**Fix:**
```bash
# Replicate CI environment locally
docker run -it node:18 bash
# Run tests in container
```

### Deployment Slow (>5 minutes)

**Optimize:**
- Cache dependencies
- Parallelize tests
- Skip unnecessary steps on non-main branches

### Tests Flaky

**Fix:**
- Add retries for network calls
- Use fixed test data
- Avoid time-dependent tests
- Mock external services

---

## Next Steps

1. ✅ Create workflow files
2. ➡️ Add GitHub secrets
3. ➡️ Test pipeline
4. ➡️ Enable branch protection
5. ➡️ Document for team

**Start with:** CI workflow, then add deployment

---

**Related Docs:**
- [Testing Guide](./TESTING_GUIDE.md)
- [Deployment Procedures](./DEPLOYMENT.md)
- [Rollback Guide](./ROLLBACK.md)
