# StarHouse Membership Dashboard

A simple, primitive web app to view and manage contacts and memberships from the StarHouse unified database.

## Features

### 📊 Membership Dashboard (NEW!)
- **Overview Stats**: Total contacts, Program Partners, Individual Members
- **Membership Levels Breakdown**: Visual breakdown by level with percentages
- **Program Partners Table**: Complete list with transaction counts and subscription status
- **Recent Transactions**: Last 10 completed transactions with member details
- **Color-coded Badges**: Visual indicators for membership levels and status

### 📇 Contacts Management
- View all contacts in a beautiful card grid layout
- Search contacts by name or email
- Click any contact to see detailed information
- Filter by tags, subscriptions, and products

### 📥 CSV Import
- Import contact data from CSV files

### 🔍 Database Info
- View database schema and diagnostics

### Technical Features
- Real-time data from Supabase
- Responsive design (works on mobile, tablet, desktop)
- Fast and lightweight (built with React + Vite)

## Prerequisites

- Node.js 18+ installed
- A Supabase account with your Starhouse database deployed
- Your Supabase project URL and anon key

## Setup Instructions

### 1. Get Your Supabase Credentials

1. Go to your Supabase project: https://app.supabase.com/project/lnagadkqejnopgfxwlkb
2. Click on **Settings** (gear icon in sidebar)
3. Click on **API**
4. Copy these two values:
   - **Project URL** (starts with `https://`)
   - **anon public** key (under "Project API keys")

### 2. Configure Environment Variables

1. Open the `.env` file in the `web-app` directory
2. Replace the placeholder values:

```env
VITE_SUPABASE_URL=https://lnagadkqejnopgfxwlkb.supabase.co
VITE_SUPABASE_ANON_KEY=your-actual-anon-key-here
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Run Development Server

```bash
npm run dev
```

The app will open at `http://localhost:5173`

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` folder.

## Deploying to Cloudflare Pages (FREE)

### Option 1: Using Cloudflare Dashboard (Easiest)

1. Go to https://dash.cloudflare.com/
2. Click **Workers & Pages** → **Create application** → **Pages**
3. Connect your GitHub repository
4. Configure build settings:
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - **Root directory:** `web-app`
5. Add environment variables:
   - `VITE_SUPABASE_URL`: Your Supabase URL
   - `VITE_SUPABASE_ANON_KEY`: Your Supabase anon key
6. Click **Save and Deploy**

Your app will be live at `https://your-project.pages.dev` in ~1 minute!

### Option 2: Using Wrangler CLI

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy
npm run build
wrangler pages deploy dist
```

## Deploying to Vercel (Alternative)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Add environment variables in Vercel dashboard:
# - VITE_SUPABASE_URL
# - VITE_SUPABASE_ANON_KEY
```

## Deploying to Netlify (Alternative)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
npm run build
netlify deploy --prod --dir=dist

# Add environment variables in Netlify dashboard
```

## Project Structure

```
web-app/
├── src/
│   ├── components/
│   │   ├── ContactsList.jsx     # Main contacts list component
│   │   └── ContactsList.css     # Styles for contacts list
│   ├── lib/
│   │   └── supabase.js          # Supabase client configuration
│   ├── App.jsx                   # Main app component
│   ├── App.css                   # App styles
│   ├── index.css                 # Global styles
│   └── main.jsx                  # Entry point
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Example environment variables
├── package.json                  # Dependencies
└── vite.config.js                # Vite configuration
```

## How It Works

1. **Data Source**: Contacts are pulled from your Supabase `contacts` table
2. **Real-time**: Uses Supabase's REST API to fetch data
3. **Search**: Client-side filtering for instant results
4. **Details Modal**: Click any contact to see full details

## Adding Features

### Enable Authentication

To add user login (so only authorized users can view contacts):

1. Install Supabase Auth:
```bash
npm install @supabase/auth-ui-react @supabase/auth-ui-shared
```

2. Wrap your app with auth:
```jsx
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'

function App() {
  const [session, setSession] = useState(null)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (!session) {
    return (
      <div style={{ maxWidth: '400px', margin: '100px auto' }}>
        <Auth supabaseClient={supabase} appearance={{ theme: ThemeSupa }} />
      </div>
    )
  }

  return <ContactsList />
}
```

### Add Transaction History

Create a `TransactionsList.jsx` component to show each contact's transaction history.

### Add Export to CSV

Add a button to export filtered contacts to CSV format.

## Costs

- **Development**: FREE
- **Hosting on Cloudflare Pages**: FREE (unlimited bandwidth!)
- **Supabase**: FREE (up to 500K API requests/month)

**Total: $0/month**

## Troubleshooting

### "Error loading contacts"

1. Check your `.env` file has correct Supabase credentials
2. Verify your Supabase project is active
3. Check browser console for detailed errors
4. Ensure the `contacts` table exists in your database

### "No contacts showing"

1. Verify data exists: Go to Supabase → Table Editor → contacts
2. Check Kajabi webhook is working (should be sending data)
3. Try clicking the "Retry" button in the app

### Build errors

1. Delete `node_modules` and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

Once this is working, you can enhance with additional modules:

1. **Events Module** - View event registrations from Ticket Tailor
2. **Donors Module** - Track donations from PayPal
3. ✅ **Memberships Module** - COMPLETE! Manage active subscriptions and Program Partners
4. **Enhanced Dashboard** - Advanced analytics and charts
5. **Member Communication** - Email integration for member outreach

## Membership Dashboard Details

The membership dashboard includes:

**Overview Tab:**
- Total member count by group (Individual vs Program Partner)
- Breakdown by membership level (Nova, Antares, Luminary, Celestial, Astral, etc.)
- Percentage distribution

**Program Partners Tab:**
- Complete list of all 25 Program Partners
- Membership levels: Luminary Partner, Celestial Partner, Astral Partner
- Transaction counts from PayPal import
- Subscription status tracking

**Recent Transactions Tab:**
- Last 10 completed transactions
- Member name, email, and membership level
- Amount and transaction type
- Real-time from PayPal import data

---

**Built with:** React + Vite + Supabase
**Last Updated:** 2025-11-01 (Membership Dashboard Added)
