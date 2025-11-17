/**
 * EditRoleDialog Component
 * FAANG Standards:
 * - Confirmation before role changes
 * - Shows role transition clearly
 * - Prevents invalid transitions
 * - Accessible with proper ARIA labels
 */

'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useStaffActions } from '@/lib/hooks/useStaffActions'
import type { StaffMember, StaffRole } from '@/lib/types/staff.types'
import { getAllRoles, RoleBadge } from './RoleBadge'
import { isRoleTransitionAllowed } from '@/lib/validations/staff'
import { Loader2, AlertTriangle, ArrowRight } from 'lucide-react'

interface EditRoleDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  staff: StaffMember | null
  currentUserEmail?: string
  onSuccess?: () => void
}

export function EditRoleDialog({
  open,
  onOpenChange,
  staff,
  currentUserEmail,
  onSuccess
}: EditRoleDialogProps) {
  const [newRole, setNewRole] = useState<StaffRole | null>(null)

  const { changeRole, isChangingRole, error, clearError } = useStaffActions(() => {
    onSuccess?.()
    handleClose()
  })

  const handleClose = () => {
    setNewRole(null)
    clearError()
    onOpenChange(false)
  }

  const handleSubmit = async () => {
    if (!staff || !newRole) return

    await changeRole(staff.email, newRole)
  }

  if (!staff) return null

  const roles = getAllRoles()
  const isSelf = staff.email === currentUserEmail
  const selectedNewRole = newRole || staff.role as StaffRole

  // Check if transition is allowed
  const transition = isRoleTransitionAllowed(
    staff.role,
    selectedNewRole,
    isSelf
  )

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Change Staff Role</DialogTitle>
          <DialogDescription>
            Update permissions for {staff.display_name || staff.email}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Current Role */}
          <div className="rounded-md bg-slate-100 p-3">
            <div className="text-sm font-medium text-slate-700 mb-1">Current Role</div>
            <RoleBadge role={staff.role as StaffRole} />
          </div>

          {/* New Role Selector */}
          <div className="space-y-2">
            <Label htmlFor="newRole">New Role</Label>
            <Select
              value={selectedNewRole}
              onValueChange={(value) => setNewRole(value as StaffRole)}
              disabled={isChangingRole}
            >
              <SelectTrigger id="newRole">
                <SelectValue placeholder="Select new role" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem
                    key={role.value}
                    value={role.value}
                    disabled={role.value === staff.role}
                  >
                    <div className="flex flex-col">
                      <span className="font-medium">{role.label}</span>
                      <span className="text-xs text-slate-500">{role.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Role Transition Preview */}
          {newRole && newRole !== staff.role && (
            <div className="flex items-center gap-2 rounded-md bg-blue-50 p-3">
              <RoleBadge role={staff.role as StaffRole} showIcon={false} />
              <ArrowRight className="h-4 w-4 text-blue-600" />
              <RoleBadge role={newRole} showIcon={false} />
            </div>
          )}

          {/* Warnings */}
          {isSelf && newRole && newRole !== 'admin' && (
            <div className="flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium">Warning</div>
                <div>You are about to demote yourself from admin. This action cannot be undone without another admin.</div>
              </div>
            </div>
          )}

          {/* Validation Error */}
          {!transition.allowed && (
            <div className="flex items-start gap-2 rounded-md bg-red-50 p-3 text-sm text-red-800">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>{transition.reason}</div>
            </div>
          )}

          {/* API Error */}
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isChangingRole}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={
              isChangingRole ||
              !newRole ||
              newRole === staff.role ||
              !transition.allowed
            }
          >
            {isChangingRole && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isChangingRole ? 'Updating...' : 'Update Role'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
