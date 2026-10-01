import { useEffect, useRef, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/AuthContext'
import { ApiError } from '../../api/errors'

/** Shortest password the form will submit. The server has no rule of its own yet. */
const MIN_PASSWORD_LENGTH = 8

/**
 * Sign in, or create an account.
 *
 * The two are one page with a tab rather than two routes, because the only
 * thing that differs is which endpoint and the confirmation field — and a
 * user who mistypes a username on the sign-in form is one click from the
 * other, not one page load.
 */
export function LoginPage() {
  const { status, login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [mode, setMode] = useState(/** @type {'signin' | 'register'} */ ('signin'))
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState(/** @type {Record<string, string>} */ ({}))
  const [formError, setFormError] = useState(/** @type {string | null} */ (null))
  const [busy, setBusy] = useState(false)

  const usernameRef = useRef(/** @type {HTMLInputElement | null} */ (null))

  // Put the cursor where the user has to start, including when they switch
  // tabs mid-form.
  useEffect(() => {
    usernameRef.current?.focus()
  }, [mode])

  // Trying to reach a protected page while already signed in should go there,
  // not show a login form.
  if (status === 'authenticated') {
    const from = /** @type {{pathname?: string}} */ (location.state?.from ?? {})
    return <Navigate to={from.pathname ?? '/'} replace />
  }

  /**
   * Everything the server would reject, caught before the round trip — the
   * server still enforces all of it, this is only so the user does not have to
   * wait for a request to be told they left a field empty.
   *
   * @returns {Record<string, string>}
   */
  function validate() {
    /** @type {Record<string, string>} */
    const found = {}

    if (username.trim() === '') {
      found.username = 'Enter a username.'
    }

    if (password === '') {
      found.password = 'Enter a password.'
    } else if (mode === 'register' && password.length < MIN_PASSWORD_LENGTH) {
      found.password = `Use at least ${MIN_PASSWORD_LENGTH} characters.`
    }

    // Confirmation is inherently a client-side concern — the API has no such
    // field and never sees it. It exists to catch a typo before an account is
    // created with a password nobody knows.
    if (mode === 'register' && confirmation !== password) {
      found.confirmation = 'The two passwords do not match.'
    }

    return found
  }

  /** @param {React.FormEvent<HTMLFormElement>} event */
  async function handleSubmit(event) {
    event.preventDefault()

    if (busy) {
      return
    }

    const found = validate()

    if (Object.keys(found).length > 0) {
      setErrors(found)
      setFormError(null)
      return
    }

    setErrors({})
    setFormError(null)
    setBusy(true)

    try {
      if (mode === 'register') {
        await register(username.trim(), password)
      } else {
        await login(username.trim(), password)
      }

      const from = /** @type {{pathname?: string}} */ (location.state?.from ?? {})
      navigate(from.pathname ?? '/', { replace: true })
    } catch (error) {
      if (error instanceof ApiError && Object.keys(error.fieldErrors).length > 0) {
        setErrors(error.fieldErrors)
      }

      // A 401 here means the credentials, not the session — saying "session
      // expired" would be a lie. The server's own sentence is the right one
      // ("Invalid username or password").
      setFormError(
        error instanceof Error ? error.message : 'Could not sign in.',
      )
      setBusy(false)
    }
  }

  /** @param {'signin' | 'register'} next */
  function switchTo(next) {
    if (next === mode) {
      return
    }

    setMode(next)
    setPassword('')
    setConfirmation('')
    setErrors({})
    setFormError(null)
  }

  const title = mode === 'signin' ? 'Sign in' : 'Create your account'

  return (
    <div className="auth">
      <div className="auth__card card">
        <h1 className="card__head">{title}</h1>

        <div className="auth__tabs" role="tablist" aria-label="Sign in or register">
          <button
            type="button"
            role="tab"
            className="auth__tab"
            aria-selected={mode === 'signin'}
            onClick={() => switchTo('signin')}
          >
            Sign in
          </button>

          <button
            type="button"
            role="tab"
            className="auth__tab"
            aria-selected={mode === 'register'}
            onClick={() => switchTo('register')}
          >
            Create account
          </button>
        </div>

        {formError !== null && (
          <div className="alert alert--error" role="alert">
            {formError}
          </div>
        )}

        <form className="form" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label className="field__label" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              name="username"
              ref={usernameRef}
              value={username}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck="false"
              aria-invalid={errors.username !== undefined}
              aria-describedby={errors.username !== undefined ? 'username-error' : undefined}
              onChange={(event) => setUsername(event.target.value)}
            />
            {errors.username !== undefined && (
              <span className="field__error" id="username-error">
                {errors.username}
              </span>
            )}
          </div>

          <div className="field">
            <label className="field__label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={password}
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              aria-invalid={errors.password !== undefined}
              aria-describedby={errors.password !== undefined ? 'password-error' : undefined}
              onChange={(event) => setPassword(event.target.value)}
            />
            {errors.password !== undefined && (
              <span className="field__error" id="password-error">
                {errors.password}
              </span>
            )}
          </div>

          {mode === 'register' && (
            <div className="field">
              <label className="field__label" htmlFor="confirmation">
                Confirm password
              </label>
              <input
                id="confirmation"
                name="confirmation"
                type="password"
                value={confirmation}
                autoComplete="new-password"
                aria-invalid={errors.confirmation !== undefined}
                aria-describedby={
                  errors.confirmation !== undefined ? 'confirmation-error' : undefined
                }
                onChange={(event) => setConfirmation(event.target.value)}
              />
              {errors.confirmation !== undefined && (
                <span className="field__error" id="confirmation-error">
                  {errors.confirmation}
                </span>
              )}
            </div>
          )}

          <div className="form__actions">
            <button type="submit" className="button" disabled={busy}>
              {busy
                ? mode === 'signin' ? 'Signing in…' : 'Creating account…'
                : mode === 'signin' ? 'Sign in' : 'Create account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
