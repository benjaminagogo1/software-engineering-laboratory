import { ApiError } from '../api/errors'

/**
 * Turns a 404 into null.
 *
 * Several analytics endpoints answer 404 for "you have no expenses yet" —
 * `/analytics/highest` has nothing to return. That is an empty state, not a
 * failure, and rendering it as an error would put "No expenses found" in red
 * on a brand-new account.
 *
 * @template T
 * @param {Promise<T>} promise
 * @returns {Promise<T | null>}
 */
export async function absentIfMissing(promise) {
  try {
    return await promise
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null
    }

    throw error
  }
}
