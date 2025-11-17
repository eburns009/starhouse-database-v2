# Email Subscription Source Reconciliation
**Date**: November 11, 2025
**Analysis**: Comparison of Kajabi, Ticket Tailor, and Database subscription statuses

## Executive Summary

Analyzed 3 data sources to reconcile email subscription status:
- **Kajabi Subscribed**: 3,423 contacts (as of 10/11)
- **Kajabi Unsubscribed**: 2,268 contacts (as of 11/10/2025)
- **Ticket Tailor Opt-ins**: 838 contacts said "Yes" to emails
- **Database**: 6,549 contacts total (3,710 subscribed, 2,839 unsubscribed)

### Key Findings

**CRITICAL - Respect Unsubscribe Preferences**:
- ⚠️ **163 contacts** are marked as UNSUBSCRIBED in Kajabi but still SUBSCRIBED in our database
- These contacts explicitly opted out and we must honor their preference

**Fix Subscription Status**:
- 7 contacts subscribed in Kajabi but unsubscribed in DB (should be updated)
- 6 contacts said "Yes" in Ticket Tailor but unsubscribed in DB (should be updated)

**Missing from Database**:
- 194 contacts subscribed in Kajabi are not in our database
- 61 Ticket Tailor opt-ins are not in our database

### Current Email List Size

**Total unique emails that should be subscribed**: 3,746
- Kajabi subscribed: 3,423
- Ticket Tailor 'Yes': 838
- Overlap: 515

**Database status of these 3,746**:
- ✓ Actually subscribed: 3,518
- ✗ NOT subscribed: 12
- ? Not in database: 216

---

## Detailed Findings

### 1. Kajabi Lists Validation

**Good News**: No overlaps between subscribed and unsubscribed lists
- The two Kajabi exports are mutually exclusive (no email appears in both)

**Database Match Rate**:
- 94% of Kajabi subscribed emails are in database (3,229 of 3,423)
- 95% of Kajabi unsubscribed emails are in database (2,155 of 2,268)

### 2. Critical Discrepancies

#### 2A. Unsubscribed in Kajabi but Subscribed in DB (163 contacts)

**PRIORITY: HIGH - Legal compliance issue**

These contacts unsubscribed in Kajabi but our database still has them as subscribed:

```
1wideopensky@gmail.com (ID: 8144958e-39cd-42c2-9cbc-e5a39cdfc8ce)
abetterhomeinspection@yahoo.com (ID: 25434b31-dc15-4f4e-b212-7767efd96ca6)
adam@engle.com (ID: 1d322b8d-faa0-429a-802c-114ae2b94599)
afoster@thirdbody.net (ID: fbd8816c-7f02-47e7-8008-b50a4c2d7686)
... (159 more)
```

**Action Required**: Update these contacts to email_subscribed = false

#### 2B. Subscribed in Kajabi but Unsubscribed in DB (7 contacts)

These contacts are subscribed in Kajabi but marked as unsubscribed in our database:

```
anne@annenorman.com (ID: 2d17d973-524f-481b-8828-1c7a81926088)
hayli@rebeccasherbs.com (ID: fc5d63c7-4a0b-4b87-9842-5334f4317b68)
heidi@heidirose.com (ID: beb7b919-67b2-44b8-b17b-50d4889b29bb)
rochelleschieck@gmail.com (ID: 34657c67-769b-44f9-9709-37eedee8afc6)
sumanomaly@gmail.com (ID: 36924a22-a05d-4ea0-ab42-5770eb4bb488)
sunday.spencer@yahoo.com (ID: c08abc77-3f2a-4fb7-b913-f9e66c34eaa7)
vedgett@bettertogetherproductions.co (ID: 6e3431d3-25e5-42f8-801b-03382252736e)
```

**Action Required**: Update these contacts to email_subscribed = true

#### 2C. Ticket Tailor "Yes" but Unsubscribed in DB (6 contacts)

These contacts explicitly said "Yes" to receive emails via Ticket Tailor but are unsubscribed in our database:

```
art@barbarafroula.com (ID: 11c6d5cb-cb5e-4b76-b65f-fc473770a0c2)
caterina.zri@gmail.com (ID: 95cb5ab9-e005-4d56-943e-bee19600459a)
cynthia_cordero@yahoo.com (ID: 5d1f4ffc-651e-42dd-b205-e6615e3f38f2)
heidi@heidirose.com (ID: beb7b919-67b2-44b8-b17b-50d4889b29bb)
newvalzoe@gmail.com (ID: 1a5790ab-fc8d-4002-b149-b0dbd0fef1b0)
zukidreams@pm.me (ID: e2fee89a-4863-42cc-ae1a-47a7a0f93746)
```

