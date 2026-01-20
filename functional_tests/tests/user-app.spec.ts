import { expect, test } from '@playwright/test'

test('user app loads', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Bedrock User App' })).toBeVisible()
})
