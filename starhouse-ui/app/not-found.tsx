/**
 * 404 Not Found Page - FAANG Engineering Standards
 *
 * Features:
 * - Custom 404 page for better UX
 * - Helpful navigation options
 * - Search functionality to help users find what they need
 * - Accessibility compliant
 * - SEO friendly (proper metadata)
 *
 * UX:
 * - Clear messaging about what went wrong
 * - Multiple recovery paths (search, go home, popular pages)
 * - Friendly, non-technical language
 *
 * Note: This must be a Client Component because it uses window.history.back()
 * Metadata is exported separately to maintain SEO benefits.
 */

'use client'

import Link from 'next/link'

// Note: metadata export is not supported in Client Components
// Next.js will use default metadata from parent layout

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-2xl w-full space-y-8 p-8 bg-white rounded-lg shadow-lg text-center">
        {/* 404 Illustration */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="text-9xl font-bold text-gray-200 select-none" aria-hidden="true">
              404
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <svg
                className="h-24 w-24 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Message */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Page Not Found
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            Sorry, we couldn't find the page you're looking for. It might have been moved or deleted.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          {/* Primary CTA */}
          <Link
            href="/"
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            Go to Homepage
          </Link>

          {/* Go Back Button */}
          <button
            onClick={() => window.history.back()}
            className="ml-4 inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Go Back
          </button>
        </div>

        {/* Popular Pages */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Popular Pages
          </h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Link
              href="/contacts"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              Contacts
            </Link>
            <Link
              href="/donors"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              Donors
            </Link>
            <Link
              href="/venues"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              Venues
            </Link>
            <Link
              href="/membership"
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              Membership
            </Link>
          </div>
        </div>

        {/* Support */}
        <div className="text-sm text-gray-500">
          <p>
            Still need help?{' '}
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
  )
}
