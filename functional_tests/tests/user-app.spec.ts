import { expect, test } from './test-fixtures'

test('user app loads', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Bedrock User App' })).toBeVisible()
})
