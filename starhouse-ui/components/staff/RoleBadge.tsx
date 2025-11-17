/**
 * RoleBadge Component
 * FAANG Standards:
 * - Visual role indicators with consistent color coding
 * - Accessible with ARIA labels
 * - Type-safe props
 */

import { Badge } from '@/components/ui/badge'
import type { StaffRole } from '@/lib/types/staff.types'
import { Shield, Edit, Eye } from 'lucide-react'

interface RoleBadgeProps {
  role: StaffRole
  showIcon?: boolean
  className?: string
}

const ROLE_CONFIG: Record<StaffRole, {
  label: string
  variant: 'default' | 'secondary' | 'destructive' | 'outline'
  icon: typeof Shield
  description: string
}> = {
  admin: {
    label: 'Admin',
    variant: 'destructive',
    icon: Shield,
    description: 'Full access + user management'
  },
  full_user: {
    label: 'Full User',
    variant: 'default',
    icon: Edit,
    description: 'View & edit data'
  },
  read_only: {
    label: 'Read Only',
    variant: 'secondary',
    icon: Eye,
    description: 'View only'
  }
}

export function RoleBadge({ role, showIcon = true, className }: RoleBadgeProps) {
  const config = ROLE_CONFIG[role]
  const Icon = config.icon

  return (
    <Badge
      variant={config.variant}
      className={className}
      title={config.description}
      aria-label={`${config.label} role: ${config.description}`}
    >
      {showIcon && <Icon className="mr-1 h-3 w-3" />}
      {config.label}
    </Badge>
  )
}

/**
 * Role description text for tooltips/help text
 */
export function getRoleDescription(role: StaffRole): string {
  return ROLE_CONFIG[role].description
}

/**
 * Get all available roles with descriptions
 * FAANG Standard: Single source of truth for role definitions
 */
export function getAllRoles(): Array<{ value: StaffRole; label: string; description: string }> {
  return (Object.entries(ROLE_CONFIG) as Array<[StaffRole, typeof ROLE_CONFIG[StaffRole]]>).map(
    ([value, config]) => ({
      value,
      label: config.label,
      description: config.description
    })
  )
}
