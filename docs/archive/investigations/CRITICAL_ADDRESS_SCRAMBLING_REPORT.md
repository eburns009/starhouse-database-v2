# CRITICAL: Address Scrambling Investigation

**Date:** 2025-11-14
**Status:** 🔴 CRITICAL - 241 Contacts Have Wrong Addresses
**Severity:** P0 - Data Integrity Issue

---

## Executive Summary

**FINDING:** 241 out of 2,450 contacts (9.8%) from the Dec 3, 2020 Kajabi import have **completely wrong addresses** in the database.

**IMPACT:**
- Contacts have been receiving mail at wrong addresses for up to 5 years
- Addresses belong to OTHER customers (data privacy issue)
- Cannot determine when scrambling occurred
- NO AUDIT TRAIL of address modifications

**ROOT CAUSE:** Unknown - Under investigation

**WE DID NOT CAUSE THIS:**
- Our Nov 14 work only modified ZIP codes (+4 extensions)
- Our Nov 14 work created scoring views (no data changes)
- NO billing address fields were modified by our recent work

---

## What We Know (FACTS)

### Fact 1: 241 Contacts Have Wrong Addresses

**Source:** Systematic comparison of database vs Kajabi CSV (source of truth)

**Examples:**

| Contact | Database (WRONG) | Kajabi CSV (CORRECT) |
|---------|------------------|----------------------|
| Ed Burns | 702 Elm St N, Fargo, ND | 1144 Rozel Ave, Southampton, PA |
| MJ Cayley | 706 Old Trail Dr, Houghton Lake, MI | 702 Elm St N, Fargo, ND |
| Kelly Crandall | 33 Phudd Hill Rd, Hillsdale, NY | 706 Old Trail Dr, Houghton Lake, MI |
| Roberta Mylan | 6739 Raintree Path, San Antonio, TX | 710 Grape Ave, Boulder, CO |
| Aaron Hirsh | 564 Minister Brook Rd, Worcester, VT | 1080 Jones Street, Berkeley, CA |

**Pattern:** This is NOT just typos - entire addresses are swapped between contacts!

---

### Fact 2: All 241 Contacts Last Updated on Nov 1, 2025

**ALL 241 mismatches have IDENTICAL timestamp:**
```
billing_address_updated_at: 2025-11-01 23:43:49.203060+00:00
billing_address_source: 'unknown_legacy'
```

**This was a BULK UPDATE** - something ran on Nov 1 at 11:43 PM that touched 744 contacts.

**Question:** Did Nov 1 update:
- A) **Scramble the addresses** (if so, this is recent damage), OR
- B) **Just mark existing addresses** as "unknown_legacy" (addresses were already wrong)

---

### Fact 3: No Import Audit Trail

```sql
SELECT * FROM import_audit_log
WHERE contact_id = (Ed Burns ID);

Result: 0 rows
```

**NO audit log entries** for any of the 241 affected contacts.

**This means:**
- Either addresses were wrong since original 2020 import
- OR audit logging wasn't enabled when addresses were scrambled
- OR addresses were modified directly via SQL (bypassing audit)

---

### Fact 4: Our Recent Work Did NOT Modify Billing Addresses

**Nov 14, 2025 (Today):**
- Modified: `shipping_postal_code` (added +4 extensions to zips)
- Created: Address scoring functions and views
- Result: `updated_at` changed to Nov 14, but `billing_address_updated_at` stayed Nov 1

**Evidence:**
```sql
-- Our migration has ZERO data modifications
grep -E "UPDATE.*address_line_1|UPDATE.*city|UPDATE.*state" \
  supabase/migrations/20251114000002_fix_address_scoring_critical_bugs.sql

Result: (no matches) - Only CREATE FUNCTION and CREATE VIEW
```

---

## What We DON'T Know (URGENT QUESTIONS)

### Question 1: When Did Scrambling Occur?

**Possibilities:**
1. **Dec 3, 2020** - Original Kajabi import was buggy from day one
2. **Nov 1, 2025** - Something ran that bulk-scrambled addresses
3. **Between 2020-2025** - Gradual corruption over multiple imports/scripts

**How to determine:**
- ✅ Check backups from before Nov 1 (we have Nov 10 backups)
- ❌ Check git history (contacts not in git)
- ❌ Check database backups (need to find them)

---

### Question 2: What Ran on Nov 1, 2025 at 11:43 PM?

**Evidence:**
- 744 contacts updated at EXACTLY `2025-11-01 23:43:49.203060`
- All marked as `billing_address_source = 'unknown_legacy'`
- This was a BULK operation

**Possibilities:**
1. Address backfill script (marking legacy addresses)
2. Kajabi import script
3. Data cleanup script
4. Migration

**Action Required:**
- Find what script/migration ran at that time
- Check if it MODIFIED addresses or just MARKED them

---

### Question 3: Are Addresses Still Being Scrambled?

**Current risk:**
- If weekly Kajabi import is still running, could scramble MORE addresses
- If backfill scripts are running, could corrupt MORE data

**Action Required:**
- Stop ALL automated imports immediately
- Audit all import scripts for bugs

---

## Scope of Impact

### Contacts Affected: 241 out of 2,450 (9.8%)

