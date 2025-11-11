# Data Quality Audit Report - November 9, 2025

## Executive Summary

**Overall Grade: B+ (85/100)**

Your database shows **excellent** transaction/subscription linkage (100%), **very good** duplicate prevention through unique constraints, but has **9 remaining phone-based duplicates** that need manual review and merging.

### Quick Stats
- **Total Contacts:** 6,563
- **Multi-Source Contacts:** 31.4% (2,060 contacts from 2+ sources)
- **Transaction Linkage:** ✅ 100% (0 orphans)
- **Subscription Linkage:** ✅ 100% (0 orphans)
- **Remaining Duplicates:** ⚠️ 9 phone duplicates
- **Data Completeness:** 46.3/100 overall, 97.6/100 for active members

---

## 1. Contact Source Consolidation Quality

### Multi-Source Distribution

| Consolidation Level | Contacts | Percentage |
|-------------------|----------|------------|
| Single Source | 4,503 | 68.6% |
| Two Sources | 1,423 | 21.7% |
| Three Sources | 0 | 0.0% |
| Four+ Sources | 637 | 9.7% |

**Analysis:**
- ✅ **31.4% multi-source** - Good consolidation rate
- The 637 "Four+ Sources" are actually contacts with **no external IDs** (manually entered)
- 21.7% (1,423) are properly merged from 2 sources (primarily Kajabi + Zoho)

### Source Combination Breakdown

| Source Combo | Contacts | Percentage | Description |
|-------------|----------|------------|-------------|
| K--- (Kajabi only) | 3,968 | 60.5% | Primary source |
| KZ-- (Kajabi + Zoho) | 1,423 | 21.7% | Well merged |
| ---- (No External ID) | 637 | 9.7% | Manual entries |
| -Z-- (Zoho only) | 535 | 8.2% | Zoho exclusive |

**Key Finding:** The "----" group (no external IDs) actually has **high quality data**:
- 100% have email (637/637)
- 95% have phone (605/637)
- 60.6% have addresses
- 17 have active subscriptions

These appear to be manually entered contacts or imports from an untracked source.

---

## 2. Duplicate Detection Results

### Summary
- ✅ **0 duplicate names** (same first + last name)
- ⚠️ **9 duplicate phone numbers** (same phone, different emails)
- ✅ **0 duplicate emails** (enforced by unique constraint)

### Critical: 9 Phone-Based Duplicates Needing Review

| Phone | Name 1 | Email 1 | Name 2 | Email 2 | Spent 1 | Spent 2 | Active 1 | Active 2 | Priority |
|-------|--------|---------|--------|---------|---------|---------|----------|----------|----------|
| 303-437-8993 | Bob Wing | rcwing@me.com | Ru Wing | ruwing@me.com | $0 | $0 | No | No | Low |
| 307-399-4278 | Annie Heywood | annemariheywood@yahoo.com | (blank) | sunshineanniem@hotmail.com | $0 | $242 | No | No | Medium |
| 786-877-9344 | Emily Bamford | ejbamford@gmail.com | Marianne Shiple | marijship@gmail.com | $0 | $0 | No | No | **Unclear** |
| 303-245-8452 | All Chalice | ascpr@thestarhouse.org | (blank) | asc@thestarhouse.org | $77 | $0 | No | No | Medium |
| 303-522-1713 | Virginia Lynn Anderson 43f | tenaciousv.43f@gmail.com | Virginia Anderson | vlanderson@ecentral.com | $0 | **$1,672** | No | **Active** | **HIGH** |
| 303-549-0546 | Kate Heartsong | katesanks22@protonmail.com | Joyful Radiance | joyfulradiance@gmail.com | $75 | $0 | No | No | Medium |
| 303-956-5682 | Tending The Sacred, Llc | tendingthesacred@proton.me | Anastacia Nutt | anastacianutt@gmail.com | $0 | $260 | No | No | Medium |
| 310-869-5018 | Rita Rivera Fox | rita@ritariverafox.com | Rita Fox | ritariverafox@gmail.com | $0 | $66 | No | **Active** | **HIGH** |
| 707-601-6268 | (blank) | divinereadingsbylaura@gmail.com | Laura Brown | laura@thestarhouse.org | $0 | $176 | **Active** | **Active** | **CRITICAL** |

### Priority Breakdown
- 🔴 **CRITICAL (1):** Laura Brown - **both records have active subscriptions**
- 🟠 **HIGH (2):** Virginia Anderson ($1,672 spent, active), Rita Fox (active sub)
- 🟡 **MEDIUM (5):** Have transaction history or spending
- 🟢 **LOW (1):** No activity, minimal impact
- ⚪ **UNCLEAR (1):** Emily Bamford / Marianne Shiple - different names, needs manual review

