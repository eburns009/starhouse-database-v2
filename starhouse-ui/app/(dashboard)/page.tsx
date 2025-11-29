import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Users, TrendingUp, DollarSign, Calendar, AlertTriangle } from 'lucide-react'
import { createClient } from '@/lib/supabase/server'
import { MailingListStats } from '@/components/dashboard/MailingListStats'
import { ValidationFirstExplainer } from '@/components/dashboard/ValidationFirstExplainer'

export default async function DashboardPage() {
  const supabase = createClient()

  // Fetch quick stats
  const { count: contactCount } = await supabase
    .from('contacts')
    .select('*', { count: 'exact', head: true })
    .is('deleted_at', null)

  // Fetch duplicate count
  const { count: duplicateCount } = await supabase
    .from('v_name_based_duplicates')
    .select('*', { count: 'exact', head: true })

  return (
    <div className="container mx-auto p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Welcome Back</h1>
        <p className="text-muted-foreground">Here's what's happening today</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Contacts</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{contactCount?.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">Active contacts in database</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+12</div>
            <p className="text-xs text-muted-foreground">New contacts added</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$12,450</div>
            <p className="text-xs text-muted-foreground">Total this month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Events this week</p>
          </CardContent>
        </Card>
      </div>

      {/* Mailing List Statistics - NEW IMPRESSIVE SECTION */}
      <div className="mt-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold">Mailing List Quality</h2>
          <p className="text-muted-foreground">Address validation and quality metrics for your campaigns</p>
        </div>

        {/* Validation-First Algorithm Explainer */}
        <div className="mb-6">
          <ValidationFirstExplainer />
        </div>

        <MailingListStats />
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <a
              href="/contacts"
              className="group flex items-center gap-4 rounded-xl border-2 border-border/50 p-4 transition-all duration-200 hover:border-primary/40 hover:bg-primary/5"
            >
              <div className="rounded-lg bg-primary/10 p-3">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-medium">Search Contacts</h3>
                <p className="text-sm text-muted-foreground">Find and manage contacts</p>
              </div>
            </a>

            {duplicateCount && duplicateCount > 0 && (
              <a
                href="/contacts/duplicates"
                className="group flex items-center gap-4 rounded-xl border-2 border-yellow-200 bg-yellow-50 p-4 transition-all duration-200 hover:border-yellow-400 hover:bg-yellow-100"
              >
                <div className="rounded-lg bg-yellow-200 p-3">
                  <AlertTriangle className="h-5 w-5 text-yellow-700" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium flex items-center gap-2">
                    Review Duplicates
                    <Badge variant="secondary" className="text-xs">
                      {duplicateCount}
                    </Badge>
                  </h3>
                  <p className="text-sm text-muted-foreground">Merge duplicate contacts</p>
                </div>
              </a>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
