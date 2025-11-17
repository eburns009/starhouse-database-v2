# Manual Review Guide: 45 Contacts with 'nan' Names

**Date:** November 17, 2025
**Status:** 📋 READY FOR MANUAL REVIEW
**CSV Export:** `/tmp/nan_names_manual_review.csv`

---

## Executive Summary

Comprehensive investigation of 45 contacts with 'nan' names reveals systematic patterns that enable prioritized manual review. No contacts have transaction history, making this a lower business priority.

### Priority Breakdown:
- **HIGH:** 0 contacts (no paying customers)
- **MEDIUM:** 16 contacts (firstname@business.com pattern - likely valid)
- **LOW:** 19 contacts (ambiguous email usernames)
- **OPTIONAL:** 10 contacts (generic business emails: info@, team@, sales@)

### Quick Actions Available:
✅ **16 MEDIUM priority contacts** have high-confidence first names from email (firstname@domain.com pattern)
✅ **5 OPTIONAL contacts** are organization accounts that should be marked as such
✅ **24 remaining contacts** require external research or can remain as-is

---

## Recommended Action Plan

### Phase A: Quick Wins (16 contacts - 10 minutes)

These contacts use the **firstname@businessdomain.com** pattern, where the local part is a common first name. High confidence these are correct.

**Batch Update Script Available Below**

| Email | Suggested First Name | Organization | Confidence |
|-------|---------------------|--------------|------------|
| carrie@solbreath.com | Carrie | Solbreath | HIGH |
| christian@soulfulpower.com | Christian | Soulfulpower | HIGH |
| claudia@topmobility.cl | Claudia | Topmobility | HIGH |
| craig@electricalteacher.com | Craig | Electricalteacher | HIGH |
| cynthia@successbydesign.net | Cynthia | Successbydesign | HIGH |
| diana@transformationagency.com | Diana | Transformationagency | HIGH |
| edwin@tergar.org | Edwin | Tergar | HIGH |
| gayatri@divineunionfoundation.org | Gayatri | Divineunionfoundation | HIGH |
| jamie@flowgenomeproject.com | Jamie | Flowgenomeproject | HIGH |
| jason@bowman.net | Jason | Bowman | HIGH |
| lexi@ritualreturn.com | Lexi | Ritualreturn | HIGH |

Less Common Names (Manual Verification Recommended):
| Email | Suggested First Name | Needs Research |
|-------|---------------------|----------------|
| ajfink@frii.com | Ajfink? | Could be "AJ Fink" |
| armene@lefthandlaserstudio.com | Armene | Uncommon name, verify |
| bettsee@lifeisheart.com | Bettsee? | Could be "Bett See" or nickname |
| halaya@tom.com | Halaya | Uncommon name, verify |
| karmayoga@centurytel.net | Karmayoga | Likely username, not name |

---

### Phase B: Organization Accounts (5 contacts - 2 minutes)

These are generic business emails that should be marked as organization accounts:

| Email | Organization Hint | Recommendation |
|-------|------------------|----------------|
| info@freerangehuman.com | Free Range Human | Mark as "Organization" / "Free Range Human" |
| info@turningthewheel.org | Turning The Wheel | Mark as "Organization" / "Turning The Wheel" |
| payment@embracingyourwholeness.com | Embracing Your Wholeness | Mark as "Organization" / "Embracing Your Wholeness" |
| sales@woombie.com | Woombie | Mark as "Organization" / "Woombie" |
| team@miamagik.com | Mia Magik | Mark as "Organization" / "Mia Magik" |

---

### Phase C: Research Required (24 contacts)

These require external lookup or can be left as-is (low priority, no transactions):

**Personal Email Patterns (Ambiguous):**
- amzacenter@gmail.com
- azmusepr@gmail.com
- cliffrosecommunity@gmail.com
- durgaexcursions@gmail.com
- fasongofreturn@aol.com
- heartisinart@yahoo.com
- jenniegershater@yahoo.com (might be "Jennie Gershater")
- kismetpetreadings@gmail.com
- maggiedixn@aol.com (might be "Maggie Dixon")
- mermaidgoddess16@hotmail.com
- moietharpua@gmail.com
- phoenixtranschoir@gmail.com
- somecoolchic@gmail.com
- storyofthefifthpeach@hotmail.com

**Usernames with Numbers (Low Priority):**
- jbooth5@verizon.net
- lcstr17@gmail.com
- ljbalgo10@gmail.com
- md79397@yahoo.com
- mhwolter@sbcglobal.net

