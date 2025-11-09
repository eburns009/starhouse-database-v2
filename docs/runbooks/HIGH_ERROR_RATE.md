# Runbook: High Error Rate

**Last Updated:** October 30, 2025
**Severity:** High
**On-Call:** Yes

---

## Symptoms

- ⚠️ Alert: "Error rate > 10% for 5 minutes"
- ⚠️ Multiple 500 errors in logs
- ⚠️ Increased customer complaints
- ⚠️ Sentry showing error spike

---

## Quick Check (60 seconds)

### 1. Identify Scope

```bash
# Check error rate by function
curl -H "apikey: $SUPABASE_KEY" \
  "https://lnagadkqejnopgfxwlkb.supabase.co/rest/v1/edge_function_logs?\
select=function_name,status_code,count&\
created_at=gte.$(date -u -d '5 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')"
```

**Questions to answer:**
- Is it all functions or just one?
- Is it all users or specific ones?
- Started suddenly or gradual increase?

### 2. Check Dependencies

```bash
# Database status
curl -I https://lnagadkqejnopgfxwlkb.supabase.co/rest/v1/

# Expected: 200 OK
# If 503: Database issue

# Check external APIs
curl -I https://api.kajabi.com/health
curl -I https://api.paypal.com/v1/
```

### 3. Recent Changes

- Check recent deployments (last 24 hours)
- Review recent git commits
- Check if any configuration changed

---

## Common Causes

### 1. Bad Deployment

**Symptoms:**
- Errors started right after deployment
- Errors in recently changed code
- Specific function affected

**Fix:**
```bash
# Rollback to previous version
git revert HEAD
git push origin main

# Or redeploy previous version
supabase functions deploy kajabi-webhook --version <previous-commit-sha>
```

**ETA:** 2-3 minutes

---

### 2. Database Performance Degradation

**Symptoms:**
- Slow response times
- Timeout errors
- `"Query timeout"` in logs

**Diagnosis:**
```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;
-- If > 80% of max: Connection pool exhausted

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check locks
SELECT * FROM pg_stat_activity WHERE wait_event IS NOT NULL;
```

**Fix:**
```sql
-- Kill long-running queries (use cautiously!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND query NOT LIKE '%pg_stat_activity%';

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_temp_fix ON table_name(column_name);
```

**ETA:** 5-10 minutes

---

### 3. External API Failure

**Symptoms:**
- Errors when calling Kajabi/PayPal/Ticket Tailor
- `"Connection refused"` or `"Timeout"`
- Platform status page shows incident

**Fix:**
```typescript
// Add to webhook handlers
const fetchWithRetry = async (url, options, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await fetch(url, options);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
};

// Temporary: Queue failed webhooks for later processing
// (Requires message queue setup)
```

**Immediate:** Accept webhook but queue for retry
**ETA:** 15-30 minutes for full fix

---

### 4. Memory/Resource Exhaustion

**Symptoms:**
- `"Out of memory"` errors
- Function timeouts
- Gradual performance degradation

**Diagnosis:**
```bash
# Check function memory usage (in Supabase dashboard)
# Look for memory leaks (increasing usage over time)
```

**Fix:**
```bash
# Restart all functions
supabase functions deploy --all --project-ref lnagadkqejnopgfxwlkb

# If recurring: Optimize code
# - Clear large arrays/objects
# - Use streaming for large files
# - Add pagination
```

**ETA:** 5 minutes to restart, 1+ hour to fix root cause

---

### 5. Bad Data/Payload

**Symptoms:**
- Validation errors
- `"TypeError"` or `"undefined"`
- Errors for specific customers only

**Diagnosis:**
```bash
# Find failing payloads in logs
# Look for common patterns
# Check if data format changed
```

**Fix:**
```typescript
// Add defensive coding
const email = payload?.data?.email || payload?.email;
if (!email || !isValidEmail(email)) {
  logger.warn('Invalid email in payload', { payload: sanitize(payload) });
  return new Response('Accepted', { status: 202 }); // Accept but don't process
}

// Add validation schema
import { z } from 'zod';

const PayloadSchema = z.object({
  email: z.string().email(),
  amount: z.number().positive(),
  // ... other fields
});

try {
  const validData = PayloadSchema.parse(payload);
  // Process validData
} catch (error) {
  logger.error('Validation failed', { error, payload });
  return new Response('Bad Request', { status: 400 });
}
```

**ETA:** 30 minutes to add validation, deploy

---

## Investigation Checklist

### Phase 1: Triage (0-5 minutes)

- [ ] Check error rate trend (increasing/stable/decreasing?)
- [ ] Identify affected functions
- [ ] Check for recent deployments
- [ ] Verify database is up
- [ ] Check external service status pages

