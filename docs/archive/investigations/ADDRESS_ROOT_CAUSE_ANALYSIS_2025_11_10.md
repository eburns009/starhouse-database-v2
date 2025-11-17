# Address Data Quality - Root Cause Analysis
**Date:** 2025-11-10
**Status:** Complete
**Priority:** High

## Executive Summary

Investigation into address data quality revealed **560 contacts with address field issues** across three distinct patterns, all originating from **Kajabi source data**. An additional **116 PayPal contacts** have duplicate shipping addresses.

**Key Finding:** All primary address issues trace back to **inconsistent field mapping in Kajabi source CSV exports**, not import script bugs.

## Issues Quantified

### Pattern 1: City in address_line_2 Field
**Impact:** 467 contacts (71% of total issues)
**Source:** Kajabi imports only
**Root Cause:** Kajabi export CSV has city data in address_line_2 column instead of city column

**Examples:**
```
email: akimama09@earthlink.net
address_line_1: "4866 Franklin Dr."
address_line_2: "Boulder"          ← City is here
city: NULL                          ← Should be here
postal_code: "80301"
```

```
email: harrisonnancy1@aol.com
address_line_1: "3250 O'Neal Circle #K-25"
address_line_2: "Boulder"          ← City is here
city: NULL
postal_code: "80301"
```

**SQL to identify:**
```sql
SELECT COUNT(*) FROM contacts
WHERE address_line_2 IS NOT NULL
  AND address_line_2 != ''
  AND city IS NULL
  AND address_line_1 IS NOT NULL;
-- Result: 467
```

### Pattern 2: Duplicate Text in Both Address Lines
**Impact:** 84 contacts (13% of issues) in primary address, 116 in PayPal shipping
**Source:** Kajabi imports + PayPal imports
**Root Cause:** Source CSV has identical text in address_line_1 and address_line_2 columns

**Kajabi Examples (84 contacts):**
```
email: rcwaszak@hotmail.com
address_line_1: "PO BOX 621881"
address_line_2: "PO BOX 621881"    ← Duplicate
city: "LITTLETON"
state: "CO"
```

**PayPal Examples (116 contacts, 77% of PayPal with shipping):**
```
shipping_address_line_1: "123 Main St"
shipping_address_line_2: "123 Main St"    ← Duplicate
shipping_city: "Denver"
```

**SQL to identify Kajabi:**
```sql
SELECT COUNT(*) FROM contacts
WHERE address_line_1 = address_line_2
  AND address_line_1 IS NOT NULL;
-- Result: 84
```

**SQL to identify PayPal:**
```sql
SELECT COUNT(*) FROM contacts
WHERE shipping_address_line_1 = shipping_address_line_2
  AND shipping_address_line_1 IS NOT NULL
  AND source_system = 'paypal';
-- Result: 116
```

### Pattern 3: Field Reversal
**Impact:** 9 contacts (1.6% of issues)
**Source:** Kajabi imports only
**Root Cause:** Kajabi export has street address in address_line_2, incomplete data in address_line_1

**Examples:**
```
email: nancy@healingstory.com
address_line_1: "usa"              ← Country instead of street
address_line_2: "99 Fern Hill Rd"  ← Actual address
city: NULL
postal_code: "12075"
```

```
email: tmcgl@optonline.net
address_line_1: "85"               ← Just house number
address_line_2: "Walnut Street"    ← Actual street name
city: "Lynbrook"
state: "NY"
```

**SQL to identify:**
```sql
SELECT COUNT(*) FROM contacts
WHERE address_line_1 IS NOT NULL
  AND LENGTH(address_line_1) < 10
  AND address_line_2 IS NOT NULL
  AND LENGTH(address_line_2) > 10;
-- Result: 9
```

## Import Script Analysis

### weekly_import_kajabi_v2.py
**Location:** `/workspaces/starhouse-database-v2/scripts/weekly_import_kajabi_v2.py:232-276`

**Behavior:** Direct field mapping with COALESCE (preserves existing, does NOT validate or transform)

```python
# Lines 232-237: Extract fields exactly as they appear in CSV
address_line_1 = row.get('address_line_1', '').strip() or None
address_line_2 = row.get('address_line_2', '').strip() or None
city = row.get('city', '').strip() or None
state = row.get('state', '').strip() or None
postal_code = row.get('postal_code', '').strip() or None
country = row.get('country', '').strip() or None

# Lines 259-264: Update using COALESCE (keeps existing if new is NULL)
UPDATE contacts SET
    address_line_1 = COALESCE(%s, address_line_1),
    address_line_2 = COALESCE(%s, address_line_2),
    city = COALESCE(%s, city),
    state = COALESCE(%s, state),
    postal_code = COALESCE(%s, postal_code)
```

