import { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [formError, setFormError] = useState('')
  const [deletingId, setDeletingId] = useState('')
  const [formState, setFormState] = useState({
    email: '',
    name: '',
    password: '',
    role: 'user',
  })

  const authHeaders = useMemo(() => {
    const token = localStorage.getItem('access_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    setError('')
    if (!API_BASE) {
      setError('VITE_API_URL is not set.')
      setLoading(false)
      return
    }
    try {
      const response = await fetch(`${API_BASE}/api/users`, {
        headers: {
          ...authHeaders,
        },
      })
      if (!response.ok) {
        throw new Error('Failed to load users')
      }
      const data = await response.json()
      setUsers(data)
    } catch (err) {
      setError('Unable to load users.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const handleDelete = async (userId) => {
    setDeletingId(userId)
    setError('')
    if (!API_BASE) {
      setError('VITE_API_URL is not set.')
      setDeletingId('')
      return
    }
    try {
      const response = await fetch(`${API_BASE}/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          ...authHeaders,
        },
      })
      if (!response.ok) {
        throw new Error('Delete failed')
      }
      setUsers((prev) => prev.filter((user) => user.id !== userId))
    } catch (err) {
      setError('Unable to delete user.')
    } finally {
      setDeletingId('')
    }
  }

  const handleOpenModal = () => {
    setFormState({
      email: '',
      name: '',
      password: '',
      role: 'user',
    })
    setFormError('')
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setFormError('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setCreating(true)
    setFormError('')
    if (!API_BASE) {
      setFormError('VITE_API_URL is not set.')
      setCreating(false)
      return
    }
    try {
      const response = await fetch(`${API_BASE}/api/users/admin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify(formState),
      })
      if (!response.ok) {
        throw new Error('Create failed')
      }
      const created = await response.json()
      setUsers((prev) => [created, ...prev])
      setIsModalOpen(false)
    } catch (err) {
      setFormError('Unable to create user.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <section className="users-section">
      <div className="section-header">
        <h2>Users</h2>
        <button type="button" className="primary" onClick={handleOpenModal}>
          Create user
        </button>
      </div>

      {error ? <div className="banner error">{error}</div> : null}

      <div className="table">
        <div className="row header">
          <span>Email</span>
          <span>Name</span>
          <span>Role</span>
          <span>Actions</span>
        </div>
        {loading ? (
          <div className="row">
            <span>Loading users...</span>
            <span />
            <span />
            <span />
          </div>
        ) : users.length === 0 ? (
          <div className="row">
            <span>No users found.</span>
            <span />
            <span />
            <span />
          </div>
        ) : (
          users.map((user) => (
            <div className="row" key={user.id}>
              <span>{user.email}</span>
              <span>{user.name}</span>
              <span className="role">{user.role}</span>
              <span>
                <button
                  type="button"
                  className="ghost danger"
                  onClick={() => handleDelete(user.id)}
                  disabled={deletingId === user.id}
                >
                  {deletingId === user.id ? 'Deleting...' : 'Delete'}
                </button>
              </span>
            </div>
          ))
        )}
      </div>

      {isModalOpen ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <div className="modal-header">
              <h3>Create user</h3>
              <button type="button" className="ghost" onClick={handleCloseModal}>
                Close
              </button>
            </div>
            {formError ? <div className="banner error">{formError}</div> : null}
            <form onSubmit={handleSubmit}>
              <label>
                Email
                <input
                  type="email"
                  value={formState.email}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, email: event.target.value }))
                  }
                  required
                />
              </label>
              <label>
                Name
                <input
                  type="text"
                  value={formState.name}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, name: event.target.value }))
                  }
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={formState.password}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, password: event.target.value }))
                  }
                  required
                />
              </label>
              <label>
                Role
                <select
                  value={formState.role}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, role: event.target.value }))
                  }
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <div className="modal-actions">
                <button type="button" className="ghost" onClick={handleCloseModal}>
                  Cancel
                </button>
                <button type="submit" className="primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create user'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  )
}
