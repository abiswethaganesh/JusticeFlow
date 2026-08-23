import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ allowedRole, children }) {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  const userRole = (user.role || '').toUpperCase()
  const reqRole = (allowedRole || '').toUpperCase()

  if (reqRole && userRole !== reqRole) {
    if (userRole === 'CITIZEN') {
      return <Navigate to="/" replace />
    }
    if (userRole === 'OFFICER') {
      return <Navigate to="/officer" replace />
    }
    return <Navigate to="/login" replace />
  }

  return children
}
