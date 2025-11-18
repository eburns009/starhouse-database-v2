'use client'

import { createClient } from '@/lib/supabase/client'
import { Users, Heart, Building, Sparkles, Home, Menu, X, Shield, KeyRound, LogOut } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { ChangePasswordDialog } from '@/components/staff/ChangePasswordDialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'

const modules = [
  { name: 'Dashboard', icon: Home, href: '/', exact: true },
  { name: 'Contacts', icon: Users, href: '/contacts' },
  { name: 'Membership', icon: Sparkles, href: '/membership' },
  { name: 'Donors', icon: Heart, href: '/donors' },
  { name: 'Venues', icon: Building, href: '/venues' },
  { name: 'Staff', icon: Shield, href: '/staff' },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [changePasswordOpen, setChangePasswordOpen] = useState(false)

  useEffect(() => {
    const checkUser = async () => {
      const supabase = createClient()
      const { data } = await supabase.auth.getUser()
      if (data.user) {
        setUser(data.user)
      } else {
        window.location.href = '/login'
      }
      setLoading(false)
    }
    checkUser()
  }, [])

  const isActive = (href: string, exact?: boolean) => {
    if (exact) {
      return pathname === href
    }
    return pathname.startsWith(href)
  }

  const handleSignOut = async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  // Show loading state while checking auth
  // Prevents flash of protected content before redirect
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Desktop Sidebar - Hidden on mobile */}
      <aside className="hidden md:flex w-64 border-r border-border/50 bg-card/30 backdrop-blur-sm">
        <div className="flex h-full flex-col w-full">
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
              const active = isActive(module.href, module.exact)
              return (
                <Link
                  key={module.href}
                  href={module.href}
                  className={cn(
                    'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200',
                    active
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-primary/5 hover:text-primary'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {module.name}
                </Link>
              )
            })}
          </nav>

          {/* User info */}
          {user && (
            <div className="border-t border-border/50 p-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="w-full justify-start gap-3 rounded-xl bg-secondary/30 px-4 py-3 h-auto hover:bg-secondary/50"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/80 text-xs font-semibold text-white">
                      {user.email?.[0].toUpperCase()}
                    </div>
                    <div className="flex-1 overflow-hidden text-left">
                      <p className="truncate text-sm font-medium">{user.email}</p>
                      <p className="text-xs text-muted-foreground">Staff Member</p>
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setChangePasswordOpen(true)}>
                    <KeyRound className="mr-2 h-4 w-4" />
                    Change Password
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleSignOut} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Navigation */}
      <div className="md:hidden fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between border-b border-border/50 bg-card/95 backdrop-blur-sm px-4">
        <h1 className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-lg font-bold text-transparent">
          StarHouse
        </h1>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground hover:bg-primary/5 hover:text-primary transition-colors"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Menu Drawer */}
      <aside
        className={cn(
          'md:hidden fixed inset-y-0 left-0 z-50 w-64 border-r border-border/50 bg-card backdrop-blur-sm transition-transform duration-300',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
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
              const active = isActive(module.href, module.exact)
              return (
                <Link
                  key={module.href}
                  href={module.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200',
                    active
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-primary/5 hover:text-primary'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {module.name}
                </Link>
              )
            })}
          </nav>

          {/* User info */}
          {user && (
            <div className="border-t border-border/50 p-4">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="w-full justify-start gap-3 rounded-xl bg-secondary/30 px-4 py-3 h-auto hover:bg-secondary/50"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/80 text-xs font-semibold text-white">
                      {user.email?.[0].toUpperCase()}
                    </div>
                    <div className="flex-1 overflow-hidden text-left">
                      <p className="truncate text-sm font-medium">{user.email}</p>
                      <p className="text-xs text-muted-foreground">Staff Member</p>
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setChangePasswordOpen(true)}>
                    <KeyRound className="mr-2 h-4 w-4" />
                    Change Password
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleSignOut} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto scrollbar-thin pt-16 md:pt-0">{children}</main>

      {/* Change Password Dialog */}
      <ChangePasswordDialog
        open={changePasswordOpen}
        onOpenChange={setChangePasswordOpen}
      />
    </div>
  )
}