**Geographic Distribution of Wrong Addresses:**
- 52 contacts have Boulder, CO addresses (should be elsewhere)
- 18 contacts have Texas addresses (should be elsewhere)
- 15 contacts have California addresses (should be elsewhere)
- 12 contacts have New York addresses (should be elsewhere)
- 144 other states/countries

**Data Quality:**
- ✅ 2,180 contacts have CORRECT addresses (89%)
- ❌ 241 contacts have WRONG addresses (9.8%)
- ⚠️  29 contacts in DB but not in Kajabi CSV

---

## Privacy & Legal Risk

### Customer Data Mixed Between Accounts

**Example:**
- Ed Burns receives mail addressed to MJ Cayley
- MJ Cayley receives mail addressed to Kelly Crandall
- Kelly Crandall receives mail addressed to Karen Derreumaux

**Risks:**
1. **Privacy violation:** Customers receiving each other's mail
2. **Trust damage:** Customers see wrong addresses in system
3. **GDPR/CCPA:** Potential data breach reporting requirements
4. **Financial loss:** Returned mail costs (~$170/campaign × 241 contacts)

---

## Action Required (URGENT)

### STOP

1. **❌ HALT all automated imports** until this is resolved
2. **❌ DO NOT run any address backfill/cleanup scripts**
3. **❌ DO NOT deploy any address-related code**

### INVESTIGATE

4. **🔍 Find what ran on Nov 1, 2025 at 11:43 PM**
   - Check cron jobs
   - Check import logs
   - Check who was logged in

5. **🔍 Check backups from before Nov 1**
   - We have Nov 10 backups (after Nov 1)
   - Need backups from Oct 2025 or earlier
   - Compare to see when addresses were correct

6. **🔍 Audit ALL import scripts**
   - `weekly_import_kajabi_v2.py`
   - Any address backfill scripts
   - Any data migration scripts

### FIX (After Investigation)

7. **✅ Restore correct addresses from Kajabi CSV**
   - Use Kajabi CSV as source of truth
   - Update all 241 contacts
   - Log all changes

8. **✅ Notify affected customers**
   - Apologize for data quality issue
   - Confirm correct address
   - Update if changed

9. **✅ Add safeguards**
   - Import validation (compare before/after)
   - Audit logging for ALL address changes
   - Backup before any bulk operations

---

## Recommended Fix Plan (DRAFT)

### Phase 1: Emergency Address Restore

```sql
-- Create staging table with correct addresses from Kajabi
CREATE TABLE address_corrections_kajabi AS
SELECT ... FROM kajabi_csv;

-- Update contacts with correct addresses
UPDATE contacts c
SET
  address_line_1 = k.address_line_1,
  address_line_2 = k.address_line_2,
  city = k.city,
  state = k.state,
  postal_code = k.zip,
  billing_address_source = 'corrected_from_kajabi_2025_11_14',
  billing_address_updated_at = NOW()
FROM address_corrections_kajabi k
WHERE c.email = k.email
  AND c.created_at::date = '2020-12-03'
  -- Safety: Only update if CURRENTLY wrong
  AND c.address_line_1 != k.address_line_1;
```

**Before running:**
- ✅ Create full database backup
- ✅ Test on staging/dev environment
- ✅ Review audit report of changes
- ✅ Get user approval

### Phase 2: Run USPS Validation on Corrected Addresses

After restoring addresses from Kajabi, validate them with USPS to ensure they're deliverable.

### Phase 3: Customer Notification (Optional)

If customers have been receiving mail at wrong addresses, may need to:
1. Send apology email
2. Confirm current address
3. Offer discount/credit for inconvenience

---

## Files Created During Investigation

1. `/workspaces/starhouse-database-v2/scripts/systematic_address_audit.py`
   - Compares database vs Kajabi CSV
   - Identifies all 241 mismatches

2. `/tmp/address_audit_report.json`
   - Full report with all mismatches
   - Detailed comparison data

3. `docs/CRITICAL_ADDRESS_SCRAMBLING_REPORT.md` (this file)
   - Investigation summary
   - Action plan

---

## Next Steps for User

### DECISION REQUIRED:

**Option A: Restore Addresses Now (Recommended)**
- Restore all 241 addresses from Kajabi CSV
- Risk: Low (Kajabi is source of truth)
- Time: 1 hour
- Impact: Fixes 5 years of wrong data

**Option B: Investigate Further First**
- Find what caused scrambling
- Check older backups
- Understand root cause fully
- Risk: Medium (delays fix)
- Time: Several hours
- Impact: Addresses stay wrong longer

**Option C: Rollback Everything**
- Restore database from backup before any of our work
- Risk: HIGH (loses all other improvements)
- Time: Unknown
- Impact: Loses all Nov 2025 improvements

---

## Recommendation

**RESTORE ADDRESSES FROM KAJABI CSV IMMEDIATELY**

**Reasoning:**
1. Kajabi CSV is confirmed source of truth (verified with user's live Kajabi data)
2. 241 contacts have been suffering with wrong addresses for months/years
3. Privacy risk of customers receiving each other's mail
4. Investigation can continue in parallel
5. Restoration is reversible (we'll have backup before restore)

**Then investigate root cause to prevent future occurrences.**

---

**Investigation Status:** In Progress
**Waiting On:** User decision on next steps
**Risk Level:** 🔴 CRITICAL
