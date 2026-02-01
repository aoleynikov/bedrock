import { test as base, expect, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const coverageEnabled = process.env.PW_COVERAGE === 'true'
const coverageDir = fileURLToPath(new URL('../coverage', import.meta.url))

const test = base

test.afterEach(async ({ page }, testInfo) => {
  if (!coverageEnabled) {
    return
  }
  const coverage = await page.evaluate(
    () => (window as Window & { __coverage__?: unknown }).__coverage__,
  )
  if (!coverage) {
    return
  }
  fs.mkdirSync(coverageDir, { recursive: true })
  const safeTitle = testInfo.title.replace(/[^\w-]+/g, '_').slice(0, 120)
  const filename = `${testInfo.project.name}-${safeTitle}-${Date.now()}.json`
  const filePath = path.join(coverageDir, filename)
  fs.writeFileSync(filePath, JSON.stringify(coverage))
})

export { test, expect, Page }
