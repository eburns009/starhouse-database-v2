# StarHouse UI - Setup Guide

**Quick 10-minute setup guide for developers**

---

## Prerequisites

- Node.js 18+ installed
- Supabase project created
- Database credentials handy

---

## Step-by-Step Setup

### 1. Install Dependencies (2 min)

```bash
cd starhouse-ui
npm install
```

### 2. Configure Environment (1 min)

```bash
# Copy template
cp .env.local.example .env.local

# Edit with your credentials
nano .env.local  # or use your preferred editor
```

Fill in:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

**Where to find these:**
- Supabase Dashboard → Settings → API

### 3. Run Database Migrations (3 min)

#### Option A: Supabase Dashboard (easiest)

1. Open Supabase Dashboard → SQL Editor
2. For each migration file (001 → 005):
   - Open file in `sql/migrations/`
   - Copy entire contents
   - Paste in SQL Editor
   - Click "Run"

#### Option B: Command Line

```bash
# Connect via psql
psql your_database_connection_string

# Run each migration
\i sql/migrations/001_add_soft_delete.sql
\i sql/migrations/002_add_audit_log.sql
\i sql/migrations/003_add_jobs_table.sql
\i sql/migrations/004_add_saved_views.sql
\i sql/migrations/005_rls_policies.sql
```

### 4. Create Test User (2 min)

Supabase Dashboard → Authentication → Users:

1. Click "+ Add User"
2. Email: `admin@starhouse.org` (or your email)
3. Password: Choose secure password
4. **Uncheck** "Send email confirmation"
5. Click "Create"

### 5. Start Dev Server (1 min)

```bash
npm run dev
```

Visit: **http://localhost:3000**

---

## Testing Your Setup

### 1. Test Login

1. Go to http://localhost:3000
2. Should redirect to `/login`
3. Enter your test user credentials
4. Should see dashboard

### 2. Test Contact Search

1. Click "Contacts" in sidebar
2. Search for any contact in your database
3. Click a contact to view details

### 3. Verify Database Connection

Check browser console for errors. Should see:
- No CORS errors
- No authentication errors
- Search results loading

---

## Common Issues

### "Invalid API key"
- Check `.env.local` has correct keys
- Restart dev server: `npm run dev`

### "No contacts found"
- Your database might be empty
- Run import scripts from main project
- Or manually add test contact via Supabase Dashboard

### Login redirects to login
- RLS policies not applied
- Run migration 005 again
- Check user was created in Supabase Auth

### Styles look broken
- Clear `.next` folder: `rm -rf .next`
- Restart: `npm run dev`

---

## Next Steps

✅ Setup complete? You're ready to:

1. **Customize Design**
   - Edit colors in `app/globals.css`
   - Modify components in `components/ui/`

2. **Add Features**
   - Build other modules (membership, donors, etc.)
   - Add edit/create contact forms
   - Implement bulk operations

3. **Deploy**
   - Push to GitHub
   - Connect to Vercel
   - Add production env vars

---

## Development Workflow

```bash
# Start dev server
npm run dev

# Type check
npm run type-check

# Lint code
npm run lint

# Build for production
npm run build
```

---

## File Structure Quick Reference

```
starhouse-ui/
├── app/
│   ├── (dashboard)/      # Protected routes
│   │   ├── contacts/     # ← Contact module is here
│   │   └── layout.tsx    # ← Sidebar navigation
│   └── login/            # ← Login page
│
├── components/
│   ├── contacts/         # ← Contact components
│   └── ui/               # ← Reusable UI
│
├── lib/
│   ├── supabase/         # ← Database clients
│   └── types/            # ← TypeScript types
│
└── sql/migrations/       # ← Database changes
```

---

## Support

Stuck? Check:
1. ✅ All migrations ran successfully
2. ✅ `.env.local` has correct credentials
3. ✅ Test user exists in Supabase
4. ✅ Dev server restarted after env changes

Still stuck? Review:
- `README.md` - Full documentation
- `docs/HOW_TO_TEST_RLS.md` - RLS testing
- Browser console for errors

---

**Setup time: ~10 minutes** ⏱️

🤖 Generated with [Claude Code](https://claude.com/claude-code)
