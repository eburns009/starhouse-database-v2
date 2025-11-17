/**
 * AddStaffDialog Component
 * FAANG Standards:
 * - React Hook Form with Zod validation
 * - Optimistic UI with loading states
 * - Comprehensive error handling
 * - Accessible form with proper labels
 * - Toast notifications for feedback
 */

'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useStaffActions } from '@/lib/hooks/useStaffActions'
import { addStaffMemberSchema, type AddStaffMemberInput } from '@/lib/validations/staff'
import { getAllRoles } from './RoleBadge'
import { Loader2 } from 'lucide-react'

interface AddStaffDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function AddStaffDialog({ open, onOpenChange, onSuccess }: AddStaffDialogProps) {
  const [roleValue, setRoleValue] = useState<string>('full_user')

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue
  } = useForm<AddStaffMemberInput>({
    resolver: zodResolver(addStaffMemberSchema),
    defaultValues: {
      role: 'full_user'
    }
  })

  const { add, isAdding, error, clearError } = useStaffActions(() => {
    onSuccess?.()
    handleClose()
  })

  const handleClose = () => {
    reset()
    setRoleValue('full_user')
    clearError()
    onOpenChange(false)
  }

  const onSubmit = async (data: AddStaffMemberInput) => {
    await add(data.email, data.role, data.displayName, data.notes)
  }

  const roles = getAllRoles()

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Staff Member</DialogTitle>
          <DialogDescription>
            Add a new staff member with specified role and permissions.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Email Field */}
          <div className="space-y-2">
            <Label htmlFor="email">
              Email <span className="text-red-500">*</span>
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="user@example.com"
              {...register('email')}
              disabled={isAdding}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? 'email-error' : undefined}
            />
            {errors.email && (
              <p id="email-error" className="text-sm text-red-500">
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Display Name Field */}
          <div className="space-y-2">
            <Label htmlFor="displayName">Display Name</Label>
            <Input
              id="displayName"
              type="text"
              placeholder="John Smith"
              {...register('displayName')}
              disabled={isAdding}
              aria-describedby={errors.displayName ? 'displayName-error' : undefined}
            />
            {errors.displayName && (
              <p id="displayName-error" className="text-sm text-red-500">
                {errors.displayName.message}
              </p>
            )}
            <p className="text-xs text-slate-500">
              Optional: Friendly name for UI display
            </p>
          </div>

          {/* Role Field */}
          <div className="space-y-2">
            <Label htmlFor="role">
              Role <span className="text-red-500">*</span>
            </Label>
            <Select
              value={roleValue}
              onValueChange={(value) => {
                setRoleValue(value)
                setValue('role', value as AddStaffMemberInput['role'])
              }}
              disabled={isAdding}
            >
              <SelectTrigger id="role" aria-label="Select role">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem key={role.value} value={role.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{role.label}</span>
                      <span className="text-xs text-slate-500">{role.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.role && (
              <p className="text-sm text-red-500">{errors.role.message}</p>
            )}
          </div>

          {/* Notes Field */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Input
              id="notes"
              type="text"
              placeholder="Team name, department, etc."
              {...register('notes')}
              disabled={isAdding}
              aria-describedby={errors.notes ? 'notes-error' : undefined}
            />
            {errors.notes && (
              <p id="notes-error" className="text-sm text-red-500">
                {errors.notes.message}
              </p>
            )}
            <p className="text-xs text-slate-500">
              Optional: Additional information or context
            </p>
          </div>

          {/* API Error */}
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isAdding}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isAdding}>
              {isAdding && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isAdding ? 'Adding...' : 'Add Staff Member'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
