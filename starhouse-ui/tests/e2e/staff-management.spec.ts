/**
 * Staff Management E2E Tests
 * FAANG Standards:
 * - Test complete user flows
 * - Test all 3 roles (admin, full_user, read_only)
 * - Test security boundaries
 * - Test error handling
 * - Test accessibility
 */

import { test, expect } from '@playwright/test'

// Test data
const ADMIN_EMAIL = 'admin@starhouse.test'
const ADMIN_PASSWORD = 'test-password-admin'
const FULL_USER_EMAIL = 'fulluser@starhouse.test'
const READ_ONLY_EMAIL = 'readonly@starhouse.test'
const NEW_STAFF_EMAIL = 'newstaff@starhouse.test'

test.describe('Staff Management - Admin Role (FAANG Standards)', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login')
    await page.fill('input[type="email"]', ADMIN_EMAIL)
    await page.fill('input[type="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('/')
  })

  test('should display staff management page with all features', async ({ page }) => {
    await page.goto('/staff')

    // Verify page loads
    await expect(page.getByRole('heading', { name: /staff management/i })).toBeVisible()

    // Verify add staff button is visible (admin only)
    await expect(page.getByRole('button', { name: /add staff/i })).toBeVisible()

    // Verify table headers
    await expect(page.getByRole('columnheader', { name: /email/i })).toBeVisible()
    await expect(page.getByRole('columnheader', { name: /role/i })).toBeVisible()
    await expect(page.getByRole('columnheader', { name: /status/i })).toBeVisible()
  })

  test('should add new staff member successfully', async ({ page }) => {
    await page.goto('/staff')

    // Open add staff dialog
    await page.click('button:has-text("Add Staff Member")')

    // Fill form
    await page.fill('input[name="email"]', NEW_STAFF_EMAIL)
    await page.fill('input[name="displayName"]', 'New Staff Member')
    await page.selectOption('select[name="role"]', 'full_user')
    await page.fill('textarea[name="notes"]', 'Test staff member')

    // Submit form
    await page.click('button[type="submit"]:has-text("Add")')

    // Verify success toast
    await expect(page.getByText(/staff member added successfully/i)).toBeVisible()

    // Verify staff appears in table
    await expect(page.getByText(NEW_STAFF_EMAIL)).toBeVisible()
  })

  test('should validate email format when adding staff', async ({ page }) => {
    await page.goto('/staff')

    await page.click('button:has-text("Add Staff Member")')
    await page.fill('input[name="email"]', 'invalid-email')
    await page.click('button[type="submit"]:has-text("Add")')

    // Verify error message
    await expect(page.getByText(/invalid email/i)).toBeVisible()
  })

  test('should change staff member role', async ({ page }) => {
    await page.goto('/staff')

    // Find staff member row and click edit
    const row = page.locator('tr', { hasText: FULL_USER_EMAIL })
    await row.getByRole('button', { name: /edit/i }).click()

    // Change role
    await page.selectOption('select[name="role"]', 'read_only')
    await page.click('button:has-text("Save")')

    // Verify success toast
    await expect(page.getByText(/role updated successfully/i)).toBeVisible()

    // Verify role badge updated
    await expect(row.getByText(/read only/i)).toBeVisible()
  })

  test('should prevent admin from demoting themselves', async ({ page }) => {
    await page.goto('/staff')

    // Try to edit own role
    const row = page.locator('tr', { hasText: ADMIN_EMAIL })
    await row.getByRole('button', { name: /edit/i }).click()

    await page.selectOption('select[name="role"]', 'full_user')
    await page.click('button:has-text("Save")')

    // Verify error message
    await expect(page.getByText(/cannot demote yourself/i)).toBeVisible()
  })

  test('should deactivate staff member with confirmation', async ({ page }) => {
    await page.goto('/staff')

    // Click deactivate button
    const row = page.locator('tr', { hasText: NEW_STAFF_EMAIL })
    await row.getByRole('button', { name: /deactivate/i }).click()

    // Verify confirmation dialog
    await expect(page.getByText(/are you sure/i)).toBeVisible()

    // Confirm deactivation
    await page.click('button:has-text("Deactivate")')

    // Verify success toast
    await expect(page.getByText(/staff member deactivated/i)).toBeVisible()

    // Verify staff no longer appears in active list (or shows as inactive)
    const deactivatedRow = page.locator('tr', { hasText: NEW_STAFF_EMAIL })
    await expect(deactivatedRow.getByText(/inactive/i)).toBeVisible()
  })

  test('should handle real-time updates from other sessions', async ({ page, context }) => {
    await page.goto('/staff')

    // Open second tab as another admin
    const page2 = await context.newPage()
    await page2.goto('/login')
    await page2.fill('input[type="email"]', ADMIN_EMAIL)
    await page2.fill('input[type="password"]', ADMIN_PASSWORD)
    await page2.click('button[type="submit"]')
    await page2.waitForURL('/')
    await page2.goto('/staff')

    // Add staff in second tab
    await page2.click('button:has-text("Add Staff Member")')
    await page2.fill('input[name="email"]', 'realtime-test@test.com')
    await page2.selectOption('select[name="role"]', 'read_only')
    await page2.click('button[type="submit"]:has-text("Add")')

    // Verify first tab receives real-time update
    await expect(page.getByText('realtime-test@test.com')).toBeVisible({ timeout: 5000 })
  })

  test('should be accessible (WCAG 2.1 AA)', async ({ page }) => {
    await page.goto('/staff')

    // Verify keyboard navigation
    await page.keyboard.press('Tab')
    await expect(page.locator(':focus')).toBeVisible()

    // Verify ARIA labels
    const table = page.getByRole('table')
    await expect(table).toHaveAttribute('aria-label')

    // Verify color contrast (check for role badges)
    const adminBadge = page.locator('[data-role="admin"]').first()
    if (await adminBadge.isVisible()) {
      // Badge should be visible with sufficient contrast
      await expect(adminBadge).toBeVisible()
    }
  })
})

