#!/usr/bin/env node
/**
 * Build Verification Script
 * FAANG Standards:
 * - Pre-build validation
 * - Environment checks
 * - Dependency audits
 * - Configuration validation
 */

const fs = require('fs')
const path = require('path')

console.log('🔍 FAANG Build Verification\n')

let hasErrors = false
let hasWarnings = false

// ============================================================================
// 1. Environment Variables Check
// ============================================================================
console.log('1️⃣  Checking environment variables...')

const requiredEnvVars = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
]

const missingEnvVars = requiredEnvVars.filter(
  (envVar) => !process.env[envVar]
)

if (missingEnvVars.length > 0) {
  console.error('   ❌ Missing required environment variables:')
  missingEnvVars.forEach((envVar) => {
    console.error(`      - ${envVar}`)
  })
  hasErrors = true
} else {
  console.log('   ✅ All required environment variables present')
}

// Validate URL format
if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
  try {
    new URL(process.env.NEXT_PUBLIC_SUPABASE_URL)
    console.log('   ✅ SUPABASE_URL format valid')
  } catch {
    console.error('   ❌ SUPABASE_URL is not a valid URL')
    hasErrors = true
  }
}

console.log()

// ============================================================================
// 2. File Structure Check
// ============================================================================
console.log('2️⃣  Checking file structure...')

const requiredFiles = [
  'package.json',
  'next.config.js',
  'tsconfig.json',
  '.eslintrc.json',
  'app/layout.tsx',
]

const missingFiles = requiredFiles.filter(
  (file) => !fs.existsSync(path.join(process.cwd(), file))
)

if (missingFiles.length > 0) {
  console.error('   ❌ Missing required files:')
  missingFiles.forEach((file) => {
    console.error(`      - ${file}`)
  })
  hasErrors = true
} else {
  console.log('   ✅ All required files present')
}

console.log()

// ============================================================================
// 3. Package.json Validation
// ============================================================================
console.log('3️⃣  Validating package.json...')

try {
  const packageJson = require('../package.json')

  // Check required scripts
  const requiredScripts = ['build', 'dev', 'start']
  const missingScripts = requiredScripts.filter(
    (script) => !packageJson.scripts || !packageJson.scripts[script]
  )

  if (missingScripts.length > 0) {
    console.error('   ❌ Missing required scripts:')
    missingScripts.forEach((script) => {
      console.error(`      - ${script}`)
    })
    hasErrors = true
  } else {
    console.log('   ✅ All required scripts present')
  }

  // Check critical dependencies
  const criticalDeps = [
    'next',
    'react',
    'react-dom',
    '@supabase/supabase-js',
    '@supabase/ssr',
  ]

  const missingDeps = criticalDeps.filter(
    (dep) => !packageJson.dependencies || !packageJson.dependencies[dep]
  )

  if (missingDeps.length > 0) {
    console.error('   ❌ Missing critical dependencies:')
    missingDeps.forEach((dep) => {
      console.error(`      - ${dep}`)
    })
    hasErrors = true
  } else {
    console.log('   ✅ All critical dependencies present')
  }
} catch (error) {
  console.error(`   ❌ Failed to parse package.json: ${error.message}`)
  hasErrors = true
}

console.log()

// ============================================================================
// 4. TypeScript Configuration Check
// ============================================================================
console.log('4️⃣  Checking TypeScript configuration...')

try {
  const tsconfig = require('../tsconfig.json')

  if (!tsconfig.compilerOptions) {
    console.error('   ❌ Missing compilerOptions in tsconfig.json')
    hasErrors = true
  } else {
    console.log('   ✅ TypeScript configuration valid')

    // Check strict mode (FAANG standard)
    if (!tsconfig.compilerOptions.strict) {
      console.warn('   ⚠️  TypeScript strict mode not enabled (recommended)')
      hasWarnings = true
    } else {
      console.log('   ✅ TypeScript strict mode enabled')
    }
  }
} catch (error) {
  console.error(`   ❌ Failed to parse tsconfig.json: ${error.message}`)
  hasErrors = true
}

console.log()

// ============================================================================
// 5. Next.js Configuration Check
// ============================================================================
console.log('5️⃣  Checking Next.js configuration...')

try {
  const nextConfig = require('../next.config.js')

  if (!nextConfig) {
    console.error('   ❌ next.config.js exports nothing')
    hasErrors = true
  } else {
    console.log('   ✅ Next.js configuration valid')

    // Check for security headers (FAANG standard)
    if (typeof nextConfig.headers === 'function') {
      console.log('   ✅ Security headers configured')
    } else {
      console.warn('   ⚠️  Security headers not configured (recommended)')
      hasWarnings = true
    }

    // Check for strict mode (FAANG standard)
    if (nextConfig.reactStrictMode) {
      console.log('   ✅ React strict mode enabled')
    } else {
      console.warn('   ⚠️  React strict mode not enabled (recommended)')
      hasWarnings = true
    }
  }
} catch (error) {
  console.error(`   ❌ Failed to parse next.config.js: ${error.message}`)
  hasErrors = true
}

console.log()

// ============================================================================
// Summary
// ============================================================================
console.log('━'.repeat(60))
console.log('📊 VERIFICATION SUMMARY')
console.log('━'.repeat(60))

if (hasErrors) {
  console.error('\n❌ Build verification FAILED')
  console.error('   Fix the errors above before deploying\n')
  process.exit(1)
} else if (hasWarnings) {
  console.warn('\n⚠️  Build verification passed with warnings')
  console.warn('   Consider addressing warnings for production deployment\n')
  process.exit(0)
} else {
  console.log('\n✅ Build verification PASSED')
  console.log('   Ready for deployment!\n')
  process.exit(0)
}
