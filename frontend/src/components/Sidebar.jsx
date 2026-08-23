import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const CITIZEN_LINKS = [
  { to: '/', label: 'Dashboard', icon: '⌂', end: true },
  { to: '/intake', label: 'Conversational Intake', icon: '💬' },
]

const OFFICER_LINKS = [
  { to: '/officer', label: 'Officer Dashboard', icon: '▤' },
]

export default function Sidebar({ open }) {
  const { isOfficer } = useAuth()

  return (
    <aside className={`app-sidebar ${open ? 'open' : ''}`}>
      {isOfficer ? (
        <>
          <div className="sidebar-section-label">Officer Portal</div>
          {OFFICER_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-link-icon">{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </>
      ) : (
        <>
          <div className="sidebar-section-label">Citizen Portal</div>
          {CITIZEN_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-link-icon">{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </>
      )}
    </aside>
  )
}
