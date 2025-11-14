import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { createClient } from '@/lib/supabase/server'
import { Mail, CheckCircle, AlertCircle, TrendingUp, Download, MapPin } from 'lucide-react'
import { CONFIDENCE_LEVELS } from '@/lib/constants/scoring'
import { calculateMailingStatistics, calculatePercentage } from '@/lib/utils/mailingStatistics'
import type { MailingListEntry } from '@/lib/types/mailing'

/**
 * Mailing List Statistics Component
 * FAANG Standard: Server-side data fetching with proper error handling
 */
export async function MailingListStats() {
  const supabase = createClient()

  // Fetch mailing list statistics with error handling
  const { data: stats, error } = await supabase
    .from('mailing_list_priority')
    .select('confidence, billing_score, shipping_score, recommended_address')
    .returns<MailingListEntry[]>()

  // Error state
  if (error) {
    console.error('[MailingListStats] Database query failed:', error)
    return (
      <Card className="border-destructive/50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p className="text-sm font-medium">Unable to load mailing statistics. Please try again later.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Empty state
  if (!stats || stats.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Mail className="h-5 w-5" />
            <p className="text-sm">No mailing data available yet.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate statistics (optimized single-pass algorithm)
  const statistics = calculateMailingStatistics(stats)
  const { total, confidenceCounts, recommendBilling, recommendShipping, avgScore, readyToMail, readyPercentage } = statistics

  // Build confidence level display data with calculated percentages
  const confidenceLevels = CONFIDENCE_LEVELS.map((level) => {
    const confidenceKey = level.label.toLowerCase().replace(' ', '_') as keyof typeof confidenceCounts
    const count = confidenceCounts[confidenceKey] || 0
    return {
      ...level,
      count,
      percentage: calculatePercentage(count, total),
    }
  })

  return (
    <div className="space-y-6">
      {/* Hero Stats */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Ready to Mail - Primary CTA */}
        <Card className="relative overflow-hidden border-2 border-primary/20 bg-gradient-to-br from-primary/5 via-primary/3 to-background">
          <div className="absolute right-0 top-0 h-32 w-32 translate-x-8 -translate-y-8 rounded-full bg-primary/10 blur-2xl" />
          <CardHeader className="relative">
            <div className="flex items-center justify-between">
              <Mail className="h-8 w-8 text-primary" />
              <Badge className="bg-primary text-primary-foreground border-0 px-3 py-1">
                Ready
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="relative">
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold">{readyToMail.toLocaleString()}</span>
                <span className="text-2xl font-semibold text-muted-foreground">
                  / {total.toLocaleString()}
                </span>
              </div>
              <p className="text-sm font-medium text-muted-foreground">Ready for Mailing</p>
              <div className="flex items-center gap-2 pt-2">
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-primary/20">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-primary/80 transition-all duration-500"
                    style={{ width: `${readyPercentage}%` }}
                  />
                </div>
                <span className="text-sm font-bold text-primary">{readyPercentage}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Average Quality Score */}
        <Card className="border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-background">
          <CardHeader>
            <div className="flex items-center justify-between">
              <TrendingUp className="h-8 w-8 text-emerald-600" />
              <CheckCircle className="h-5 w-5 text-emerald-600/50" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold">{avgScore}</span>
                <span className="text-2xl font-semibold text-muted-foreground">/ 100</span>
              </div>
              <p className="text-sm font-medium text-muted-foreground">Average Quality Score</p>
              <div className="flex gap-1 pt-2">
                {[...Array(10)].map((_, i) => (
                  <div
                    key={i}
                    className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                      i < Math.round(avgScore / 10)
                        ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                        : 'bg-muted'
                    }`}
                  />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address Recommendations */}
        <Card className="border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-background">
          <CardHeader>
            <div className="flex items-center justify-between">
              <MapPin className="h-8 w-8 text-blue-600" />
              <AlertCircle className="h-5 w-5 text-blue-600/50" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm font-medium text-muted-foreground">Recommended Addresses</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Billing</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-blue-500"
                        style={{ width: `${calculatePercentage(recommendBilling, total)}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-blue-600">
                      {calculatePercentage(recommendBilling, total)}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Shipping</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-purple-500"
                        style={{ width: `${calculatePercentage(recommendShipping, total)}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-purple-600">
                      {calculatePercentage(recommendShipping, total)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Confidence Level Breakdown */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Address Quality Distribution</CardTitle>
              <CardDescription>Confidence levels based on validation, recency, and transaction history</CardDescription>
            </div>
            <a
              href="/contacts"
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:bg-primary/90"
            >
              <Download className="h-4 w-4" />
              Export List
            </a>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {confidenceLevels.map((level) => (
              <div key={level.label} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`h-3 w-3 rounded-full ${level.color}`} />
                    <span className="font-medium">{level.label}</span>
                    <span className="text-sm text-muted-foreground">· {level.description}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-muted-foreground">
                      {level.count.toLocaleString()} contacts
                    </span>
                    <Badge className={`${level.bgColor} ${level.borderColor} ${level.textColor} border font-semibold`}>
                      {level.percentage}%
                    </Badge>
                  </div>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-muted/50">
                  <div
                    className={`h-full rounded-full ${level.color} transition-all duration-700 ease-out`}
                    style={{ width: `${level.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="mt-6 rounded-xl border border-border/50 bg-muted/30 p-4">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <CheckCircle className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold">
                  {readyToMail.toLocaleString()} addresses ready for your next mailing campaign
                </p>
                <p className="text-xs text-muted-foreground">
                  {confidenceCounts.very_high.toLocaleString()} premium quality addresses with recent validation and transaction history
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="group cursor-pointer transition-all hover:border-primary/40 hover:shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-emerald-500/10 p-4 transition-all group-hover:bg-emerald-500/20">
                <Mail className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">Export High-Quality List</h3>
                <p className="text-sm text-muted-foreground">
                  {readyToMail.toLocaleString()} contacts ready for mail merge
                </p>
              </div>
              <Download className="h-5 w-5 text-muted-foreground transition-all group-hover:text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="group cursor-pointer transition-all hover:border-blue-500/40 hover:shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-blue-500/10 p-4 transition-all group-hover:bg-blue-500/20">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">Validate Addresses</h3>
                <p className="text-sm text-muted-foreground">
                  Run USPS validation to improve scores
                </p>
              </div>
              <CheckCircle className="h-5 w-5 text-muted-foreground transition-all group-hover:text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
