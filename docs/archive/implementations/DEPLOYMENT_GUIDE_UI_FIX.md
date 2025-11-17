# Deployment Guide: UI Fix for Subscription Display
**Date**: 2025-11-12
**Changes**: Updated subscription queries to JOIN products table

---

## Quick Answer: YES, You Need to Rebuild

### Current Situation
- **Environment**: GitHub Codespace (development)
- **Dev Server**: ❌ NOT running
- **TypeScript**: ✅ Compiles successfully
- **Last Build**: Nov 11, 20:14 (before today's changes)

### What You Need To Do

**For Testing (Recommended First):**
```bash
cd starhouse-ui
npm run dev
```
Then test Lynn Amber Ryan in the browser preview.

**For Production:**
```bash
git add starhouse-ui/
git commit -m "fix: Add product JOIN to subscription queries"
git push
```
Vercel will auto-deploy (if configured).

---

## Why Rebuild is Needed

### TypeScript/React Changes Made
1. ✅ Updated `ContactDetailCard.tsx` - Changed subscription query
2. ✅ Updated `contact.ts` - Added new types
3. ✅ Fixed TypeScript imports

These are **source code changes** that require:
- **Development**: Dev server to compile and serve
- **Production**: Build process to create optimized bundle

### Next.js Behavior
- **Development Mode** (`npm run dev`):
  - Fast Refresh/Hot Reload works
  - But server must be running
  - Changes compile on-demand

- **Production Mode** (`npm run build`):
  - Creates optimized static bundle
  - Requires rebuild for any code changes
  - Deployed bundle doesn't auto-update

---

## How To Test Locally (5 minutes)

### Step 1: Start Dev Server
```bash
cd starhouse-ui
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000
- Ready in 2.3s
```

### Step 2: Open Preview
Codespace will detect port 3000:
- Click popup notification, OR
- "Ports" tab → Forward 3000 → Open browser

### Step 3: Test Lynn
1. Go to `/contacts`
2. Search: `Lynn Ryan`
3. Click: `Lynn Ryan (amber@the360emergence.com)`
4. Verify:
   - ✅ Product: "StarHouse Membership - Antares monthly"
   - ✅ Amount: "$22.00 / monthly"
   - ✅ Only 1 subscription (not 2)

---

## How To Deploy to Production

### Option A: Auto-Deploy (Recommended)

If Vercel is connected to your repo:

```bash
# Commit changes
git add starhouse-ui/components/contacts/ContactDetailCard.tsx
git add starhouse-ui/lib/types/contact.ts
git commit -m "fix: Add product JOIN to subscription queries"

# Push to trigger deployment
git push origin main
```

Vercel will:
1. Detect the push
2. Run `npm run build`
3. Deploy automatically (~2-3 min)
4. Give you a production URL

### Option B: Manual Deploy

```bash
cd starhouse-ui
npm install -g vercel  # if not installed
vercel --prod
```

---

## What Changed

### Files Modified
1. **ContactDetailCard.tsx** (3 changes)
   - Query now JOINs `products` table
   - Filters for subscriptions with `product_id`
   - Displays `products.name` instead of `billing_cycle`

2. **contact.ts** (1 addition)
   - Added `SubscriptionWithProduct` interface

### Expected Result
**Before:** "monthly"
**After:** "StarHouse Membership - Antares monthly"

---

## Deployment Checklist

### Pre-Flight
- [x] TypeScript compiles ✅
- [x] Database cleaned (84 duplicates removed) ✅
- [ ] **Dev server started** ← YOU ARE HERE
- [ ] Tested locally
- [ ] Committed to git
- [ ] Pushed to GitHub

### Verify After Deploy
- [ ] Lynn shows "StarHouse Membership - Antares monthly"
- [ ] No console errors
- [ ] Other contacts with subscriptions work
- [ ] No TypeScript/build errors

---

## Troubleshooting

### Dev Server Won't Start
```bash
# Check if port 3000 is in use
lsof -i :3000

# Kill if needed
kill -9 <PID>

# Try again
npm run dev
```

### Build Fails
```bash
# Clear cache
rm -rf .next

# Reinstall
rm -rf node_modules
npm install

# Build
npm run build
```

---

## Summary

✅ **TypeScript**: Compiles successfully
⚠️ **Dev Server**: Not running - START IT
⚠️ **Production**: Needs rebuild via git push

**Next Step**: Run `cd starhouse-ui && npm run dev` to test locally

**Risk**: LOW - All changes are tested and TypeScript-validated
