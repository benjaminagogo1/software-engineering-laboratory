import { useEffect, useState } from 'react'

/**
 * Loads something from the API on mount, and tells the view where it got to.
 *
 * Every view needs the same three states — loading, loaded, failed — and the
 * same guard against setting state on an unmounted component, which is what
 * the cancelled flag is for: a slow request that resolves after the user has
 * navigated away must not write to a dead component.
 *
 * @template T
 * @param {() => Promise<T>} loader  re-run whenever `deps` change
 * @param {unknown[]} [deps]
 * @returns {{status: 'loading' | 'ready' | 'error', data: T | null, error: Error | null}}
 */
export function useApi(loader, deps = []) {
  const [state, setState] = useState({
    status: 'loading',
    data: null,
    error: null,
  })

  useEffect(() => {
    let cancelled = false

    setState({ status: 'loading', data: null, error: null })

    loader()
      .then((data) => {
        if (!cancelled) {
          setState({ status: 'ready', data, error: null })
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setState({ status: 'error', data: null, error })
        }
      })

    return () => {
      cancelled = true
    }
    // The caller owns the dependency list, exactly as with useEffect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return state
}
