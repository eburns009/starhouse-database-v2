# Address Root Cause Analysis - Ed Burns & Similar Cases

**Date:** 2025-11-14  
**Investigator:** Claude Code  
**Trigger:** Ed Burns (eburns009@gmail.com) showing wrong city/state/zip for 2nd address

---

## Executive Summary

**Root Cause:** Data quality issue in Kajabi where 3 contacts have two completely different addresses incorrectly stored as Line 1 + Line 2 in a single billing address object.

**Impact:** 3 contacts (Ed Burns, Tataya Bailey, Laura Blanco) showing incorrect/confusing address displays.

**Status:** 
- ✅ Root cause identified
- ✅ UI fixed to display correctly with available data
- ⏳ Kajabi data cleanup required (manual)

---

## Investigation Timeline

### Initial Report
User reported Ed Burns' 2nd address showing "Southampton, PA 18966" instead of "Boulder, CO 80306"

### Database Analysis (2025-11-14)

**Findings:**
1. No audit logs - `audit_log` table is empty (audit tracking not yet active)
2. No import audit trails for Ed Burns
3. Contact created: 2020-12-03 from Kajabi
4. Last updated: 2025-11-13 22:43:05 (bulk city name standardization)
5. Data structure unchanged since original Kajabi import

**Ed Burns Current Data:**
```
address_line_1: 1144 Rozel Ave
address_line_2: 3472 Sunshine Canyon Rd  ← DIFFERENT ADDRESS!
city: Southampton
state: PA
postal_code: 18966

shipping_address_line_1: PO Box 4547
shipping_address_line_2: 3472 Sunshine Canyon Rd
shipping_city: Boulder
shipping_state: CO
shipping_postal_code: 80306
```

### Pattern Analysis

**Searched for:** All contacts with address_line_2 starting with a street number  
**Found:** 10 contacts total

**Categories:**

1. **CRITICAL - Different Addresses (3 contacts):**
   - Ed Burns - Two addresses in different cities
   - Tataya Bailey - Two addresses in different cities
   - Laura Blanco - Two addresses in same city (Spain)

2. **NON-CRITICAL - Duplicates (7 contacts):**
   - Same address with minor formatting differences
   - Apartment/unit numbers
   - No data quality issue, just redundant

---

## Root Cause: Kajabi Data Structure

**How it happened:**

Kajabi's billing address form has:
```
Address Line 1: [text field]
Address Line 2: [text field]
City: [text field]
State: [text field]
Zip: [text field]
```

**Expected use:**
```
Line 1: 1144 Rozel Ave
Line 2: Apt 5B         ← Same address, just unit number
City: Southampton
State: PA
Zip: 18966
```

**What actually happened:**
```
Line 1: 1144 Rozel Ave     ← First complete address
Line 2: 3472 Sunshine Canyon Rd  ← SECOND complete address!
City: Southampton          ← Only applies to Line 1!
State: PA
Zip: 18966
```

**Why this is wrong:**
- Kajabi stores ONE city/state/zip for the billing address
- If Line 2 is a different address, it has the WRONG city/state/zip
- The system assumes Line 1 + Line 2 are parts of the same address

---

## Solution Implemented

### UI Fix (2025-11-14)

**File:** `starhouse-ui/components/contacts/ContactDetailCard.tsx`

**Changes:**

1. **Detect when address_line_2 is a separate address** (lines 235-240)
2. **Use shipping data for correct city/state/zip** (lines 257-277)
3. **Add city/state/zip to shipping address display** (lines 308-311)

**Result for Ed Burns:**
- ✅ Primary: 1144 Rozel Ave, Southampton, PA 18966
- ✅ Alternate: 3472 Sunshine Canyon Rd, Boulder, CO 80306 (from shipping data)
- ✅ Shipping: PO Box 4547, Boulder, CO 80306

**Before UI fix:**
- ❌ Alternate showed: 3472 Sunshine Canyon Rd, Southampton, PA 18966 (WRONG!)

### Kajabi Cleanup Required

See: `/tmp/kajabi_fix_guide.md` for detailed steps

**Summary:**
1. Log into Kajabi
2. Edit each of the 3 critical contacts
3. Remove the incorrect address from Line 2
4. Keep only the current/primary address in billing address fields

**Post-Kajabi cleanup (optional):**
```sql
-- After fixing Kajabi, optionally clean database
UPDATE contacts SET address_line_2 = NULL WHERE email = 'eburns009@gmail.com';
UPDATE contacts SET address_line_2 = NULL WHERE email = 'tataya@prismaleadership.com';
UPDATE contacts SET address_line_2 = NULL WHERE email = 'blancogutierrezlaura@gmail.com';
```

---

## Why Database vs. UI?

**Question:** Is this a database issue or UI issue?

**Answer:** BOTH.

1. **Database (Data Quality):**
   - Database correctly reflects what Kajabi sent
   - But Kajabi's data is malformed (two addresses in one object)
   - Source: Kajabi

2. **UI (Display Logic):**
   - UI needs to handle the malformed data gracefully
   - Solution: Use shipping address data as fallback
   - Fixed: 2025-11-14

---

## Prevention

**Going forward:**

Since you're not using Kajabi webhooks anymore, this is a one-time cleanup issue.

**Best practice for address data entry:**
- Address Line 2 should only be used for: Apt, Suite, Unit, Floor, Building, etc.
- Never enter a completely different street address in Line 2
- Use separate "Shipping Address" fields for alternate addresses

---

## Files Modified

1. `starhouse-ui/components/contacts/ContactDetailCard.tsx`
   - Added shipping city/state/postal_code to shipping address variant (lines 308-311)
   - Previous fix (Nov 13): Use shipping data for alternate address city/state/zip

2. `docs/ADDRESS_ROOT_CAUSE_ANALYSIS.md` (this file)
   - Complete investigation documentation

---

## Next Steps

- [ ] User: Fix 3 contacts in Kajabi (see `/tmp/kajabi_fix_guide.md`)
- [ ] User: Optionally clean database with SQL after Kajabi fixes
- [ ] Future: Consider adding webhook validation if re-enabling Kajabi webhooks

---

## Affected Contacts Summary

| Email | Issue | Status | Action Required |
|-------|-------|--------|-----------------|
| eburns009@gmail.com | Different cities (PA vs CO) | Critical | Remove Line 2 in Kajabi |
| tataya@prismaleadership.com | Different cities (AZ vs CO?) | Critical | Research + remove Line 2 |
| blancogutierrezlaura@gmail.com | Different streets (Spain) | Medium | Verify + possibly remove Line 2 |

---

**Investigation Complete:** 2025-11-14  
**UI Fix Status:** ✅ Complete  
**Kajabi Fix Status:** ⏳ User action required  
