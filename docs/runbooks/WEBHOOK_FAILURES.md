# Runbook: Webhook Failures

**Last Updated:** October 30, 2025
**Severity:** High
**On-Call:** Yes

---

## Symptoms

- ❌ Webhook endpoint returning 500 errors
- ❌ Transactions not appearing in database
- ❌ Contacts not being created
- ❌ Supabase logs showing "Transaction creation failed"
- ❌ Alert: "Webhook failure rate > 10%"

---

## Quick Diagnosis (30 seconds)

### Check Current Status

```bash
# Test webhooks are responding
curl -I https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/health

# Expected: HTTP/2 200
# If 503/500: Service down
```

### Check Logs

1. Go to Supabase logs: https://app.supabase.com/project/lnagadkqejnopgfxwlkb/logs/edge-functions

2. Filter by:
   - Function: `kajabi-webhook` or `paypal-webhook` or `ticket-tailor-webhook`
   - Severity: Error
   - Time: Last 15 minutes

3. Look for common errors:
   - `"No email found"` → Bad payload
   - `"Database connection failed"` → DB issue
   - `"Invalid signature"` → Webhook verification issue
   - `"Rate limit exceeded"` → Attack/spike in traffic

---

## Common Causes & Fixes

### 1. Database Connection Failed

**Symptoms:**
```
Error: "connect ETIMEDOUT" or "Database connection failed"
```

**Diagnosis:**
```bash
# Check database status
curl -H "apikey: $SUPABASE_KEY" \
  "https://lnagadkqejnopgfxwlkb.supabase.co/rest/v1/contacts?select=count&limit=1"

# Expected: Returns count
# If timeout: Database down
```

**Resolution:**

1. Check Supabase status: https://status.supabase.com
2. If Supabase incident: Wait for resolution
3. If no incident:
   ```bash
   # Restart edge functions
   supabase functions deploy kajabi-webhook
   supabase functions deploy paypal-webhook
   supabase functions deploy ticket-tailor-webhook
   ```
4. Verify fix:
   ```bash
   curl -X POST https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/kajabi-webhook \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

**ETA:** 2-5 minutes

---

### 2. Invalid Webhook Signature

**Symptoms:**
```
Error: "Invalid webhook signature" or "Unauthorized"
Log: 401 responses
```

**Diagnosis:**
```bash
# Check if webhook secret is set
supabase secrets list --project-ref lnagadkqejnopgfxwlkb | grep WEBHOOK_SECRET
```

**Resolution:**

1. Verify webhook secret in platform:
   - Kajabi: Settings → Webhooks → Show secret
   - PayPal: Developer dashboard → Webhooks → Show secret
   - Ticket Tailor: Settings → Webhooks → Show secret

2. Update Supabase secret:
   ```bash
   supabase secrets set \
     KAJABI_WEBHOOK_SECRET="<new-secret>" \
     --project-ref lnagadkqejnopgfxwlkb
   ```

3. Redeploy function:
   ```bash
   supabase functions deploy kajabi-webhook
   ```

4. Test with valid webhook from platform dashboard

**ETA:** 5 minutes

---

### 3. Rate Limit Exceeded

**Symptoms:**
```
Error: "Rate limit exceeded"
HTTP 429 responses
Sudden spike in traffic
```

**Diagnosis:**
```bash
# Check recent request volume
# In Supabase logs, count requests in last 5 minutes
# If > 500: Likely attack or bug causing retry storm
```

**Resolution:**

1. **Immediate:** Block suspicious IPs
   ```sql
   -- Check for suspicious patterns
   SELECT
     ip_address,
     COUNT(*) as request_count,
     MIN(created_at) as first_request,
     MAX(created_at) as last_request
   FROM edge_function_logs
   WHERE function_name = 'kajabi-webhook'
     AND created_at > NOW() - INTERVAL '5 minutes'
   GROUP BY ip_address
   HAVING COUNT(*) > 100
   ORDER BY request_count DESC;
   ```

2. **If legitimate traffic spike:**
   - Increase rate limit temporarily
   - Scale up Supabase plan
   - Contact Supabase support

3. **If attack:**
   - Add IP to blocklist
   - Enable Cloudflare DDoS protection
   - Notify security team

**ETA:** 10-15 minutes

---

### 4. Invalid Payload Format

**Symptoms:**
```
Error: "Validation failed" or "Required field missing"
TypeError: Cannot read property 'email' of undefined
```

**Diagnosis:**

1. Check recent webhook payload in logs
2. Compare to expected format
3. Check if platform changed API format

**Resolution:**

1. **Short-term:** Add error handling for malformed payload
   ```typescript
   // Add to webhook handler
   if (!payload.data?.email) {
     logger.warn('Invalid payload: missing email', { payload });
     return new Response('Accepted', { status: 202 }); // Accept but don't process
   }
   ```

2. **Long-term:** Update validation schema
3. **Immediate:** Notify sender to fix payloads

**ETA:** 15-30 minutes

---

### 5. Function Timeout

**Symptoms:**
```
Error: "Function timeout" or "504 Gateway Timeout"
Duration: > 10 seconds
```

**Diagnosis:**
```bash
# Check function execution time in logs
# Look for slow database queries
```

**Resolution:**

1. Check for slow queries:
   ```sql
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   WHERE mean_exec_time > 1000
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. Optimize slow queries (add indexes)
3. Break up large operations
4. Increase function timeout (max 300s)

