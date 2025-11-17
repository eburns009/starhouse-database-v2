# Staff Management User Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-17
**For:** Starhouse Staff Members

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding Roles](#understanding-roles)
4. [Managing Staff (Admin Only)](#managing-staff-admin-only)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Introduction

The Starhouse Staff Management system allows administrators to control who has access to the system and what level of permissions they have. This guide will help you understand how to use the staff management features.

### What You Can Do

**If you're an Admin:**
- Add new staff members
- Change staff roles
- Deactivate staff members
- View all staff activity

**If you're a Full User:**
- View staff list
- Edit contacts and donors
- Cannot manage other staff members

**If you're Read Only:**
- View staff list
- View contacts and donors
- Cannot edit anything

---

## Getting Started

### Accessing Staff Management

1. Log in to your Starhouse account
2. Click on **"Staff"** in the main navigation menu
3. You'll see a list of all staff members

![Staff Management Screenshot](./images/staff-management-overview.png)

### What You'll See

The staff management page shows:
- **Email Address**: Each staff member's email
- **Display Name**: Optional friendly name
- **Role Badge**: Color-coded role indicator
  - 🔴 **Admin** (Red) - Full access
  - 🔵 **Full User** (Blue) - Can edit data
  - ⚪ **Read Only** (Gray) - View only
- **Status**: Active or Inactive
- **Last Login**: When they last accessed the system
- **Actions**: Edit or deactivate (Admin only)

---

## Understanding Roles

### Role Comparison

| Feature | Admin | Full User | Read Only |
|---------|-------|-----------|-----------|
| View Contacts | ✅ | ✅ | ✅ |
| Edit Contacts | ✅ | ✅ | ❌ |
| Delete Contacts | ✅ | ❌ | ❌ |
| Add Staff Members | ✅ | ❌ | ❌ |
| Change Staff Roles | ✅ | ❌ | ❌ |
| Deactivate Staff | ✅ | ❌ | ❌ |
| View Reports | ✅ | ✅ | ✅ |
| Export Data | ✅ | ✅ | ❌ |
| System Settings | ✅ | ❌ | ❌ |

### When to Use Each Role

**Admin Role:**
- Organization leaders
- IT administrators
- People who need to manage other staff

**Full User Role:**
- Staff who regularly update contact information
- People who process donations
- Team members who need to edit data

**Read Only Role:**
- Board members who need visibility
- Consultants or contractors
- Staff in training
- Anyone who needs to view but not modify

---

## Managing Staff (Admin Only)

### Adding a New Staff Member

1. Click the **"Add Staff Member"** button (top right)
2. Fill in the form:
   - **Email** (required): Their work email address
   - **Display Name** (optional): Friendly name like "John Smith"
   - **Role** (required): Select appropriate role
   - **Notes** (optional): Internal notes about this person
3. Click **"Add Staff Member"**
4. They'll receive an email invitation to set up their account

**Best Practices:**
- Use work email addresses, not personal emails
- Start new staff with "Read Only" role during training
- Add notes about their department or responsibilities
- Verify email address is correct before adding

**Example:**

```
Email: john.smith@starhouse.org
Display Name: John Smith
Role: Full User
Notes: Development team, hired Nov 2025
```

---

### Changing a Staff Member's Role

1. Find the staff member in the list
2. Click the **edit icon** (pencil) next to their name
3. Select the new role from the dropdown
4. Click **"Save Changes"**
5. Confirm the change in the dialog

**Important Notes:**
- Changes take effect immediately
- The person will be logged out and need to log back in
- You cannot demote yourself from Admin
- Role changes are logged in the audit trail

**When to Change Roles:**
- Promoting someone after training → Read Only to Full User
- New responsibilities → Full User to Admin
- Reducing access → Full User to Read Only
- Employee departing → Any role to Deactivated

---

### Deactivating a Staff Member

1. Find the staff member in the list
2. Click the **deactivate icon** (trash) next to their name
3. Confirm deactivation in the dialog
4. They will be immediately logged out and cannot log back in

**What Happens When You Deactivate:**
- ❌ They cannot log in
- ✅ Their historical data remains (audit trail)
- ✅ You can reactivate them later if needed
- ✅ Their email address becomes available for a new staff member

**Important:**
- Always deactivate staff when they leave the organization
- Don't delete - deactivate (maintains audit trail)
- Consider changing role to Read Only before complete deactivation

---

### Reactivating a Staff Member

1. At the top of the staff list, toggle "Show Inactive"
2. Find the deactivated staff member
3. Click the **reactivate icon**
4. They can now log in again with their previous role

---

## Common Tasks

### Finding a Specific Staff Member

**Search by Email:**
1. Use the search box at the top of the list
2. Type any part of their email address
3. List filters automatically

**Sort by Column:**
1. Click any column header to sort
2. Click again to reverse sort order
3. Options: Email, Role, Status, Last Login

### Viewing Staff Activity

1. Click on a staff member's name
2. View their activity log:
   - When they were added
   - Who added them
   - Role changes
   - Last login time
   - Recent actions

### Exporting Staff List

1. Click the **"Export"** button (top right)
2. Choose format: CSV or PDF
3. File downloads automatically
4. Includes: Email, Role, Status, Last Login

---

## Troubleshooting

### I Can't Add a Staff Member

**Problem:** "Add Staff Member" button is greyed out or missing

**Solutions:**
1. **Check your role**: Only Admins can add staff
   - Go to your profile → View your role
   - If you're not an Admin, ask an existing Admin to add the person
2. **Refresh the page**: Sometimes the UI needs a refresh
3. **Check your internet connection**: Ensure you're online

---

### New Staff Member Didn't Receive Invitation Email

**Solutions:**
1. **Check spam folder**: Invitation may be in junk/spam
2. **Verify email address**: Check for typos in the email
   - Click edit → Verify email is correct
3. **Resend invitation**:
   - Click the **"Resend Invite"** button next to their name
4. **Wait 5 minutes**: Email delivery can be delayed

---

### I Can't Change Someone's Role

**Problem:** Getting an error when trying to change a role

**Common Causes:**
1. **Self-demotion**: You cannot demote yourself from Admin
   - Ask another Admin to change your role
2. **No permission**: Only Admins can change roles
3. **Already that role**: Person is already assigned that role

---

### Staff Member Can't Log In

**Solutions:**
1. **Check if active**:
   - Find them in the staff list
   - Look for "Active" status
   - If inactive, reactivate them
2. **Check their role**:
   - Deactivated staff cannot log in
   - Verify they have an assigned role
3. **Password reset**:
   - They may need to reset their password
   - Send them to the "Forgot Password" link

---

## FAQ

### How many Admins should we have?

**Recommendation:** 2-3 Admins

**Why:**
- Ensures someone can always manage staff
- Prevents single point of failure
- But not so many that security becomes lax

**Best Practice:**
- Primary Admin: Organization leader or IT lead
- Backup Admin: Deputy or senior staff member
- Emergency Admin: Board member or external advisor

---

### Can I see who made changes to staff?

**Yes!** All changes are logged.

**To view:**
1. Click on a staff member's name
2. Scroll to "Activity Log"
3. See full history of changes

**What's logged:**
- Who added the staff member
- When they were added
- All role changes (who changed it and when)
- Deactivation (who deactivated and when)
- Reactivation events

---

### What happens if we lose all our Admins?

**Recovery Process:**
1. Contact Starhouse Support: support@starhouse.org
2. Provide proof of organization ownership
3. Support team can manually promote an existing staff member to Admin
4. Process takes 24-48 hours for security verification

**Prevention:**
- Always maintain 2-3 active Admins
- Document Admin contacts in a secure location
- Review Admin list quarterly

---

### Can staff members have multiple roles?

**No.** Each staff member has exactly one role.

**Why:**
- Simplifies permission management
- Clearer security boundaries
- Easier to audit

**If someone needs mixed permissions:**
- Assign the role with the highest level of access they need
- Consider if that person should be an Admin

---

### How do I know if someone is logged in right now?

**Currently:** The system shows "Last Login" timestamp

**To see:**
1. Go to Staff Management
2. Look at "Last Login" column
3. Recent timestamps (within minutes) indicate current session

**Future Feature:**
- Live "Online Now" indicator (coming soon)

---

### Can I bulk import staff members?

**Not Yet.** Currently you must add staff one at a time.

**Workaround:**
1. Prepare a list with: Email, Role, Display Name
2. Add them individually (takes ~30 seconds each)
3. Contact support@starhouse.org for bulk imports (25+ users)

**Coming Soon:**
- CSV import for bulk staff addition
- Automated onboarding workflows

---

### What's the difference between Deactivate and Delete?

| Action | Deactivate | Delete |
|--------|------------|--------|
| Can log in? | ❌ No | ❌ No |
| Historical data kept? | ✅ Yes | ❌ No |
| Can be restored? | ✅ Yes | ❌ No |
| Audit trail | ✅ Maintained | ❌ Lost |

**Best Practice:** Always use Deactivate, never Delete

**Why:**
- Maintains audit trail
- Complies with record-keeping requirements
- Can restore if needed (e.g., rehire)

---

## Getting Help

### Support Channels

**Email:** support@starhouse.org
**Response Time:** Within 24 hours

**Phone:** 1-800-STARHOUSE
**Hours:** Mon-Fri, 9am-5pm EST

**Documentation:**
- [API Documentation](./STAFF_MANAGEMENT_API.md)
- [Implementation Plan](./STAFF_MANAGEMENT_UI_IMPLEMENTATION_PLAN.md)

### Reporting Issues

When reporting an issue, please include:
1. Your role (Admin, Full User, Read Only)
2. What you were trying to do
3. What happened instead
4. Screenshot if possible
5. Time/date of the issue

**Example:**
```
Role: Admin
Action: Trying to add new staff member
Issue: Getting "Email already exists" error but I don't see them in the list
Screenshot: attached
Time: 2025-11-17 3:30pm EST
```

---

## Best Practices

### Security

✅ **DO:**
- Use strong, unique passwords
- Log out when leaving your computer
- Review staff list monthly
- Deactivate former employees immediately
- Use work email addresses only

❌ **DON'T:**
- Share login credentials
- Give Admin access unnecessarily
- Leave inactive staff members active
- Use personal email addresses
- Grant access to contractors without time limits

### Workflow

✅ **DO:**
- Start new staff with Read Only role during training
- Promote to Full User after training complete
- Document role changes in Notes field
- Keep Display Names updated
- Review permissions quarterly

❌ **DON'T:**
- Give everyone Admin access "just in case"
- Forget to deactivate departing staff
- Leave role changes undocumented
- Grant access without approval

---

## Appendix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Open search |
| `Ctrl/Cmd + N` | Add new staff (Admin only) |
| `Esc` | Close dialog |
| `Tab` | Navigate form fields |
| `Enter` | Submit form |

### Status Indicators

| Icon | Meaning |
|------|---------|
| 🟢 | Online now |
| 🟡 | Active (last login < 7 days) |
| ⚪ | Active (last login > 7 days) |
| 🔴 | Inactive/Deactivated |

---

**Questions or Feedback?**
Contact: support@starhouse.org

**Document Version:** 1.0.0
**Last Updated:** 2025-11-17
