'use client'

import { useState } from 'react'
import { Avatar } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Mail,
  Phone,
  Building2,
  Copy,
  Check,
  X,
  Pencil,
  Crown,
  UserCheck,
  Heart,
} from 'lucide-react'
import { formatName, getInitials } from '@/lib/utils'
import type { Contact } from '@/lib/types/contact'
import type { DonorSummary, MembershipStatus } from './types'

interface ContactHeaderProps {
  contact: Contact
  donorSummary: DonorSummary | null
  membershipStatus: MembershipStatus | null
  onEdit: () => void
  onClose: () => void
}

/**
 * Contact header with name, badges, and key contact info
 * FAANG Standard: Follows CRM best practices from UI research
 */
export function ContactHeader({
  contact,
  donorSummary,
  membershipStatus,
  onEdit,
  onClose,
}: ContactHeaderProps) {
  const [copiedEmail, setCopiedEmail] = useState(false)

  const handleCopyEmail = async () => {
    try {
      await navigator.clipboard.writeText(contact.email)
      setCopiedEmail(true)
      setTimeout(() => setCopiedEmail(false), 2000)
    } catch (err) {
      console.error('Failed to copy email:', err)
    }
  }

  // Determine donor level badge
  const getDonorBadge = () => {
    if (!donorSummary) return null

    if (donorSummary.is_major_donor) {
      return (
        <Badge className="bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300">
          <Crown className="h-3 w-3 mr-1" />
          Major Donor
        </Badge>
      )
    }

    if (donorSummary.lifetime_amount >= 500) {
      return (
        <Badge className="bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300">
          <Heart className="h-3 w-3 mr-1" />
          Mid-Level
        </Badge>
      )
    }

    if (donorSummary.lifetime_amount > 0) {
      return (
        <Badge variant="secondary">
          <Heart className="h-3 w-3 mr-1" />
          Donor
        </Badge>
      )
    }

    return null
  }

  // Determine membership badge
  const getMembershipBadge = () => {
    if (!membershipStatus) return null

    const status = membershipStatus.membership_status?.toLowerCase()

    if (status === 'active') {
      return (
        <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300">
          <UserCheck className="h-3 w-3 mr-1" />
          Active Member
        </Badge>
      )
    }

    if (status === 'expiring') {
      return (
        <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-300">
          <UserCheck className="h-3 w-3 mr-1" />
          Expiring Soon
        </Badge>
      )
    }

    if (status === 'expired' || status === 'cancelled') {
      return (
        <Badge variant="outline" className="text-muted-foreground">
          Past Member
        </Badge>
      )
    }

    return null
  }

  const donorBadge = getDonorBadge()
  const membershipBadge = getMembershipBadge()

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          {/* Avatar */}
          <Avatar
            initials={getInitials(contact.first_name, contact.last_name)}
            className="h-16 w-16 text-lg flex-shrink-0"
          />

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Name Row */}
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="text-xl font-bold truncate">
                  {formatName(contact.first_name, contact.last_name)}
                </h2>
                {contact.paypal_business_name && (
                  <p className="text-sm text-muted-foreground flex items-center gap-1.5 mt-0.5">
                    <Building2 className="h-3.5 w-3.5" />
                    {contact.paypal_business_name}
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onEdit}
                  className="h-8 w-8 p-0"
                  title="Edit contact"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0"
                  title="Close"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Status Badges */}
            <div className="flex flex-wrap gap-1.5 mt-2">
              {donorBadge}
              {membershipBadge}
              <Badge variant="outline" className="text-xs capitalize">
                {contact.source_system.replace('_', ' ')}
              </Badge>
            </div>

            {/* Contact Methods */}
            <div className="mt-4 space-y-2">
              {/* Email */}
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <a
                  href={`mailto:${contact.email}`}
                  className="text-sm font-mono text-primary hover:underline truncate"
                >
                  {contact.email}
                </a>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 flex-shrink-0"
                  onClick={handleCopyEmail}
                  title="Copy email"
                >
                  {copiedEmail ? (
                    <Check className="h-3 w-3 text-green-600" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              </div>

              {/* Phone */}
              {contact.phone && (
                <div className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  <a
                    href={`tel:${contact.phone}`}
                    className="text-sm font-mono text-primary hover:underline"
                  >
                    {contact.phone}
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