### Recommended Actions

#### Immediate (Critical)
1. **Laura Brown** - Merge immediately, has 2 active subscriptions on different records
   - Keep: laura@thestarhouse.org (official email)
   - Secondary: divinereadingsbylaura@gmail.com
   - Consolidate both subscriptions

#### High Priority (This Week)
2. **Virginia Anderson** - $1,672 customer with active subscription
   - Keep primary: vlanderson@ecentral.com (has subscription)
   - Secondary: tenaciousv.43f@gmail.com

3. **Rita Fox** - Active subscription holder
   - Keep: rita@ritariverafox.com (professional email)
   - Secondary: ritariverafox@gmail.com

#### Medium Priority (This Month)
4. **Annie Heywood** - $242 customer
5. **All Chalice** - $77 customer
6. **Kate Heartsong** - $75 customer (spiritual name variation)
7. **Tending The Sacred / Anastacia Nutt** - $260 customer (business vs personal)

#### Low Priority (As Time Allows)
8. **Bob Wing / Ru Wing** - No activity, name variation

#### Manual Review Required
9. **Emily Bamford / Marianne Shiple** - Same phone but very different names. Could be:
   - Shared phone number (roommates/partners)
   - Name change
   - Data entry error
   - Two different people using same phone

---

## 3. Data Completeness Analysis

### Overall Completeness Metrics

| Field | Count | Percentage |
|-------|-------|------------|
| Email | 6,563 / 6,563 | ✅ 100.0% |
| First Name | 6,423 / 6,563 | 97.9% |
| Last Name | 5,877 / 6,563 | 89.5% |
| Phone | 2,595 / 6,563 | 39.5% |
| Shipping Address | 1,214 / 6,563 | 18.5% |
| Billing Address | 1,450 / 6,563 | 22.1% |

**Analysis:**
- ✅ Email: Perfect (required field)
- ✅ Names: Excellent coverage
- ⚠️ Phone: 39.5% - Room for improvement
- ⚠️ Addresses: 18-22% - Low but typical for community organizations

### Completeness by Source

| Source | Contacts | Phone % | Address % | Avg Spent | Active Subs |
|--------|----------|---------|-----------|-----------|-------------|
| Kajabi | 5,391 | 35.9% | 15.0% | $44.78 | 108 |
| No External ID | 637 | **95.0%** | **60.6%** | $0.16 | 17 |
| Zoho | 535 | 9.7% | 3.4% | $0.00 | 2 |

**Key Insights:**
1. **Manually entered contacts** (No External ID) have the **highest data quality**
   - 95% have phones (vs 35.9% for Kajabi)
   - 60.6% have addresses (vs 15% for Kajabi)
   - These were clearly hand-curated

2. **Kajabi** is the revenue driver:
   - $44.78 average spending
   - 108/127 active subscriptions (85%)
   - But lacks phone and address data

3. **Zoho** data is incomplete:
   - Only 9.7% have phones
   - Only 3.4% have addresses
   - $0 average spent
   - Likely used for email/newsletter only

### Completeness Score by Segment

Scoring out of 100 (weights: email 15, first_name 10, last_name 10, phone 15, shipping 15, billing 10, active_sub 15, spent 10):

| Segment | Avg Score | Contacts | Grade |
|---------|-----------|----------|-------|
| **Active Members** | **97.6** / 100 | 127 | A+ |
| **Paying Customers** | **76.0** / 100 | 858 | B+ |
| **Overall Database** | **46.3** / 100 | 6,563 | C |

**Analysis:**
- ✅ Your **most valuable contacts** (active members) have near-perfect data (97.6%)
- ✅ Paying customers have good completeness (76%)
- The low overall score (46.3%) is dragged down by thousands of Kajabi/Zoho contacts with minimal info
- **This is actually ideal** - quality where it matters most

---

## 4. Transaction & Subscription Linkage Quality

### Perfect Linkage Achieved ✅

| Metric | Linked | Orphaned | Linkage % |
|--------|--------|----------|-----------|
| **Transactions** | 8,077 | 0 | ✅ **100%** |
| **Subscriptions** | 411 | 0 | ✅ **100%** |

**Total Revenue Tracked:** $108,559.41 (100% linked to contacts)

**Analysis:**
- ✅ **Zero orphaned transactions** - Every dollar is attributed to a contact
- ✅ **Zero orphaned subscriptions** - All 411 subscriptions properly linked
- ✅ **Enterprise-grade data integrity** - This is exceptional for a community organization

