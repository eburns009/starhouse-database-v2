/**
 * Reset Password Dialog Component
 * FAANG Standards:
 * - Confirmation dialog before triggering reset
 * - Clear messaging about what will happen
 * - Loading states during async operation
 * - Toast notifications for feedback
 * - Error handling with retry
 */

'use client'

import { useState } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { resetStaffPassword } from '@/lib/api/staff'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'

interface ResetPasswordDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  staffEmail: string
  staffDisplayName?: string
}

export function ResetPasswordDialog({
  open,
  onOpenChange,
  staffEmail,
  staffDisplayName
}: ResetPasswordDialogProps) {
  const [isResetting, setIsResetting] = useState(false)

  const handleReset = async () => {
    try {
      setIsResetting(true)

      const result = await resetStaffPassword(staffEmail)

      if (result.success) {
        toast.success('Password reset email sent', {
          description: `${staffDisplayName || staffEmail} will receive instructions to reset their password.`
        })
        onOpenChange(false)
      } else {
        // Handle specific error codes
        if (result.error?.code === 'STAFF_NOT_FOUND') {
          toast.error('Staff member not found', {
            description: 'The staff member may have been deleted.'
          })
        } else if (result.error?.code === 'STAFF_INACTIVE') {
          toast.error('Cannot reset password', {
            description: 'This staff member is inactive. Please reactivate them first.'
          })
        } else if (result.error?.code === 'FORBIDDEN') {
          toast.error('Permission denied', {
            description: 'Only administrators can reset passwords.'
          })
        } else {
          toast.error('Failed to send reset email', {
            description: result.error?.message || 'Please try again or contact support.'
          })
        }
      }
    } catch (error) {
      console.error('[ResetPasswordDialog] Unexpected error:', error)
      toast.error('An unexpected error occurred', {
        description: 'Please try again or contact support.'
      })
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Reset Password?</AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            <p>
              This will send a password reset email to{' '}
              <span className="font-medium text-slate-900">
                {staffDisplayName || staffEmail}
              </span>
              .
            </p>
            <p className="text-sm">
              They will receive an email with a secure link to set a new password.
              The link expires in 24 hours.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isResetting}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault()
              handleReset()
            }}
            disabled={isResetting}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isResetting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isResetting ? 'Sending...' : 'Send Reset Email'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
