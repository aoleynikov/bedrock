import { expect, Page } from '@playwright/test'

const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com'
const adminPassword = process.env.ADMIN_PASSWORD || 'admin1234'
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

export const adminCredentials = {
  email: adminEmail,
  password: adminPassword,
}

export const adminBackendUrl = backendUrl

export const loginAsAdmin = async (page: Page) => {
  await page.goto('/login')
  await page.getByLabel('Email').fill(adminEmail)
  await page.getByLabel('Password').fill(adminPassword)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/users$/)
}
