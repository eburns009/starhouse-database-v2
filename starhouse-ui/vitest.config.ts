/**
 * Vitest Configuration
 * FAANG Standards:
 * - Fast test execution with proper mocking
 * - Accurate coverage reporting
 * - Environment setup for React components
 * - Path aliases matching Next.js config
 */

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    // Environment
    environment: 'jsdom',

    // Setup files
    setupFiles: ['./tests/setup.ts'],

    // Coverage configuration (FAANG standard: >90% coverage)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/**',
        'dist/',
        '.next/',
      ],
      lines: 90,
      functions: 90,
      branches: 85,
      statements: 90,
    },

    // Global test configuration
    globals: true,

    // Test timeout (FAANG standard: fast tests)
    testTimeout: 10000,

    // Exclude patterns
    exclude: [
      'node_modules',
      'dist',
      '.next',
      'e2e/**',
    ],
  },

  // Path resolution (match Next.js config)
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
})
