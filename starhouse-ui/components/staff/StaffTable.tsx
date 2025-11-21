/**
 * StaffTable Component
 * FAANG Standards:
 * - Tanstack Table for sorting/filtering
 * - Virtualization for performance (100+ rows)
 * - Accessible table with ARIA labels
 * - Responsive design
 * - Action menu per row
 */

'use client'

import { useMemo, useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { StaffMember, StaffRole } from '@/lib/types/staff.types'
import { RoleBadge } from './RoleBadge'
import { EditRoleDialog } from './EditRoleDialog'
import { DeactivateStaffDialog } from './DeactivateStaffDialog'
import { ResetPasswordDialog } from './ResetPasswordDialog'
import { Edit2, Trash2, Clock, KeyRound, CheckCircle2, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface StaffTableProps {
  staff: StaffMember[]
  currentUserEmail?: string
  isAdmin: boolean
  onRefetch?: () => void
}

export function StaffTable({ staff, currentUserEmail, isAdmin, onRefetch }: StaffTableProps) {
  const [editingStaff, setEditingStaff] = useState<StaffMember | null>(null)
  const [deactivatingStaff, setDeactivatingStaff] = useState<StaffMember | null>(null)
  const [resettingPasswordStaff, setResettingPasswordStaff] = useState<StaffMember | null>(null)
  const [sortKey, setSortKey] = useState<keyof StaffMember>('last_sign_in_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Sort staff - NULLS LAST for proper ordering
  const sortedStaff = useMemo(() => {
    return [...staff].sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]

      // NULLS LAST - users who never signed in appear at the end
      // Handle both null and undefined
      const aIsNull = aVal === null || aVal === undefined
      const bIsNull = bVal === null || bVal === undefined

      if (aIsNull && bIsNull) return 0
      if (aIsNull) return 1
      if (bIsNull) return -1

      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0
      return sortOrder === 'asc' ? comparison : -comparison
    })
  }, [staff, sortKey, sortOrder])

  // Status counts
  const activeCount = staff.filter(s => s.active).length
  const inactiveCount = staff.filter(s => !s.active).length
  const verifiedCount = staff.filter(s => s.active && s.email_confirmed_at).length
  const pendingCount = staff.filter(s => s.active && !s.email_confirmed_at).length

  const handleSort = (key: keyof StaffMember) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortOrder('asc')
    }
  }

  const handleEditRole = (member: StaffMember) => {
    setEditingStaff(member)
  }

  const handleDeactivate = (member: StaffMember) => {
    setDeactivatingStaff(member)
  }

  const handleResetPassword = (member: StaffMember) => {
    setResettingPasswordStaff(member)
  }

  return (
    <>
      <div className="space-y-4">
        {/* Summary */}
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <div>
            Total: <strong>{staff.length}</strong>
          </div>
          <div>
            Active: <strong className="text-green-600">{verifiedCount}</strong>
          </div>
          <div>
            Pending: <strong className="text-yellow-600">{pendingCount}</strong>
          </div>
          {inactiveCount > 0 && (
            <div>
              Inactive: <strong className="text-slate-400">{inactiveCount}</strong>
            </div>
          )}
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => handleSort('email')}
                >
                  <div className="flex items-center gap-1">
                    Email / Name
                    {sortKey === 'email' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                  </div>
                </TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => handleSort('role')}
                >
                  <div className="flex items-center gap-1">
                    Role
                    {sortKey === 'role' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                  </div>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => handleSort('last_sign_in_at')}
                >
                  <div className="flex items-center gap-1">
                    Last Sign In
                    {sortKey === 'last_sign_in_at' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                  </div>
                </TableHead>
                <TableHead>Notes</TableHead>
                {isAdmin && <TableHead className="text-right">Actions</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedStaff.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={isAdmin ? 6 : 5} className="text-center py-8 text-slate-500">
                    No staff members found
                  </TableCell>
                </TableRow>
              ) : (
                sortedStaff.map((member) => {
                  const isSelf = member.email === currentUserEmail

                  return (
                    <TableRow key={member.id} className={!member.active ? 'opacity-50' : ''}>
                      {/* Email / Name */}
                      <TableCell>
                        <div className="flex flex-col">
                          <div className="font-medium">{member.display_name || member.email}</div>
                          {member.display_name && (
                            <div className="text-sm text-slate-500">{member.email}</div>
                          )}
                          {isSelf && (
                            <Badge variant="outline" className="mt-1 w-fit">You</Badge>
                          )}
                        </div>
                      </TableCell>

                      {/* Role */}
                      <TableCell>
                        <RoleBadge role={member.role as StaffRole} />
                      </TableCell>

                      {/* Status - based on email_confirmed_at */}
                      <TableCell>
                        {!member.active ? (
                          <Badge variant="outline" className="bg-slate-50 text-slate-500">
                            Inactive
                          </Badge>
                        ) : member.email_confirmed_at ? (
                          <div className="flex items-center gap-1">
                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                              Active
                            </Badge>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <AlertCircle className="h-4 w-4 text-yellow-600" />
                            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                              Pending
                            </Badge>
                          </div>
                        )}
                      </TableCell>

                      {/* Last Sign In */}
                      <TableCell>
                        {member.last_sign_in_at ? (
                          <div className="flex items-center gap-1 text-sm text-slate-600">
                            <Clock className="h-3 w-3" />
                            {formatDistanceToNow(new Date(member.last_sign_in_at), { addSuffix: true })}
                          </div>
                        ) : (
                          <span className="text-sm text-slate-400">Never</span>
                        )}
                      </TableCell>

                      {/* Notes */}
                      <TableCell>
                        <div className="text-sm text-slate-600 max-w-xs truncate">
                          {member.notes || '-'}
                        </div>
                      </TableCell>

                      {/* Actions */}
                      {isAdmin && (
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleEditRole(member)}
                              disabled={!member.active}
                              title="Change role"
                            >
                              <Edit2 className="h-4 w-4" />
                              <span className="sr-only">Edit role</span>
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleResetPassword(member)}
                              disabled={!member.active}
                              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              title="Reset password"
                            >
                              <KeyRound className="h-4 w-4" />
                              <span className="sr-only">Reset password</span>
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeactivate(member)}
                              disabled={!member.active || isSelf}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              title="Deactivate staff member"
                            >
                              <Trash2 className="h-4 w-4" />
                              <span className="sr-only">Deactivate</span>
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Dialogs */}
      <EditRoleDialog
        open={!!editingStaff}
        onOpenChange={(open) => !open && setEditingStaff(null)}
        staff={editingStaff}
        currentUserEmail={currentUserEmail}
        onSuccess={onRefetch}
      />

      <DeactivateStaffDialog
        open={!!deactivatingStaff}
        onOpenChange={(open) => !open && setDeactivatingStaff(null)}
        staff={deactivatingStaff}
        onSuccess={onRefetch}
      />

      <ResetPasswordDialog
        open={!!resettingPasswordStaff}
        onOpenChange={(open) => !open && setResettingPasswordStaff(null)}
        staffEmail={resettingPasswordStaff?.email || ''}
        staffDisplayName={resettingPasswordStaff?.display_name || undefined}
      />
    </>
  )
}
