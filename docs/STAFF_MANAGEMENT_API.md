# Staff Management API Documentation

**Version:** 1.0.0
**Date:** 2025-11-17
**Standards:** FAANG-Level Architecture

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Methods](#api-methods)
4. [Type Definitions](#type-definitions)
5. [Error Handling](#error-handling)
6. [React Hooks](#react-hooks)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Overview

The Staff Management API provides type-safe, secure operations for managing staff members with three-tier access control (Admin, Full User, Read Only). All operations include comprehensive error handling, validation, and audit logging.

### Key Features

- **Type Safety**: Full TypeScript support with generated types
- **Security**: Row-Level Security (RLS) enforcement
- **Real-time**: Supabase Realtime subscriptions
- **Error Handling**: Specific error types for better debugging
- **Validation**: Input validation before database operations
- **Audit Trail**: Automatic logging of all changes

---

## Authentication & Authorization

### Three-Tier Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full access + manage users + system settings |
| **Full User** | View/edit contacts, donors, transactions (no user management) |
| **Read Only** | View-only access (no edits, no user management) |

### Security Layers

1. **Client-side**: React hooks check permissions before rendering UI
2. **API Layer**: Validation and authorization checks in API methods
3. **Database**: Row-Level Security (RLS) policies enforce access control

```typescript
// Example: Check if user is admin
const { isAdmin, canEdit } = useCurrentStaff()

if (isAdmin) {
  // Show admin-only features
}
```

---

## API Methods

### `getStaffMembers()`

Fetches all staff members sorted by role and email.

**Returns:** `Promise<APIResponse<StaffMember[]>>`

```typescript
import { getStaffMembers } from '@/lib/api/staff'

const result = await getStaffMembers()

if (result.success) {
  console.log(result.data) // StaffMember[]
} else {
  console.error(result.error.message)
}
```

**Success Response:**
```typescript
{
  success: true,
  data: [
    {
      email: "admin@starhouse.org",
      display_name: "Admin User",
      role: "admin",
      active: true,
      added_at: "2025-11-17T10:00:00Z",
      last_login_at: "2025-11-17T15:30:00Z",
      notes: null
    },
    // ... more staff members
  ]
}
```

---

### `getCurrentStaff()`

Gets current user's staff information and permissions.

**Returns:** `Promise<APIResponse<StaffMember & { isAdmin: boolean; canEdit: boolean }>>`

```typescript
import { getCurrentStaff } from '@/lib/api/staff'

const result = await getCurrentStaff()

if (result.success) {
  const { isAdmin, canEdit, role } = result.data
  console.log(`User role: ${role}`)
  console.log(`Can edit: ${canEdit}`)
}
```

**Success Response:**
```typescript
{
  success: true,
  data: {
    email: "user@starhouse.org",
    role: "full_user",
    isAdmin: false,
    canEdit: true,
    // ... other StaffMember properties
  }
}
```

**Error Response (Unauthorized):**
```typescript
{
  success: false,
  error: {
    message: "No active session",
    code: "UNAUTHORIZED"
  }
}
```

---

### `addStaffMember(email, role, displayName?, notes?)`

Adds a new staff member. **Admin only.**

**Parameters:**
- `email` (string, required): Valid email address
- `role` (StaffRole, required): One of `'admin'`, `'full_user'`, `'read_only'`
- `displayName` (string, optional): Display name for the staff member
- `notes` (string, optional): Internal notes

**Returns:** `Promise<APIResponse<{ email: string; role: string }>>`

```typescript
import { addStaffMember } from '@/lib/api/staff'

const result = await addStaffMember(
  'newuser@starhouse.org',
  'full_user',
  'New User',
  'Added via onboarding'
)

if (result.success) {
  console.log(`Added: ${result.data.email}`)
}
```

**Validation:**
- Email must be valid format
- Role must be one of: `admin`, `full_user`, `read_only`
- Only admins can add staff members
- Email must be unique

**Error Responses:**

```typescript
// Invalid email
{
  success: false,
  error: {
    message: "Invalid email format",
    code: "VALIDATION_ERROR"
  }
}

// Duplicate email
{
  success: false,
  error: {
    message: "Staff member already exists",
    code: "VALIDATION_ERROR"
  }
}

// Unauthorized
{
  success: false,
  error: {
    message: "Only admins can add staff members",
    code: "UNAUTHORIZED"
  }
}
```

---

### `changeStaffRole(email, newRole)`

Changes a staff member's role. **Admin only.**

**Parameters:**
- `email` (string, required): Email of staff member
- `newRole` (StaffRole, required): New role to assign

**Returns:** `Promise<APIResponse<{ email: string; oldRole: string; newRole: string }>>`

```typescript
import { changeStaffRole } from '@/lib/api/staff'

const result = await changeStaffRole(
  'user@starhouse.org',
  'admin'
)

if (result.success) {
  console.log(`Changed ${result.data.email} from ${result.data.oldRole} to ${result.data.newRole}`)
}
```

**Security:**
- Admins cannot demote themselves
- Only admins can change roles
- Changes are logged in audit trail

**Error Response (Self-demotion):**
```typescript
{
  success: false,
  error: {
    message: "Cannot demote yourself from admin",
    code: "VALIDATION_ERROR"
  }
}
```

---

### `deactivateStaffMember(email)`

Deactivates a staff member (soft delete). **Admin only.**

**Parameters:**
- `email` (string, required): Email of staff member to deactivate

**Returns:** `Promise<APIResponse<{ email: string; deactivatedAt: string }>>`

```typescript
import { deactivateStaffMember } from '@/lib/api/staff'

const result = await deactivateStaffMember('user@starhouse.org')

if (result.success) {
  console.log(`Deactivated at: ${result.data.deactivatedAt}`)
}
```

**Important:**
- This is a soft delete (sets `active = false`)
- Deactivated staff cannot log in
- Historical data remains intact
- Can be reactivated by admin if needed

---

### `updateLastLogin()`

Updates the current user's last login timestamp. Called automatically.

**Returns:** `Promise<APIResponse<void>>`

```typescript
import { updateLastLogin } from '@/lib/api/staff'

// Automatically called on login
await updateLastLogin()
```

**Behavior:**
- Silent fail if user not authenticated
- Non-critical operation (errors are logged but not thrown)

---

## Type Definitions

### `StaffRole`

```typescript
type StaffRole = 'admin' | 'full_user' | 'read_only'
```

### `StaffMember`

```typescript
interface StaffMember {
  email: string
  display_name: string | null
  role: StaffRole
  active: boolean
  added_at: string
  added_by: string | null
  deactivated_at: string | null
  deactivated_by: string | null
  last_login_at: string | null
  notes: string | null
}
```

### `APIResponse<T>`

```typescript
interface APIResponse<T> {
  success: boolean
  data?: T
  error?: {
    message: string
    code: string
    details?: unknown
  }
}
```

---

## Error Handling

### Error Classes

All errors extend from `StaffAPIError`:

```typescript
class StaffAPIError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: unknown
  )
}

class UnauthorizedError extends StaffAPIError {
  // code: 'UNAUTHORIZED'
}

class ValidationError extends StaffAPIError {
  // code: 'VALIDATION_ERROR'
}
```

### Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `UNAUTHORIZED` | User not authenticated or insufficient permissions | Redirect to login or show permission error |
| `VALIDATION_ERROR` | Invalid input data | Show validation message to user |
| `FETCH_ERROR` | Database query failed | Retry or show generic error |
| `ADD_ERROR` | Failed to add staff member | Check logs, show error message |
| `CHANGE_ROLE_ERROR` | Failed to change role | Check logs, show error message |
| `DEACTIVATE_ERROR` | Failed to deactivate | Check logs, show error message |
| `UNKNOWN_ERROR` | Unexpected error | Log error, show generic message |

### Error Handling Pattern

```typescript
import { addStaffMember, ValidationError, UnauthorizedError } from '@/lib/api/staff'

const result = await addStaffMember(email, role)

if (!result.success) {
  switch (result.error.code) {
    case 'VALIDATION_ERROR':
      // Show validation message to user
      setFormError(result.error.message)
      break

    case 'UNAUTHORIZED':
      // Redirect to login or show permission error
      router.push('/login')
      break

    default:
      // Generic error handling
      console.error(result.error)
      toast.error('An unexpected error occurred')
  }
}
```

---

## React Hooks

### `useStaffMembers()`

Fetches staff members with real-time updates.

```typescript
import { useStaffMembers } from '@/lib/hooks/useStaffMembers'

function StaffList() {
  const { staff, loading, error, refetch } = useStaffMembers()

  if (loading) return <Skeleton />
  if (error) return <Error message={error} />

  return (
    <div>
      {staff.map(member => (
        <StaffRow key={member.email} member={member} />
      ))}
      <button onClick={refetch}>Refresh</button>
    </div>
  )
}
```

**Features:**
- Automatic real-time subscriptions
- Loading states
- Error handling
- Manual refetch capability

---

### `useCurrentStaff()`

Gets current user's staff info and permissions.

```typescript
import { useCurrentStaff } from '@/lib/hooks/useCurrentStaff'

function Header() {
  const { staff, isAdmin, canEdit, loading } = useCurrentStaff()

  if (loading) return <Skeleton />

  return (
    <div>
      <p>Welcome, {staff?.display_name || staff?.email}</p>
      {isAdmin && <AdminPanel />}
      {canEdit && <EditButton />}
    </div>
  )
}
```

**Properties:**
- `staff`: Full staff member object or null
- `isAdmin`: Boolean - true if role is 'admin'
- `canEdit`: Boolean - true if role is 'admin' or 'full_user'
- `loading`: Boolean - true while fetching
- `error`: String or null - error message if failed

---

## Best Practices

### 1. Always Check Success Before Using Data

```typescript
const result = await getStaffMembers()

if (result.success) {
  // ✅ Safe to use result.data
  processStaffMembers(result.data)
} else {
  // ✅ Handle error
  handleError(result.error)
}

// ❌ NEVER do this
const data = result.data // Could be undefined!
```

### 2. Use TypeScript for Type Safety

```typescript
// ✅ TypeScript will catch invalid roles
await addStaffMember('user@test.com', 'invalid_role') // Error!

// ✅ TypeScript enforces required parameters
await addStaffMember('user@test.com') // Error: missing role!
```

### 3. Handle All Error Cases

```typescript
if (!result.success) {
  // ✅ Handle specific error types
  if (result.error.code === 'UNAUTHORIZED') {
    redirectToLogin()
  } else if (result.error.code === 'VALIDATION_ERROR') {
    showValidationError(result.error.message)
  } else {
    logError(result.error)
    showGenericError()
  }
}
```

### 4. Use Hooks for Real-time Updates

```typescript
// ✅ Hook automatically subscribes to changes
const { staff } = useStaffMembers()

// ❌ Manual polling is inefficient
setInterval(async () => {
  const result = await getStaffMembers()
  setStaff(result.data)
}, 5000)
```

### 5. Validate Input Before API Calls

```typescript
// ✅ Validate before calling API
if (!email.includes('@')) {
  setError('Invalid email')
  return
}

await addStaffMember(email, role)

// ❌ Relying only on API validation
await addStaffMember(email, role) // Will fail, wasted API call
```

---

## Examples

### Complete Admin Workflow

```typescript
import {
  getStaffMembers,
  addStaffMember,
  changeStaffRole,
  deactivateStaffMember
} from '@/lib/api/staff'

async function adminWorkflow() {
  // 1. Get all staff members
  const staffResult = await getStaffMembers()
  if (!staffResult.success) {
    console.error(staffResult.error)
    return
  }

  console.log(`Total staff: ${staffResult.data.length}`)

  // 2. Add new staff member
  const addResult = await addStaffMember(
    'newuser@starhouse.org',
    'full_user',
    'New User'
  )

  if (addResult.success) {
    console.log(`Added: ${addResult.data.email}`)
  }

  // 3. Promote user to admin
  const roleResult = await changeStaffRole(
    'newuser@starhouse.org',
    'admin'
  )

  if (roleResult.success) {
    console.log(`Promoted to admin`)
  }

  // 4. Deactivate user
  const deactivateResult = await deactivateStaffMember(
    'olduser@starhouse.org'
  )

  if (deactivateResult.success) {
    console.log(`Deactivated at: ${deactivateResult.data.deactivatedAt}`)
  }
}
```

### React Component Example

```typescript
import { useState } from 'react'
import { useStaffMembers, useCurrentStaff } from '@/lib/hooks'
import { addStaffMember } from '@/lib/api/staff'
import { Button, Input, Select } from '@/components/ui'

export function StaffManagement() {
  const { staff, loading, refetch } = useStaffMembers()
  const { isAdmin } = useCurrentStaff()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<StaffRole>('full_user')

  const handleAdd = async () => {
    const result = await addStaffMember(email, role)

    if (result.success) {
      toast.success('Staff member added')
      setEmail('')
      refetch()
    } else {
      toast.error(result.error.message)
    }
  }

  if (!isAdmin) return <div>Access denied</div>

  return (
    <div>
      <h1>Staff Management</h1>

      <div>
        <Input
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="Email"
        />
        <Select value={role} onChange={setRole}>
          <option value="admin">Admin</option>
          <option value="full_user">Full User</option>
          <option value="read_only">Read Only</option>
        </Select>
        <Button onClick={handleAdd}>Add</Button>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {staff.map(member => (
              <tr key={member.email}>
                <td>{member.email}</td>
                <td>{member.role}</td>
                <td>{member.active ? 'Active' : 'Inactive'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
```

---

## Security Considerations

1. **Never bypass RLS policies** - Always use Supabase client, never raw SQL from client
2. **Validate on both client and server** - Client validation for UX, server for security
3. **Use HTTPS only** - All API calls must be over HTTPS in production
4. **Rate limiting** - Consider implementing rate limits for sensitive operations
5. **Audit logging** - All admin actions are logged automatically
6. **Session management** - Use Supabase's built-in session handling

---

## Support

For issues or questions:
- Check the [User Guide](./STAFF_MANAGEMENT_USER_GUIDE.md)
- Review [Implementation Plan](./STAFF_MANAGEMENT_UI_IMPLEMENTATION_PLAN.md)
- Contact: dev@starhouse.org

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0
**Maintainer:** Starhouse Dev Team
