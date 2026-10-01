import { Link } from 'react-router-dom'

/** A path this app does not have. Distinct from "you may not see this". */
export function NotFoundPage() {
  return (
    <div className="auth">
      <div className="auth__card card">
        <h1 className="card__head">Page not found</h1>
        <p className="muted">
          That address does not match anything in this app.
        </p>
        <p>
          <Link to="/">Go to the overview</Link>
        </p>
      </div>
    </div>
  )
}