**ETA:** 30+ minutes (requires code changes)

---

## Emergency Bypass

**If webhooks are completely down and transactions are being lost:**

### Option 1: Replay Webhooks

Most platforms allow replaying webhooks:

**Kajabi:**
1. Go to Settings → Webhooks
2. Find failed webhooks
3. Click "Replay"

**PayPal:**
1. Developer Dashboard → Webhooks
2. View event history
3. Click "Resend"

**Ticket Tailor:**
1. Settings → Webhooks
2. Event log → Resend

### Option 2: Manual Data Entry

```sql
-- Manually insert transaction
INSERT INTO transactions (
  contact_id,
  amount,
  currency,
  status,
  transaction_type,
  transaction_date,
  kajabi_transaction_id
) VALUES (
  (SELECT id FROM contacts WHERE email = 'customer@example.com'),
  99.99,
  'USD',
  'completed',
  'purchase',
  NOW(),
  'manual-entry-123'
);
```

### Option 3: CSV Import

If many transactions lost:

1. Export from platform (Kajabi, PayPal, etc.)
2. Use import script:
   ```bash
   python3 scripts/update_contacts_from_transactions.py
   ```

---

## Prevention

### Monitor These Metrics

1. **Webhook Success Rate:** Should be > 95%
   - Alert if < 95% for 5 minutes

2. **Average Latency:** Should be < 2 seconds
   - Alert if p95 > 5 seconds

3. **Error Rate:** Should be < 5%
   - Alert if > 10% for 5 minutes

4. **Database Connection Time:** Should be < 100ms
   - Alert if > 500ms

### Weekly Checks

- [ ] Review error logs (Monday morning)
- [ ] Check webhook platform status pages
- [ ] Verify all secrets are not expiring
- [ ] Test each webhook with dummy event

### Monthly Maintenance

- [ ] Rotate webhook secrets
- [ ] Review and optimize slow queries
- [ ] Update dependencies
- [ ] Load test webhooks

---

## Escalation

### Level 1: On-call Engineer (You)
- Follow this runbook
- Attempt fixes
- Monitor resolution

### Level 2: Engineering Lead (15 min)
If not resolved in 15 minutes:
- Escalate to @engineering-lead on Slack
- Provide:
  - Symptoms
  - Steps attempted
  - Current error logs

### Level 3: CTO (30 min)
If not resolved in 30 minutes OR revenue impact > $1K:
- Page CTO via PagerDuty
- Enable emergency bypass
- Consider platform status page update

---

## Post-Incident

### After Resolution

1. **Document:**
   - What broke
   - Root cause
   - How it was fixed
   - How long outage lasted

2. **Notify:**
   - Internal stakeholders
   - Affected customers (if any)
   - Update status page

3. **Follow-up:**
   - Schedule post-mortem (within 48 hours)
   - Create preventive measure tickets
   - Update runbook with learnings

### Post-Mortem Template

```markdown
## Incident: Webhook Failures - [Date]

**Duration:** [X hours Y minutes]
**Impact:** [N transactions lost/delayed]
**Revenue Impact:** [$X]

**Timeline:**
- HH:MM - First alert
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Verified resolution

**Root Cause:**
[What actually broke]

**Contributing Factors:**
[What made it worse]

**Resolution:**
[How we fixed it]

**Prevention:**
[What we'll do to prevent recurrence]

**Action Items:**
- [ ] [Ticket] Add monitoring for X
- [ ] [Ticket] Improve error handling
- [ ] [Ticket] Update documentation
```

---

## Related Runbooks

- [High Error Rate](./HIGH_ERROR_RATE.md)
- [Database Connection Issues](./DATABASE_ISSUES.md)
- [Performance Degradation](./PERFORMANCE_DEGRADATION.md)

---

## Quick Reference

### Important URLs
- Supabase Logs: https://app.supabase.com/project/lnagadkqejnopgfxwlkb/logs
- Status Page: https://status.supabase.com
- PagerDuty: https://starhouse.pagerduty.com

### Key Commands
```bash
# Check health
curl https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/health

# View logs
supabase functions log kajabi-webhook --project-ref lnagadkqejnopgfxwlkb

# Redeploy
supabase functions deploy kajabi-webhook --project-ref lnagadkqejnopgfxwlkb

# Test webhook
curl -X POST [webhook-url] -H "Content-Type: application/json" -d '{"test": true}'
```

---

**Last Tested:** [Date]
**Next Review:** [Date + 1 month]
