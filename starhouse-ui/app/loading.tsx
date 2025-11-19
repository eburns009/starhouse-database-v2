/**
 * Global Loading UI - FAANG Engineering Standards
 *
 * Features:
 * - Shown during route transitions and Suspense boundaries
 * - Prevents layout shift with skeleton UI
 * - Accessible loading indicators
 * - Smooth animations
 *
 * UX:
 * - Clear indication that content is loading
 * - Prevents blank white screen
 * - Matches app's visual design
 */

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        {/* Spinner */}
        <div className="relative inline-block">
          <div
            className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"
            role="status"
            aria-label="Loading"
          >
            <span className="sr-only">Loading...</span>
          </div>

          {/* Pulse effect behind spinner */}
          <div className="absolute inset-0 rounded-full bg-blue-100 opacity-25 animate-ping"></div>
        </div>

        {/* Loading Text */}
        <p className="mt-4 text-gray-600 font-medium">
          Loading...
        </p>

        {/* Optional: Add subtle hint for slow connections */}
        <p className="mt-2 text-sm text-gray-400">
          This should only take a moment
        </p>
      </div>
    </div>
  )
}
