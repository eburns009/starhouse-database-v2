import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { createClient } from '@/lib/supabase/server'
import { Mail, CheckCircle, AlertCircle, TrendingUp, AlertTriangle, ShieldCheck } from 'lucide-react'
import { CONFIDENCE_LEVELS } from '@/lib/constants/scoring'
import { calculateMailingStatistics, calculatePercentage } from '@/lib/utils/mailingStatistics'
import type { MailingListEntry } from '@/lib/types/mailing'
import { ExportHighConfidenceButton } from './ExportMailingListButton'

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

  // Fetch NCOA statistics (contacts table)
  const { data: ncoaData } = await supabase
    .from('contacts')
    .select('ncoa_move_date, address_validated')
    .not('ncoa_move_date', 'is', null)

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
  const { total, confidenceCounts, avgScore, readyToMail, readyPercentage } = statistics

  // Calculate NCOA statistics
  const ncoaMoveCount = ncoaData?.length || 0
  const ncoaPercentage = total > 0 ? Math.round((ncoaMoveCount / total) * 100) : 0

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

        {/* NCOA Moves - Alert Status */}
        <Card className={`border-2 ${ncoaMoveCount > 0 ? 'border-destructive/30 bg-gradient-to-br from-destructive/10 to-background' : 'border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-background'}`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              {ncoaMoveCount > 0 ? (
                <AlertTriangle className="h-8 w-8 text-destructive" />
              ) : (
                <ShieldCheck className="h-8 w-8 text-emerald-600" />
              )}
              <Badge className={ncoaMoveCount > 0 ? 'bg-destructive' : 'bg-emerald-600'}>
                {ncoaMoveCount > 0 ? 'Action Required' : 'All Clear'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold">{ncoaMoveCount.toLocaleString()}</span>
                <span className="text-2xl font-semibold text-muted-foreground">
                  / {total.toLocaleString()}
                </span>
              </div>
              <p className="text-sm font-medium text-muted-foreground">
                {ncoaMoveCount > 0 ? 'NCOA Moves Detected' : 'No Recent Moves'}
              </p>
              {ncoaMoveCount > 0 && (
                <div className="mt-3 rounded-lg bg-destructive/10 p-2">
                  <p className="text-xs font-medium text-destructive">
                    ⚠️ {ncoaMoveCount} contact{ncoaMoveCount !== 1 ? 's' : ''} moved to new address
                  </p>
                </div>
              )}
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
              <CardDescription>
                Validation-first scoring: USPS confirmation is proof of deliverability
              </CardDescription>
            </div>
            <ExportHighConfidenceButton />
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
                  {readyToMail.toLocaleString()} USPS-validated addresses ready for your next mailing campaign
                </p>
                <p className="text-xs text-muted-foreground">
                  All addresses in High and Very High tiers have USPS confirmation of deliverability
                  {ncoaMoveCount > 0 && (
                    <span className="text-destructive font-medium"> • {ncoaMoveCount} NCOA moves excluded for protection</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* NCOA Details Alert (if moves detected) */}
      {ncoaMoveCount > 0 && (
        <Card className="border-2 border-destructive/30 bg-destructive/5">
          <CardHeader>
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-destructive" />
              <div>
                <CardTitle className="text-lg text-destructive">NCOA Moves Detected</CardTitle>
                <CardDescription>
                  National Change of Address updates from USPS
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg bg-background border border-destructive/20 p-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-1">Contacts Moved</div>
                    <div className="text-2xl font-bold text-destructive">{ncoaMoveCount.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-1">Percentage</div>
                    <div className="text-2xl font-bold text-destructive">{ncoaPercentage}%</div>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 p-3">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  <strong>Action Required:</strong> Review and update addresses before your next mailing campaign to avoid undeliverable mail and wasted costs.
                </p>
              </div>

              <div className="text-xs text-muted-foreground">
                <strong>What is NCOA?</strong> The National Change of Address (NCOA) database is maintained by the USPS and contains address changes filed by individuals and businesses. Regular NCOA processing helps maintain list accuracy and reduce waste.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
              <Mail className="h-5 w-5 text-muted-foreground transition-all group-hover:text-primary" />
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
