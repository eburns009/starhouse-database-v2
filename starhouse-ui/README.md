# StarHouse UI

**Elegant, FAANG-grade contact management system built with Next.js 14**

Beautiful interface designed with modern aesthetics featuring soft purples, warm tones, and refined UI components.

---

## ✨ Features

- **Simple & Powerful Contact Search** - Search by name, email, or phone
- **Elegant Detail Cards** - Beautiful contact profiles with full history
- **Real-time Data** - Supabase integration with SSR support
- **Audit Trail** - Complete logging of all data changes
- **Row Level Security** - Database-level access control
- **Responsive Design** - Works beautifully on all devices

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd starhouse-ui
npm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Supabase credentials:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Run Database Migrations

Apply the new migrations to your Supabase database:

```bash
# Connect to your database
psql your_database_connection_string

# Run migrations in order
\i sql/migrations/001_add_soft_delete.sql
\i sql/migrations/002_add_audit_log.sql
\i sql/migrations/003_add_jobs_table.sql
\i sql/migrations/004_add_saved_views.sql
\i sql/migrations/005_rls_policies.sql
```

**Or via Supabase Dashboard:**
1. Go to SQL Editor
2. Copy/paste each migration file
3. Run them in order (001 → 005)

### 4. Create a Test User

In Supabase Dashboard:
1. Go to **Authentication** → **Users**
2. Click **Add User**
3. Email: `admin@starhouse.org`
4. Password: Choose a secure password
5. Disable email confirmation (for testing)
6. Click **Create user**

### 5. Start Development Server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

---

## 📁 Project Structure

```
starhouse-ui/
├── app/
│   ├── (dashboard)/          # Dashboard routes (protected)
│   │   ├── layout.tsx        # Shared layout with sidebar
│   │   ├── page.tsx          # Dashboard home
│   │   ├── contacts/         # Contact module
│   │   ├── membership/       # Membership module (coming soon)
│   │   ├── donors/           # Donors module (coming soon)
│   │   ├── venues/           # Venues module (coming soon)
│   │   └── offerings/        # Offerings module (coming soon)
│   ├── login/                # Auth pages
│   └── layout.tsx            # Root layout
│
├── components/
│   ├── contacts/             # Contact-specific components
│   │   ├── ContactSearchResults.tsx
│   │   └── ContactDetailCard.tsx
│   └── ui/                   # Reusable UI components
│
├── lib/
│   ├── supabase/             # Supabase clients
│   │   ├── server.ts         # Server Components
│   │   ├── client.ts         # Client Components
│   │   └── middleware.ts     # Auth middleware
│   ├── types/                # TypeScript types
│   └── utils.ts              # Utility functions
│
└── sql/migrations/           # Database migrations
```

---

## 🎨 Design System

### Color Palette

- **Primary:** Soft purple/lavender (`hsl(270, 60%, 65%)`)
- **Secondary:** Warm rose (`hsl(340, 50%, 95%)`)
- **Accent:** Soft peach (`hsl(20, 60%, 95%)`)
- **Background:** Light lavender (`hsl(280, 20%, 99%)`)

### Components

All UI components feature:
- Rounded corners (12-16px)
- Soft shadows
- Smooth transitions (200ms)
- Elegant hover states
- Accessible design (WCAG AA)

---

## 🔐 Security

### Row Level Security (RLS)

The app uses a **simple staff model**:
- All authenticated users have full access
- Service role for backend operations
- Suitable for teams <5-7 people

**When to upgrade:** See `docs/FUTURE_RLS_MIGRATION.md` when your team grows.

### Audit Logging

All data modifications are logged to `audit_log` table:
- Who made the change
- What changed (before/after)
- When it happened
- IP address and user agent

### Testing RLS

See `docs/HOW_TO_TEST_RLS.md` for complete testing guide.

---

## 🛠️ Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### Generate Database Types

After schema changes:

```bash
npm run db:types
```

This generates TypeScript types from your Supabase schema.

---

## 📦 Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Database:** PostgreSQL (Supabase)
- **Auth:** Supabase Auth
- **Styling:** Tailwind CSS
- **Components:** Radix UI primitives
- **Icons:** Lucide React

---

## 🎯 Contact Module Usage

### Search Contacts

1. Navigate to **Contacts** in sidebar
2. Type name, email, or phone in search box
3. Results appear instantly (debounced)
4. Click any contact to view details

### View Contact Details

Contact detail card shows:
- ✅ Full contact information
- ✅ Total revenue and transaction count
- ✅ Active subscriptions
- ✅ Recent transactions (last 5)
- ✅ Notes
- ✅ External system links

---

## 🚢 Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy

Vercel automatically:
- Builds optimized production bundle
- Provisions edge network
- Manages environment variables
- Provides preview deployments

### Environment Variables for Production

```env
NEXT_PUBLIC_SUPABASE_URL=your_production_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_production_service_key
NEXT_PUBLIC_APP_URL=https://your-domain.com
```

---

## 📚 Additional Documentation

- `sql/migrations/` - Database schema changes
- `docs/FUTURE_RLS_MIGRATION.md` - Role-based security guide
- `docs/HOW_TO_TEST_RLS.md` - RLS testing instructions
- `docs/FAANG_CODE_REVIEW_ACTION_PLAN.md` - Code quality standards

---

## 🎨 Customization

### Change Colors

Edit `app/globals.css`:

```css
:root {
  --primary: 270 60% 65%;     /* Your brand color */
  --secondary: 340 50% 95%;   /* Secondary accent */
  /* ... */
}
```

### Add New Module

1. Create folder: `app/(dashboard)/your-module/`
2. Add `page.tsx` for your module
3. Update sidebar in `app/(dashboard)/layout.tsx`

---

## 🤝 Contributing

This is a production system. Major changes should:
1. Follow FAANG standards (see action plan)
2. Include tests
3. Update documentation
4. Be reviewed before deployment

---

## ⚡ Performance

- Server-side rendering for instant page loads
- Optimistic UI updates
- Debounced search (300ms)
- Lazy loading for large lists
- Image optimization with next/image

---

## 📞 Support

For questions or issues:
1. Check documentation in `docs/`
2. Review migration files in `sql/migrations/`
3. Test RLS policies (see `docs/HOW_TO_TEST_RLS.md`)

---

**Built with ❤️ using FAANG-grade standards**

🤖 Generated with [Claude Code](https://claude.com/claude-code)