**Action Required**: Update these contacts to email_subscribed = true

### 3. Ticket Tailor Analysis

**Total unique emails in Ticket Tailor**: 2,375

**Consent Breakdown**:
- Yes to emails: 838 (35.3%)
- No to emails: 234 (9.9%)
- Blank/no answer: 1,300 (54.7%)

**Database Match**:
- 777 of 838 "Yes" respondents are in database (92.7%)
- Of those in database, 771 are correctly marked as subscribed (99.2%)
- 61 "Yes" respondents are not in database yet

### 4. Missing Contacts

**Kajabi Subscribed Not in Database**: 194 contacts
- These are marked as subscribed in Kajabi but don't exist in our database
- May be newer signups or contacts that were never imported

**Ticket Tailor Opt-ins Not in Database**: 61 contacts
- These said "Yes" to emails but aren't in our system yet
- Should be imported to capture their consent

---

## Recommendations

### Immediate Actions (Priority 1)

1. **Respect Unsubscribe Preferences** - Update 163 contacts
   - These contacts unsubscribed in Kajabi and must be marked as unsubscribed in DB
   - Legal compliance requirement (CAN-SPAM, GDPR)

2. **Honor Opt-ins** - Update 13 contacts (7 from Kajabi + 6 from Ticket Tailor)
   - These contacts have provided consent but are marked as unsubscribed

### Follow-up Actions (Priority 2)

3. **Import Missing Contacts** - Consider importing 255 contacts
   - 194 from Kajabi subscribed list
   - 61 from Ticket Tailor opt-ins
   - Verify these are legitimate opt-ins before importing

### Process Improvements (Priority 3)

4. **Establish Single Source of Truth**
   - Determine whether Kajabi or database should be authoritative
   - Implement regular sync to prevent future discrepancies

5. **Audit Ticket Tailor Imports**
   - 1,300 contacts didn't answer the email question (54.7%)
   - Consider whether to add them to list or treat as no consent

---

## Data Quality Notes

### Strengths
- ✓ No overlap between Kajabi subscribed/unsubscribed lists
- ✓ 99.2% accuracy for Ticket Tailor opt-ins that are in database
- ✓ High match rate (94-95%) between Kajabi and database

### Concerns
- ⚠️ 163 contacts subscribed in DB but unsubscribed in Kajabi (compliance risk)
- ⚠️ 255 contacts with consent not in database (missed opportunities)
- ⚠️ No clear sync process between Kajabi and database

---

## Next Steps

1. Review and approve recommended updates
2. Run SQL scripts to update subscription statuses (see scripts below)
3. Decide on import strategy for missing contacts
4. Establish ongoing sync process between Kajabi and database

---

## SQL Scripts

### Script 1: Respect Unsubscribe Preferences (163 contacts)

```sql
-- CRITICAL: Mark as unsubscribed those who unsubscribed in Kajabi
-- These contacts explicitly opted out and we must honor their preference

UPDATE contacts
SET
    email_subscribed = false,
    updated_at = NOW()
WHERE email ILIKE ANY (ARRAY[
    -- List of 163 emails from Kajabi unsubscribed who are marked as subscribed in DB
    -- (Full list to be generated from analysis results)
])
AND email_subscribed = true;
```

### Script 2: Honor Opt-ins (13 contacts)

```sql
-- Mark as subscribed those who are subscribed in Kajabi or said Yes in Ticket Tailor
-- but are currently marked as unsubscribed in DB

UPDATE contacts
SET
    email_subscribed = true,
    updated_at = NOW()
WHERE email ILIKE ANY (ARRAY[
    'anne@annenorman.com',
    'hayli@rebeccasherbs.com',
    'heidi@heidirose.com',
    'rochelleschieck@gmail.com',
    'sumanomaly@gmail.com',
    'sunday.spencer@yahoo.com',
    'vedgett@bettertogetherproductions.co',
    'art@barbarafroula.com',
    'caterina.zri@gmail.com',
    'cynthia_cordero@yahoo.com',
    'newvalzoe@gmail.com',
    'zukidreams@pm.me'
])
AND email_subscribed = false;
```

---

## Files Analyzed

1. `/workspaces/starhouse-database-v2/kajabi 3 files review/1011_email_subscribed.csv` (3,423 records)
2. `/workspaces/starhouse-database-v2/kajabi 3 files review/11102025unsubscribed.csv` (2,268 records)
3. `/workspaces/starhouse-database-v2/kajabi 3 files review/ticket_tailor_data.csv` (4,822 orders, 2,375 unique emails)
4. Database `contacts` table (6,549 records)

## Analysis Script

Full analysis performed by: `scripts/analyze_email_subscription_sources.py`
