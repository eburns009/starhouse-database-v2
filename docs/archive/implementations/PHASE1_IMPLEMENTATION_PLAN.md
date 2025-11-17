# Phase 1: Email Subscription Compliance - Implementation Plan

**Target Completion**: End of Week 1
**Risk Level**: MEDIUM (touching subscription data)
**Rollback Time**: < 5 minutes

---

## Pre-Implementation Checklist

- [ ] Design document reviewed and approved by user
- [ ] Full database backup completed
- [ ] Subscription audit baseline captured
- [ ] Rollback procedure tested on staging
- [ ] All scripts code-reviewed

---

## Step 1: Create Baseline & Backup

**Objective**: Capture current state for comparison and rollback

**Script**: `scripts/phase1_01_create_baseline.sql`

```sql
-- Creates:
-- 1. Full contacts table backup
-- 2. Full contact_emails table backup
-- 3. Subscription baseline metrics
-- 4. List of all contacts that will be modified
```

**Verification**:
```bash
# Check backup tables exist
./db.sh -c "SELECT COUNT(*) FROM contacts_backup_phase1"

# Verify baseline metrics match current state
./db.sh -c "SELECT * FROM subscription_baseline_phase1"
```

**Success Criteria**:
- Backup tables created
- Row counts match
- Baseline report generated

---

## Step 2: Identify and Review Lost Opt-Ins

**Objective**: Generate list of 50 contacts for manual review

**Script**: `scripts/phase1_02_identify_lost_optins.sql`

**Output**: `reports/lost_optins_review_$(date).csv`

**Manual Review Required**:
For each of the 50 contacts, verify:
1. Duplicate had valid opt-in (from Kajabi or Ticket Tailor)
2. Merge was correct (not a mistake)
3. Contact should be re-subscribed

**Review Template**:
```
Contact ID: [UUID]
Current Email: [email]
Current Status: Opted Out
Duplicate Email: [dup_email]
Duplicate Status: Opted In
Duplicate Source: [kajabi/ticket_tailor/manual]
Merged Date: [date]

APPROVE RESUBSCRIBE? [YES/NO]
REASON IF NO: [text]
```

**Approval Required**: User must approve 100% of list before proceeding

---

## Step 3: Add Protection Mechanisms

**Objective**: Prevent future subscription data loss

**Script**: `scripts/phase1_03_add_protection.sql`

### 3.1. Add Schema Changes
```sql
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS
  subscription_protected BOOLEAN DEFAULT false,
  subscription_source TEXT,  -- 'kajabi', 'ticket_tailor', 'manual'
  subscription_last_import_at TIMESTAMP;
```

### 3.2. Mark Protected Contacts
```sql
-- Ticket Tailor opt-ins (36 contacts)
UPDATE contacts
SET
  subscription_protected = true,
  subscription_source = 'ticket_tailor'
WHERE source_system = 'ticket_tailor'
  AND email_subscribed = true;

-- Kajabi opt-ins from confirmed list
UPDATE contacts
SET subscription_source = 'kajabi'
WHERE kajabi_id IS NOT NULL
  AND email_subscribed = true;
```

**Verification**:
```sql
SELECT
  subscription_source,
  COUNT(*) as protected_count
FROM contacts
WHERE subscription_protected = true OR subscription_source IS NOT NULL
GROUP BY subscription_source;
```

---

## Step 4: Restore Lost Opt-Ins (WITH APPROVAL)

**Objective**: Re-subscribe the 50 approved contacts

**Script**: `scripts/phase1_04_restore_optins.sql`

**Input Required**: Approved list from Step 2

```sql
-- DRY RUN MODE FIRST
BEGIN;

-- Show what will be updated
SELECT
  c.id,
  c.email,
  c.first_name || ' ' || c.last_name as name,
  'false' as current_status,
  'true' as new_status,
  cmb.duplicate_contact_data->>'email' as source_email,
  cmb.duplicate_contact_data->>'source_system' as source
FROM contacts c
JOIN contacts_merge_backup cmb ON c.id = cmb.primary_contact_id
WHERE c.id IN (
  -- APPROVED IDS ONLY (populated from approved CSV)
  -- Example: '8109792b-9bcb-4cef-87e4-0fb658fe372e'
);

-- User reviews output, confirms it matches approved list

ROLLBACK;  -- DRY RUN

-- ACTUAL EXECUTION (after approval)
BEGIN;

UPDATE contacts
SET
  email_subscribed = true,
  subscription_source = (
    SELECT cmb.duplicate_contact_data->>'source_system'
    FROM contacts_merge_backup cmb
    WHERE cmb.primary_contact_id = contacts.id
    LIMIT 1
  ),
  updated_at = NOW()
WHERE id IN (
  -- PASTE APPROVED IDS HERE
);

-- Verification before commit
SELECT
  'Contacts updated' as metric,
  COUNT(*) as count
FROM contacts
WHERE updated_at > NOW() - INTERVAL '1 minute'
  AND email_subscribed = true;

-- MANUAL DECISION POINT
-- User confirms count matches approved list (50 contacts)

COMMIT;  -- or ROLLBACK if count doesn't match
```

