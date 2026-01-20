import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './components/AdminLayout.jsx'
import RequireAdmin from './components/RequireAdmin.jsx'
import AdminHome from './pages/AdminHome.jsx'
import AdminLogin from './pages/AdminLogin.jsx'
import UserManagement from './pages/UserManagement.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AdminLogin />} />
      <Route
        element={
          <RequireAdmin>
            <AdminLayout />
          </RequireAdmin>
        }
      >
        <Route index element={<AdminHome />} />
        <Route path="users" element={<UserManagement />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
