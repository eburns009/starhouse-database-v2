# Staff Authentication Deployment Guide

**Quick deployment instructions for the new authentication system**

---

## Prerequisites

- Supabase CLI installed
- Supabase project configured
- Environment variables set

---

## Deployment Steps

### 1. Deploy Edge Functions

```bash
# Navigate to project root
cd /workspaces/starhouse-database-v2

# Deploy invite function
supabase functions deploy invite-staff-member

# Deploy password reset function
supabase functions deploy reset-staff-password

# Verify deployment
supabase functions list
```

### 2. Set Environment Variables (if not already set)

```bash
# In Supabase dashboard > Edge Functions > Settings
PUBLIC_APP_URL=https://your-app-domain.com
```

### 3. Configure Email Templates (Optional)

In Supabase Dashboard:
1. Go to Authentication > Email Templates
2. Customize "Invite user" template
3. Customize "Reset password" template
4. Save changes

### 4. Deploy Frontend

```bash
cd starhouse-ui
npm run build
# Deploy to your hosting platform (Vercel, etc.)
```

### 5. Verify Deployment

Test each flow:

**Test 1: Add Staff Member**
```bash
# Log in as admin
# Navigate to /staff
# Click "Add Staff Member"
# Fill form and submit
# ✓ Check invitation email received
```

**Test 2: Password Reset**
```bash
# As admin, click password reset icon
# ✓ Verify reset email received
```

**Test 3: Self-Service Password Change**
```bash
# As any user, click profile menu
# Select "Change Password"
# ✓ Verify password updates successfully
```

---

## Rollback Plan

If issues occur:

```bash
# Revert Edge Functions
supabase functions delete invite-staff-member
supabase functions delete reset-staff-password

# Frontend: Use previous deployment
# (Keep existing staff management UI, just won't create auth accounts)
```

---

## Post-Deployment

1. Monitor Edge Function logs for errors
2. Check email delivery rates
3. Verify no orphaned auth accounts
4. Update team documentation

---

## Support

- **Edge Function Logs:** Supabase Dashboard > Edge Functions > Logs
- **Auth Logs:** Supabase Dashboard > Authentication > Users
- **Email Logs:** Supabase Dashboard > Authentication > Logs

---

**Estimated deployment time:** 10-15 minutes
