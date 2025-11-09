# Program Partner Compliance UI Integration Guide

## Overview
This guide explains how to integrate Program Partner compliance tracking into the contacts UI.

## What Has Been Implemented

### 1. Database Changes ✅
- Added `is_expected_program_partner` boolean field to `contacts` table
- Created `program_partner_compliance` view for querying compliance status
- Updated `v_contact_list_with_subscriptions` view to include:
  - `is_expected_program_partner` - Boolean flag for expected partners
  - `partner_compliance_status` - Enum: `compliant`, `needs_upgrade`, `no_membership`, `trial`
  - `partner_compliance_message` - Human-readable compliance message

### 2. React Components Created ✅
- `ProgramPartnerComplianceFilter` - Filter dropdown component
- `ComplianceBadge` - Visual indicator for compliance status
- `ComplianceSummary` - Dashboard widget with statistics

## Integration Steps

### Step 1: Add Filter State to ContactListEnhanced

In `/web-app/src/components/contacts/ContactListEnhanced.jsx`, add the new filter state:

```jsx
// Add to existing filter state (around line 43)
const [partnerComplianceFilter, setPartnerComplianceFilter] = useState('all')
```

### Step 2: Import the New Components

Add imports at the top of `ContactListEnhanced.jsx`:

```jsx
import ProgramPartnerComplianceFilter, { ComplianceBadge } from './ProgramPartnerComplianceFilter'
```

### Step 3: Update the fetchContacts Function

In the `fetchContacts` function (around line 126), add the compliance filter logic:

```jsx
// After existing filters (around line 144)

// Apply Program Partner compliance filter
if (partnerComplianceFilter === 'expected') {
  query = query.eq('is_expected_program_partner', true)
} else if (partnerComplianceFilter === 'compliant') {
  query = query.eq('partner_compliance_status', 'compliant')
} else if (partnerComplianceFilter === 'needs_upgrade') {
  query = query.eq('partner_compliance_status', 'needs_upgrade')
} else if (partnerComplianceFilter === 'no_membership') {
  query = query.eq('partner_compliance_status', 'no_membership')
}
```

### Step 4: Update the useEffect Dependency Array

Add `partnerComplianceFilter` to the dependency array (around line 94):

```jsx
useEffect(() => {
  fetchContacts()
}, [searchQuery, roleFilter, subscriptionFilter, advancedFilters, currentPage, sortBy, sortOrder, partnerComplianceFilter])
```

### Step 5: Add the Filter UI

Add the filter component to the UI (in the filters section):

```jsx
{/* Add after existing filters */}
<div className="mb-4">
  <ProgramPartnerComplianceFilter
    value={partnerComplianceFilter}
    onChange={setPartnerComplianceFilter}
  />
</div>
```

### Step 6: Display Compliance Badges in Contact List

Update the contact row rendering to show compliance badges:

```jsx
{/* In the contact row rendering, add: */}
{contact.is_expected_program_partner && (
  <ComplianceBadge
    status={contact.partner_compliance_status}
    message={contact.partner_compliance_message}
  />
)}
```

## Example Usage

### Filtering for Non-Compliant Partners

```javascript
// Filter for partners who need to upgrade
setPartnerComplianceFilter('needs_upgrade')

// Filter for partners with no membership
setPartnerComplianceFilter('no_membership')

// Show all expected partners
setPartnerComplianceFilter('expected')
```

### Displaying Compliance Status

```jsx
// In contact list or detail view
<div className="flex items-center space-x-2">
  <span className="text-sm text-gray-600">{contact.full_name}</span>
  {contact.is_expected_program_partner && (
    <ComplianceBadge
      status={contact.partner_compliance_status}
      message={contact.partner_compliance_message}
    />
  )}
</div>
```

## Database Queries

### Get All Non-Compliant Partners

```javascript
const { data, error } = await supabase
  .from('v_contact_list_with_subscriptions')
  .select('*')
  .eq('is_expected_program_partner', true)
  .neq('partner_compliance_status', 'compliant')
```

### Get Compliance Statistics

```javascript
const { data, error } = await supabase
  .from('program_partner_compliance')
  .select('compliance_status')

// Process results to get counts
const stats = {
  compliant: data.filter(d => d.compliance_status === 'compliant').length,
  needs_upgrade: data.filter(d => d.compliance_status === 'needs_upgrade').length,
  no_membership: data.filter(d => d.compliance_status === 'no_membership').length,
  total: data.length
}
```

## Compliance Status Values

| Status | Icon | Meaning | Color |
|--------|------|---------|-------|
| `compliant` | ✅ | Has active Program Partner subscription | Green |
| `needs_upgrade` | ⚠️ | Has Individual membership, needs upgrade | Yellow |
| `no_membership` | ❌ | No active membership at all | Red |
| `trial` | ⏳ | In trial period | Blue |

## Next Steps

1. **Add Email Notifications**: Create automated emails for non-compliant partners
2. **Dashboard Widget**: Add `ComplianceSummary` to the main dashboard
3. **Bulk Actions**: Add ability to email all non-compliant partners
4. **Reports**: Export non-compliant partners list to CSV
5. **Automated Reminders**: Set up monthly compliance check reminders

## Testing

### Test the Filter
1. Go to Contacts page
2. Select "Expected Partners" from Program Partner Status filter
3. Verify 41 contacts are shown
4. Select "Compliant" - should show 13 contacts
5. Select "Needs Upgrade" - should show 11 contacts
6. Select "No Membership" - should show 17 contacts

### Test the Badges
1. View contact list
2. Verify badges appear next to expected partners
3. Hover over badges to see detailed compliance messages
4. Check color coding matches status

## Database Schema Reference

### Contacts Table
```sql
ALTER TABLE contacts
ADD COLUMN is_expected_program_partner BOOLEAN DEFAULT FALSE;
```

### Views Available
- `program_partner_compliance` - Detailed compliance view with all expected partners
- `v_contact_list_with_subscriptions` - Main contact list view (now includes compliance fields)

### Compliance Status Enum
- `compliant` - Has active Program Partner subscription
- `needs_upgrade` - Has Individual membership
- `no_membership` - No active subscription
- `trial` - In trial period
