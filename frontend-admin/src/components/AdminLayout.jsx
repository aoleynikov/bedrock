import { NavLink, Outlet, useNavigate } from 'react-router-dom'

export default function AdminLayout() {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <main className="admin">
      <header>
        <div>
          <h1>Admin Dashboard</h1>
          <p>User management for Bedrock.</p>
        </div>
        <nav className="nav">
          <NavLink to="/" end>
            Overview
          </NavLink>
          <NavLink to="/users">Users</NavLink>
          <button type="button" className="ghost" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </header>
      <Outlet />
    </main>
  )
}
