/**
 * Next.js Configuration
 * FAANG Standards:
 * - Environment validation at build time
 * - Strict TypeScript and ESLint checks
 * - Security headers
 * - Performance optimization
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Strict mode for better error detection (FAANG standard)
  reactStrictMode: true,

  // TypeScript configuration (FAANG standard: fail fast on errors)
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint configuration (FAANG standard: enforce code quality)
  eslint: {
    ignoreDuringBuilds: false,
  },

  // Existing experimental features
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },

  // Image optimization
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },

  // Security headers (FAANG standard + Enhanced CSP)
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()'
          },
          // Content Security Policy (CSP)
          // Note: This is a strict CSP - adjust as needed for your use case
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // unsafe-inline needed for Next.js
              "style-src 'self' 'unsafe-inline'", // unsafe-inline needed for Tailwind
              "img-src 'self' data: https:",
              "font-src 'self' data:",
              "connect-src 'self' https://*.supabase.co wss://*.supabase.co https://vercel.live", // Supabase + Vercel
              "frame-ancestors 'self'",
              "base-uri 'self'",
              "form-action 'self'",
              "upgrade-insecure-requests",
            ].join('; ')
          },
        ],
      },
    ]
  },

  // Performance optimization (FAANG standard: remove console logs in production)
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn']
    } : false,
  },
}

// FAANG Standard: Validate required environment variables at build time
const requiredEnvVars = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
]

const missingEnvVars = requiredEnvVars.filter(
  (envVar) => !process.env[envVar]
)

if (missingEnvVars.length > 0 && process.env.NODE_ENV !== 'test') {
  console.warn('⚠️  Warning: Missing environment variables:')
  missingEnvVars.forEach((envVar) => {
    console.warn(`   - ${envVar}`)
  })
  console.warn('\nSet these in .env.local for local development')
  console.warn('or in Vercel dashboard for production.')

  // Only fail in CI/production (FAANG standard: fail fast in production)
  if (process.env.CI && (process.env.VERCEL || process.env.NODE_ENV === 'production')) {
    throw new Error('Missing required environment variables in production build')
  }
}

module.exports = nextConfig
