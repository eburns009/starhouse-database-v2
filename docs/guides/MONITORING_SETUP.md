# Monitoring & Observability Setup

**Priority:** 🔴 P0 (Critical)
**Last Updated:** October 30, 2025
**Estimated Time:** 1-2 days

---

## Table of Contents

1. [Overview](#overview)
2. [Current State](#current-state)
3. [Structured Logging](#structured-logging)
4. [Metrics & Dashboards](#metrics--dashboards)
5. [Alerting](#alerting)
6. [Health Checks](#health-checks)
7. [Error Tracking](#error-tracking)
8. [Performance Monitoring](#performance-monitoring)

---

## Overview

**Current State:** No monitoring ⚠️
**You are flying blind** - no visibility into production issues.

### Why Monitoring is Critical

Without monitoring:
- ❌ Issues discovered by users (bad!)
- ❌ No performance baseline
- ❌ Can't diagnose failures
- ❌ No capacity planning data

With monitoring:
- ✅ Alert before users affected
- ✅ Quick root cause analysis
- ✅ Data-driven decisions
- ✅ Proactive scaling

---

## Current State

### What's Missing

1. **No Structured Logging**
   - Using `console.log()` (production anti-pattern)
   - No correlation IDs
   - No log aggregation

2. **No Metrics**
   - Webhook success/failure rates unknown
   - Database latency unknown
   - No business metrics (revenue, signups)

3. **No Alerts**
   - No one knows when things break
   - No on-call rotation
   - No escalation policy

4. **No Dashboards**
   - No real-time health view
   - No historical trends
   - No SLA tracking

---

## Structured Logging

### Replace console.log with Proper Logger

**Create: `supabase/functions/_shared/logger.ts`**

```typescript
export interface LogContext {
  requestId?: string;
  userId?: string;
  contactId?: string;
  transactionId?: string;
  amount?: number;
  email?: string;
  [key: string]: any;
}

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

export class Logger {
  private service: string;
  private environment: string;

  constructor(service: string) {
    this.service = service;
    this.environment = Deno.env.get('ENVIRONMENT') || 'production';
  }

  private log(level: LogLevel, message: string, context?: LogContext) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      service: this.service,
      environment: this.environment,
      message,
      ...context
    };

    // In production, send to log aggregation service
    if (this.environment === 'production') {
      // TODO: Send to DataDog, CloudWatch, or Supabase Logs API
      console.log(JSON.stringify(logEntry));
    } else {
      // Pretty print in development
      console.log(`[${level.toUpperCase()}] ${this.service}: ${message}`, context || '');
    }
  }

  debug(message: string, context?: LogContext) {
    this.log(LogLevel.DEBUG, message, context);
  }

  info(message: string, context?: LogContext) {
    this.log(LogLevel.INFO, message, context);
  }

  warn(message: string, context?: LogContext) {
    this.log(LogLevel.WARN, message, context);
  }

  error(message: string, context?: LogContext) {
    this.log(LogLevel.ERROR, message, context);
  }
}
```

### Usage in Webhooks

**Before:**
```typescript
// ❌ Bad
console.log('Received Kajabi webhook:', payload);
console.error('Error processing webhook:', error);
```

**After:**
```typescript
// ✅ Good
import { Logger } from '../_shared/logger.ts';

const logger = new Logger('kajabi-webhook');

serve(async (req) => {
  const requestId = crypto.randomUUID();

  try {
    const payload = await req.json();

    logger.info('Webhook received', {
      requestId,
      eventType: payload.event_type,
      payloadSize: JSON.stringify(payload).length
    });

    // Process webhook...

    logger.info('Webhook processed successfully', {
      requestId,
      contactId: contact.id,
      transactionId: transaction.id,
      amount: transaction.amount,
      processingTimeMs: Date.now() - startTime
    });

    return new Response(JSON.stringify({ success: true, requestId }), {
      status: 200,
      headers: { ...corsHeaders }
    });

  } catch (error) {
    logger.error('Webhook processing failed', {
      requestId,
      error: error.message,
      stack: error.stack,
      payload: sanitizePayload(payload) // Remove sensitive data
    });

    return new Response(
      JSON.stringify({ error: 'Internal server error', requestId }),
      { status: 500, headers: { ...corsHeaders } }
    );
  }
});
```

### Benefits

- **Searchable:** Find all logs for a specific requestId
- **Structured:** Easy to parse and analyze
- **Context-rich:** Know exactly what happened
- **Traceable:** Follow a request through the system

---

## Metrics & Dashboards

### Key Metrics to Track

#### 1. Webhook Metrics

- **Success Rate:** `successful_webhooks / total_webhooks`
- **Error Rate:** `failed_webhooks / total_webhooks`
- **Latency:** p50, p95, p99 response times
- **Throughput:** Requests per minute

#### 2. Business Metrics

- **New Contacts:** Contacts created per day
- **Revenue:** Total transaction amount per day
- **Active Subscriptions:** Count of active subscriptions
- **Churn Rate:** Cancelled subscriptions / total subscriptions

#### 3. Database Metrics

- **Query Latency:** Average query execution time
- **Connection Pool:** Active/idle connections
- **Slow Queries:** Queries taking >1s

#### 4. System Metrics

- **CPU Usage:** % utilization
- **Memory Usage:** MB used
- **Error Rate:** Errors per minute
- **Uptime:** % availability

### Implementation Options

#### Option 1: Supabase Built-in Monitoring (Quick Start)

1. Go to: https://app.supabase.com/project/lnagadkqejnopgfxwlkb/logs
2. View edge function logs
3. Filter by severity, function, date

**Pros:** Free, already set up
**Cons:** Basic, no custom metrics

#### Option 2: DataDog (Recommended for Production)

**Setup:**

```typescript
// Install DataDog Deno SDK
import { datadogLogs } from 'https://esm.sh/@datadog/browser-logs';

datadogLogs.init({
  clientToken: Deno.env.get('DATADOG_CLIENT_TOKEN'),
  site: 'datadoghq.com',
  service: 'starhouse-webhooks',
  env: 'production',
  forwardErrorsToLogs: true,
  sessionSampleRate: 100
});

// Send custom metrics
datadogLogs.logger.info('Webhook processed', {
  eventType: 'order.created',
  amount: 100.00,
  customMetric: 'webhook_success'
});
```

**Cost:** $15/month for 1M logs

#### Option 3: CloudWatch (AWS)

If using AWS infrastructure:

```typescript
import { CloudWatchLogs } from "https://deno.land/x/aws_sdk/client-cloudwatch-logs/mod.ts";

const client = new CloudWatchLogs({
  region: "us-west-2",
  credentials: {
    accessKeyId: Deno.env.get('AWS_ACCESS_KEY_ID'),
    secretAccessKey: Deno.env.get('AWS_SECRET_ACCESS_KEY')
  }
});

await client.putLogEvents({
  logGroupName: '/starhouse/webhooks',
  logStreamName: 'kajabi-webhook',
  logEvents: [{
    timestamp: Date.now(),
    message: JSON.stringify(logEntry)
  }]
});
```

---

## Alerting

### Alert Rules

#### Critical Alerts (Page Immediately)

1. **Webhook Failure Rate > 10%**
   ```
   Condition: (failed_webhooks / total_webhooks) > 0.10 for 5 minutes
   Action: Page on-call engineer
   ```

2. **Database Connection Failure**
   ```
   Condition: Database unreachable
   Action: Page on-call + notify team
   ```

3. **Payment Processing Failure**
   ```
   Condition: Transaction creation fails
   Action: Page on-call (money at risk!)
   ```

#### Warning Alerts (Notify Team)

4. **High Latency**
   ```
   Condition: p95 latency > 5 seconds for 10 minutes
   Action: Slack notification
   ```

5. **Low Success Rate**
   ```
   Condition: Success rate < 95% for 10 minutes
   Action: Slack notification
   ```

6. **Unusual Traffic Spike**
   ```
   Condition: Requests > 2x normal for 5 minutes
   Action: Slack notification (potential attack)
   ```

### Setup with Better Uptime

**Free tier: 10 monitors**

1. Sign up: https://betterstack.com/uptime
2. Add monitors:
   - Kajabi webhook endpoint
   - PayPal webhook endpoint
   - Ticket Tailor webhook endpoint
   - Web app URL

3. Configure alerts:
   - Email: your-email@example.com
   - Slack: #alerts channel
   - SMS: (for critical alerts)

### Setup with PagerDuty

**For production on-call:**

1. Create service: "StarHouse Production"
2. Add escalation policy:
   - Primary: On-call engineer (immediate)
   - Secondary: Engineering manager (after 15 min)
   - Tertiary: CTO (after 30 min)

3. Integration:
```typescript
async function sendAlert(severity: string, message: string, details: any) {
  await fetch('https://events.pagerduty.com/v2/enqueue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      routing_key: Deno.env.get('PAGERDUTY_ROUTING_KEY'),
      event_action: 'trigger',
      payload: {
        summary: message,
        severity,
        source: 'starhouse-webhooks',
        custom_details: details
      }
    })
  });
}
```

---

## Health Checks

### Add Health Check Endpoint

**Create: `supabase/functions/health/index.ts`**

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

serve(async (req) => {
  const startTime = Date.now();
  const checks: any = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    checks: {}
  };

  // Check database connection
  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const { error } = await supabase
      .from('contacts')
      .select('id')
      .limit(1);

    checks.checks.database = {
      status: error ? 'unhealthy' : 'healthy',
      latencyMs: Date.now() - startTime,
      error: error?.message
    };

    if (error) checks.status = 'unhealthy';

  } catch (error) {
    checks.checks.database = {
      status: 'unhealthy',
      error: error.message
    };
    checks.status = 'unhealthy';
  }

  // Check environment variables
  checks.checks.config = {
    status: Deno.env.get('SUPABASE_URL') ? 'healthy' : 'unhealthy'
  };

  // System info
  checks.system = {
    uptime: performance.now(),
    version: '1.0.0',
    environment: Deno.env.get('ENVIRONMENT') || 'production'
  };

  return new Response(
    JSON.stringify(checks),
    {
      status: checks.status === 'healthy' ? 200 : 503,
      headers: { 'Content-Type': 'application/json' }
    }
  );
});
```

**Deploy:**
```bash
supabase functions deploy health
```

**Monitor:**
- Add to Better Uptime: Check every 1 minute
- Expected response: `{ "status": "healthy" }`
- Alert if status !== "healthy" or response time > 5s

---

## Error Tracking

### Sentry Integration (Recommended)

**Setup:**

```typescript
// supabase/functions/_shared/sentry.ts
import * as Sentry from "https://deno.land/x/sentry/index.mjs";

Sentry.init({
  dsn: Deno.env.get('SENTRY_DSN'),
  environment: Deno.env.get('ENVIRONMENT') || 'production',
  tracesSampleRate: 1.0
});

export function captureError(error: Error, context?: any) {
  Sentry.captureException(error, {
    extra: context
  });
}

export function captureMessage(message: string, level: 'info' | 'warning' | 'error') {
  Sentry.captureMessage(message, level);
}
```

**Usage:**
```typescript
import { captureError } from '../_shared/sentry.ts';

try {
  // ... webhook processing
} catch (error) {
  captureError(error, {
    webhook: 'kajabi',
    eventType: payload.event_type,
    requestId
  });
  throw error;
}
```

**Benefits:**
- Automatic error grouping
- Stack traces
- Affected user tracking
- Release tracking

**Cost:** Free for 5K errors/month

---

## Performance Monitoring

### Query Performance

**Enable slow query logging:**

```sql
-- Run in Supabase SQL Editor
ALTER DATABASE postgres SET log_min_duration_statement = 1000; -- Log queries > 1s

-- View slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### API Performance

**Track endpoint latency:**

```typescript
const performanceTimer = (name: string) => {
  const start = performance.now();
  return () => {
    const duration = performance.now() - start;
    logger.info('Performance metric', {
      metric: name,
      durationMs: duration
    });
    return duration;
  };
};

// Usage
const endTimer = performanceTimer('handleOrder');
await handleOrder(supabase, payload);
endTimer();
```

---

## Quick Start Checklist

### Week 1: Basic Monitoring

- [ ] Replace all `console.log` with structured logger
- [ ] Set up Better Uptime (free)
- [ ] Deploy health check endpoint
- [ ] Configure basic Slack alerts

### Week 2: Advanced Monitoring

- [ ] Set up Sentry error tracking
- [ ] Create monitoring dashboard
- [ ] Configure PagerDuty
- [ ] Document on-call procedures

### Month 1: Full Observability

- [ ] Implement custom metrics
- [ ] Set up business metrics dashboard
- [ ] Configure log retention
- [ ] Establish SLA targets

---

## Next Steps

1. ✅ Implement structured logging (today)
2. ➡️ Set up health checks
3. ➡️ Configure uptime monitoring
4. ➡️ Add error tracking
5. ➡️ Create dashboards

**Start with:** Structured logging - foundation for everything else.

---

**Related Docs:**
- [Runbook: High Error Rate](../runbooks/HIGH_ERROR_RATE.md)
- [Logging Standards](./LOGGING_STANDARDS.md)
- [Alerting Guide](./ALERTING.md)
