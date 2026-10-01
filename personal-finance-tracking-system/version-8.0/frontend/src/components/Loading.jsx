/**
 * Shown while a view is waiting on the API.
 *
 * `role="status"` so a screen reader announces it rather than leaving the
 * user with silence between two page states.
 *
 * @param {{label?: string}} props
 */
export function Loading({ label = 'Loading…' }) {
  return (
    <p className="loading" role="status">
      {label}
    </p>
  )
}
