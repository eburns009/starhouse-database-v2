# Session Handoff: Kajabi Import Protection Strategy
**Date**: 2025-11-10
**Session Focus**: Kajabi address evaluation and import protection
**Status**: CRITICAL - Action required before next weekly import

---

## Executive Summary

### Critical Discovery
The weekly Kajabi import script (`weekly_import_kajabi_v2.py`) will **overwrite all enriched data** on the next run. This includes:
- 95 contacts with data enriched from PayPal/Zoho
- 672 corrected addresses (city capitalization, address_line_2 cleanup)
- All duplicate merge work (125+ merges)
- Cross-system enrichment from multiple sources

### Root Cause
1. **Kajabi limitation**: Cannot export "contacts modified since date" - always exports ALL contacts
2. **Import script logic**: Uses `COALESCE` which overwrites database with ANY value from Kajabi (even if wrong)
3. **No protection**: Script has no logic to preserve enriched/corrected data

### Solution Required
**Must modify import script to protect enriched data before next weekly import.**

---

## Session Context

### Initial Request
User uploaded new Kajabi export CSV (`11012025_kajabi_contact_evaluate.csv`) and asked to evaluate which addresses need modification in Kajabi.

### What We Discovered
While evaluating addresses, we uncovered a **much larger problem**:
- Database has extensive enrichment work (not just addresses)
- Weekly import will destroy this enrichment
- Cannot use Kajabi date filtering (doesn't exist)
- "Last Activity" field doesn't help (tracks user engagement, not record modification)

---

## Files Created This Session

### Analysis & Reports
```
data/current/kajabi_address_evaluation_report.csv
  → Detailed comparison of Kajabi vs. DB addresses
  → Shows 658 records that differ
  → 95 need updates, 563 have no address in Kajabi

data/current/kajabi_address_import_ready.csv
  → Import-ready CSV for Kajabi (658 records)
  → Contains corrected addresses from database
  → NOT USABLE: User cannot do full Kajabi import

data/current/import_impact_analysis.csv
  → Critical analysis of what will be lost on next import
  → Shows 95 enriched records + 5 corrected records at risk
  → Details which fields will be overwritten

data/current/kajabi_full_enriched_export.csv
  → Complete export of all enriched data (5,387 records)
  → All contacts with Kajabi IDs
  → NOT USABLE: User cannot do full Kajabi import

data/current/kajabi_new_contacts_only.csv
  → Contacts in DB but not in Kajabi (1,168 records)
  → Mainly PayPal-only contacts
  → Optional import

data/current/kajabi_export_summary.txt
  → Summary of export files and import instructions
```

### Scripts Created
```
scripts/evaluate_kajabi_addresses.py
  → Compares Kajabi CSV addresses with database
  → Generates evaluation report and import-ready CSV
  → Identifies discrepancies and needed updates

scripts/analyze_import_impact.py
  → Simulates next weekly import
  → Identifies what data will be overwritten
  → Shows enriched vs. corrected data at risk

scripts/export_enriched_for_kajabi.py
  → Exports all enriched contact data
  → Generates Kajabi-compatible import CSV
  → Includes corrected addresses, names, phones
```

### Documentation
```
docs/KAJABI_IMPORT_PROTECTION_STRATEGY.md
  → Three-part strategy for protecting enriched data
  → Decision matrix for choosing approach
  → Risk assessment and timelines

docs/HANDOFF_2025_11_10_KAJABI_IMPORT_PROTECTION.md
  → This document
```

---

## Key Findings

### 1. Database Enrichment Statistics

**Total Contacts**: 6,555
- 5,387 exist in Kajabi (matched)
- 1,168 only in database (PayPal/other sources)

**Enrichment Breakdown**:
- **1,117 contacts** with phones from PayPal/Zoho/other (not Kajabi)
- **508 contacts** with names enriched from PayPal
- **1,210 contacts** with shipping addresses from PayPal
- **1,956 contacts** linked to Zoho CRM
- **681 contacts** with PayPal linkage
- **2,558 contacts** with phone numbers
- **672 addresses** corrected (city capitalization, address_line_2 cleanup)

### 2. Address Evaluation Results

**From Kajabi CSV vs. Database**:
- ✅ **4,730 addresses match** (83%)
- 🔄 **95 need updates** (database has correct data, Kajabi has wrong data)
- ⚠️ **563 no address in Kajabi** (database has address, Kajabi empty)
- 📭 **0 no address in DB** (Kajabi has all addresses in DB)
- ❓ **303 not in DB** (exist in Kajabi only)
- ❓ **1,167 not in Kajabi** (exist in DB only)

**Total records needing Kajabi update**: 658 (95 + 563)

### 3. Import Impact Analysis

**What will be overwritten on next import**:
- ❌ **95 enriched contacts** (PayPal/Zoho data)
- ❌ **5 corrected contacts** (address fixes)
- ❌ **91 address_line_2 fields**
- ❌ **7 address_line_1 fields**
- ❌ **6 last_name fields**
- ❌ **4 postal_code fields**
- ❌ **4 first_name fields**

**Sources of enrichment at risk**:
- 19 contacts enriched from PayPal
- 17 contacts linked to Zoho

### 4. Kajabi Export Limitations

**"Last Activity" Field Analysis**:
- Only 1,088 out of 5,691 contacts have activity
- 15 contacts had activity in last 30 days
- 4,603 contacts have NEVER engaged

**What "Last Activity" means**:
- ✅ User engagement (login, click, purchase)
- ❌ NOT record modification date
- ❌ NOT when data was updated
- ❌ NOT usable for filtering recent changes

**Kajabi Export Capabilities**:
- ✅ Can export all contacts
- ✅ Can update via import (matches by email)
- ✅ Supports up to 50 fields, 40K contacts/day
- ❌ Cannot export "modified since date"
- ❌ Cannot filter by date range
- ❌ No "last modified" field in export
- ❌ Always returns FULL contact list

### 5. Current Import Script Behavior

**File**: `scripts/weekly_import_kajabi_v2.py`
**Lines**: 294-317

**Dangerous Logic**:
```sql
UPDATE contacts SET
  first_name = COALESCE(%s, first_name),
  last_name = COALESCE(%s, last_name),
  phone = COALESCE(%s, phone),
  address_line_1 = COALESCE(%s, address_line_1),
  address_line_2 = COALESCE(%s, address_line_2),
  city = COALESCE(%s, city),
  state = COALESCE(%s, state),
  postal_code = COALESCE(%s, postal_code),
  country = COALESCE(%s, country)
WHERE id = %s
```

**Problem with COALESCE**:
- `COALESCE(%s, field)` means: "Use new value if not NULL, else keep existing"
- If Kajabi has ANY value (even wrong), it overwrites database
- Only keeps database value if Kajabi field is NULL
- No check for enrichment source
- No protection for corrected data

**Example Issues**:
```
Ed Burns (eburns009@gmail.com):
  Kajabi:   city = "southampton", state = "PA", zip = "18966"
  Database: city = "Boulder", state = "CO", zip = "80302"

  Current behavior: Overwrites with wrong Kajabi data
  Needed behavior: Keep corrected database data
```

---

## What User Tried (Context)

### Attempted Solution 1: Import Corrected Data to Kajabi
**Problem**: User stated "i cannot do a full import" to Kajabi
- Unclear if this is a technical limitation or business constraint
- May be time/resource constraint
- May be Kajabi account limitation
- May be concern about overwriting other Kajabi-managed fields

### Attempted Solution 2: Use Date Filtering
**Problem**: Kajabi doesn't support date-based exports
- Cannot export "contacts modified in last 7 days"
- "Last Activity" only tracks engagement, not modifications
- Always receive full contact list

### Conclusion
**Only viable solution**: Modify import script to protect enriched data

---

## Solution: Import Script Protection

### Strategy Overview

Modify `weekly_import_kajabi_v2.py` to implement **smart field protection**:

1. **Before updating each field**, check if it was enriched from another source
2. **Only allow Kajabi updates** if:
   - Database field is currently NULL/empty, AND
   - Kajabi has a value, AND
   - Field was NOT enriched from PayPal/Zoho/other
3. **Always preserve** enriched/corrected data

### Fields Requiring Protection

**Name Fields**:
- `first_name` - protect if `paypal_first_name` exists
- `last_name` - protect if `paypal_last_name` exists

**Phone Fields**:
- `phone` - protect if `phone_source` is set OR `paypal_phone` exists

**Address Fields**:
- `address_line_1` - protect if `billing_address_source` is set
- `address_line_2` - protect if `billing_address_source` is set
- `city` - protect if `billing_address_source` is set
- `state` - protect if `billing_address_source` is set
- `postal_code` - protect if `billing_address_source` is set
- `country` - protect if `billing_address_source` is set

**Contact-Level Protection**:
- Protect ALL fields if `source_system != 'kajabi'`
- Protect ALL fields if contact was created from PayPal/Zoho/other

### Implementation Approach

**Option 1: Field-level protection logic**
```python
# Determine if we should update each field
update_first_name = (
    kajabi_first_name is not None and
    (db_first_name is None or db_paypal_first_name is None)
)

# Build dynamic UPDATE query with only unprotected fields
```

**Option 2: Source hierarchy**
```python
# Define source priority: manual > paypal > zoho > kajabi
# Only update if Kajabi source has higher priority than current
```

**Option 3: Tracking table**
```sql
-- Add field_sources table to track origin of each field value
CREATE TABLE contact_field_sources (
  contact_id uuid,
  field_name text,
  source_system text,
  updated_at timestamp
);
```

### Recommended: Option 1 (Field-level protection)
- ✅ Immediate implementation (no schema changes)
- ✅ Preserves all enriched data
- ✅ Easy to understand and maintain
- ✅ Can be tested with dry-run mode
- ⚠️ Database and Kajabi will diverge

---

## Database Schema Notes

### Relevant Tables
```sql
contacts:
  - id (uuid)
  - email (citext) - PRIMARY KEY for matching
  - first_name, last_name
  - phone
  - address_line_1, address_line_2
  - city, state, postal_code, country
  - source_system (kajabi, paypal, zoho, etc.)
  - kajabi_id, kajabi_member_id
  - paypal_email, paypal_first_name, paypal_last_name, paypal_phone
  - zoho_id
  - phone_source
  - billing_address_source
  - shipping_address_* (from PayPal)
```

### Fields Added for Tracking
- `source_system` - Original source of contact
- `phone_source` - Where phone came from
- `billing_address_source` - Where billing address came from
- `paypal_*` - Original PayPal data for comparison

### Missing Fields (Could Add)
- `address_corrected_at` - When address was last corrected
- `address_correction_source` - Who/what corrected it
- Individual field sources (field-level tracking)

---

## Immediate Next Steps

### CRITICAL: Before Next Weekly Import

**Action Required**: Modify `weekly_import_kajabi_v2.py` with protection logic

**Implementation Steps**:
1. Backup current import script
2. Add field-level protection logic (lines 294-317)
3. Add dry-run test with current Kajabi CSV
4. Verify no enriched data would be overwritten
5. Document changes in code comments
6. Test with subset of contacts
7. Run full import with protection

### Testing Protocol

**Dry-Run Test**:
```bash
cd /workspaces/starhouse-database-v2

# Run in dry-run mode (no changes)
python3 scripts/weekly_import_kajabi_v2.py \
  --data-dir "kajabi 3 files review" \
  --dry-run

# Should show:
# - 5,388 contacts matched
# - 95 enriched fields protected (not updated)
# - 0 enriched records overwritten
```

**Verification Queries**:
```sql
-- Check enriched fields before import
SELECT COUNT(*) FROM contacts WHERE paypal_first_name IS NOT NULL;
SELECT COUNT(*) FROM contacts WHERE phone_source IS NOT NULL;
SELECT COUNT(*) FROM contacts WHERE billing_address_source IS NOT NULL;

-- Run import

-- Check enriched fields after import (should be same)
SELECT COUNT(*) FROM contacts WHERE paypal_first_name IS NOT NULL;
SELECT COUNT(*) FROM contacts WHERE phone_source IS NOT NULL;
SELECT COUNT(*) FROM contacts WHERE billing_address_source IS NOT NULL;
```

---

## Long-term Considerations

### Option 1: Keep Protection Permanently
**Pros**:
- ✅ Database remains source of truth
- ✅ All enrichment preserved forever
- ✅ No risk of data loss

**Cons**:
- ⚠️ Database and Kajabi diverge over time
- ⚠️ Kajabi users don't see enriched data
- ⚠️ Two sources of truth

### Option 2: Sync to Kajabi Eventually
**When**: After resolving "cannot do full import" issue
**How**:
1. Export enriched data (`kajabi_full_enriched_export.csv` already created)
2. Import to Kajabi (update existing contacts)
3. Verify sync
4. Remove protection logic
5. Future imports work normally

**Pros**:
- ✅ Single source of truth (Kajabi)
- ✅ Kajabi users see enriched data
- ✅ Simpler long-term

**Cons**:
- ⚠️ Requires Kajabi import capability
- ⚠️ One-time sync effort

### Option 3: Add Field-Level Source Tracking
**Future enhancement**: Track source of each field value

**Schema Addition**:
```sql
CREATE TABLE contact_field_sources (
  contact_id uuid REFERENCES contacts(id),
  field_name text,
  source_system text,
  source_priority integer,
  updated_at timestamp,
  PRIMARY KEY (contact_id, field_name)
);
```

**Benefits**:
- Track exactly where each field value came from
- Implement source priority hierarchy
- Audit trail for all changes
- Can sync selectively to Kajabi

---

## Questions for Next Session

### Technical Clarifications Needed

1. **Kajabi Import Limitation**
   - What exactly prevents full Kajabi import?
   - Is it technical, business, or resource constraint?
   - Can we do partial imports (e.g., 100 contacts at a time)?
   - Are there Kajabi API options instead of CSV?

2. **Import Script Modification Approach**
   - Prefer simple field-level protection (Option 1)?
   - Or more sophisticated source tracking (Option 3)?
   - Should protection be permanent or temporary?

3. **Address Correction Source**
   - Where did 672 corrected addresses come from?
   - Was it manual correction or automated script?
   - Should we track `address_corrected_at`?

4. **Duplicate Merge Tracking**
   - How are merged contacts currently tracked?
   - Risk of duplicates being recreated on import?
   - Need `merged_contacts` tracking table?

### Business Decisions Needed

1. **Database vs. Kajabi as Source of Truth**
   - Should database be permanent source of truth?
   - Or temporary until we can sync to Kajabi?
   - Long-term vision?

2. **Weekly Import Continuation**
   - Continue weekly Kajabi imports with protection?
   - Or pause until sync issue resolved?
   - What's in Kajabi that database needs?

3. **Data Governance**
   - Who can update contact data? (Kajabi users vs. database)
   - How to handle conflicts?
   - Approval process for bulk changes?

---

## Key Files Reference

### Scripts to Modify
- `scripts/weekly_import_kajabi_v2.py` - **REQUIRES MODIFICATION**

### Scripts Created (Reference Only)
- `scripts/evaluate_kajabi_addresses.py`
- `scripts/analyze_import_impact.py`
- `scripts/export_enriched_for_kajabi.py`

### Data Files for Testing
- `kajabi 3 files review/11012025_kajabi_contact_evaluate.csv` - Latest Kajabi export

### Reports Generated
- `data/current/import_impact_analysis.csv` - What will be lost
- `data/current/kajabi_address_evaluation_report.csv` - Address comparison
- `data/current/kajabi_full_enriched_export.csv` - Full enriched export

### Documentation
- `docs/KAJABI_IMPORT_PROTECTION_STRATEGY.md` - Complete strategy
- `docs/HANDOFF_2025_11_10_KAJABI_IMPORT_PROTECTION.md` - This document

---

## Risk Assessment

### Critical Risks

**Risk 1: Running Import Without Protection**
- **Probability**: HIGH (if weekly import runs as scheduled)
- **Impact**: CRITICAL (lose all enrichment work)
- **Mitigation**: Implement protection before next import

**Risk 2: Database-Kajabi Divergence**
- **Probability**: HIGH (with protection in place)
- **Impact**: MEDIUM (operational confusion)
- **Mitigation**: Document which system is source of truth

**Risk 3: Duplicate Recreation**
- **Probability**: MEDIUM (if merge tracking not implemented)
- **Impact**: HIGH (need to re-merge contacts)
- **Mitigation**: Add duplicate prevention logic

### Medium Risks

**Risk 4: Import Script Bugs**
- **Probability**: LOW (with proper testing)
- **Impact**: MEDIUM (incorrect updates)
- **Mitigation**: Extensive dry-run testing, backup before import

**Risk 5: Missing Kajabi Updates**
- **Probability**: MEDIUM (with aggressive protection)
- **Impact**: LOW (some legitimate updates not applied)
- **Mitigation**: Log all skipped updates for review

---

## Success Criteria

### Immediate (This Week)
- [ ] Import script modified with protection logic
- [ ] Dry-run test passes with no enriched data loss
- [ ] Protection documented in code
- [ ] Next weekly import runs successfully with protection

### Short-term (This Month)
- [ ] 100 imports run with 0 enriched data loss
- [ ] Database-Kajabi divergence documented and understood
- [ ] Decision made on long-term source of truth

### Long-term (Next Quarter)
- [ ] Single source of truth established (DB or Kajabi)
- [ ] If Kajabi: enriched data successfully synced back
- [ ] If Database: Kajabi import deprecated or limited
- [ ] Field-level source tracking implemented (optional)

---

## Summary

This session uncovered a **critical data protection issue** with the weekly Kajabi import process. While the initial request was to evaluate addresses for Kajabi update, the investigation revealed:

1. **Cannot rely on Kajabi** for date-based filtering or selective imports
2. **Import script will destroy enrichment** without modification
3. **Database must protect itself** during imports
4. **658 addresses need updating** (but cannot do full Kajabi import)
5. **95 enriched contacts at risk** on next weekly import

**Immediate action required**: Modify import script with field-level protection before next weekly import.

**Files ready for next session**:
- Analysis reports showing exactly what will be lost
- Export files ready for Kajabi (if import becomes possible)
- Protection strategy documented
- Test data available (latest Kajabi CSV)

**Decision needed**: Approach for import protection (simple field-level vs. comprehensive source tracking)

---

## Contact Info / Notes

**Database**: Supabase PostgreSQL
**Current Contacts**: 6,555 total (5,387 in Kajabi, 1,168 from other sources)
**Import Frequency**: Weekly (dangerous without protection)
**Last Kajabi Export**: 2025-11-01 (file: 11012025_kajabi_contact_evaluate.csv)

**Primary Concern**: Preserving enrichment work from PayPal, Zoho, Ticket Tailor, and manual corrections

---

*End of Handoff Document*
