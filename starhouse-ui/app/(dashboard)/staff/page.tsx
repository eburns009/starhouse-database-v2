/**
 * Staff Management Page
 * FAANG Standards:
 * - Role-based access control (admin only)
 * - Real-time updates via Supabase subscriptions
 * - Optimistic UI with loading states
 * - Comprehensive error handling with retry
 * - Accessible UI with proper semantics
 * - Responsive design (mobile-first)
 */

'use client'

import { useState } from 'react'
import { useStaffMembers } from '@/lib/hooks/useStaffMembers'
import { useCurrentUser } from '@/lib/hooks/useCurrentUser'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { StaffTable } from '@/components/staff/StaffTable'
import { AddStaffDialog } from '@/components/staff/AddStaffDialog'
import { Plus, RefreshCw, Shield, AlertCircle, Loader2 } from 'lucide-react'

export default function StaffManagementPage() {
  const [addDialogOpen, setAddDialogOpen] = useState(false)

  // Hooks
  const { user, loading: userLoading, error: userError, isAdmin } = useCurrentUser()
  const { staff, loading: staffLoading, error: staffError, refetch } = useStaffMembers()

  // Loading state
  if (userLoading || staffLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
          <p className="text-sm text-slate-500">Loading staff management...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (userError) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <CardTitle>Access Denied</CardTitle>
            </div>
            <CardDescription>
              You don't have permission to access staff management.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-4">
              {userError}
            </p>
            <p className="text-sm text-slate-500">
              Please contact an administrator if you believe this is an error.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Authorization check
  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2 text-yellow-600">
              <Shield className="h-5 w-5" />
              <CardTitle>Admin Access Required</CardTitle>
            </div>
            <CardDescription>
              Staff management is only available to administrators.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-md bg-slate-100 p-3 text-sm">
                <div className="font-medium text-slate-700">Your current role:</div>
                <div className="text-slate-600 mt-1">{user?.role || 'Unknown'}</div>
              </div>
              <p className="text-sm text-slate-500">
                Contact an administrator to request admin access if needed.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Staff loading error
  if (staffError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Staff Management</h1>
            <p className="text-slate-500 mt-1">
              Manage staff members and their permissions
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              <CardTitle>Failed to Load Staff</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-4">{staffError}</p>
            <Button onClick={refetch} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Staff Management</h1>
          <p className="text-slate-500 mt-1">
            Manage staff members and their permissions
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            title="Refresh staff list"
          >
            <RefreshCw className="h-4 w-4" />
            <span className="sr-only">Refresh</span>
          </Button>

          <Button onClick={() => setAddDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Staff Member
          </Button>
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Role Permissions</CardTitle>
          <CardDescription>
            Understanding staff access levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-red-600" />
                <div className="font-medium">Admin</div>
              </div>
              <p className="text-sm text-slate-600">
                Full access + manage users + system settings
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-blue-600" />
                <div className="font-medium">Full User</div>
              </div>
              <p className="text-sm text-slate-600">
                View & edit contacts, products, transactions
              </p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-slate-600" />
                <div className="font-medium">Read Only</div>
              </div>
              <p className="text-sm text-slate-600">
                View-only access to all data
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Staff Table */}
      <Card>
        <CardHeader>
          <CardTitle>Staff Members</CardTitle>
          <CardDescription>
            All staff members with their current roles and status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <StaffTable
            staff={staff}
            currentUserEmail={user?.email}
            isAdmin={isAdmin}
            onRefetch={refetch}
          />
        </CardContent>
      </Card>

      {/* Add Staff Dialog */}
      <AddStaffDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSuccess={refetch}
      />
    </div>
  )
}
