# CI/CD Setup Guide - Automated Deployments

**Automate your deployments with GitHub Actions**

---

## Overview

This guide sets up automated deployments so that when you push code to GitHub:
- ✅ **Edge Functions** auto-deploy to Supabase
- ✅ **Frontend** auto-deploys to Vercel
- ✅ **No manual steps** required

---

## Prerequisites

- GitHub repository (✅ you already have this)
- Supabase account
- Vercel account

---

## Setup Steps

### Step 1: Get Supabase Credentials (5 minutes)

#### 1.1 Get Access Token
1. Go to: https://supabase.com/dashboard/account/tokens
2. Click: **"Generate new token"**
3. Name: `GitHub Actions`
4. Copy the token (starts with `sbp_...`)
5. **Save this** - you'll need it in Step 3

#### 1.2 Get Project ID
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to: **Settings** → **General**
4. Copy **Project ID** (also called Reference ID)
5. **Save this** - you'll need it in Step 3

---

### Step 2: Get Vercel Credentials (5 minutes)

#### 2.1 Get Vercel Token
1. Go to: https://vercel.com/account/tokens
2. Click: **"Create Token"**
3. Name: `GitHub Actions`
4. Scope: `Full Access` (or limit to specific projects)
5. Copy the token (starts with `vercel_...`)
6. **Save this** - you'll need it in Step 3

#### 2.2 Get Vercel Project IDs
1. Go to: https://vercel.com/dashboard
2. Select your project (starhouse-ui)
3. Go to: **Settings** → **General**
4. Copy:
   - **Project ID** (under "Project Settings")
   - **Organization ID** (under "Organization")
5. **Save these** - you'll need them in Step 3

#### 2.3 Get Supabase Environment Variables
From your `.env.local` file:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

### Step 3: Add Secrets to GitHub (5 minutes)

1. Go to: https://github.com/eburns009/starhouse-database-v2/settings/secrets/actions
2. Click: **"New repository secret"**
3. Add these secrets one by one:

#### Supabase Secrets
```
Name: SUPABASE_ACCESS_TOKEN
Value: sbp_your_token_here

Name: SUPABASE_PROJECT_ID
Value: your_project_id_here
```

#### Vercel Secrets
```
Name: VERCEL_TOKEN
Value: vercel_your_token_here

Name: VERCEL_ORG_ID
Value: your_org_id_here

Name: VERCEL_PROJECT_ID
Value: your_project_id_here
```

#### Frontend Environment Variables
```
Name: NEXT_PUBLIC_SUPABASE_URL
Value: https://your-project.supabase.co

Name: NEXT_PUBLIC_SUPABASE_ANON_KEY
Value: your_anon_key_here
```

---

### Step 4: Test the CI/CD (2 minutes)

#### Option A: Push a Change
```bash
# Make a small change
echo "# Testing CI/CD" >> README.md
git add README.md
git commit -m "test: Trigger CI/CD deployment"
git push
```

#### Option B: Manual Trigger
1. Go to: https://github.com/eburns009/starhouse-database-v2/actions
2. Select workflow: **"Deploy Supabase Edge Functions"**
3. Click: **"Run workflow"** → **"Run workflow"**
4. Repeat for: **"Deploy Frontend to Vercel"**

---

### Step 5: Verify Deployment (2 minutes)

1. **Watch GitHub Actions:**
   - Go to: https://github.com/eburns009/starhouse-database-v2/actions
   - See workflows running in real-time
   - ✅ Should show green checkmarks when done

2. **Verify Supabase:**
   - Go to: https://supabase.com/dashboard/project/_/functions
   - You should see:
     - `invite-staff-member` (deployed)
     - `reset-staff-password` (deployed)

3. **Verify Vercel:**
   - Go to: https://vercel.com/dashboard
   - Check latest deployment
   - Click to view live site

---

## How It Works

### Workflow 1: Supabase Edge Functions

**Triggers:**
- Any push to `main` branch that changes files in `supabase/functions/`
- Manual trigger via GitHub Actions UI

**What it does:**
1. Checks out code
2. Installs Supabase CLI
3. Deploys both Edge Functions
4. Verifies deployment

**Duration:** ~2 minutes

---

### Workflow 2: Vercel Frontend