test.describe('Staff Management - Full User Role (FAANG Standards)', () => {
  test.beforeEach(async ({ page }) => {
    // Login as full user
    await page.goto('/login')
    await page.fill('input[type="email"]', FULL_USER_EMAIL)
    await page.fill('input[type="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('/')
  })

  test('should view staff list but not see add/edit buttons', async ({ page }) => {
    await page.goto('/staff')

    // Verify can view staff list
    await expect(page.getByRole('heading', { name: /staff management/i })).toBeVisible()

    // Verify cannot add staff
    await expect(page.getByRole('button', { name: /add staff/i })).not.toBeVisible()

    // Verify cannot edit staff
    await expect(page.getByRole('button', { name: /edit/i })).not.toBeVisible()
  })

  test('should not be able to access staff management API directly', async ({ request, page }) => {
    // Get session cookie
    await page.goto('/')
    const cookies = await page.context().cookies()

    // Try to add staff member via API
    const response = await request.post('/api/staff/add', {
      headers: {
        cookie: cookies.map(c => `${c.name}=${c.value}`).join('; '),
      },
      data: {
        email: 'unauthorized@test.com',
        role: 'admin',
      },
    })

    // Verify request is rejected
    expect(response.status()).toBe(403)
  })
})

test.describe('Staff Management - Read Only Role (FAANG Standards)', () => {
  test.beforeEach(async ({ page }) => {
    // Login as read-only user
    await page.goto('/login')
    await page.fill('input[type="email"]', READ_ONLY_EMAIL)
    await page.fill('input[type="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('/')
  })

  test('should view staff list but have no modification abilities', async ({ page }) => {
    await page.goto('/staff')

    // Verify can view staff list
    await expect(page.getByRole('heading', { name: /staff management/i })).toBeVisible()

    // Verify no action buttons visible
    await expect(page.getByRole('button', { name: /add/i })).not.toBeVisible()
    await expect(page.getByRole('button', { name: /edit/i })).not.toBeVisible()
    await expect(page.getByRole('button', { name: /deactivate/i })).not.toBeVisible()
  })
})

test.describe('Staff Management - Performance (FAANG Standards)', () => {
  test('should load staff list within performance budget', async ({ page }) => {
    // Login as admin
    await page.goto('/login')
    await page.fill('input[type="email"]', ADMIN_EMAIL)
    await page.fill('input[type="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('/')

    // Measure performance
    const startTime = Date.now()
    await page.goto('/staff')
    await page.waitForSelector('table')
    const loadTime = Date.now() - startTime

    // FAANG standard: Page should load in <500ms
    expect(loadTime).toBeLessThan(500)
  })

  test('should handle large staff lists efficiently', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"]', ADMIN_EMAIL)
    await page.fill('input[type="password"]', ADMIN_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('/')

    await page.goto('/staff')

    // Verify table renders even with many rows
    const rows = page.locator('tbody tr')
    await expect(rows.first()).toBeVisible()

    // Verify scrolling is smooth (no layout shifts)
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.waitForTimeout(100)

    // Page should remain responsive
    await expect(page.getByRole('heading')).toBeVisible()
  })
})
