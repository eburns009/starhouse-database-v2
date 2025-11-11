import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Users, Heart, Building, Sparkles, Home } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

const modules = [
  { name: 'Dashboard', icon: Home, href: '/', exact: true },
  { name: 'Contacts', icon: Users, href: '/contacts' },
  { name: 'Membership', icon: Sparkles, href: '/membership' },
  { name: 'Donors', icon: Heart, href: '/donors' },
  { name: 'Venues', icon: Building, href: '/venues' },
]

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border/50 bg-card/30 backdrop-blur-sm">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center border-b border-border/50 px-6">
            <h1 className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-xl font-bold text-transparent">
              StarHouse
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            {modules.map((module) => {
              const Icon = module.icon
              return (
                <Link
                  key={module.href}
                  href={module.href}
                  className={cn(
                    'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200',
                    'text-muted-foreground hover:bg-primary/5 hover:text-primary'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {module.name}
                </Link>
              )
            })}
          </nav>

          {/* User info */}
          <div className="border-t border-border/50 p-4">
            <div className="flex items-center gap-3 rounded-xl bg-secondary/30 px-4 py-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/80 text-xs font-semibold text-white">
                {user.email?.[0].toUpperCase()}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium">{user.email}</p>
                <p className="text-xs text-muted-foreground">Staff Member</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto scrollbar-thin">{children}</main>
    </div>
  )
}
