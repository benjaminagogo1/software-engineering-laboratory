import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { setCsrfToken, setUnauthorizedHandler } from '../api/client'
import { auth } from '../api/endpoints'

/**
 * The session, as the rest of the app sees it.
 *
 * Three states, not two: a page load starts out not knowing whether it is
 * signed in, and rendering the sign-in form during that moment makes a
 * logged-in user flash a login screen on every refresh. 'loading' is the
 * state that prevents it.
 *
 * @typedef {'loading' | 'authenticated' | 'anonymous'} SessionStatus
 *
 * @typedef {object} AuthValue
 * @property {SessionStatus} status
 * @property {{id: number, username: string} | null} user
 * @property {(username: string, password: string) => Promise<void>} login
 * @property {(username: string, password: string) => Promise<void>} register
 * @property {() => Promise<void>} logout
 */

/** @type {React.Context<AuthValue | null>} */
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [status, setStatus] = useState(/** @type {SessionStatus} */ ('loading'))
  const [user, setUser] = useState(
    /** @type {{id: number, username: string} | null} */ (null),
  )

  const forget = useCallback(() => {
    setCsrfToken(null)
    setUser(null)
    setStatus('anonymous')
  }, [])

  const remember = useCallback((session) => {
    // The CSRF token lives here and nowhere else. It is not written to
    // localStorage or a readable cookie on purpose: both are reachable by any
    // script injected into the page, which is exactly what double-submit is
    // designed to survive.
    setCsrfToken(session.csrf_token ?? null)
    setUser({ id: session.id, username: session.username })
    setStatus('authenticated')
  }, [])

  // Any 401 from anywhere in the app ends the session in this one place,
  // rather than in every view that happens to make a request.
  //
  // A rejected sign-in is also a 401, so this fires there too. It is harmless
  // — forgetting a session nobody had is a no-op, and the page is already
  // anonymous — but it is why login() re-reads /me rather than trusting the
  // form: the state it lands in is the server's answer, not this callback's.
  useEffect(() => {
    setUnauthorizedHandler(forget)

    return () => setUnauthorizedHandler(null)
  }, [forget])

  // The boot check. Cookie auth is invisible to the client — the session
  // cookie is httpOnly, so the page cannot look and see whether it is there.
  // Asking the server is the only way to know, and it doubles as the way to
  // recover the CSRF token after a reload.
  useEffect(() => {
    let cancelled = false

    auth
      .me()
      .then((session) => {
        if (!cancelled) {
          remember(session)
        }
      })
      .catch(() => {
        if (!cancelled) {
          forget()
        }
      })

    return () => {
      cancelled = true
    }
  }, [forget, remember])

  const login = useCallback(
    async (username, password) => {
      await auth.login({ username, password })

      // /login answers with tokens, not with the user, so ask who we are
      // rather than assuming the form's username is what the server stored.
      remember(await auth.me())
    },
    [remember],
  )

  const register = useCallback(
    async (username, password) => {
      await auth.register({ username, password })

      // Registering does not sign you in — the server answers 201 and nothing
      // else — so the next step is an ordinary login.
      await login(username, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    try {
      await auth.logout()
    } catch {
      // An already-expired session is not a failure to log out of; the local
      // state is dropped either way.
    }

    forget()
  }, [forget])

  const value = useMemo(
    () => ({ status, user, login, register, logout }),
    [status, user, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/** @returns {AuthValue} */
export function useAuth() {
  const value = useContext(AuthContext)

  if (value === null) {
    throw new Error('useAuth was called outside an AuthProvider')
  }

  return value
}
