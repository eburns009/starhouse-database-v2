import { ErrorCodes, ErrorCode } from './error-codes.ts';
import type { SupabaseClient } from '@supabase/supabase-js';

export interface ErrorInfo {
  code: ErrorCode;
  message: string;
  stack?: string;
  retryable: boolean;
}

/**
 * Categorize an error and determine if it's retryable
 */
export function categorizeError(error: Error): ErrorInfo {
  const message = error.message;
  const stack = error.stack?.slice(0, 5000); // Limit stack size

  // Authentication errors
  if (message.includes('Invalid signature') || message.includes('signature verification failed')) {
    return { code: ErrorCodes.INVALID_SIGNATURE, message, stack, retryable: false };
  }
  if (message.includes('Missing') && message.includes('header')) {
    return { code: ErrorCodes.MISSING_AUTH_HEADER, message, stack, retryable: false };
  }
  if (message.includes('expired') && message.includes('token')) {
    return { code: ErrorCodes.EXPIRED_TOKEN, message, stack, retryable: false };
  }

  // Rate limiting
  if (message.includes('rate limit') || message.includes('too many requests')) {
    return { code: ErrorCodes.RATE_LIMITED, message, stack, retryable: true };
  }
  if (message.includes('nonce') && message.includes('already used')) {
    return { code: ErrorCodes.NONCE_REUSED, message, stack, retryable: false };
  }

  // Validation
  if (message.includes('validation') || message.includes('invalid')) {
    if (message.includes('email')) {
      return { code: ErrorCodes.INVALID_EMAIL, message, stack, retryable: false };
    }
    if (message.includes('country')) {
      return { code: ErrorCodes.INVALID_COUNTRY_CODE, message, stack, retryable: false };
    }
    if (message.includes('required')) {
      return { code: ErrorCodes.MISSING_REQUIRED_FIELD, message, stack, retryable: false };
    }
    return { code: ErrorCodes.VALIDATION_FAILED, message, stack, retryable: false };
  }

  // Database errors
  if (message.includes('database') || message.includes('postgres') || message.includes('pg')) {
    if (message.includes('timeout')) {
      return { code: ErrorCodes.DB_TIMEOUT, message, stack, retryable: true };
    }
    if (message.includes('constraint') || message.includes('duplicate key')) {
      return { code: ErrorCodes.DB_CONSTRAINT_VIOLATION, message, stack, retryable: false };
    }
    return { code: ErrorCodes.DB_CONNECTION_ERROR, message, stack, retryable: true };
  }

  // Business logic
  if (message.includes('contact not found')) {
    return { code: ErrorCodes.CONTACT_NOT_FOUND, message, stack, retryable: false };
  }
  if (message.includes('duplicate transaction')) {
    return { code: ErrorCodes.DUPLICATE_TRANSACTION, message, stack, retryable: false };
  }

  // External API errors
  if (message.includes('api') || message.includes('external')) {
    if (message.includes('timeout')) {
      return { code: ErrorCodes.EXTERNAL_API_TIMEOUT, message, stack, retryable: true };
    }
    return { code: ErrorCodes.EXTERNAL_API_ERROR, message, stack, retryable: true };
  }

  // Default
  return { code: ErrorCodes.UNKNOWN_ERROR, message, stack, retryable: true };
}

/**
 * Calculate next retry time with exponential backoff
 * 1st retry: 1 minute
 * 2nd retry: 5 minutes
 * 3rd retry: 30 minutes
 */
export function calculateNextRetry(retryCount: number): Date | null {
  const delays = [60, 300, 1800]; // seconds
  if (retryCount >= delays.length) return null;

  const delaySeconds = delays[retryCount];
  return new Date(Date.now() + delaySeconds * 1000);
}

/**
 * Log a failed webhook event to the Dead Letter Queue
 */
export async function logToDLQ(
  supabase: SupabaseClient,
  source: string,
  eventType: string,
  payload: any,
  error: Error,
  webhookEventId?: string
): Promise<ErrorInfo> {
  const errorInfo = categorizeError(error);
  const nextRetry = errorInfo.retryable ? calculateNextRetry(0) : null;

  console.error(`[DLQ] Logging failed event to DLQ:`, {
    source,
    eventType,
    errorCode: errorInfo.code,
    retryable: errorInfo.retryable,
    nextRetry
  });

  try {
    const { error: insertError } = await supabase
      .from('dlq_events')
      .insert({
        webhook_event_id: webhookEventId,
        source,
        event_type: eventType,
        payload,
        error_message: errorInfo.message.slice(0, 2000), // Limit length
        error_code: errorInfo.code,
        error_stack: errorInfo.stack,
        retry_count: 0,
        next_retry_at: nextRetry?.toISOString()
      });

    if (insertError) {
      console.error('[DLQ] Failed to log to DLQ:', insertError);
    } else {
      console.log(`[DLQ] Event logged successfully. Code: ${errorInfo.code}, Retryable: ${errorInfo.retryable}`);
    }
  } catch (dlqError) {
    console.error('[DLQ] Exception while logging to DLQ:', dlqError);
  }

  return errorInfo;
}

/**
 * Helper to update webhook_events table with error info
 */
export async function updateWebhookEventError(
  supabase: SupabaseClient,
  webhookEventId: string,
  errorInfo: ErrorInfo
): Promise<void> {
  try {
    await supabase
      .from('webhook_events')
      .update({
        status: 'failed',
        error_message: errorInfo.message.slice(0, 2000),
        error_code: errorInfo.code,
        processed_at: new Date().toISOString()
      })
      .eq('id', webhookEventId);
  } catch (updateError) {
    console.error('[DLQ] Failed to update webhook_events:', updateError);
  }
}

/**
 * Wrapper for webhook processing with automatic DLQ logging
 */
export async function processWithDLQ<T>(
  supabase: SupabaseClient,
  source: string,
  eventType: string,
  payload: any,
  webhookEventId: string | undefined,
  processFn: () => Promise<T>
): Promise<{ success: boolean; data?: T; error?: ErrorInfo }> {
  try {
    const data = await processFn();
    return { success: true, data };
  } catch (error) {
    console.error(`[${source}] Processing failed:`, error);

    // Log to DLQ
    const errorInfo = await logToDLQ(
      supabase,
      source,
      eventType,
      payload,
      error as Error,
      webhookEventId
    );

    // Update webhook_events if we have an ID
    if (webhookEventId) {
      await updateWebhookEventError(supabase, webhookEventId, errorInfo);
    }

    return { success: false, error: errorInfo };
  }
}
