import { defineConfig } from '@playwright/test'

const userAppUrl = process.env.USER_APP_URL || 'http://localhost:5173'
const adminAppUrl = process.env.ADMIN_APP_URL || 'http://localhost:5174'

export default defineConfig({
  testDir: './tests',
  use: {
    headless: true,
  },
  projects: [
    {
      name: 'user-app',
      testMatch: '**/user-*.spec.ts',
      use: {
        baseURL: userAppUrl,
      },
    },
    {
      name: 'admin-app',
      testMatch: '**/admin-*.spec.ts',
      use: {
        baseURL: adminAppUrl,
      },
    },
  ],
})
