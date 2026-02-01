import { expect, test } from './test-fixtures'
import { adminBackendUrl, adminCredentials, loginAsAdmin } from './admin-helpers'

test('admin login page loads', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Admin Login' })).toBeVisible()
})

test('redirects to login when unauthenticated', async ({ page }) => {
  await page.goto('/users')
  await expect(page).toHaveURL(/\/login$/)
})

test('redirects to login with invalid token', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'invalid-token')
  })
  await page.goto('/users')
  await expect(page).toHaveURL(/\/login$/)
})

test('shows error for invalid credentials', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill(adminCredentials.email)
  await page.getByLabel('Password').fill('wrong-password')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByText('Invalid credentials.')).toBeVisible()
})

test('shows admin access required for non-admin user', async ({ page, request }) => {
  const timestamp = Date.now()
  const email = `user-${timestamp}@example.com`
  const password = 'password123'

  const response = await request.post(`${adminBackendUrl}/api/users`, {
    data: {
      email,
      name: `User ${timestamp}`,
      password,
    },
  })
  expect(response.ok()).toBeTruthy()

  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByText('Admin access required.')).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})

test('logs in with admin credentials', async ({ page }) => {
  await loginAsAdmin(page)
  await expect(page.getByRole('heading', { name: 'Users' })).toBeVisible()
})

test('logout clears token and redirects to login', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Logout' }).click()
  await expect(page).toHaveURL(/\/login$/)
  const token = await page.evaluate(() => localStorage.getItem('access_token'))
  expect(token).toBeNull()
})
