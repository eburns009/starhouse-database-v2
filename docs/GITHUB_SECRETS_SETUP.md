# GitHub Secrets Setup Guide

## Required Secrets for Automated Deployment

To enable automated edge function deployments, you need to configure the following GitHub repository secrets.

---

## 🔑 Secrets to Configure

### 1. SUPABASE_ACCESS_TOKEN

**Purpose:** Authenticates GitHub Actions to deploy edge functions to Supabase

**How to Get:**
1. Go to: https://supabase.com/dashboard/account/tokens
2. Click "Generate new token"
3. Name it: `GitHub Actions Deployment`
4. Copy the token value

**How to Set:**

**Option A: Via GitHub CLI (Recommended)**
```bash
gh secret set SUPABASE_ACCESS_TOKEN --body "sbp_your_token_here"
```

**Option B: Via GitHub Web UI**
1. Go to your repository: https://github.com/eburns009/starhouse-database-v2
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `SUPABASE_ACCESS_TOKEN`
5. Value: Your token from step 1
6. Click **Add secret**

---

### 2. SUPABASE_PROJECT_ID

**Purpose:** Identifies which Supabase project to deploy to

**Value:** `lnagadkqejnopgfxwlkb`

**How to Set:**

**Option A: Via GitHub CLI**
```bash
gh secret set SUPABASE_PROJECT_ID --body "lnagadkqejnopgfxwlkb"
```

**Option B: Via GitHub Web UI**
1. Go to repository Settings → Secrets and variables → Actions
2. Click **New repository secret**
3. Name: `SUPABASE_PROJECT_ID`
4. Value: `lnagadkqejnopgfxwlkb`
5. Click **Add secret**

---

## ✅ Verification

After setting the secrets, verify they're configured:

```bash
# List all secrets (won't show values, just names)
gh secret list
```

You should see:
```
SUPABASE_ACCESS_TOKEN  Updated YYYY-MM-DD
SUPABASE_PROJECT_ID    Updated YYYY-MM-DD
```

---

## 🚀 What Happens After Setup

Once secrets are configured, **every push to main** will automatically:

1. ✅ Detect changes to `supabase/functions/**`
2. ✅ Deploy updated edge functions
3. ✅ Verify deployment succeeded
4. ✅ Show results in GitHub Actions tab

**Manual triggers** are also available:
- Go to Actions tab → Deploy Supabase Edge Functions → Run workflow

---

## 🔒 Security Best Practices

- **Never commit tokens** to git
- **Rotate tokens** every 90 days
- **Use minimal permissions** - only grant what's needed
- **Monitor deployments** in GitHub Actions logs
- **Audit secret access** regularly

---

## 🆘 Troubleshooting

### Secret not working?
1. Verify secret name matches exactly (case-sensitive)
2. Check for extra spaces or line breaks in value
3. Regenerate token if it's expired

### Deployment still failing?
1. Check GitHub Actions logs: Repository → Actions tab
2. Verify Supabase project ID is correct
3. Ensure token has sufficient permissions

---

## 📚 References

- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Supabase CLI Access Tokens](https://supabase.com/docs/guides/cli/managing-config#access-tokens)
- [GitHub Actions Workflows](https://docs.github.com/en/actions/using-workflows)
