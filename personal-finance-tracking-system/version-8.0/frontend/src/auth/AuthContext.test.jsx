import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'
import { RequireAuth } from '../components/RequireAuth'
import { stubServer } from '../test/stubServer'

/**
 * The provider on its own, with a button per action, so the session state can
 * be read without a page in the way.
 */
function Harness() {
  const { status, user, login, register, logout } = useAuth()

  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="user">{user?.username ?? 'none'}</span>
      <button
        type="button"
        onClick={() => login('ben', 'hunter2000').catch(() => {})}
      >
        Log in
      </button>
      <button
        type="button"
        onClick={() => register('ben', 'hunter2000').catch(() => {})}
      >
        Register
      </button>
      <button type="button" onClick={() => logout()}>
        Log out
      </button>
    </div>
  )
}

/** @param {string} [initialPath] */
function renderHarness(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Harness />
      </AuthProvider>
    </MemoryRouter>,
  )
}

const SESSION = { id: 1, username: 'ben', csrf_token: 'csrf-from-me' }
const SIGNED_OUT = { status: 401, body: { detail: 'Not authenticated' } }

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('booting', () => {
  it('asks the server who we are, since the cookie is unreadable to script', async () => {
    const { calls } = stubServer({ 'GET /me': { body: SESSION } })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    expect(calls[0]).toMatchObject({ method: 'GET', path: '/me' })
    expect(screen.getByTestId('user')).toHaveTextContent('ben')
  })

  it('starts out loading, so a signed-in reload does not flash a login form', async () => {
    stubServer({ 'GET /me': { body: SESSION } })

    renderHarness()

    expect(screen.getByTestId('status')).toHaveTextContent('loading')

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })
  })

  it('settles on anonymous when there is no session', async () => {
    stubServer({ 'GET /me': SIGNED_OUT })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })
  })

  it('treats an unreachable server as signed out rather than spinning forever', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })
  })
})

describe('logging in', () => {
  it('signs in and confirms who we are with /me', async () => {
    let signedIn = false

    const { calls } = stubServer({
      'GET /me': () => (signedIn ? { body: SESSION } : SIGNED_OUT),
      'POST /login': () => {
        signedIn = true
        return {
          body: {
            access_token: 'a.b.c',
            token_type: 'bearer',
            csrf_token: 'csrf-from-login',
          },
        }
      },
    })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })

    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    expect(screen.getByTestId('user')).toHaveTextContent('ben')
    expect(calls.map((call) => call.path)).toEqual(['/me', '/login', '/me'])
  })

  it('carries the CSRF token from login into the next write', async () => {
    let signedIn = false

    stubServer({
      'GET /me': () => (signedIn ? { body: SESSION } : SIGNED_OUT),
      'POST /login': () => {
        signedIn = true
        return { body: { access_token: 'a.b.c', token_type: 'bearer', csrf_token: 'csrf-1' } }
      },
      'POST /expenses': { status: 201, body: { result: 'ok' } },
    })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })

    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    // /me is the authoritative source: it answers with the token minted into
    // this session, which is what every later write has to echo.
    const { api } = await import('../api/client')
    await api.post('/expenses', { name: 'Lunch' })

    expect(vi.mocked(fetch).mock.calls.at(-1)[1].headers['X-CSRF-Token']).toBe(
      'csrf-from-me',
    )
  })

  it('leaves the session alone when the password is rejected', async () => {
    stubServer({
      'GET /me': SIGNED_OUT,
      'POST /login': { status: 401, body: { detail: 'Invalid username or password' } },
    })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })

    // The button's handler swallows the rejection; what matters is that a
    // failed login does not leave the app claiming to be signed in.
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))

    await waitFor(() => {
      expect(vi.mocked(fetch).mock.calls.some((call) => call[0] === '/login')).toBe(true)
    })

    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })
})

describe('registering', () => {
  it('creates the account and then signs in', async () => {
    let registered = false

    const { calls } = stubServer({
      'GET /me': () => (registered ? { body: SESSION } : SIGNED_OUT),
      'POST /register': () => {
        registered = true
        return { status: 201, body: { id: 1, username: 'ben' } }
      },
      'POST /login': {
        body: { access_token: 'a.b.c', token_type: 'bearer', csrf_token: 'csrf-1' },
      },
    })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })

    await userEvent.click(screen.getByRole('button', { name: 'Register' }))

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    // Registering does not sign you in — the API answers 201 and nothing more.
    expect(calls.map((call) => call.path)).toEqual([
      '/me',
      '/register',
      '/login',
      '/me',
    ])
  })
})

describe('signing out', () => {
  it('clears the session', async () => {
    stubServer({
      'GET /me': { body: SESSION },
      'POST /logout': { body: { message: 'Logged out' } },
    })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })

    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('clears it even when the server has already forgotten the session', async () => {
    stubServer({
      'GET /me': { body: SESSION },
      // The cookie expired between the boot check and the click, so the call
      // is a 401 — which is not a reason to stay stuck signed in.
      'POST /logout': SIGNED_OUT,
    })

    renderHarness()

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    await userEvent.click(screen.getByRole('button', { name: 'Log out' }))

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })
  })
})

describe('a guarded route', () => {
  /** @param {string} initialPath */
  function renderGuarded(initialPath) {
    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/expenses"
              element={
                <RequireAuth>
                  <span>Expense list</span>
                </RequireAuth>
              }
            />
            <Route path="/login" element={<span>Sign in form</span>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )
  }

  it('sends a signed-out visitor to the sign-in page', async () => {
    stubServer({ 'GET /me': SIGNED_OUT })

    renderGuarded('/expenses')

    await waitFor(() => {
      expect(screen.getByText('Sign in form')).toBeInTheDocument()
    })

    expect(screen.queryByText('Expense list')).not.toBeInTheDocument()
  })

  it('shows the page once the session is confirmed', async () => {
    stubServer({ 'GET /me': { body: SESSION } })

    renderGuarded('/expenses')

    await waitFor(() => {
      expect(screen.getByText('Expense list')).toBeInTheDocument()
    })
  })

  it('waits for the boot check rather than redirecting on a hunch', async () => {
    stubServer({ 'GET /me': { body: SESSION } })

    renderGuarded('/expenses')

    // Not redirected, and not shown either — the only honest thing to render
    // while the answer is unknown is the loading state.
    expect(screen.queryByText('Sign in form')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Expense list')).toBeInTheDocument()
    })
  })
})
