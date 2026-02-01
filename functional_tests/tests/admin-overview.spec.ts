import { expect, test } from './test-fixtures'
import { loginAsAdmin } from './admin-helpers'

test('overview page renders welcome cards', async ({ page }) => {
  await loginAsAdmin(page)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible()
  await expect(page.getByText('Select a section from the navigation.')).toBeVisible()
  await expect(page.getByText('Manage user accounts and roles.')).toBeVisible()
})

test('navigation switches between overview and users', async ({ page }) => {
  await loginAsAdmin(page)
  await expect(page.getByRole('button', { name: 'Create user' })).toBeVisible()

  await page.getByRole('link', { name: 'Overview' }).click()
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible()

  await page.getByRole('link', { name: 'Users' }).click()
  await expect(page.getByRole('button', { name: 'Create user' })).toBeVisible()
})