**Triggers:**
- Any push to `main` branch that changes files in `starhouse-ui/`
- Manual trigger via GitHub Actions UI

**What it does:**
1. Checks out code
2. Installs Node.js dependencies
3. Builds Next.js app
4. Deploys to Vercel production

**Duration:** ~3 minutes

---

## Workflow Files

The CI/CD is configured in:
- `.github/workflows/deploy-supabase.yml` - Edge Functions deployment
- `.github/workflows/deploy-vercel.yml` - Frontend deployment

---

## Testing Your Setup

### Test 1: Edge Function Deployment
1. Make a change to an Edge Function:
   ```bash
   # Add a comment
   echo "// Test change" >> supabase/functions/invite-staff-member/index.ts
   git add .
   git commit -m "test: Update Edge Function"
   git push
   ```
2. Watch GitHub Actions deploy it automatically
3. ✅ Verify in Supabase Dashboard

### Test 2: Frontend Deployment
1. Make a change to the UI:
   ```bash
   # Update a comment
   echo "// Test change" >> starhouse-ui/app/(dashboard)/staff/page.tsx
   git add .
   git commit -m "test: Update frontend"
   git push
   ```
2. Watch GitHub Actions deploy it automatically
3. ✅ Verify on Vercel

---

## Troubleshooting

### Issue: Workflow not triggering

**Solution:**
- Check that secrets are added correctly
- Verify branch name is `main` (not `master`)
- Check GitHub Actions is enabled for your repo

### Issue: Supabase deployment fails

**Common causes:**
- Invalid `SUPABASE_ACCESS_TOKEN`
- Wrong `SUPABASE_PROJECT_ID`
- Token doesn't have required permissions

**Fix:**
1. Regenerate token with full permissions
2. Update secret in GitHub
3. Re-run workflow

### Issue: Vercel deployment fails

**Common causes:**
- Invalid `VERCEL_TOKEN`
- Wrong project/org IDs
- Missing environment variables

**Fix:**
1. Verify all Vercel secrets are correct
2. Check Vercel dashboard for errors
3. Ensure project is linked correctly

---

## Security Best Practices

✅ **Do:**
- Use GitHub Secrets for all credentials
- Rotate tokens periodically (every 90 days)
- Use least-privilege tokens when possible
- Monitor deployment logs for issues

❌ **Don't:**
- Commit tokens to code
- Share tokens publicly
- Use personal tokens for production
- Ignore failed deployments

---

## Monitoring

### GitHub Actions Dashboard
- View all deployments: https://github.com/eburns009/starhouse-database-v2/actions
- Get email notifications on failures (enable in settings)

### Slack Notifications (Optional)
Add Slack integration to get deployment notifications:
1. Create Slack webhook
2. Add to GitHub Actions
3. Get instant alerts

---

## Maintenance

### Updating Workflows

To modify deployment behavior:
1. Edit `.github/workflows/*.yml`
2. Commit and push
3. Workflows update automatically

### Disabling CI/CD

To temporarily disable:
1. Go to: Repository Settings → Actions → General
2. Select: "Disable Actions"

Or disable specific workflows:
1. Go to: Actions tab
2. Select workflow
3. Click: "..." → "Disable workflow"

---

## Next Steps

After setup is complete:

1. **Test the complete flow:**
   - Make a code change
   - Push to GitHub
   - Watch automatic deployment
   - Verify in production

2. **Add more automation:**
   - Run tests before deployment
   - Notify team on Slack
   - Create preview deployments for PRs

3. **Monitor regularly:**
   - Check GitHub Actions weekly
   - Review failed deployments
   - Update tokens before expiration

---

## Benefits of CI/CD

✅ **Faster Deployments:** Push code → Auto-deploy (no manual steps)
✅ **Fewer Errors:** Automated process reduces mistakes
✅ **Audit Trail:** Every deployment logged in GitHub
✅ **Team Collaboration:** Everyone can deploy safely
✅ **Rollback Easy:** Redeploy previous commit to rollback

---

## Summary

**Total Setup Time:** ~20 minutes

**After Setup:**
- Push to `main` → Auto-deploy ✅
- No manual deployment steps needed ✅
- Full visibility in GitHub Actions ✅

**You're now set up for modern, automated deployments!** 🚀
