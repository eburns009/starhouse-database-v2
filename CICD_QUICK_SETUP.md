# 🚀 CI/CD Quick Setup - 20 Minutes

**Automate deployments: Push code → Auto-deploy to Supabase + Vercel**

---

## ✅ What You Get

After this setup:
- Push to GitHub → Edge Functions deploy automatically
- Push to GitHub → Frontend deploys automatically
- No manual deployment steps ever again

---

## 📋 Setup Checklist (20 minutes)

### □ Step 1: Get Supabase Credentials (5 min)

1. **Get Access Token:**
   - Go to: https://supabase.com/dashboard/account/tokens
   - Click "Generate new token"
   - Name: `GitHub Actions`
   - **Copy token** (starts with `sbp_...`)

2. **Get Project ID:**
   - Go to: https://supabase.com/dashboard → Your Project
   - Settings → General
   - **Copy "Reference ID"**

---

### □ Step 2: Get Vercel Credentials (5 min)

1. **Get Vercel Token:**
   - Go to: https://vercel.com/account/tokens
   - Click "Create Token"
   - Name: `GitHub Actions`
   - **Copy token** (starts with `vercel_...`)

2. **Get Project Info:**
   - Go to: https://vercel.com/dashboard → Your Project
   - Settings → General
   - **Copy:**
     - Project ID
     - Organization ID

---

### □ Step 3: Add Secrets to GitHub (5 min)

Go to: https://github.com/eburns009/starhouse-database-v2/settings/secrets/actions

Click "New repository secret" and add:

```
SUPABASE_ACCESS_TOKEN    = sbp_your_token_here
SUPABASE_PROJECT_ID      = your_project_id_here

VERCEL_TOKEN             = vercel_your_token_here
VERCEL_ORG_ID            = your_org_id_here
VERCEL_PROJECT_ID        = your_vercel_project_id_here

NEXT_PUBLIC_SUPABASE_URL = https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY = your_anon_key_here
```

---

### □ Step 4: Push Workflows to GitHub (2 min)

Workflows are already created! Just push them:

```bash
git add .github/workflows/
git commit -m "ci: Add GitHub Actions for automated deployment"
git push
```

---

### □ Step 5: Test It Works (3 min)

**Option A: Automatic Test**
```bash
# Make a small change
echo "# CI/CD is live!" >> README.md
git add README.md
git commit -m "test: Trigger CI/CD"
git push
```

**Option B: Manual Trigger**
1. Go to: https://github.com/eburns009/starhouse-database-v2/actions
2. Select: "Deploy Supabase Edge Functions"
3. Click: "Run workflow" → "Run workflow"

**Watch it deploy:**
- GitHub Actions tab shows progress in real-time
- ✅ Green checkmark = success!

---

## 🎯 After Setup

### Every time you push to `main`:

```bash
git add .
git commit -m "feat: Add new feature"
git push  # ← This triggers automatic deployment!
```

**What happens automatically:**
1. GitHub Actions runs
2. Edge Functions deploy to Supabase (~2 min)
3. Frontend deploys to Vercel (~3 min)
4. You get email if anything fails
5. ✅ Done!

---

## 📊 Monitoring

**View deployments:**
- GitHub Actions: https://github.com/eburns009/starhouse-database-v2/actions
- Supabase: https://supabase.com/dashboard/project/_/functions
- Vercel: https://vercel.com/dashboard

---

## 🆘 Troubleshooting

### ❌ Workflow fails?

**Check:**
1. All secrets added correctly in GitHub?
2. Tokens have correct permissions?
3. Project IDs are accurate?

**Fix:**
- Update secrets in GitHub
- Re-run workflow (Actions tab → "Re-run jobs")

### ❌ Functions not deploying?

**Verify:**
- `SUPABASE_ACCESS_TOKEN` is valid
- `SUPABASE_PROJECT_ID` is correct
- Check Supabase logs

### ❌ Frontend not deploying?

**Verify:**
- `VERCEL_TOKEN` is valid
- `VERCEL_PROJECT_ID` and `VERCEL_ORG_ID` are correct
- Check Vercel dashboard for errors

---

## 📚 Full Documentation

- **Complete Guide:** [docs/SETUP_CICD.md](docs/SETUP_CICD.md)
- **Troubleshooting:** [docs/SETUP_CICD.md#troubleshooting](docs/SETUP_CICD.md#troubleshooting)

---

## ✨ Benefits

✅ **No manual deployments** - Push code, it deploys automatically
✅ **Faster releases** - 5 minutes from code to production
✅ **Fewer errors** - Automated process is consistent
✅ **Full history** - Every deployment logged in GitHub
✅ **Team ready** - Anyone can deploy safely

---

**Next Step:** Follow the checklist above to set up CI/CD in 20 minutes!