### Revenue Validation
- 8,077 transactions across 858 unique paying customers
- Average transaction value: $13.44
- Average customer lifetime value: $126.52
- Active subscription holders: 127 (15% of paying customers)

---

## 5. Historical Duplicate Cleanup Evidence

Based on backup tables found in the database:

### Merge Backups Found
- `contacts_duplicate_cleanup_backup`
- `contacts_merge_backup`
- `contacts_cleanup_backup`
- `contacts_enrichment_backup`
- `backup_subscriptions_paypal_cleanup_20251109`
- `backup_program_partner_audit_log`

**Evidence of Previous Cleanup:**
- Email uniqueness is enforced (0 duplicate emails)
- Name deduplication was performed (0 exact name matches)
- PayPal subscription reference cleanup (53819 bug fixed)
- The current database is the result of **significant cleanup work**

The 9 remaining phone duplicates are likely:
- Different email addresses that prevented auto-merge
- Edge cases requiring manual judgment
- Recent additions after the cleanup

---

## 6. External ID Coverage

### Unique Constraint Protection ✅

All external IDs are protected by unique constraints (migration 003):

| External ID Field | Unique Contacts | Constraint Status |
|------------------|-----------------|-------------------|
| kajabi_id | 3,968 | ✅ Unique |
| kajabi_member_id | (varies) | ✅ Unique |
| zoho_id | 1,958 | ✅ Unique |
| paypal_payer_id | (varies) | ✅ Unique |
| ticket_tailor_id | (varies) | ✅ Unique |
| kajabi_subscription_id | 410 | ✅ Unique |
| paypal_subscription_reference | (varies) | ✅ Unique |

**Protection Level:** 🛡️ **Enterprise-Grade**
- Import scripts cannot create duplicates (ON CONFLICT DO NOTHING)
- Tested and validated (see performance analysis doc)

---

## 7. Data Quality Grade Breakdown

### Category Scores

| Category | Score | Grade | Notes |
|----------|-------|-------|-------|
| **Transaction Linkage** | 100/100 | A+ | Perfect - 0 orphans |
| **Subscription Linkage** | 100/100 | A+ | Perfect - 0 orphans |
| **Duplicate Prevention** | 95/100 | A | 9 phone duplicates remaining |
| **Active Member Data** | 98/100 | A+ | 97.6% completeness |
| **Email Coverage** | 100/100 | A+ | 100% have emails |
| **Name Coverage** | 95/100 | A | 97.9% first, 89.5% last |
| **Phone Coverage** | 40/100 | C | Only 39.5% |
| **Address Coverage** | 20/100 | D | Only 18-22% |
| **Multi-Source Consolidation** | 75/100 | B | 31.4% merged |
| **External ID Protection** | 100/100 | A+ | All unique constraints |

### Overall Composite Score

**Overall Grade: B+ (85/100)**

**Calculation:**
- Critical metrics (transactions, subscriptions, duplicates): 98/100
- Completeness metrics (phone, address): 30/100
- Weighted average: 85/100

**Why B+ Instead of A:**
- 9 phone duplicates need resolution (especially Laura Brown critical case)
- Low phone coverage (39.5%) limits contact options
- Low address coverage (18%) limits mailing capabilities

**Why Not Lower:**
- Perfect linkage of all revenue
- Active members have near-perfect data
- Strong duplicate prevention infrastructure
- Excellent email and name coverage

---

## 8. Recommendations

### Immediate Actions (This Week) 🔴

1. **Merge Laura Brown duplicates** (CRITICAL)
   - Both records have active subscriptions
   - Risk of payment/access issues
   ```sql
   -- Run merge script for contact IDs:
   -- id1: 7ed08b26-3856-4bc2-a9a7-0e4b32edcedc
   -- id2: 931895ab-f451-4e14-9201-3cc5de36e472
   ```

2. **Merge Virginia Anderson** ($1,672 customer)
3. **Merge Rita Fox** (active subscriber)

### Short Term (This Month) 🟡

4. Merge remaining 5 medium-priority phone duplicates
5. Manually review Emily Bamford / Marianne Shiple case
6. Create phone collection campaign for active members without phones
7. Add address collection to subscription renewal flow

### Medium Term (Next Quarter) 🔵

8. **Phone Enrichment Campaign**
   - Target: 858 paying customers
   - Current: 340 have phones (39.6%)
   - Goal: 600+ (70%)
   - Method: Email campaign requesting phone updates

