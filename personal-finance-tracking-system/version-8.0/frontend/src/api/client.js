/**
 * The only module in the client that knows about HTTP.
 *
 * Two things live here rather than at the call sites, because getting either
 * wrong is a security bug, not a style problem:
 *
 *   - `credentials: 'include'`, without which the httpOnly session cookie is
 *     never sent;
 *   - the X-CSRF-Token header on every write, which is what the server checks
 *     to know the request came from this origin.
 */

import { toApiError } from './errors'

const CSRF_HEADER = 'X-CSRF-Token'

/**
 * Held in a module variable, never in localStorage: a token in storage is
 * readable by any script that gets injected into the page.
 *
 * @type {string | null}
 */
let csrfToken = null

/** @type {(() => void) | null} */
let onUnauthorized = null

/** @param {string | null} token */
export function setCsrfToken(token) {
  csrfToken = token
}

/**
 * Called when the server rejects a request as unauthenticated, so the session
 * can be dropped in one place instead of in every view.
 *
 * @param {(() => void) | null} handler
 */
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

/**
 * @param {'GET' | 'POST' | 'PUT' | 'DELETE'} method
 * @param {string} path
 * @param {unknown} [body]
 * @returns {Promise<any>}
 */
async function request(method, path, body) {
  /** @type {Record<string, string>} */
  const headers = { Accept: 'application/json' }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  // Reads never need it — only a request that changes state can be the forged
  // cross-site kind this defends against.
  if (method !== 'GET' && csrfToken !== null) {
    headers[CSRF_HEADER] = csrfToken
  }

  const response = await fetch(path, {
    method,
    headers,
    credentials: 'include',
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (!response.ok) {
    const error = await toApiError(response)

    if (error.isUnauthorized) {
      onUnauthorized?.()
    }

    throw error
  }

  // A response with no body — a 204 — is not a failure, it just has nothing
  // to parse.
  if (response.status === 204) {
    return undefined
  }

  return response.json()
}

export const api = {
  /** @param {string} path */
  get: (path) => request('GET', path),
  /** @param {string} path @param {unknown} body */
  post: (path, body) => request('POST', path, body),
  /** @param {string} path @param {unknown} body */
  put: (path, body) => request('PUT', path, body),
  /** @param {string} path */
  remove: (path) => request('DELETE', path),
}
