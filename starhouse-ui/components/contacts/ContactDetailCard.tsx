'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Avatar } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatName, getInitials, formatCurrency, formatDate } from '@/lib/utils'
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Calendar,
  DollarSign,
  CreditCard,
  Loader2,
  ExternalLink,
  User,
} from 'lucide-react'
import type {
  Contact,
  AlternateEmail,
  Transaction,
  SubscriptionWithProduct,
  NameVariant,
  PhoneVariant,
  AddressVariant,
} from '@/lib/types/contact'

interface ContactDetailCardProps {
  contactId: string
  onClose: () => void
}

/**
 * Extract all name variants from contact data
 * FAANG Standard: Pure function, no side effects
 */
function extractNameVariants(contact: Contact): NameVariant[] {
  const variants: NameVariant[] = []

  // Primary name
  if (contact.first_name || contact.last_name) {
    variants.push({
      first_name: contact.first_name,
      last_name: contact.last_name,
      source: contact.source_system,
      label: 'Primary Name',
    })
  }

  // PayPal name
  if (contact.paypal_first_name || contact.paypal_last_name) {
    variants.push({
      first_name: contact.paypal_first_name,
      last_name: contact.paypal_last_name,
      source: 'paypal',
      label: 'PayPal Name',
    })
  }

  // Business name
  if (contact.paypal_business_name) {
    variants.push({
      first_name: contact.paypal_business_name,
      last_name: null,
      source: 'paypal',
      label: 'Business Name',
    })
  }

  // Additional name
  if (contact.additional_name) {
    variants.push({
      first_name: contact.additional_name,
      last_name: null,
      source: contact.additional_name_source || 'unknown',
      label: 'Additional Name',
    })
  }

  return variants
}

/**
 * Extract all phone variants from contact data
 */
function extractPhoneVariants(contact: Contact): PhoneVariant[] {
  const variants: PhoneVariant[] = []

  if (contact.phone) {
    variants.push({
      number: contact.phone,
      source: contact.source_system,
      label: 'Primary Phone',
      country_code: contact.phone_country_code,
    })
  }

  if (contact.paypal_phone && contact.paypal_phone !== contact.phone) {
    variants.push({
      number: contact.paypal_phone,
      source: 'paypal',
      label: 'PayPal Phone',
    })
  }

  return variants
}

/**
 * Check if a string looks like a complete address (not just line 2)
 * FAANG Standard: Data quality heuristics
 */
function looksLikeCompleteAddress(line: string): boolean {
  if (!line) return false

  // Contains street number + street name pattern
  const hasStreetNumber = /^\d+\s+/.test(line.trim())

  // Contains common address indicators
  const hasAddressKeywords = /\b(street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct|circle|blvd|boulevard|box|po box)\b/i.test(line)

  return hasStreetNumber || hasAddressKeywords
}

/**
 * Extract all address variants from contact data
 * Handles cases where address_line_2 contains a separate address
 */
function extractAddressVariants(contact: Contact): AddressVariant[] {
  const variants: AddressVariant[] = []

  // Check if address_line_2 looks like a separate address
  const line2IsSeparateAddress =
    contact.address_line_2 &&
    looksLikeCompleteAddress(contact.address_line_2) &&
    contact.address_line_1 &&
    contact.address_line_2 !== contact.address_line_1

  // Primary address (address_line_1 only if line_2 is separate)
  if (contact.address_line_1) {
    variants.push({
      line_1: contact.address_line_1,
      line_2: line2IsSeparateAddress ? null : contact.address_line_2,
      city: contact.city,
      state: contact.state,
      postal_code: contact.postal_code,
      country: contact.country,
      source: contact.source_system,
      label: 'Primary Address',
    })
  }

  // If address_line_2 is a separate address, add it as alternate
  if (line2IsSeparateAddress) {
    variants.push({
      line_1: contact.address_line_2,
      line_2: null,
      city: contact.city,
      state: contact.state,
      postal_code: contact.postal_code,
      country: contact.country,
      source: contact.source_system,
      label: 'Alternate Address (from line 2)',
    })
  }

  // Additional alternate address fields (if different from above)
  if (contact.address && contact.address !== contact.address_line_1 && contact.address !== contact.address_line_2) {
    variants.push({
      line_1: contact.address,
      line_2: contact.address_2 || null,
      city: null,
      state: null,
      postal_code: null,
      country: null,
      source: contact.source_system,
      label: 'Additional Address',
    })
  }

  // Shipping address
  if (contact.shipping_address_line_1) {
    // Check if shipping line 2 is different from other addresses
    const shippingLine2 =
      contact.shipping_address_line_2 !== contact.address_line_1 &&
      contact.shipping_address_line_2 !== contact.address_line_2 &&
      contact.shipping_address_line_2 !== contact.address
        ? contact.shipping_address_line_2
        : null

    variants.push({
      line_1: contact.shipping_address_line_1,
      line_2: shippingLine2,
      city: null,
      state: null,
      postal_code: null,
      country: null,
      source: 'paypal',
      label: 'Shipping Address',
      status: contact.shipping_address_status,
    })
  }

  return variants
}

