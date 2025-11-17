# Email Subscription Compliance System - FAANG-Level Design

**Status**: Draft for Review
**Author**: Claude Code
**Date**: 2025-11-10
**Priority**: **CRITICAL** - Compliance & Legal Risk

---

## Executive Summary

**Problem**: Email subscription tracking is broken across merges and imports, creating compliance risk and potential list corruption.

**Impact**:
- 50 confirmed lost opt-ins in last 30 days
- 151 subscription conflicts during merges (40% of all recent merges)
- No single source of truth for subscription status
- Risk of CAN-SPAM/GDPR violations

**Solution**: Implement proper email subscription tracking system with Kajabi + Ticket Tailor as authoritative sources.

---

## Current State Analysis

### Data Inventory

| Source | Total Contacts | Opt-In Rate | Has External ID | Notes |
|--------|---------------|-------------|-----------------|-------|
| **Kajabi** | 5,387 (82%) | 62.91% | 5,386 have kajabi_id | **Primary source of truth** |
| **Zoho** | 516 (8%) | 0% | All have zoho_id | CRM data, no opt-ins |
| **Manual** | 253 (4%) | 99.60% | No external ID | Manually added, trusted |
| **Ticket Tailor** | 241 (4%) | 14.94% | **0 have ticket_tailor_id!** | **36 opted in - need protection** |
| **PayPal** | 152 (2%) | 21.71% | No paypal_payer_id | Transaction data only |

**Total Active Contacts**: 6,549

### Critical Issues Identified

#### 1. **Merge Process Destroys Subscription Data**
```sql
-- 151 subscription conflicts in last 30 days (40% of merges!)
-- 50 contacts lost their opt-in status
-- 105 contacts gained opt-in status (compliance violation if they didn't opt in)
```

**Root Cause**: Merge scripts keep primary contact's subscription status, ignoring duplicate's status.

#### 2. **No Subscription Tracking Per Email**
- `contacts.email_subscribed` is a boolean on the contact
- `contact_emails` table has NO subscription tracking fields
- When contact has multiple emails, we don't know which email(s) are subscribed

#### 3. **Ticket Tailor External IDs Missing**
- 241 Ticket Tailor contacts
- **0 have `ticket_tailor_id` set**
- Cannot reliably identify or protect Ticket Tailor contacts
- **36 opted-in contacts at risk of being overwritten**

#### 4. **Import Scripts Don't Check Alternate Emails**
```python
# PayPal import only checks:
WHERE email = %s OR paypal_email = %s

# Kajabi import only checks:
WHERE email = %s

# MISSING: additional_email, contact_emails table
```

Result: 143 duplicate PayPal contacts created in last 7 days (all with $0 spent)

#### 5. **Source System Changes During Merge**
- 20+ recent merges changed `source_system` field
- Example: Ticket Tailor contact merged into Kajabi contact
- Kajabi import may overwrite Ticket Tailor opt-in on next import

---

## Compliance Requirements

### Legal Framework
1. **CAN-SPAM Act** (US): Must honor opt-outs within 10 business days
2. **GDPR** (EU): Must have explicit consent, cannot assume consent
3. **Email Deliverability**: ISPs monitor complaint rates

### Business Rules (Defined by User)

**PRIMARY SOURCES OF TRUTH**:
1. **Kajabi**: All contacts with `kajabi_id` - subscription status is authoritative
2. **Ticket Tailor**: 36 contacts who opted in - MUST be preserved

**SECONDARY SOURCES** (informational only):
3. PayPal: Transaction data, not subscription intent
4. Zoho: CRM data, no opt-ins (all marked false)
5. Manual: Trusted but should defer to Kajabi if conflict

---

## Proposed Solution Architecture

### Phase 1: Immediate Fixes (This Week)

#### 1.1. Fix Lost Opt-Ins from Recent Merges
**Action**: Restore 50 opt-ins that were lost
**Safety**: Use `contacts_merge_backup` to identify and restore

```sql
-- Rule: If EITHER contact was opted in, result should be opted in
UPDATE contacts c
SET email_subscribed = true
WHERE id IN (
  SELECT primary_contact_id
  FROM contacts_merge_backup
  WHERE (duplicate_contact_data->>'email_subscribed')::boolean = true
    AND merged_at > NOW() - INTERVAL '30 days'
);
```

**Risk**: LOW - Restoring confirmed opt-ins
**Review Required**: YES - Manual review of all 50 contacts

#### 1.2. Add Ticket Tailor Protection
**Action**: Tag all Ticket Tailor opt-ins to prevent overwrites

```sql
-- Add protection flag
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  subscription_protected BOOLEAN DEFAULT false;

-- Mark Ticket Tailor opt-ins as protected
UPDATE contacts
SET subscription_protected = true
WHERE source_system = 'ticket_tailor'
  AND email_subscribed = true;
```