**Safety Checks**:
1. Dry-run shows exactly 50 contacts
2. All IDs match approved list
3. No contacts being subscribed that weren't approved
4. Backup exists and is verified

---

## Step 5: Deploy Enhanced Contact Lookup Function

**Objective**: Prevent future duplicate creation

**Script**: `scripts/phase1_05_deploy_lookup_function.sql`

```sql
CREATE OR REPLACE FUNCTION find_contact_by_any_email(search_email CITEXT)
RETURNS UUID AS $$
DECLARE
    contact_id_result UUID;
BEGIN
    search_email := LOWER(TRIM(search_email));

    SELECT c.id INTO contact_id_result
    FROM contacts c
    WHERE c.deleted_at IS NULL
      AND (
        c.email = search_email
        OR c.additional_email = search_email
        OR c.paypal_email = search_email
        OR c.zoho_email = search_email
        OR EXISTS (
          SELECT 1
          FROM contact_emails ce
          WHERE ce.contact_id = c.id
            AND ce.email = search_email
        )
      )
    LIMIT 1;

    RETURN contact_id_result;
END;
$$ LANGUAGE plpgsql STABLE;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_contacts_all_emails_lookup ON contacts
  USING gin((ARRAY[email, additional_email, paypal_email, zoho_email]));
```

**Testing**:
```sql
-- Test 1: Find by primary email
SELECT find_contact_by_any_email('amber@the360emergence.com');
-- Expected: Returns Lynn Ryan's ID

-- Test 2: Find by additional email
SELECT find_contact_by_any_email('sacredartsspace@gmail.com');
-- Expected: Returns same ID (Lynn Ryan)

-- Test 3: Non-existent email
SELECT find_contact_by_any_email('nonexistent@test.com');
-- Expected: Returns NULL
```

---

## Step 6: Post-Implementation Verification

**Objective**: Confirm all changes were successful

**Script**: `scripts/phase1_06_verify.sql`

### Verification Checklist

```sql
-- 1. Verify subscription count increased by exactly 50
SELECT
  'Subscription Increase' as metric,
  (SELECT COUNT(*) FROM contacts WHERE email_subscribed = true) -
  (SELECT subscribed_count FROM subscription_baseline_phase1) as difference,
  CASE
    WHEN (SELECT COUNT(*) FROM contacts WHERE email_subscribed = true) -
         (SELECT subscribed_count FROM subscription_baseline_phase1) = 50
    THEN '✓ PASS'
    ELSE '✗ FAIL'
  END as status;

-- 2. Verify no unexpected changes
SELECT
  'Unexpected Unsubscribes' as metric,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 0 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM contacts c
JOIN contacts_backup_phase1 cb ON c.id = cb.id
WHERE cb.email_subscribed = true
  AND c.email_subscribed = false
  AND c.id NOT IN (SELECT id FROM approved_unsubscribes_list);

-- 3. Verify protection flags set
SELECT
  'Protected Ticket Tailor Opt-ins' as metric,
  COUNT(*) as count,
  CASE WHEN COUNT(*) = 36 THEN '✓ PASS' ELSE '✗ FAIL' END as status
FROM contacts
WHERE subscription_protected = true
  AND subscription_source = 'ticket_tailor';

-- 4. Verify lookup function works
SELECT
  'Lookup Function Test' as metric,
  CASE
    WHEN find_contact_by_any_email('amber@the360emergence.com') IS NOT NULL
      AND find_contact_by_any_email('sacredartsspace@gmail.com') = find_contact_by_any_email('amber@the360emergence.com')
    THEN '✓ PASS'
    ELSE '✗ FAIL'
  END as status;

-- 5. Generate diff report
SELECT
  c.id,
  c.email,
  cb.email_subscribed as before_phase1,
  c.email_subscribed as after_phase1,
  c.subscription_source,
  c.subscription_protected
FROM contacts c
JOIN contacts_backup_phase1 cb ON c.id = cb.id
WHERE c.email_subscribed != cb.email_subscribed
ORDER BY c.email_subscribed DESC, c.email;
```

**Success Criteria**:
- All 6 verification checks pass
- Diff report matches approved changes exactly
- No unexpected subscription changes

---

## Step 7: Monitoring Setup

**Objective**: Track subscription metrics going forward

**Script**: `scripts/phase1_07_setup_monitoring.sql`

