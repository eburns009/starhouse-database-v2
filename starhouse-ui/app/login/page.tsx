'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  // Intercept fetch to debug invalid parameter
  useEffect(() => {
    const originalFetch = window.fetch
    window.fetch = function(...args) {
      console.log('[FETCH INTERCEPTOR] Called with:', {
        url: args[0],
        options: args[1],
        optionsType: typeof args[1],
        optionsKeys: args[1] ? Object.keys(args[1]) : null,
      })

      // Log each option in detail
      if (args[1]) {
        Object.entries(args[1]).forEach(([key, value]) => {
          console.log(`[FETCH INTERCEPTOR] ${key}:`, {
            value,
            type: typeof value,
            constructor: value?.constructor?.name
          })

          // If it's headers, log each header
          if (key === 'headers' && value && typeof value === 'object') {
            console.log('[FETCH INTERCEPTOR] Headers breakdown:')
            Object.entries(value).forEach(([headerKey, headerValue]) => {
              console.log(`  ${headerKey}:`, {
                value: headerValue,
                type: typeof headerValue,
                length: typeof headerValue === 'string' ? headerValue.length : null,
                isValid: typeof headerValue === 'string' || typeof headerValue === 'number'
              })
            })
          }
        })
      }

      return originalFetch.apply(this, args)
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      console.log('[Login] Starting login process...')
      const supabase = createClient()
      console.log('[Login] Supabase client created, calling signInWithPassword...')

      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      console.log('[Login] signInWithPassword completed:', { error })

      if (error) {
        console.error('[Login] Auth error:', error)
        setError(error.message)
        setLoading(false)
      } else {
        console.log('[Login] Success, redirecting...')
        router.push('/')
        router.refresh()
      }
    } catch (err) {
      console.error('[Login] Caught exception:', err)
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary/5 via-background to-secondary/10 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/80">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl">Welcome to StarHouse</CardTitle>
            <CardDescription className="mt-2">
              Sign in to access your dashboard
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="name@starhouse.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
