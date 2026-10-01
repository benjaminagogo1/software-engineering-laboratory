import { useEffect, useState } from 'react'

/**
 * A value that only updates once it has stopped changing.
 *
 * Used for the search box: typing "groceries" should be one request, not
 * nine, and the server owns what "matches" means so the filtering cannot be
 * done here instead.
 *
 * @template T
 * @param {T} value
 * @param {number} [delay] milliseconds of quiet before the value is released
 * @returns {T}
 */
export function useDebouncedValue(value, delay = 250) {
  const [settled, setSettled] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delay)

    return () => clearTimeout(timer)
  }, [value, delay])

  return settled
}
