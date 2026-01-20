const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
const adminAppUrl = process.env.ADMIN_APP_URL || 'http://localhost:5174'
const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com'
const adminPassword = process.env.ADMIN_PASSWORD || 'admin1234'
const timeoutMs = Number(process.env.WAIT_TIMEOUT_MS || 60000)
const intervalMs = 1000

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const fetchWithTimeout = async (url, options = {}) => {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), 5000)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    return response
  } finally {
    clearTimeout(id)
  }
}

const waitForHealth = async () => {
  try {
    const response = await fetchWithTimeout(`${backendUrl}/api/health`)
    return response.ok
  } catch {
    return false
  }
}

const waitForAdminApp = async () => {
  try {
    const response = await fetchWithTimeout(`${adminAppUrl}/login`)
    return response.ok
  } catch {
    return false
  }
}

const waitForAdminLogin = async () => {
  try {
    const response = await fetchWithTimeout(`${backendUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: adminEmail,
        password: adminPassword,
        strategy: 'credentials',
      }),
    })
    if (!response.ok) {
      return false
    }
    const data = await response.json()
    return Boolean(data.access_token)
  } catch {
    return false
  }
}

const waitForStack = async () => {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const [healthOk, adminAppOk] = await Promise.all([waitForHealth(), waitForAdminApp()])
    if (healthOk && adminAppOk) {
      const loginOk = await waitForAdminLogin()
      if (loginOk) {
        return
      }
    }
    await sleep(intervalMs)
  }
  throw new Error('Timed out waiting for stack readiness')
}

await waitForStack()
