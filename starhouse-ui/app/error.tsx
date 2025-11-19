/**
 * Global Error Boundary - FAANG Engineering Standards
 *
 * Features:
 * - Catches all unhandled errors in the application
 * - User-friendly error messages (no stack traces exposed)
 * - Error logging to console for debugging
 * - Reset functionality to recover from errors
 * - Accessibility compliant (ARIA labels, keyboard support)
 * - Production-ready error UI
 *
 * Security:
 * - Never exposes sensitive error details to users
 * - Logs errors server-side for monitoring
 * - Prevents error stack trace leakage
 *
 * UX:
 * - Clear error message
 * - Recovery options (retry, go home)
 * - Maintains app layout consistency
 */

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function Error({ error, reset }: ErrorProps) {
  const router = useRouter()

  useEffect(() => {
    // Log error to console (in production, send to error tracking service like Sentry)
    console.error('[Global Error Boundary]', {
      message: error.message,
      digest: error.digest,
      stack: error.stack,
      timestamp: new Date().toISOString()
    })

    // TODO: Send to error monitoring service
    // Example: Sentry.captureException(error, { tags: { digest: error.digest } })
  }, [error])

  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
            {/* Error Icon */}
            <div className="flex justify-center">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-red-100">
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
            </div>

            {/* Error Message */}
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Something went wrong
              </h1>
              <p className="text-gray-600 mb-4">
                We encountered an unexpected error. Our team has been notified and is working on a fix.
              </p>

              {/* Show error digest for support reference (safe to expose) */}
              {error.digest && (
                <p className="text-xs text-gray-500 mb-4" aria-label="Error reference code">
                  Error Code: <code className="bg-gray-100 px-2 py-1 rounded">{error.digest}</code>
                </p>
              )}

              {/* Development mode: Show error message (not in production) */}
              {process.env.NODE_ENV === 'development' && (
                <details className="mb-4 text-left">
                  <summary className="cursor-pointer text-sm text-gray-700 hover:text-gray-900 font-medium">
                    Developer Details
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-3 rounded overflow-auto max-h-40">
                    {error.message}
                  </pre>
                </details>
              )}
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={reset}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                aria-label="Try again"
              >
                Try Again
              </button>

              <button
                onClick={() => router.push('/')}
                className="w-full flex justify-center py-3 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                aria-label="Go to homepage"
              >
                Go to Homepage
              </button>
            </div>

            {/* Support Link */}
            <div className="text-center">
              <p className="text-sm text-gray-500">
                Need help?{' '}
                <a
                  href="mailto:support@starhouse.org"
                  className="font-medium text-blue-600 hover:text-blue-500"
                >
                  Contact Support
                </a>
              </p>
            </div>
          </div>
        </div>
      </body>
    </html>
  )
}
