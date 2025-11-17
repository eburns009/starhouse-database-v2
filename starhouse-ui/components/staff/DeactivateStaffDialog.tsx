/**
 * DeactivateStaffDialog Component
 * FAANG Standards:
 * - Confirmation dialog for destructive action
 * - Clear consequences communicated
 * - Accessible with proper ARIA labels
 * - Prevents accidental clicks
 */

'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useStaffActions } from '@/lib/hooks/useStaffActions'
import type { StaffMember } from '@/lib/types/staff.types'
import { RoleBadge } from './RoleBadge'
import { Loader2, AlertTriangle } from 'lucide-react'

interface DeactivateStaffDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  staff: StaffMember | null
  onSuccess?: () => void
}

export function DeactivateStaffDialog({
  open,
  onOpenChange,
  staff,
  onSuccess
}: DeactivateStaffDialogProps) {
  const { deactivate, isDeactivating, error, clearError } = useStaffActions(() => {
    onSuccess?.()
    handleClose()
  })

  const handleClose = () => {
    clearError()
    onOpenChange(false)
  }

  const handleDeactivate = async () => {
    if (!staff) return
    await deactivate(staff.email)
  }

  if (!staff) return null

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Deactivate Staff Member</DialogTitle>
          <DialogDescription>
            This action will remove access for this staff member.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Staff Info */}
          <div className="rounded-md bg-slate-100 p-4 space-y-2">
            <div className="font-medium">{staff.display_name || staff.email}</div>
            {staff.display_name && (
              <div className="text-sm text-slate-600">{staff.email}</div>
            )}
            <RoleBadge role={staff.role as any} />
            {staff.notes && (
              <div className="text-sm text-slate-600 mt-2">Notes: {staff.notes}</div>
            )}
          </div>

          {/* Warning */}
          <div className="flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800">
            <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium">Consequences of deactivation:</div>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>This user will lose all access immediately</li>
                <li>They will not be able to log in</li>
                <li>This action can be reversed by an admin</li>
                <li>All audit trail data will be preserved</li>
              </ul>
            </div>
          </div>

          {/* API Error */}
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* Confirmation Text */}
          <div className="text-sm text-slate-600">
            Are you sure you want to deactivate <strong>{staff.display_name || staff.email}</strong>?
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isDeactivating}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDeactivate}
            disabled={isDeactivating}
          >
            {isDeactivating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isDeactivating ? 'Deactivating...' : 'Deactivate'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
