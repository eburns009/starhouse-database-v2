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

  // Security headers (FAANG standard)
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
            value: 'max-age=63072000; includeSubDomains'
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