### Phase 2: Diagnosis (5-15 minutes)

- [ ] Sample error logs (read 10-20 errors)
- [ ] Identify error patterns
- [ ] Check affected user count
- [ ] Review recent code changes
- [ ] Check system metrics (CPU, memory, connections)

### Phase 3: Resolution (15-30 minutes)

- [ ] Apply fix (rollback, patch, or workaround)
- [ ] Deploy fix
- [ ] Verify error rate decreasing
- [ ] Monitor for 10 minutes
- [ ] Confirm resolution

---

## Monitoring During Incident

### Watch These Metrics

```bash
# Error rate (check every minute)
watch -n 60 'curl -s "https://lnagadkqejnopgfxwlkb.supabase.co/functions/v1/metrics" | grep error_rate'

# Active errors (real-time)
# In Supabase dashboard: Logs → Filter: error → Live

# Success rate (should increase after fix)
# Target: Back to > 95%
```

### Success Criteria

✅ Error rate < 5% for 10 consecutive minutes
✅ No new error patterns emerging
✅ Latency back to normal (< 2s p95)
✅ Customer complaints stopped

---

## Communication Template

### Internal (Slack #incidents)

```
🚨 INCIDENT: High Error Rate

Status: [Investigating|Identified|Fixing|Monitoring|Resolved]
Severity: High
Impact: [X%] of requests failing
Started: [HH:MM UTC]
ETA: [XX minutes]

Current Actions:
- [What you're doing right now]

Next Update: [In X minutes]
```

### External (If customer-facing)

```
We're experiencing elevated error rates affecting [feature/service].
Our team is actively working on a fix.
ETA: [XX minutes]

Status updates: https://status.yoursite.com
```

---

## Preventive Measures

### Short-term (This Week)

1. **Add Better Error Handling**
   ```typescript
   try {
     // Risky operation
   } catch (error) {
     logger.error('Operation failed', { error, context });
     // Graceful degradation instead of 500
     return fallbackResponse();
   }
   ```

2. **Add Circuit Breaker**
   ```typescript
   // Skip external API if failing
   if (apiErrorRate > 0.5) {
     return queueForLater(payload);
   }
   ```

3. **Improve Monitoring**
   - Add alerting for error rate > 5%
   - Set up error rate dashboard
   - Enable error sampling in Sentry

### Long-term (This Month)

4. **Load Testing**
   ```bash
   # Test with 10x normal load
   artillery quick --count 1000 --num 10 https://your-webhook-url
   ```

5. **Chaos Engineering**
   - Randomly kill functions
   - Simulate database slowness
   - Test external API failures

6. **Automated Rollback**
   - Deploy canary (5% traffic)
   - Auto-rollback if error rate > 10%
   - Gradual rollout (5% → 25% → 50% → 100%)

---

## Escalation Path

### Level 1: On-Call Engineer (0-15 min)
- Follow runbook
- Attempt fixes
- Update #incidents channel

### Level 2: Senior Engineer (15-30 min)
If not resolved or getting worse:
- @senior-engineer on Slack
- Share investigation findings
- Request additional help

### Level 3: Engineering Manager (30-60 min)
If revenue impacted or escalating:
- Page via PagerDuty
- Consider emergency maintenance window
- Prepare customer communication

---

## Post-Incident Actions

### Immediate (Within 1 hour)

1. **Verify Full Recovery**
   - Error rate < 2% for 30 minutes
   - No lingering issues
   - All services healthy

2. **Document**
   - Save error logs
   - Screenshot metrics
   - List timeline of events

3. **Communicate**
   - Internal: "Incident resolved"
   - External (if needed): Status update
   - Thank responders

### Follow-up (Within 48 hours)

4. **Post-Mortem**
   - Schedule meeting (all responders)
   - Use template from Webhook Failures runbook
   - Focus on prevention

5. **Action Items**
   - Create tickets for fixes
   - Assign owners
   - Set deadlines

6. **Update Runbook**
   - Add new scenarios encountered
   - Document new fixes
   - Update escalation if needed

---

## Quick Reference

### Key Metrics
- **Normal Error Rate:** < 2%
- **Warning Threshold:** > 5%
- **Critical Threshold:** > 10%
- **Normal Latency:** < 2s (p95)
- **Warning Latency:** > 5s (p95)

### Common Commands
```bash
# View recent errors
supabase functions log --filter "status_code=gte.500" \
  --project-ref lnagadkqejnopgfxwlkb

# Rollback deployment
git revert HEAD && git push

# Restart all functions
supabase functions deploy --all

# Check database health
psql -h aws-0-us-west-1.pooler.supabase.com \
  -p 6543 -U ***REMOVED*** \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

---

**Last Tested:** [Date]
**Next Review:** [Date + 1 month]
