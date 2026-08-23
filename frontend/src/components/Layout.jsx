import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const { isOfficer } = useAuth()
  const portalLabel = isOfficer ? 'Officer Portal' : 'Citizen Portal'

  return (
    <div className="app-shell">
      <Header onMenuToggle={() => setMenuOpen((v) => !v)} portalLabel={portalLabel} />
      <div className="app-body">
        <Sidebar open={menuOpen} />
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