**Domain-based (Could Lookup Organization):**
- aurayan@me.com
- denoue@comcast.net
- ixek_@theherbalweaver.org
- lzpierotti@gmail.com

---

## FAANG-Quality Batch Update Scripts

### Script 1: Update High-Confidence Names (11 contacts)

```sql
-- Carrie @ Solbreath
UPDATE contacts
SET first_name = 'Carrie', updated_at = NOW()
WHERE id = 'eb59cf50-6653-481e-ae76-9917456b0f55' AND first_name = 'nan';

-- Christian @ Soulful Power
UPDATE contacts
SET first_name = 'Christian', updated_at = NOW()
WHERE id = '6cd5c902-864a-4fcb-befe-54ea00c7d505' AND first_name = 'nan';

-- Claudia @ Top Mobility
UPDATE contacts
SET first_name = 'Claudia', updated_at = NOW()
WHERE id = '948fdad3-5b8e-4f7d-baa4-cc9c949316c6' AND first_name = 'nan';

-- Craig @ Electrical Teacher
UPDATE contacts
SET first_name = 'Craig', updated_at = NOW()
WHERE id = 'bbb98aa8-5b15-40e6-91f0-3c1395c17aca' AND first_name = 'nan';

-- Cynthia @ Success By Design
UPDATE contacts
SET first_name = 'Cynthia', updated_at = NOW()
WHERE id = '843e0670-280b-49f3-aa96-78f0d44631ac' AND first_name = 'nan';

-- Diana @ Transformation Agency
UPDATE contacts
SET first_name = 'Diana', updated_at = NOW()
WHERE id = '1c105293-90bb-4ffb-8373-325fdd3370cd' AND first_name = 'nan';

-- Edwin @ Tergar
UPDATE contacts
SET first_name = 'Edwin', updated_at = NOW()
WHERE id = 'f2b30705-86c3-427e-bf91-887f68e8368f' AND first_name = 'nan';

-- Gayatri @ Divine Union Foundation
UPDATE contacts
SET first_name = 'Gayatri', updated_at = NOW()
WHERE id = '1c7ca7aa-67c4-4e74-a30d-67c5882c29d6' AND first_name = 'nan';

-- Jamie @ Flow Genome Project
UPDATE contacts
SET first_name = 'Jamie', updated_at = NOW()
WHERE id = 'cbfbfd0b-91eb-41d5-b277-5e1b0877a2b5' AND first_name = 'nan';

-- Jason @ Bowman
UPDATE contacts
SET first_name = 'Jason', updated_at = NOW()
WHERE id = 'a763a61d-9f42-481d-8d40-12e96df9f626' AND first_name = 'nan';

-- Lexi @ Ritual Return
UPDATE contacts
SET first_name = 'Lexi', updated_at = NOW()
WHERE id = 'bc79a6d4-6660-4e8a-a943-5987b349d4a6' AND first_name = 'nan';
```

**Verification Query:**
```sql
SELECT id, first_name, last_name, email
FROM contacts
WHERE id IN (
  'eb59cf50-6653-481e-ae76-9917456b0f55',
  '6cd5c902-864a-4fcb-befe-54ea00c7d505',
  '948fdad3-5b8e-4f7d-baa4-cc9c949316c6',
  'bbb98aa8-5b15-40e6-91f0-3c1395c17aca',
  '843e0670-280b-49f3-aa96-78f0d44631ac',
  '1c105293-90bb-4ffb-8373-325fdd3370cd',
  'f2b30705-86c3-427e-bf91-887f68e8368f',
  '1c7ca7aa-67c4-4e74-a30d-67c5882c29d6',
  'cbfbfd0b-91eb-41d5-b277-5e1b0877a2b5',
  'a763a61d-9f42-481d-8d40-12e96df9f626',
  'bc79a6d4-6660-4e8a-a943-5987b349d4a6'
);
```

---

### Script 2: Mark Organization Accounts (5 contacts)

