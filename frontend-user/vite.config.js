import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import istanbul from 'vite-plugin-istanbul'

const coverageEnabled = process.env.PW_COVERAGE === 'true'

export default defineConfig({
  server: {
    allowedHosts: ['bedrock_frontend_user', 'localhost', '127.0.0.1'],
  },
  plugins: [
    react(),
    coverageEnabled
      ? istanbul({
        include: 'src/**/*',
        exclude: ['node_modules', 'tests', 'coverage', 'coverage-report'],
        extension: ['.js', '.jsx', '.ts', '.tsx'],
        requireEnv: true,
        env: 'PW_COVERAGE',
      })
      : null,
  ].filter(Boolean),
})
