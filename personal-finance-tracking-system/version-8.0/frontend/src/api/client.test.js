import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api, setCsrfToken, setUnauthorizedHandler } from './client'
import { ApiError } from './errors'
import { stubServer } from '../test/stubServer'

afterEach(() => {
  vi.unstubAllGlobals()
})

beforeEach(() => {
  // The token is module state, so it carries between tests in a file.
  setCsrfToken(null)
  setUnauthorizedHandler(null)
})

describe('the request itself', () => {
  it('sends the session cookie', async () => {
    stubServer({ 'GET /expenses': { body: [] } })

    await api.get('/expenses')

    // Without this the httpOnly cookie is never attached, and every call is a
    // 401 in the browser while every test that mocks the client module passes.
    expect(vi.mocked(fetch).mock.calls[0][1].credentials).toBe('include')
  })

  it('sends the CSRF header on a write', async () => {
    stubServer({ 'POST /expenses': { status: 201, body: { result: 'ok' } } })
    setCsrfToken('token-from-login')

    await api.post('/expenses', { name: 'Lunch' })

    expect(vi.mocked(fetch).mock.calls[0][1].headers['X-CSRF-Token']).toBe(
      'token-from-login',
    )
  })

  it('does not send it on a read', async () => {
    stubServer({ 'GET /expenses': { body: [] } })
    setCsrfToken('token-from-login')

    await api.get('/expenses')

    expect(vi.mocked(fetch).mock.calls[0][1].headers['X-CSRF-Token']).toBeUndefined()
  })

  it('sends no CSRF header while signed out, rather than an empty one', async () => {
    stubServer({ 'POST /login': { body: { access_token: 'a', csrf_token: 'c' } } })

    await api.post('/login', { username: 'ben', password: 'secret' })

    expect(vi.mocked(fetch).mock.calls[0][1].headers['X-CSRF-Token']).toBeUndefined()
  })

  it('serialises the body as JSON', async () => {
    const { calls } = stubServer({ 'POST /expenses': { status: 201, body: {} } })

    await api.post('/expenses', { name: 'Lunch', amount: 12.5 })

    expect(calls[0].body).toEqual({ name: 'Lunch', amount: 12.5 })
    expect(vi.mocked(fetch).mock.calls[0][1].headers['Content-Type']).toBe(
      'application/json',
    )
  })
})

describe('responses', () => {
  it('returns the parsed body', async () => {
    stubServer({ 'GET /me': { body: { id: 1, username: 'ben', csrf_token: 'c' } } })

    await expect(api.get('/me')).resolves.toEqual({
      id: 1,
      username: 'ben',
      csrf_token: 'c',
    })
  })

  it('treats a 204 as success with nothing to read', async () => {
    stubServer({ 'DELETE /expenses/1': { status: 204 } })

    await expect(api.remove('/expenses/1')).resolves.toBeUndefined()
  })

  it('throws an ApiError carrying the server sentence', async () => {
    stubServer({ 'DELETE /expenses': { status: 403, body: { detail: 'Invalid CSRF token' } } })

    await expect(api.remove('/expenses')).rejects.toThrow('Invalid CSRF token')
  })

  it('drops the session when the server says 401', async () => {
    stubServer({ 'GET /me': { status: 401, body: { detail: 'Not authenticated' } } })
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)

    await expect(api.get('/me')).rejects.toBeInstanceOf(ApiError)

    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('leaves the session alone for any other failure', async () => {
    stubServer({ 'POST /expenses': { status: 400, body: { detail: 'Amount must be greater than zero' } } })
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)

    await expect(api.post('/expenses', {})).rejects.toBeInstanceOf(ApiError)

    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
