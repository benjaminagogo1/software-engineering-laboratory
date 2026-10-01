import { vi } from 'vitest'

/**
 * A stand-in for the API, at the `fetch` boundary.
 *
 * Stubbing the network rather than the client module is deliberate: it means
 * the tests exercise the real request() — the CSRF header, the credentials
 * option, the error handling — instead of a mock of it that would happily
 * agree with a bug.
 *
 * @typedef {{status?: number, body?: unknown, headers?: Record<string, string>}} Reply
 *
 * @param {Record<string, Reply | ((request: Request) => Reply)>} routes
 *   keyed "METHOD /path"; a key of "*" catches every method
 * @returns {{calls: Array<{method: string, path: string, body: unknown, headers: Record<string, string>}>}}
 */
export function stubServer(routes) {
  const calls = []

  const fetchMock = vi.fn(async (path, options = {}) => {
    const method = options.method ?? 'GET'
    const headers = options.headers ?? {}

    calls.push({
      method,
      path,
      body: options.body === undefined ? undefined : JSON.parse(options.body),
      headers,
    })

    const route = routes[`${method} ${path}`] ?? routes[`* ${path}`] ?? routes['*']

    if (route === undefined) {
      return new Response(JSON.stringify({ detail: `No stub for ${method} ${path}` }), {
        status: 404,
        headers: { 'content-type': 'application/json' },
      })
    }

    const reply = typeof route === 'function' ? route({ method, path, options }) : route
    const status = reply.status ?? 200

    if (status === 204 || reply.body === undefined) {
      return new Response(null, { status, headers: reply.headers })
    }

    return new Response(JSON.stringify(reply.body), {
      status,
      headers: { 'content-type': 'application/json', ...reply.headers },
    })
  })

  vi.stubGlobal('fetch', fetchMock)

  return { calls }
}
