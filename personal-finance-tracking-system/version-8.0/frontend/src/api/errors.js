/**
 * One error type for everything the API can refuse with, so no view has to
 * know how FastAPI happens to shape a particular failure.
 *
 * The API answers with two incompatible bodies:
 *   - a raised HTTPException   -> {detail: "Amount must be greater than zero"}
 *   - a pydantic validation    -> {detail: [{loc: [...], msg: "..."}, ...]}
 *
 * Rendering the second one without flattening it puts "[object Object]" on the
 * screen, which is the bug this module exists to prevent.
 */

const GENERIC_MESSAGE = 'Something went wrong. Please try again.'

export class ApiError extends Error {
  /**
   * @param {number} status
   * @param {string} message  safe to render as-is
   * @param {Record<string, string>} [fieldErrors]  keyed by form field name
   */
  constructor(status, message, fieldErrors = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }

  get isUnauthorized() {
    return this.status === 401
  }
}

/** @param {unknown} value */
function isObject(value) {
  return typeof value === 'object' && value !== null
}

/**
 * The field name pydantic reports, minus the location prefix.
 *
 * A loc looks like ["body", "amount"], or ["body", "items", 3, "name"] for a
 * nested list; the last string is the field the user actually has to fix.
 *
 * @param {unknown} loc
 * @returns {string | null}
 */
function fieldName(loc) {
  if (!Array.isArray(loc)) {
    return null
  }

  const named = loc.filter(
    (part) => typeof part === 'string' && part !== 'body' && part !== 'query',
  )

  const last = named[named.length - 1]

  return typeof last === 'string' ? last : null
}

/**
 * Turns whatever the server sent into one ApiError.
 *
 * @param {number} status
 * @param {unknown} body  the parsed JSON body, or null if there wasn't one
 * @returns {ApiError}
 */
export function apiErrorFrom(status, body) {
  if (!isObject(body) || !('detail' in body)) {
    return new ApiError(status, GENERIC_MESSAGE)
  }

  const { detail } = body

  // A raised HTTPException: the detail is the sentence the server wrote.
  if (typeof detail === 'string') {
    return new ApiError(status, detail)
  }

  // A validation error: one entry per problem, each naming a field.
  if (Array.isArray(detail)) {
    /** @type {Record<string, string>} */
    const fieldErrors = {}
    /** @type {string[]} */
    const messages = []

    for (const item of detail) {
      const message = isObject(item) && typeof item.msg === 'string'
        ? item.msg
        : 'is not valid'
      const field = isObject(item) ? fieldName(item.loc) : null

      if (field !== null) {
        fieldErrors[field] = message
      }

      messages.push(field === null ? message : `${field}: ${message}`)
    }

    if (messages.length === 0) {
      return new ApiError(status, GENERIC_MESSAGE)
    }

    return new ApiError(status, messages.join('; '), fieldErrors)
  }

  return new ApiError(status, GENERIC_MESSAGE)
}

/**
 * Reads a failed response into an ApiError.
 *
 * A non-JSON body is possible — a proxy error, an HTML error page — and is a
 * failure like any other rather than a crash in the error path itself.
 *
 * @param {Response} response
 * @returns {Promise<ApiError>}
 */
export async function toApiError(response) {
  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  return apiErrorFrom(response.status, body)
}
