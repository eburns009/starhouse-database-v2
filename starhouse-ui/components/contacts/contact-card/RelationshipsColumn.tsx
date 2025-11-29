'use client'

import { Badge } from '@/components/ui/badge'
import {
  CreditCard,
  Calendar,
  ShoppingBag,
  TrendingUp,
  Heart,
} from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { CollapsibleSection } from './CollapsibleSection'
import type { TransactionWithProduct, SubscriptionWithProduct } from '@/lib/types/contact'
import type { DonorSummary, MembershipStatus } from './types'

interface RelationshipsColumnProps {
  transactions: TransactionWithProduct[]
  subscriptions: SubscriptionWithProduct[]
  donorSummary: DonorSummary | null
  membershipStatus: MembershipStatus | null
  totalRevenue: number
  totalTransactionCount: number
}

/**
 * Get product name from transaction using multi-source fallback
 */
function getTransactionDisplayName(transaction: TransactionWithProduct): string {
  if (transaction.products?.name) {
    return transaction.products.name
  }
  if (transaction.subscriptions?.products?.name) {
    return transaction.subscriptions.products.name
  }
  if (transaction.quickbooks_memo) {
    return transaction.quickbooks_memo
  }
  if (transaction.raw_source && typeof transaction.raw_source === 'object') {
    const eventName = (transaction.raw_source as Record<string, unknown>).event_name
    if (typeof eventName === 'string' && eventName.trim()) {
      return eventName
    }
  }
  return transaction.transaction_type.replace('_', ' ')
}

/**
 * Right column: Relationships (donations, membership, transactions, purchases)
 * FAANG Standard: Follows two-column layout from UI research
 */
