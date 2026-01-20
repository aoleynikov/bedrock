import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_URL
const TOKEN_KEY = 'access_token'

const getRoleFromToken = (token) => {
  if (!token) {
    return null
  }
  const parts = token.split('.')
  if (parts.length < 2) {
    return null
  }
  try {
    const payload = JSON.parse(atob(parts[1]))
    return payload.role || null
  } catch (error) {
    return null
  }
}

export default function AdminLogin() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    if (!API_BASE) {
      setError('VITE_API_URL is not set.')
      return
    }
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          strategy: 'credentials',
        }),
      })

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const data = await response.json()
      const token = data.access_token
      const role = getRoleFromToken(token)

      if (!token || role !== 'admin') {
        setError('Admin access required.')
        return
      }

      localStorage.setItem(TOKEN_KEY, token)
      navigate('/users')
    } catch (err) {
      setError('Invalid credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <h1>Admin Login</h1>
        <p>Sign in with an admin account.</p>
        {error ? <div className="banner error">{error}</div> : null}
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button type="submit" className="primary" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  )
}