#### 1.3. Deploy Enhanced Contact Lookup
**Action**: Update import scripts to check ALL email fields

**Implementation**: See "Duplicate Prevention" section

---

### Phase 2: Subscription Tracking Redesign (Next 2 Weeks)

#### 2.1. Add Per-Email Subscription Tracking

```sql
ALTER TABLE contact_emails ADD COLUMN IF NOT EXISTS
  email_subscribed BOOLEAN DEFAULT NULL,
  email_subscription_source TEXT,  -- 'kajabi', 'ticket_tailor', etc.
  email_subscribed_at TIMESTAMP WITH TIME ZONE,
  email_unsubscribed_at TIMESTAMP WITH TIME ZONE,
  unsubscribe_reason TEXT;
```

#### 2.2. Migration Strategy

**Step 1**: Populate `contact_emails.email_subscribed` from current data
```sql
-- For primary email
UPDATE contact_emails ce
SET
  email_subscribed = c.email_subscribed,
  email_subscription_source = c.source_system
FROM contacts c
WHERE ce.contact_id = c.id
  AND ce.is_primary = true;
```

**Step 2**: Handle alternate emails
- Manual review of 375 contacts with `additional_email`
- Determine subscription status for each alternate email
- Document decisions

#### 2.3. Subscription Hierarchy Rules

When determining if a contact is subscribed:

```python
def is_contact_subscribed(contact_id):
    """
    A contact is subscribed if ANY of their emails is subscribed.

    Priority order:
    1. Kajabi email with subscription = YES
    2. Ticket Tailor email with subscription = YES
    3. Manual email with subscription = YES
    4. Default: NO
    """
    emails = get_all_contact_emails(contact_id, subscribed_only=True)

    # Check Kajabi first (authoritative)
    if any(e.source == 'kajabi' and e.subscribed for e in emails):
        return True, 'kajabi'

    # Check Ticket Tailor (protected opt-ins)
    if any(e.source == 'ticket_tailor' and e.subscribed for e in emails):
        return True, 'ticket_tailor'

    # Check Manual (trusted)
    if any(e.source == 'manual' and e.subscribed for e in emails):
        return True, 'manual'

    return False, None
```

---

### Phase 3: Import Process Hardening (Week 3)

#### 3.1. Pre-Import Validation

**Required before ANY import**:
```bash
# 1. Dry-run with duplicate detection
python scripts/weekly_import_kajabi_v2.py --dry-run --report duplicates

# 2. Generate subscription diff report
python scripts/generate_subscription_diff.py \
  --current-db \
  --new-import data/current/v2_contacts.csv \
  --output reports/subscription_changes_$(date +%Y%m%d).csv

# 3. Manual review of ANY subscription changes
# 4. Approve import
# 5. Execute import
```

#### 3.2. Merge Process Updates

**New Merge Logic**:
```sql
CREATE OR REPLACE FUNCTION merge_contacts_v2(
  p_primary_id UUID,
  p_duplicate_id UUID
) RETURNS VOID AS $$
BEGIN
  -- RULE 1: Preserve ALL emails
  INSERT INTO contact_emails (contact_id, email, source, email_subscribed)
  SELECT
    p_primary_id,
    ce.email,
    ce.source,
    ce.email_subscribed
  FROM contact_emails ce
  WHERE ce.contact_id = p_duplicate_id
  ON CONFLICT (contact_id, email) DO UPDATE
  SET email_subscribed = EXCLUDED.email_subscribed OR contact_emails.email_subscribed;

  -- RULE 2: If EITHER contact subscribed, result is subscribed
  UPDATE contacts
  SET email_subscribed = (
    SELECT bool_or(email_subscribed)
    FROM contact_emails
    WHERE contact_id = p_primary_id
  )
  WHERE id = p_primary_id;

  -- RULE 3: Preserve subscription protection
  UPDATE contacts
  SET subscription_protected = (
    SELECT bool_or(subscription_protected)
    FROM (
      VALUES
        ((SELECT subscription_protected FROM contacts WHERE id = p_primary_id)),
        ((SELECT subscription_protected FROM contacts WHERE id = p_duplicate_id))
    ) AS v(sub_protected)
  )
  WHERE id = p_primary_id;

  -- Continue with standard merge...
END;
$$ LANGUAGE plpgsql;
```

---

## Testing Strategy

### Unit Tests
1. Merge preserves opt-ins (both directions)
2. Merge preserves multiple emails
3. Import doesn't create duplicates
4. Subscription hierarchy logic

### Integration Tests
1. Full Kajabi import (with subscription changes)
2. Ticket Tailor import (protect existing opt-ins)
3. Merge + re-import scenarios

### Compliance Tests
1. No opt-ins lost during any operation
2. No auto-subscriptions (only explicit opt-ins)
3. Audit trail for all subscription changes

### Data Quality Tests
1. No duplicate emails within a contact
2. Primary email always in contact_emails
3. Subscription counts match across tables

