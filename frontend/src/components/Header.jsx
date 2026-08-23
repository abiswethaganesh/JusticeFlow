import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Header({ onMenuToggle, portalLabel }) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="app-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button className="menu-toggle" onClick={onMenuToggle} aria-label="Toggle navigation menu">
          ☰
        </button>
        <div className="app-brand">
          <span className="app-brand-mark">JF</span>
          <span>
            JusticeFlow
            <span className="app-brand-subtitle">AI-Assisted Criminal Justice Workflow Platform</span>
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {isAuthenticated && user && (
          <div style={{ textAlign: 'right', fontSize: '0.85rem' }}>
            <div style={{ fontWeight: 600 }}>{user.full_name}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted, #64748b)' }}>
              {user.role === 'OFFICER' ? user.station_branch : user.phone}
            </div>
          </div>
        )}

        <span className="app-portal-tag">{portalLabel}</span>

        {isAuthenticated && (
          <button
            onClick={handleLogout}
            className="btn btn-ghost"
            style={{
              padding: '0.35rem 0.65rem',
              fontSize: '0.82rem',
              border: '1px solid var(--color-border)',
            }}
          >
            Logout
          </button>
        )}
      </div>
    </header>
  )
}