/**
 * Format address for display
 */
function formatAddress(address: AddressVariant): string {
  const parts = [
    address.line_1,
    address.line_2,
    [address.city, address.state].filter(Boolean).join(', '),
    address.postal_code,
    address.country,
  ].filter(Boolean)

  return parts.join('\n')
}

export function ContactDetailCard({
  contactId,
  onClose,
}: ContactDetailCardProps) {
  const [contact, setContact] = useState<Contact | null>(null)
  const [alternateEmails, setAlternateEmails] = useState<AlternateEmail[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [subscriptions, setSubscriptions] = useState<SubscriptionWithProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchContactDetails = async () => {
      try {
        const supabase = createClient()

        // Fetch contact
        const { data: contactData, error: contactError } = await supabase
          .from('contacts')
          .select('*')
          .eq('id', contactId)
          .single()

        if (contactError) throw contactError

        // Fetch alternate emails
        const { data: emailsData, error: emailsError } = await supabase
          .from('contact_emails')
          .select('id, email, email_type, is_primary, is_outreach, source, verified')
          .eq('contact_id', contactId)
          .order('is_primary', { ascending: false })
          .order('created_at', { ascending: false })

        if (emailsError) {
          console.error('Error fetching emails:', emailsError)
        }

        // Fetch transactions
        const { data: transactionsData, error: transactionsError } = await supabase
          .from('transactions')
          .select('*')
          .eq('contact_id', contactId)
          .order('transaction_date', { ascending: false })
          .limit(5)

        if (transactionsError) {
          console.error('Error fetching transactions:', transactionsError)
        }

        // Fetch subscriptions with product information (JOIN)
        const { data: subscriptionsData, error: subscriptionsError } = await supabase
          .from('subscriptions')
          .select(`
            *,
            products (
              id,
              name,
              product_type
            )
          `)
          .eq('contact_id', contactId)
          .not('product_id', 'is', null)  // Only show subscriptions with products
          .order('created_at', { ascending: false })

        if (subscriptionsError) {
          console.error('Error fetching subscriptions:', subscriptionsError)
        }

        setContact(contactData)
        setAlternateEmails(emailsData || [])
        setTransactions(transactionsData || [])
        setSubscriptions(subscriptionsData || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contact')
        console.error('Error loading contact:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchContactDetails()
  }, [contactId])

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </Card>
    )
  }

  if (error || !contact) {
    return (
      <Card className="p-8">
        <div className="text-center">
          <p className="text-destructive">{error || 'Contact not found'}</p>
          <Button onClick={onClose} variant="outline" className="mt-4">
            Back to search
          </Button>
        </div>
      </Card>
    )
  }

  // Extract all variants
  const nameVariants = extractNameVariants(contact)
  const phoneVariants = extractPhoneVariants(contact)
  const addressVariants = extractAddressVariants(contact)

  // Calculate stats
  const totalRevenue = transactions
    .filter((t) => t.transaction_type !== 'refund')
    .reduce((sum, t) => sum + Number(t.amount), 0)

  const activeSubscriptions = subscriptions.filter((s) => s.status === 'active')

  return (
    <div className="space-y-4">
      {/* Back Button */}
      <Button variant="ghost" onClick={onClose} className="gap-2">
        <ArrowLeft className="h-4 w-4" />
        Back to search
      </Button>

      {/* Header Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-6">
            <Avatar
              initials={getInitials(contact.first_name, contact.last_name)}
              className="h-20 w-20 text-lg"
            />

            <div className="flex-1 space-y-3">
              <div>
                <h2 className="text-2xl font-bold">
                  {formatName(contact.first_name, contact.last_name)}
                </h2>
                <div className="mt-2 flex flex-wrap gap-2">
                  {contact.email_subscribed && <Badge>Email Subscribed</Badge>}
                  <Badge variant="outline" className="capitalize">
                    {contact.source_system.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">
                Total Revenue
              </span>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalRevenue)}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              {transactions.length}{' '}
              {transactions.length === 1 ? 'transaction' : 'transactions'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">
                Active Subscriptions
              </span>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeSubscriptions.length}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              {subscriptions.length} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">
                Member Since
              </span>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDate(contact.created_at)}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              Source: {contact.source_system}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Contact Information Sections */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Names */}
        {nameVariants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-4 w-4" />
                Names
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {nameVariants.map((variant, idx) => (
                <div key={idx} className="rounded-lg bg-muted/30 p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium">
                        {formatName(variant.first_name, variant.last_name)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {variant.label} • {variant.source}
                      </p>
                    </div>
                    {idx === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Emails */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="h-4 w-4" />
              Email Addresses
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Primary email from contacts table */}
            <div className="rounded-lg bg-muted/30 p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <a
                    href={`mailto:${contact.email}`}
                    className="font-medium hover:text-primary"
                  >
                    {contact.email}
                  </a>
                  <p className="text-xs text-muted-foreground">
                    Primary • {contact.source_system}
                  </p>
                </div>
                <Badge variant="secondary" className="text-xs">
                  Primary
                </Badge>
              </div>
            </div>

            {/* Alternate emails */}
            {alternateEmails.map((altEmail) => (
              <div key={altEmail.id} className="rounded-lg bg-muted/30 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 overflow-hidden">
                    <a
                      href={`mailto:${altEmail.email}`}
                      className="block truncate font-medium hover:text-primary"
                    >
                      {altEmail.email}
                    </a>
                    <div className="flex flex-wrap gap-1 text-xs text-muted-foreground">
                      <span className="capitalize">{altEmail.email_type}</span>
                      <span>• {altEmail.source}</span>
                      {altEmail.verified && <span>• ✓ Verified</span>}
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    {altEmail.is_outreach && (
                      <Badge variant="default" className="text-xs">
                        Outreach
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {alternateEmails.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No alternate emails found
              </p>
            )}
          </CardContent>
        </Card>

        {/* Phones */}
        {phoneVariants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Phone className="h-4 w-4" />
                Phone Numbers
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {phoneVariants.map((variant, idx) => (
                <div key={idx} className="rounded-lg bg-muted/30 p-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <a
                        href={`tel:${variant.number}`}
                        className="font-medium hover:text-primary"
                      >
                        {variant.number}
                      </a>
                      <p className="text-xs text-muted-foreground">
                        {variant.label} • {variant.source}
                        {variant.country_code && ` • ${variant.country_code}`}
                      </p>
                    </div>
                    {idx === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Addresses */}
        {addressVariants.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <MapPin className="h-4 w-4" />
                Addresses
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {addressVariants.map((variant, idx) => (
                <div key={idx} className="rounded-lg bg-muted/30 p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="whitespace-pre-line text-sm font-medium">
                        {formatAddress(variant)}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {variant.label} • {variant.source}
                        {variant.status && ` • ${variant.status}`}
                      </p>
                    </div>
                    {idx === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Primary
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent Transactions */}
      {transactions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between rounded-xl border border-border/50 p-3 transition-colors hover:bg-accent/50"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">
                        {transaction.transaction_type.replace('_', ' ')}
                      </span>
                      <Badge
                        variant={
                          transaction.status === 'completed'
                            ? 'default'
                            : transaction.status === 'failed'
                            ? 'destructive'
                            : 'outline'
                        }
                        className="text-xs"
                      >
                        {transaction.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(transaction.transaction_date)}
                      {transaction.payment_method && ` • ${transaction.payment_method}`}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      {formatCurrency(
                        Number(transaction.amount),
                        transaction.currency
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Subscriptions */}
      {activeSubscriptions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Subscriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeSubscriptions.map((subscription) => (
                <div
                  key={subscription.id}
                  className="flex items-center justify-between rounded-xl border border-border/50 p-3"
                >
                  <div className="space-y-1">
                    <div className="font-medium">
                      {subscription.products?.name || subscription.billing_cycle || 'Subscription'}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {subscription.next_billing_date &&
                        `Next billing: ${formatDate(subscription.next_billing_date)}`}
                    </p>
                  </div>
                  <div className="text-right">
                    {subscription.amount && (
                      <div className="font-semibold">
                        {formatCurrency(
                          Number(subscription.amount),
                          subscription.currency
                        )}
                        <span className="ml-1 text-xs font-normal text-muted-foreground">
                          / {subscription.billing_cycle}
                        </span>
                      </div>
                    )}
                    <Badge variant="default" className="mt-1 text-xs">
                      {subscription.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {contact.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm text-muted-foreground">
              {contact.notes}
            </p>
          </CardContent>
        </Card>
      )}

      {/* External Links */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">External Systems</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {contact.kajabi_id && (
            <div className="flex items-center justify-between rounded-lg bg-muted/30 p-3">
              <div>
                <p className="text-sm font-medium">Kajabi</p>
                <p className="text-xs text-muted-foreground">ID: {contact.kajabi_id}</p>
              </div>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </div>
          )}
          {contact.zoho_id && (
            <div className="flex items-center justify-between rounded-lg bg-muted/30 p-3">
              <div>
                <p className="text-sm font-medium">Zoho CRM</p>
                <p className="text-xs text-muted-foreground">ID: {contact.zoho_id}</p>
              </div>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </div>
          )}
          {contact.mailchimp_id && (
            <div className="flex items-center justify-between rounded-lg bg-muted/30 p-3">
              <div>
                <p className="text-sm font-medium">Mailchimp</p>
                <p className="text-xs text-muted-foreground">
                  ID: {contact.mailchimp_id}
                </p>
              </div>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
