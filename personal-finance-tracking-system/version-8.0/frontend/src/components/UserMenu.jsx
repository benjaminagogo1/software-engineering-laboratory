import { useState } from 'react'

import { useAuth } from '../auth/AuthContext'

/**
 * Who is signed in, and the way out.
 *
 * The button disables itself while the request is in flight so a second click
 * cannot queue a second logout — and because logout() clears local state
 * whether or not the call succeeds, there is no failure branch to render.
 */
export function UserMenu() {
  const { user, logout } = useAuth()
  const [signingOut, setSigningOut] = useState(false)

  async function handleSignOut() {
    setSigningOut(true)
    await logout()
  }

  return (
    <>
      <span className="muted">{user?.username}</span>
      <button
        type="button"
        className="button button--ghost button--small"
        onClick={handleSignOut}
        disabled={signingOut}
      >
        {signingOut ? 'Signing out…' : 'Sign out'}
      </button>
    </>
  )
}