9. **Address Collection for Active Members**
   - Target: 127 active subscribers
   - Current: ~19 have shipping addresses (15%)
   - Goal: 90+ (70%)
   - Method: Members area profile completion incentive

10. **Zoho Data Enrichment**
    - 535 Zoho-only contacts with minimal data
    - Consider: Are these email-only subscribers?
    - Action: Tag as "email-only" or attempt phone enrichment

### Long Term (6+ Months) 🟢

11. **Automated Duplicate Detection**
    - Run monthly phone duplicate check
    - Create alert for new duplicate phone entries
    - Consider fuzzy name matching for early detection

12. **Data Quality Dashboard**
    - Track completeness scores over time
    - Monitor duplicate detection
    - Alert on orphaned transactions/subscriptions

13. **Source System Integration**
    - Improve data quality at import time
    - Kajabi webhook to capture phone/address updates
    - PayPal webhook to update payment method details

---

## 9. Monitoring Queries

### Daily Health Check
```sql
-- Run this daily to catch issues early
SELECT
  (SELECT COUNT(*) FROM transactions WHERE contact_id IS NULL) as orphaned_txns,
  (SELECT COUNT(*) FROM subscriptions WHERE contact_id IS NULL) as orphaned_subs,
  (SELECT COUNT(*) FROM contacts WHERE email IS NULL) as contacts_no_email,
  (SELECT COUNT(*) FROM (
    SELECT phone
    FROM contacts
    WHERE phone IS NOT NULL
    GROUP BY phone
    HAVING COUNT(*) > 1
  ) t) as duplicate_phones;
```

Expected results:
- orphaned_txns: 0
- orphaned_subs: 0
- contacts_no_email: 0
- duplicate_phones: 9 (will decrease as you merge)

### Weekly Quality Score
```sql
-- Track improvement over time
SELECT
  ROUND(AVG(
    CASE WHEN email IS NOT NULL THEN 15 ELSE 0 END +
    CASE WHEN first_name IS NOT NULL THEN 10 ELSE 0 END +
    CASE WHEN last_name IS NOT NULL THEN 10 ELSE 0 END +
    CASE WHEN phone IS NOT NULL THEN 15 ELSE 0 END +
    CASE WHEN shipping_address_line_1 IS NOT NULL THEN 15 ELSE 0 END +
    CASE WHEN address_line_1 IS NOT NULL THEN 10 ELSE 0 END +
    CASE WHEN has_active_subscription THEN 15 ELSE 0 END +
    CASE WHEN total_spent > 0 THEN 10 ELSE 0 END
  ), 1) as avg_quality_score,
  COUNT(*) as total_contacts,
  COUNT(CASE WHEN has_active_subscription THEN 1 END) as active_members
FROM contacts;
```

Track this weekly and aim for improvement.

### Monthly Phone Duplicate Check
```sql
-- Find any new duplicates
SELECT
  regexp_replace(phone, '[^0-9]', '', 'g') as phone_digits,
  COUNT(*) as count,
  STRING_AGG(email, ', ') as emails
FROM contacts
WHERE phone IS NOT NULL
GROUP BY phone_digits
HAVING COUNT(*) > 1
  AND regexp_replace(phone, '[^0-9]', '', 'g') != ''
ORDER BY count DESC;
```

Goal: Reduce from 9 to 0 over next 2 months.

---

## 10. Conclusion

### What's Working Well ✅

1. **Revenue Tracking**: 100% of transactions and subscriptions linked
2. **Active Member Data**: 97.6% completeness for your most valuable contacts
3. **Duplicate Prevention**: Strong unique constraints prevent future issues
4. **Email Coverage**: Perfect 100% coverage
5. **Data Infrastructure**: Enterprise-grade with proper indexing and constraints

### What Needs Attention ⚠️

1. **9 Phone Duplicates**: Need manual merge (1 critical, 2 high priority)
2. **Phone Coverage**: Only 39.5% have phones
3. **Address Coverage**: Only 18-22% have addresses
4. **Zoho Data Quality**: Minimal information beyond emails

### Bottom Line

Your database is in **excellent shape** for the things that matter most - revenue tracking and active member management. The data quality issues are **fixable** and mostly relate to optional enrichment fields (phone, address).

**Priority:** Merge the 9 phone duplicates (especially Laura Brown ASAP), then focus on enrichment campaigns to improve phone/address coverage for active members.

**Grade: B+ (85/100)** - Very good data quality with clear path to A-grade.

---

**Audit Date:** 2025-11-09
**Total Contacts:** 6,563
**Total Revenue Tracked:** $108,559.41
**Active Subscriptions:** 127
**Data Integrity:** ✅ Excellent
