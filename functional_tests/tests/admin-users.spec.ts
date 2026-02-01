import { expect, test } from './test-fixtures'
import { adminCredentials, loginAsAdmin } from './admin-helpers'

test.beforeEach(async ({ page }) => {
  await loginAsAdmin(page)
})

test('user list shows admin user', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Users' })).toBeVisible()
  await expect(page.getByText('Loading users...')).toHaveCount(0)
  await expect(page.locator('.row', { hasText: adminCredentials.email })).toBeVisible()
})

test('admin can create and delete a user', async ({ page }) => {
  const timestamp = Date.now()
  const email = `playwright-${timestamp}@example.com`
  const name = `Playwright ${timestamp}`

  await page.getByRole('button', { name: 'Create user' }).click()

  const dialog = page.getByRole('dialog')
  await expect(dialog.getByRole('heading', { name: 'Create user' })).toBeVisible()
  await dialog.getByLabel('Email').fill(email)
  await dialog.getByLabel('Name').fill(name)
  await dialog.getByLabel('Password').fill('password123')
  await dialog.getByLabel('Role').selectOption('user')
  await dialog.getByRole('button', { name: 'Create user' }).click()

  const userRow = page.locator('.row', { hasText: email })
  await expect(userRow).toBeVisible()
  await userRow.getByRole('button', { name: 'Delete' }).click()
  await expect(userRow).toHaveCount(0)
})

test('admin can create an admin user', async ({ page }) => {
  const timestamp = Date.now()
  const email = `playwright-admin-${timestamp}@example.com`
  const name = `Playwright Admin ${timestamp}`

  await page.getByRole('button', { name: 'Create user' }).click()

  const dialog = page.getByRole('dialog')
  await expect(dialog.getByRole('heading', { name: 'Create user' })).toBeVisible()
  await dialog.getByLabel('Email').fill(email)
  await dialog.getByLabel('Name').fill(name)
  await dialog.getByLabel('Password').fill('password123')
  await dialog.getByLabel('Role').selectOption('admin')
  await dialog.getByRole('button', { name: 'Create user' }).click()

  const userRow = page.locator('.row', { hasText: email })
  await expect(userRow).toBeVisible()
  await expect(userRow.locator('.role')).toHaveText('admin')
  await userRow.getByRole('button', { name: 'Delete' }).click()
  await expect(userRow).toHaveCount(0)
})