export function RelationshipsColumn({
  transactions,
  subscriptions,
  donorSummary,
  membershipStatus,
  totalRevenue,
  totalTransactionCount,
}: RelationshipsColumnProps) {
  const activeSubscriptions = subscriptions.filter(s => s.status === 'active')

  // Filter donation transactions - check is_donation field if present
  // Using type assertion for fields that may exist in database but not in strict types
  const donationTransactions = transactions.filter(t => {
    return (t as unknown as { is_donation?: boolean }).is_donation === true
  })
  const purchaseTransactions = transactions.filter(t => {
    return (t as unknown as { is_donation?: boolean }).is_donation !== true
  })

  return (
    <div className="space-y-3">
      {/* Donor Summary (conditional - only show if has donations) */}
      {donorSummary && donorSummary.lifetime_amount > 0 && (
        <CollapsibleSection
          title="Giving History"
          icon={<Heart className="h-4 w-4" />}
          defaultOpen={true}
        >
          <div className="space-y-3">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-md bg-muted/50 p-2.5 text-center">
                <p className="text-lg font-bold">{formatCurrency(donorSummary.lifetime_amount)}</p>
                <p className="text-xs text-muted-foreground">Lifetime Giving</p>
              </div>
              <div className="rounded-md bg-muted/50 p-2.5 text-center">
                <p className="text-lg font-bold">{donorSummary.lifetime_count}</p>
                <p className="text-xs text-muted-foreground">Total Gifts</p>
              </div>
              <div className="rounded-md bg-muted/50 p-2.5 text-center">
                <p className="text-lg font-bold">{formatCurrency(donorSummary.ytd_amount)}</p>
                <p className="text-xs text-muted-foreground">YTD Giving</p>
              </div>
              <div className="rounded-md bg-muted/50 p-2.5 text-center">
                <p className="text-lg font-bold">{formatCurrency(donorSummary.average_gift)}</p>
                <p className="text-xs text-muted-foreground">Average Gift</p>
              </div>
            </div>

            {/* Additional Info */}
            <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t border-border">
              {donorSummary.first_gift_date && (
                <p>First gift: {formatDate(donorSummary.first_gift_date)}</p>
              )}
              {donorSummary.last_gift_date && (
                <p>Last gift: {formatDate(donorSummary.last_gift_date)}</p>
              )}
              {donorSummary.largest_gift > 0 && (
                <p>Largest gift: {formatCurrency(donorSummary.largest_gift)}</p>
              )}
            </div>

            {/* Flags */}
            <div className="flex flex-wrap gap-1.5">
              {donorSummary.is_major_donor && (
                <Badge className="text-xs bg-amber-100 text-amber-800">Major Donor</Badge>
              )}
              {donorSummary.do_not_solicit && (
                <Badge variant="destructive" className="text-xs">Do Not Solicit</Badge>
              )}
              {donorSummary.recognition_name && (
                <Badge variant="outline" className="text-xs">
                  Recognition: {donorSummary.recognition_name}
                </Badge>
              )}
            </div>

            {/* Recent Donations */}
            {donationTransactions.length > 0 && (
              <div className="pt-2 border-t border-border">
                <p className="text-xs font-medium text-muted-foreground mb-2">Recent Donations</p>
                <div className="space-y-1.5">
                  {donationTransactions.slice(0, 5).map((txn) => (
                    <div
                      key={txn.id}
                      className="flex items-center justify-between text-sm py-1.5 px-2 rounded bg-muted/30"
                    >
                      <span className="text-muted-foreground">
                        {formatDate(txn.transaction_date)}
                      </span>
                      <span className="font-medium">{formatCurrency(Number(txn.amount))}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>
      )}

      {/* Membership Status (conditional - only show if has membership) */}
      {membershipStatus && (
        <CollapsibleSection
          title="Membership"
          icon={<CreditCard className="h-4 w-4" />}
          defaultOpen={true}
        >
          <div className="space-y-3">
            {/* Status */}
            <div className="flex items-center justify-between">
              <span className="text-sm">Status</span>
              <Badge
                variant={membershipStatus.membership_status === 'active' ? 'default' : 'secondary'}
                className={
                  membershipStatus.membership_status === 'active'
                    ? 'bg-emerald-100 text-emerald-800'
                    : ''
                }
              >
                {membershipStatus.membership_status}
              </Badge>
            </div>

            {/* Details */}
            <div className="text-sm space-y-1.5">
              {membershipStatus.membership_fee > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Fee</span>
                  <span>{formatCurrency(membershipStatus.membership_fee)}/{membershipStatus.billing_cycle || 'period'}</span>
                </div>
              )}
              {membershipStatus.member_since && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Member Since</span>
                  <span>{formatDate(membershipStatus.member_since)}</span>
                </div>
              )}
              {membershipStatus.next_billing_date && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Next Billing</span>
                  <span>{formatDate(membershipStatus.next_billing_date)}</span>
                </div>
              )}
              {membershipStatus.lifetime_value > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Lifetime Value</span>
                  <span className="font-medium">{formatCurrency(membershipStatus.lifetime_value)}</span>
                </div>
              )}
            </div>
          </div>
        </CollapsibleSection>
      )}

      {/* Active Subscriptions */}
      <CollapsibleSection
        title="Subscriptions"
        count={activeSubscriptions.length}
        icon={<Calendar className="h-4 w-4" />}
        defaultOpen={activeSubscriptions.length > 0}
        isEmpty={subscriptions.length === 0}
        emptyMessage="No subscriptions"
      >
        <div className="space-y-2">
          {subscriptions.map((sub) => (
            <div key={sub.id} className="rounded-md border border-border p-2.5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium">
                    {sub.products?.name || 'Subscription'}
                  </p>
                  {sub.products?.product_type && (
                    <p className="text-xs text-muted-foreground capitalize">
                      {sub.products.product_type}
                    </p>
                  )}
                </div>
                <Badge
                  variant={sub.status === 'active' ? 'default' : 'secondary'}
                  className={`text-[10px] ${
                    sub.status === 'active' ? 'bg-emerald-100 text-emerald-800' : ''
                  }`}
                >
                  {sub.status}
                </Badge>
              </div>
              {sub.next_billing_date && (
                <p className="text-xs text-muted-foreground mt-1">
                  {sub.status === 'active' ? 'Renews' : 'Ended'}: {formatDate(sub.next_billing_date)}
                </p>
              )}
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Transaction Summary */}
      <CollapsibleSection
        title="All Transactions"
        count={totalTransactionCount}
        icon={<TrendingUp className="h-4 w-4" />}
        isEmpty={transactions.length === 0}
        emptyMessage="No transactions recorded"
      >
        <div className="space-y-3">
          {/* Summary Stats */}
          <div className="flex items-center justify-between p-2.5 rounded-md bg-muted/50">
            <span className="text-sm text-muted-foreground">Total Revenue</span>
            <span className="text-lg font-bold">{formatCurrency(totalRevenue)}</span>
          </div>

          {/* Recent Transactions */}
          <div className="space-y-1.5">
            {transactions.slice(0, 5).map((txn) => (
              <div
                key={txn.id}
                className="flex items-center justify-between text-sm py-2 px-2.5 rounded border border-border"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{getTransactionDisplayName(txn)}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(txn.transaction_date)}
                    {txn.payment_method && ` • ${txn.payment_method}`}
                  </p>
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  <p className="font-medium">{formatCurrency(Number(txn.amount))}</p>
                  <Badge
                    variant={txn.status === 'completed' ? 'secondary' : 'outline'}
                    className="text-[10px]"
                  >
                    {txn.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>

          {totalTransactionCount > 5 && (
            <p className="text-xs text-muted-foreground text-center">
              Showing 5 of {totalTransactionCount} transactions
            </p>
          )}
        </div>
      </CollapsibleSection>

      {/* Purchases (non-donation transactions with products) */}
      {purchaseTransactions.length > 0 && (
        <CollapsibleSection
          title="Purchases"
          count={purchaseTransactions.length}
          icon={<ShoppingBag className="h-4 w-4" />}
          isEmpty={purchaseTransactions.length === 0}
          emptyMessage="No purchases recorded"
        >
          <div className="space-y-1.5">
            {purchaseTransactions.slice(0, 5).map((txn) => (
              <div
                key={txn.id}
                className="flex items-center justify-between text-sm py-2 px-2.5 rounded border border-border"
              >
                <div className="min-w-0">
                  <p className="font-medium truncate">{getTransactionDisplayName(txn)}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(txn.transaction_date)}</p>
                </div>
                <span className="font-medium flex-shrink-0 ml-2">
                  {formatCurrency(Number(txn.amount))}
                </span>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}
    </div>
  )
}
