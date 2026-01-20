import { Navigate } from 'react-router-dom'

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

export default function RequireAdmin({ children }) {
  const token = localStorage.getItem(TOKEN_KEY)
  const role = getRoleFromToken(token)

  if (!token || role !== 'admin') {
    return <Navigate to="/login" replace />
  }

  return children
}
