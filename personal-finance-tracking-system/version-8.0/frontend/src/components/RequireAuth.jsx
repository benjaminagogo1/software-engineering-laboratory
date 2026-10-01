import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Loading } from './Loading'

/**
 * Keeps a route for signed-in users.
 *
 * The redirect carries where the user was heading, so signing in lands them
 * on the page they asked for rather than dumping them on the dashboard.
 *
 * This is a convenience, not a security boundary: the API refuses every
 * request it receives without a valid session. A client-side guard only
 * decides what is worth rendering.
 *
 * @param {{children: React.ReactNode}} props
 */
export function RequireAuth({ children }) {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    return <Loading label="Checking your session…" />
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