---

## Rollback Strategy

### Backup Before Each Phase
```sql
-- Full backup
CREATE TABLE contacts_backup_phase1 AS SELECT * FROM contacts;
CREATE TABLE contact_emails_backup_phase1 AS SELECT * FROM contact_emails;

-- Subscription-specific backup
CREATE TABLE subscription_audit_$(date) AS
SELECT
  c.id,
  c.email,
  c.email_subscribed,
  c.source_system,
  ARRAY_AGG(ce.email ORDER BY ce.is_primary DESC) as all_emails,
  ARRAY_AGG(ce.email_subscribed ORDER BY ce.is_primary DESC) as all_sub_status
FROM contacts c
LEFT JOIN contact_emails ce ON c.id = ce.contact_id
GROUP BY c.id;
```

### Rollback Procedure
```sql
-- If Phase 1 fails
TRUNCATE contacts;
INSERT INTO contacts SELECT * FROM contacts_backup_phase1;

-- Verify rollback
SELECT COUNT(*) FROM contacts WHERE email_subscribed = true;
-- Should match pre-migration count
```

---

## Monitoring & Alerts

### Metrics to Track
1. **Subscription Rate**: % of contacts opted in (target: maintain current ~63%)
2. **Lost Opt-Ins**: Contacts with `email_subscribed = false` where backup shows `true`
3. **Duplicate Creation Rate**: New contacts/week that match existing emails
4. **Merge Conflicts**: % of merges with subscription conflicts

### Alerts
- **CRITICAL**: Any decrease in total subscribed contacts
- **WARNING**: >5% subscription conflicts in weekly merge batch
- **INFO**: New Ticket Tailor opt-ins detected

---

## Implementation Timeline

| Week | Phase | Tasks | Owner | Review |
|------|-------|-------|-------|--------|
| 1 | Phase 1 | Fix lost opt-ins, add protection flags | TBD | User |
| 2 | Phase 2a | Design per-email tracking schema | TBD | User |
| 2 | Phase 2b | Migration script + dry-run | TBD | User |
| 3 | Phase 2c | Execute migration | TBD | User |
| 3 | Phase 3a | Update import scripts | TBD | User |
| 4 | Phase 3b | Update merge scripts | TBD | User |
| 4 | Testing | Full regression test suite | TBD | User |

---

## Open Questions for Review

1. **Ticket Tailor IDs**: Why are they not set? Need to populate?
2. **Kajabi Re-import Risk**: If we run a new Kajabi import, will it overwrite our fixes?
3. **Primary Name/Email Policy**: Confirm that Kajabi contact name/email should be primary
4. **Historical Data**: Do we need to restore opt-ins from merges older than 30 days?
5. **Unsubscribe Tracking**: Do we need to track unsubscribe timestamps/reasons?

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Lost opt-ins during migration** | Medium | **CRITICAL** | Full backup + dry-run + manual review |
| **Auto-subscribing opted-out contacts** | Low | **CRITICAL** | Subscription hierarchy rules + testing |
| **Kajabi overwriting changes** | High | High | Import diff report + approval process |
| **Duplicate creation continues** | High | Medium | Enhanced lookup function + monitoring |
| **Performance impact** | Low | Low | Indexed queries + batch processing |

---

## Success Criteria

**Phase 1 Complete**:
- [ ] All 50 lost opt-ins restored
- [ ] 36 Ticket Tailor opt-ins protected
- [ ] Zero duplicates in next weekly import
- [ ] Migration plan approved

**Phase 2 Complete**:
- [ ] Per-email subscription tracking live
- [ ] All existing subscriptions migrated correctly
- [ ] Verification report shows 100% accuracy

**Phase 3 Complete**:
- [ ] Import scripts use enhanced lookup
- [ ] Merge scripts preserve all subscriptions
- [ ] Monitoring dashboard deployed
- [ ] Zero subscription losses for 30 days

---

## Appendices

### A. Current Schema
```sql
-- contacts table
email_subscribed BOOLEAN DEFAULT false  -- Single flag, no history

-- contact_emails table (NO subscription tracking currently)
```

### B. Proposed Schema Changes
```sql
-- contact_emails table additions
ALTER TABLE contact_emails ADD COLUMN
  email_subscribed BOOLEAN DEFAULT NULL,
  email_subscription_source TEXT,
  email_subscribed_at TIMESTAMP,
  email_unsubscribed_at TIMESTAMP,
  unsubscribe_reason TEXT;

-- contacts table additions
ALTER TABLE contacts ADD COLUMN
  subscription_protected BOOLEAN DEFAULT false,
  subscription_last_verified_at TIMESTAMP;
```

### C. References
- [CAN-SPAM Compliance Guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business)
- [GDPR Email Marketing Requirements](https://gdpr.eu/email-marketing/)

---

**Next Steps**: Schedule review meeting to approve Phase 1 implementation.
