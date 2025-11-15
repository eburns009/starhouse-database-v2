import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ShieldCheck, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react'

/**
 * Validation-First Scoring Explainer
 * FAANG Standard: Educational component with clean design
 * Explains the validation-first scoring algorithm deployed 2025-11-15
 */
export function ValidationFirstExplainer() {
  return (
    <Card className="border-blue-500/20 bg-gradient-to-br from-blue-500/5 to-background">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/10 p-2">
            <ShieldCheck className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <CardTitle className="text-lg">Validation-First Address Scoring</CardTitle>
            <CardDescription>USPS validation is now the primary quality indicator</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* What Changed */}
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              What Changed
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Our address scoring algorithm now prioritizes USPS validation above all other factors.
              If USPS confirms an address is deliverable (DPV='Y'), it receives a base score of 60-70
              points, making it automatically "High" confidence.
            </p>
          </div>

          {/* How It Works */}
          <div className="rounded-lg bg-muted/50 p-4 space-y-3">
            <h4 className="font-semibold text-sm">How Addresses Are Scored</h4>

            <div className="space-y-2 text-xs">
              <div className="flex items-start gap-2">
                <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 border-emerald-200 shrink-0">
                  Very High
                </Badge>
                <p className="text-muted-foreground leading-relaxed">
                  USPS validated (70pts) + recent transaction (+20pts) + recent update (+10pts) = 75-100pts
                </p>
              </div>

              <div className="flex items-start gap-2">
                <Badge variant="secondary" className="bg-blue-100 text-blue-700 border-blue-200 shrink-0">
                  High
                </Badge>
                <p className="text-muted-foreground leading-relaxed">
                  USPS validated with DPV='Y' confirmation = 60-70pts baseline
                </p>
              </div>

              <div className="flex items-start gap-2">
                <Badge variant="secondary" className="bg-amber-100 text-amber-700 border-amber-200 shrink-0">
                  Medium
                </Badge>
                <p className="text-muted-foreground leading-relaxed">
                  Partial USPS validation (missing secondary address) = 50pts
                </p>
              </div>

              <div className="flex items-start gap-2">
                <Badge variant="secondary" className="bg-red-100 text-red-700 border-red-200 shrink-0">
                  Very Low
                </Badge>
                <p className="text-muted-foreground leading-relaxed">
                  NCOA move detected (customer moved) = 0pts - <strong>DO NOT MAIL</strong>
                </p>
              </div>
            </div>
          </div>

          {/* Key Benefits */}
          <div className="space-y-2">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              Key Benefits
            </h4>
            <ul className="text-sm text-muted-foreground space-y-1 pl-4">
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 shrink-0">✓</span>
                <span>All High/Very High contacts have USPS-confirmed deliverable addresses</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 shrink-0">✓</span>
                <span>NCOA moves automatically excluded (0 points) to prevent wasted mail</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 shrink-0">✓</span>
                <span>Expected deliverability: 95%+ for High confidence addresses</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 shrink-0">✓</span>
                <span>Estimated savings: $2,600/year in prevented wasted postage</span>
              </li>
            </ul>
          </div>

          {/* Warning */}
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex-1 space-y-1">
                <p className="text-xs font-semibold text-amber-700 dark:text-amber-300">
                  Important: Only Mail to High/Very High Confidence
                </p>
                <p className="text-xs text-amber-600/80 dark:text-amber-400/80">
                  Medium and Low confidence addresses may have incomplete validation.
                  NCOA moves (Very Low) should never be mailed to prevent returns and protect sender reputation.
                </p>
              </div>
            </div>
          </div>

          {/* Footer Note */}
          <div className="pt-3 border-t border-border/50">
            <p className="text-xs text-muted-foreground">
              <strong>Algorithm deployed:</strong> November 15, 2025 •
              <a href="/docs/VALIDATION_FIRST_SCORING_DEPLOYMENT_SUCCESS.md" className="text-primary hover:underline ml-1">
                View technical details →
              </a>
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