```sql
CREATE TABLE subscription_metrics_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  measured_at TIMESTAMP DEFAULT NOW(),
  total_contacts INTEGER,
  subscribed_contacts INTEGER,
  opt_in_rate NUMERIC(5,2),
  protected_contacts INTEGER,
  kajabi_subscribed INTEGER,
  ticket_tailor_subscribed INTEGER,
  notes TEXT
);

-- Initial snapshot
INSERT INTO subscription_metrics_history (
  total_contacts,
  subscribed_contacts,
  opt_in_rate,
  protected_contacts,
  kajabi_subscribed,
  ticket_tailor_subscribed,
  notes
)
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN email_subscribed = true THEN 1 END) as subscribed,
  ROUND(100.0 * COUNT(CASE WHEN email_subscribed = true THEN 1 END) / COUNT(*), 2),
  COUNT(CASE WHEN subscription_protected = true THEN 1 END),
  COUNT(CASE WHEN subscription_source = 'kajabi' AND email_subscribed = true THEN 1 END),
  COUNT(CASE WHEN subscription_source = 'ticket_tailor' AND email_subscribed = true THEN 1 END),
  'Phase 1 completed'
FROM contacts
WHERE deleted_at IS NULL;

-- Create daily snapshot function
CREATE OR REPLACE FUNCTION record_subscription_metrics()
RETURNS void AS $$
BEGIN
  INSERT INTO subscription_metrics_history (
    total_contacts, subscribed_contacts, opt_in_rate,
    protected_contacts, kajabi_subscribed, ticket_tailor_subscribed
  )
  SELECT
    COUNT(*),
    COUNT(CASE WHEN email_subscribed = true THEN 1 END),
    ROUND(100.0 * COUNT(CASE WHEN email_subscribed = true THEN 1 END) / COUNT(*), 2),
    COUNT(CASE WHEN subscription_protected = true THEN 1 END),
    COUNT(CASE WHEN subscription_source = 'kajabi' AND email_subscribed = true THEN 1 END),
    COUNT(CASE WHEN subscription_source = 'ticket_tailor' AND email_subscribed = true THEN 1 END)
  FROM contacts
  WHERE deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;
```

---

## Rollback Procedure

**If ANY verification fails:**

```sql
BEGIN;

-- 1. Restore contacts table
TRUNCATE contacts;
INSERT INTO contacts SELECT * FROM contacts_backup_phase1;

-- 2. Restore contact_emails table (if modified)
TRUNCATE contact_emails;
INSERT INTO contact_emails SELECT * FROM contact_emails_backup_phase1;

-- 3. Verify rollback
SELECT
  'Rollback Verification' as check,
  CASE
    WHEN (SELECT COUNT(*) FROM contacts WHERE email_subscribed = true) =
         (SELECT subscribed_count FROM subscription_baseline_phase1)
    THEN '✓ Rollback successful'
    ELSE '✗ Rollback failed - CRITICAL'
  END as status;

COMMIT;
```

**Rollback Time**: < 5 minutes
**Data Loss**: None (all changes reversed)

---

## Communication Plan

### Before Implementation
- [ ] Email stakeholders: "Phase 1 email compliance fixes scheduled for [DATE]"
- [ ] Expected downtime: None (read-only operations during verification)
- [ ] Testing window: [TIME RANGE]

### During Implementation
- [ ] Progress updates every 30 minutes
- [ ] Immediate notification if verification fails
- [ ] Rollback decision within 15 minutes if issues found

### After Implementation
- [ ] Success email with metrics
- [ ] Diff report attached
- [ ] Monitoring dashboard link

---

## Sign-Off Required

**Before proceeding with execution:**

- [ ] Design document approved by: ___________________
- [ ] Lost opt-ins list reviewed by: ___________________
- [ ] Rollback procedure tested by: ___________________
- [ ] Execution scheduled for: ___________________

**Execution Approval:**

- [ ] All pre-checks passed
- [ ] Backup verified
- [ ] Dry-run output reviewed
- [ ] Final approval to execute: ___________________

---

## Timeline

| Step | Duration | Dependencies | Go/No-Go |
|------|----------|--------------|----------|
| 1. Baseline | 10 min | None | Auto |
| 2. Review List | 2-4 hours | User review | **MANUAL** |
| 3. Add Protection | 5 min | Step 1 | Auto |
| 4. Restore Opt-ins | 15 min | Step 2 approved | **MANUAL** |
| 5. Deploy Lookup | 5 min | Testing | Auto |
| 6. Verification | 10 min | All above | Auto |
| 7. Monitoring | 5 min | Step 6 passed | Auto |

**Total Execution Time**: ~1 hour (excluding review)
**Total Project Time**: 1-2 days (including review)

---

**Next Action**: User approval required to proceed with Step 1 (Create Baseline).
