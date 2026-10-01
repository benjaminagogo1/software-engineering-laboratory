/**
 * A failure the user needs to read, rendered as text.
 *
 * React escapes children, so this is safe for any message the server sends —
 * including one that quotes what the user typed.
 *
 * @param {{error: unknown, onRetry?: () => void}} props
 */
export function ErrorNote({ error, onRetry }) {
  const message =
    error instanceof Error ? error.message : 'Something went wrong.'

  return (
    <div className="alert alert--error" role="alert">
      <span>{message}</span>

      {onRetry !== undefined && (
        <button type="button" className="button button--small" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