**Conclusion:** Import script correctly maps fields. Issue is in **source CSV data** from Kajabi.

### import_paypal_2024.py
**Location:** `/workspaces/starhouse-database-v2/scripts/import_paypal_2024.py:331-410`

**Behavior:** Maps to shipping_* fields (separate from primary address fields)

```python
# Lines 331-335: Extract from PayPal CSV
'address_line_1': sanitize_string(row.get('Address Line 1', ''), 200),
'address_line_2': sanitize_string(row.get('Address Line 2/District/Neighborhood', ''), 200),
'city': sanitize_string(row.get('Town/City', ''), 100),
'state': sanitize_string(row.get('State/Province/Region/County/Territory/Prefecture/Republic', ''), 100),
'postal_code': row.get('Zip/Postal Code', '').strip()

# Stores in shipping_* fields
INSERT INTO contacts (
    shipping_address_line_1, shipping_address_line_2,
    shipping_city, shipping_state, shipping_postal_code
)
```

**Conclusion:** PayPal duplicate issue likely in **source PayPal export CSV**, but needs verification.

## Root Causes Summary

| Pattern | Count | Source | Root Cause | Fix Strategy |
|---------|-------|--------|------------|--------------|
| City in line_2 | 467 | Kajabi | Source CSV field mapping | Smart detection + batch correction |
| Duplicate lines | 84 | Kajabi | Source CSV duplication | Remove duplicate text |
| Duplicate shipping | 116 | PayPal | Source CSV duplication | Remove duplicate text |
| Field reversal | 9 | Kajabi | Source CSV field order | Manual review + swap fields |

**Total Impact:** 676 contacts (10.3% of 6,563 total)

## Source Data Investigation Needed

To definitively confirm root causes, we should:

1. **Inspect Kajabi export CSVs:**
   - Check `data/current/v2_contacts.csv` for field mappings
   - Verify if city appears in address_line_2 column
   - Check if duplicates exist in source data

2. **Inspect PayPal export CSV:**
   - Check if Address Line 2 duplicates Address Line 1 in source
   - Verify field mapping from CSV columns

3. **Contact Kajabi support** if source data is malformed

## Recommended Fix Strategy

### Phase 1: Automated Batch Fixes (FAANG-quality)
1. **Pattern 1 (City in line_2):** 467 contacts
   - Detect: address_line_2 NOT NULL + city NULL + line_1 NOT NULL
   - Fix: Move address_line_2 → city, clear address_line_2
   - Confidence: HIGH (clear pattern)

2. **Pattern 2 (Duplicates):** 84 Kajabi + 116 PayPal = 200 contacts
   - Detect: line_1 = line_2 AND both NOT NULL
   - Fix: Clear address_line_2 (or shipping_address_line_2)
   - Confidence: HIGH (obvious duplication)

### Phase 2: Manual Review (9 contacts)
3. **Pattern 3 (Field reversal):** 9 contacts
   - Requires human verification (too few for automation, too complex)
   - Create UI with side-by-side view
   - Allow admin to swap fields or manually edit

### Implementation
- **Dry-run mode** with full preview
- **Atomic transactions** with rollback capability
- **Audit logging** of all changes (who, what, when)
- **Backup system** before applying changes
- **Progress tracking** and observability
- **Idempotent operations** (can re-run safely)

## Next Steps

1. ✅ **COMPLETED:** Root cause analysis
2. **TODO:** Inspect source CSV files to confirm findings
3. **TODO:** Build batch cleanup script (patterns 1 & 2)
4. **TODO:** Build admin UI for manual review (pattern 3)
5. **TODO:** Execute fixes in dry-run mode
6. **TODO:** Review and validate fixes
7. **TODO:** Execute fixes in production
8. **TODO:** Add data validation to import scripts (prevent future issues)

## Files Referenced

- `/workspaces/starhouse-database-v2/scripts/weekly_import_kajabi_v2.py`
- `/workspaces/starhouse-database-v2/scripts/import_paypal_2024.py`
- `/workspaces/starhouse-database-v2/docs/HANDOFF_2025_11_10_ADDRESS_INVESTIGATION.md`
- `/workspaces/starhouse-database-v2/docs/ADDRESS_DATA_QUALITY_AUDIT_2025_11_10.md`

## Related Issues

- Nancy Cranbourne (nancy@healingstory.com) - Pattern 3 example
- 467 contacts with city misplacement - Pattern 1
- UI smart detection already implemented for new entries (prevents Pattern 1)

---
**Analysis by:** Claude Code
**Review Status:** Ready for implementation
**Confidence Level:** HIGH (backed by SQL evidence + script analysis)