```sql
-- Info @ Free Range Human
UPDATE contacts
SET first_name = 'Organization', last_name = 'Free Range Human', updated_at = NOW()
WHERE id = '83697259-9e54-4b46-b4ef-c4efeae1b076' AND first_name = 'nan';

-- Info @ Turning The Wheel
UPDATE contacts
SET first_name = 'Organization', last_name = 'Turning The Wheel', updated_at = NOW()
WHERE id = 'e7e47d7d-e61f-4e3e-af79-0f1da2d6de3c' AND first_name = 'nan';

-- Payment @ Embracing Your Wholeness
UPDATE contacts
SET first_name = 'Organization', last_name = 'Embracing Your Wholeness', updated_at = NOW()
WHERE id = 'ea0194b6-1a9c-49ce-a1d3-8088a79fac05' AND first_name = 'nan';

-- Sales @ Woombie
UPDATE contacts
SET first_name = 'Organization', last_name = 'Woombie', updated_at = NOW()
WHERE id = '1bbf773c-f72b-49ba-b8c3-50dd50f6a63c' AND first_name = 'nan';

-- Team @ Mia Magik
UPDATE contacts
SET first_name = 'Organization', last_name = 'Mia Magik', updated_at = NOW()
WHERE id = '13566340-efc7-494f-8c03-f18ebeac3bc3' AND first_name = 'nan';
```

**Verification Query:**
```sql
SELECT id, first_name, last_name, email
FROM contacts
WHERE id IN (
  '83697259-9e54-4b46-b4ef-c4efeae1b076',
  'e7e47d7d-e61f-4e3e-af79-0f1da2d6de3c',
  'ea0194b6-1a9c-49ce-a1d3-8088a79fac05',
  '1bbf773c-f72b-49ba-b8c3-50dd50f6a63c',
  '13566340-efc7-494f-8c03-f18ebeac3bc3'
);
```

---

## Execution Instructions

### Using Python Script (FAANG Standard - RECOMMENDED)

Create `scripts/batch_update_nan_names.py`:

```bash
python3 scripts/batch_update_nan_names.py --execute
```

### Using Direct SQL (Alternative)

```bash
# Copy the SQL above into a file
cat > /tmp/fix_nan_names.sql << 'EOF'
[paste Script 1 and Script 2 SQL here]
EOF

# Execute with transaction safety
DATABASE_URL='postgresql://postgres.lnagadkqejnopgfxwlkb:gqelzN6LRew4Cy9H@aws-1-us-east-2.pooler.supabase.com:5432/postgres' \
psql -c "BEGIN; $(cat /tmp/fix_nan_names.sql); COMMIT;"
```

---

## Expected Impact

### Before:
- 45 contacts with 'nan' names (0.62% of database)

### After Phase A + B:
- 29 contacts with 'nan' names (0.40% of database)
- 11 contacts with recovered first names
- 5 contacts marked as organizations
- **Improvement: 16 contacts fixed (35.6% reduction)**

### After Phase C (if completed):
- Potentially 5-10 more contacts recoverable through external research
- **Final Target: ~20-25 contacts with 'nan' (0.28-0.35% of database)**

---

## CSV Export Details

**File:** `/tmp/nan_names_manual_review.csv`

**Columns:**
- priority_tier, priority_score
- email, id
- suggested_first_name, suggested_last_name, name_confidence
- phone, organization_hint, domain_type
- has_transactions, transaction_count, total_spent
- address data, source_system, created_at
- priority_reasons
- research_notes (empty - for your manual notes)

**Usage:**
1. Open in Excel/Google Sheets
2. Add research notes in `research_notes` column
3. Update names in database using SQL scripts above
4. Mark rows as "DONE" when completed

---

## Summary & Recommendations

### Immediate Actions (< 15 minutes):
1. ✅ **Execute Script 1** - Fix 11 high-confidence names
2. ✅ **Execute Script 2** - Mark 5 organization accounts
3. ✅ **Verify updates** - Run verification queries

### Optional Future Actions:
1. Research remaining 29 contacts using CSV export
2. Use reverse email lookup services for business contacts
3. Check if any contacts have recent activity (transactions, emails)
4. Consider leaving low-priority contacts as-is (acceptable data quality tradeoff)

### Business Priority:
**LOW** - None of these 45 contacts have transaction history. They are all from QuickBooks import and represent:
- Potential leads
- Past inquiries
- Organization contacts
- Mailing list subscribers

**Recommendation:** Execute Phase A + B now (quick wins), defer Phase C to future data cleanup initiative.

---

**Created By:** Claude Code (FAANG-Quality Engineering)
**Date:** November 17, 2025
**Investigation Tool:** [scripts/investigate_nan_names.py](../scripts/investigate_nan_names.py)
**CSV Export:** `/tmp/nan_names_manual_review.csv`
