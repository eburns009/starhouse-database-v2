# Kajabi Import Protection Strategy
**Date**: 2025-11-10
**Critical Issue**: Next Kajabi import will overwrite enriched data

## Problem Statement

### Current Situation
- **Database has 6,555 contacts** with enriched data from multiple sources:
  - 1,117 phone numbers from PayPal/Zoho/other sources
  - 508 names enriched from PayPal
  - 1,210 shipping addresses from PayPal
  - 1,956 contacts linked to Zoho
  - 672 addresses corrected (capitalization, StarHouse de-duplication)
  - 125+ duplicate contacts merged

### The Problem
- **Kajabi doesn't support date-based exports** (can't export "new contacts since last week")
- Weekly import script receives **full Kajabi export** every time
- Current import logic uses `COALESCE` which means:
  - If Kajabi has a value (even if wrong), it overwrites database
  - Only keeps database value if Kajabi field is NULL
- **Result**: Every weekly import overwrites all enriched/corrected data

### Impact of Next Import (Without Protection)
- ❌ **95 contacts with enriched data** would be overwritten
- ❌ **5 contacts with corrected data** would be lost
- ❌ **19 PayPal-enriched contacts** would lose data
- ❌ **17 Zoho-linked contacts** would lose data
- ❌ **All duplicate merge work** would be undone (duplicates recreated)

## Solution: Three-Part Strategy

### Part 1: IMMEDIATE - Protect Enriched Data (Import Script Modification)

**Goal**: Modify `weekly_import_kajabi_v2.py` to NEVER overwrite enriched data

**Implementation**:
1. Add field-level protection logic
2. Check if each field was enriched from another source
3. Only allow Kajabi to update fields that are:
   - Currently empty/null in database, OR
   - NOT enriched from another source

**Protected Fields**:
- `first_name` - if `paypal_first_name` exists
- `last_name` - if `paypal_last_name` exists
- `phone` - if `phone_source` is set or `paypal_phone` exists
- `address_*` - if `billing_address_source` is set
- All fields for contacts where `source_system != 'kajabi'`

**Benefits**:
- ✅ Immediate protection
- ✅ No data loss
- ✅ Preserves all enrichment work
- ✅ Can run weekly imports safely

**Drawbacks**:
- ⚠️ Database and Kajabi will be out of sync
- ⚠️ Kajabi users won't see corrected data
- ⚠️ Temporary solution only

### Part 2: SHORT-TERM - Export Enriched Data to Kajabi

**Goal**: Update Kajabi with all corrected/enriched data so it becomes the clean source

**Steps**:
1. Export ALL contacts from database (5,388 that exist in both systems)
2. Include ALL enriched fields:
   - Corrected names
   - Validated phone numbers
   - Corrected addresses (city capitalization, address_line_2 cleanup)
   - All enriched data
3. Import to Kajabi using their bulk import
4. Re-export clean CSV from Kajabi
5. Verify data integrity

**Export File**: `kajabi_full_enriched_export.csv`
- Contains: email, Kajabi ID, all contact fields
- Format: Kajabi-compatible import format
- Records: 5,388 matched contacts (plus 658 needing address updates)

**Benefits**:
- ✅ Kajabi becomes clean source of truth
- ✅ Database and Kajabi back in sync
- ✅ Future imports work normally
- ✅ Kajabi users see corrected data

**Timeline**:
- Generate export: Today
- Import to Kajabi: This week
- Verify sync: Next week
- Remove protections: Week after

### Part 3: LONG-TERM - Prevent Duplicate Creation

**Goal**: Ensure weekly imports never recreate merged duplicates

**Implementation**:
1. Track merged contacts in database (add `merged_from` table)
2. Before creating new contact, check if email was previously merged
3. If merged, link to primary contact instead
4. Add duplicate detection to import script

**Protected Against**:
- Multiple emails for same person (already merged)
- Multiple phone numbers for same person
- Multiple addresses for same person
- Name variations (already merged)

**Benefits**:
- ✅ Preserves merge work
- ✅ Prevents duplicate recreation
- ✅ Maintains clean database

## Recommended Action Plan

### Today (Immediate)
1. ✅ Generate impact analysis (DONE)
2. ✅ Generate Kajabi export with enriched data (NEXT)
3. ⏳ Modify import script with protection logic (OPTIONAL, for safety)

### This Week
1. Review Kajabi export file
2. Import enriched data to Kajabi
3. Verify data in Kajabi UI
4. Re-export from Kajabi to verify

### Next Week
1. Run weekly import with new Kajabi CSV (should match database)
2. Verify no data loss
3. Remove protection logic if data matches

### Ongoing
1. Run weekly imports normally
2. Monitor for data quality issues
3. Add duplicate prevention logic if needed

## Files Generated

### Analysis Files
- `data/current/import_impact_analysis.csv` - Detailed impact report
- `data/current/kajabi_address_evaluation_report.csv` - Address comparison

### Export Files (To Be Generated)
- `data/current/kajabi_full_enriched_export.csv` - Complete export for Kajabi import
- `data/current/kajabi_new_contacts_only.csv` - Contacts in DB but not in Kajabi (optional)

## Decision Matrix

### If you CAN import to Kajabi this week:
→ **Use Part 2 (Export to Kajabi)**
→ Best long-term solution
→ Gets database and Kajabi in sync

### If you CANNOT import to Kajabi:
→ **Use Part 1 (Protect enriched data)**
→ Prevents data loss immediately
→ Accept that DB and Kajabi will diverge

### If you want MAXIMUM safety:
→ **Use Part 1 + Part 2 together**
→ Protect immediately AND sync later
→ Best of both worlds

## Risk Assessment

### Without Any Protection
- **Risk**: CRITICAL
- **Impact**: All enrichment work lost
- **Probability**: 100% on next import
- **Recommendation**: DO NOT RUN next import without protection

### With Part 1 Only (Protection)
- **Risk**: LOW
- **Impact**: Database and Kajabi diverge
- **Probability**: 100% (by design)
- **Recommendation**: Acceptable short-term, must sync eventually

### With Part 2 Only (Kajabi Export)
- **Risk**: MEDIUM
- **Impact**: If import fails, one more week of divergence
- **Probability**: 10-20% (import issues)
- **Recommendation**: Have backup plan ready

### With Part 1 + Part 2 (Both)
- **Risk**: MINIMAL
- **Impact**: Protected during transition
- **Probability**: <5%
- **Recommendation**: BEST APPROACH

## Next Steps

**Your decision needed**:
1. Generate Kajabi export with enriched data? (Recommended: YES)
2. Modify import script with protections? (Recommended: YES for safety)
3. Timeline for importing to Kajabi? (Recommended: This week)

Once you decide, I'll implement accordingly.
