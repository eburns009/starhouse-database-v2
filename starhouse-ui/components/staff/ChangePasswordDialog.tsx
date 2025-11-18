/**
 * Change Password Dialog Component (Self-service)
 * FAANG Standards:
 * - React Hook Form with Zod validation
 * - Password strength indicator
 * - Show/hide password toggle
 * - Real-time validation feedback
 * - Security best practices (min length, complexity)
 */

'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
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
import { changeOwnPassword } from '@/lib/api/staff'
import { toast } from 'sonner'
import { Eye, EyeOff, Loader2, CheckCircle2, XCircle } from 'lucide-react'

const passwordSchema = z.object({
  newPassword: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string()
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword']
})

type PasswordFormData = z.infer<typeof passwordSchema>

interface ChangePasswordDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ChangePasswordDialog({ open, onOpenChange }: ChangePasswordDialogProps) {
  const [isChanging, setIsChanging] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    mode: 'onChange'
  })

  const newPassword = watch('newPassword')

  // Password strength calculation
  const getPasswordStrength = (password: string): {
    score: number
    label: string
    color: string
  } => {
    if (!password) return { score: 0, label: '', color: '' }

    let score = 0
    if (password.length >= 8) score++
    if (password.length >= 12) score++
    if (/[A-Z]/.test(password)) score++
    if (/[a-z]/.test(password)) score++
    if (/[0-9]/.test(password)) score++
    if (/[^A-Za-z0-9]/.test(password)) score++

    if (score <= 2) return { score, label: 'Weak', color: 'bg-red-500' }
    if (score <= 4) return { score, label: 'Medium', color: 'bg-yellow-500' }
    return { score, label: 'Strong', color: 'bg-green-500' }
  }

  const passwordStrength = getPasswordStrength(newPassword)

  const handleClose = () => {
    reset()
    setShowPassword(false)
    setShowConfirm(false)
    onOpenChange(false)
  }

  const onSubmit = async (data: PasswordFormData) => {
    try {
      setIsChanging(true)

      const result = await changeOwnPassword(data.newPassword)

      if (result.success) {
        toast.success('Password changed successfully', {
          description: 'Your password has been updated. You may need to log in again.'
        })
        handleClose()
      } else {
        // Handle specific error codes
        if (result.error?.code === 'WEAK_PASSWORD') {
          toast.error('Password too weak', {
            description: 'Please choose a stronger password.'
          })
        } else if (result.error?.code === 'UNAUTHORIZED') {
          toast.error('Session expired', {
            description: 'Please log in again to change your password.'
          })
        } else {
          toast.error('Failed to change password', {
            description: result.error?.message || 'Please try again.'
          })
        }
      }
    } catch (error) {
      console.error('[ChangePasswordDialog] Unexpected error:', error)
      toast.error('An unexpected error occurred', {
        description: 'Please try again or contact support.'
      })
    } finally {
      setIsChanging(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[450px]">
        <DialogHeader>
          <DialogTitle>Change Your Password</DialogTitle>
          <DialogDescription>
            Choose a strong password to keep your account secure.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* New Password Field */}
          <div className="space-y-2">
            <Label htmlFor="newPassword">
              New Password <span className="text-red-500">*</span>
            </Label>
            <div className="relative">
              <Input
                id="newPassword"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter new password"
                {...register('newPassword')}
                disabled={isChanging}
                aria-invalid={!!errors.newPassword}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>

            {/* Password Strength Indicator */}
            {newPassword && (
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${passwordStrength.color}`}
                      style={{ width: `${(passwordStrength.score / 6) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-600">
                    {passwordStrength.label}
                  </span>
                </div>

                {/* Password Requirements */}
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-1">
                    {newPassword.length >= 8 ? (
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-slate-400" />
                    )}
                    <span className={newPassword.length >= 8 ? 'text-green-600' : 'text-slate-500'}>
                      At least 8 characters
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {/[A-Z]/.test(newPassword) ? (
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-slate-400" />
                    )}
                    <span className={/[A-Z]/.test(newPassword) ? 'text-green-600' : 'text-slate-500'}>
                      One uppercase letter
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {/[a-z]/.test(newPassword) ? (
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-slate-400" />
                    )}
                    <span className={/[a-z]/.test(newPassword) ? 'text-green-600' : 'text-slate-500'}>
                      One lowercase letter
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {/[0-9]/.test(newPassword) ? (
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-slate-400" />
                    )}
                    <span className={/[0-9]/.test(newPassword) ? 'text-green-600' : 'text-slate-500'}>
                      One number
                    </span>
                  </div>
                </div>
              </div>
            )}

            {errors.newPassword && (
              <p className="text-sm text-red-500">{errors.newPassword.message}</p>
            )}
          </div>

          {/* Confirm Password Field */}
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">
              Confirm Password <span className="text-red-500">*</span>
            </Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirm ? 'text' : 'password'}
                placeholder="Confirm new password"
                {...register('confirmPassword')}
                disabled={isChanging}
                aria-invalid={!!errors.confirmPassword}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                tabIndex={-1}
              >
                {showConfirm ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isChanging}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isChanging}>
              {isChanging && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isChanging ? 'Changing...' : 'Change Password'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
