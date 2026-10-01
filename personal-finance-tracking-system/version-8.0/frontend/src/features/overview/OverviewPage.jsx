import { expenses } from '../../api/endpoints'
import { useAuth } from '../../auth/AuthContext'
import { ErrorNote } from '../../components/ErrorNote'
import { Loading } from '../../components/Loading'
import { useApi } from '../../lib/useApi'
import { formatDate, formatMoney, formatMonth } from '../../lib/money'

/** How many recent expenses the overview shows before it stops being a summary. */
const RECENT_LIMIT = 5

/**
 * The landing page: what has been spent, and the last few things that made it
 * that way.
 *
 * This is also the app's proof of life — it is the first page to make an
 * authenticated request, so if the session cookie or the CSRF handshake were
 * wrong, this is where it would show.
 */
export function OverviewPage() {
  const { user } = useAuth()
  const { status, data, error } = useApi(() => expenses.list(), [])

  const list = data ?? []
  // Kobo, and integers, so both sums are exact however many rows they cover.
  const total = list.reduce((sum, expense) => sum + expense.amount_cents, 0)

  const thisMonthKey = list
    .map((expense) => expense.date.slice(0, 7))
    .sort()
    .at(-1)

  const thisMonthTotal = list
    .filter((expense) => expense.date.slice(0, 7) === thisMonthKey)
    .reduce((sum, expense) => sum + expense.amount_cents, 0)

  const recent = [...list]
    .sort((left, right) => right.date.localeCompare(left.date) || right.id - left.id)
    .slice(0, RECENT_LIMIT)

  return (
    <>
      <div className="page-head">
        <h1>Overview</h1>
        <p className="page-head__subtitle">
          {user === null ? 'Your spending' : `Signed in as ${user.username}`}
        </p>
      </div>

      {status === 'loading' && <Loading label="Loading your expenses…" />}

      {status === 'error' && <ErrorNote error={error} />}

      {status === 'ready' && (
        <div className="stack">
          <div className="tiles">
            <div className="tile">
              <span className="tile__label">Total recorded</span>
              <span className="tile__value money money--large">
                {formatMoney(total)}
              </span>
              <span className="tile__note">
                across {list.length} {list.length === 1 ? 'expense' : 'expenses'}
              </span>
            </div>

            <div className="tile">
              <span className="tile__label">
                {thisMonthKey === undefined ? 'Latest month' : formatMonth(thisMonthKey)}
              </span>
              <span className="tile__value money money--large">
                {formatMoney(thisMonthTotal)}
              </span>
              <span className="tile__note">most recent month with activity</span>
            </div>
          </div>

          <div className="card">
            <h2 className="card__head">Recent expenses</h2>

            {recent.length === 0 ? (
              <p className="empty">
                Nothing recorded yet. Add your first expense to see it here.
              </p>
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Name</th>
                      <th scope="col">Category</th>
                      <th scope="col" className="numeric">
                        Amount
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((expense) => (
                      <tr key={expense.id}>
                        <td>
                          <time dateTime={expense.date}>
                            {formatDate(expense.date)}
                          </time>
                        </td>
                        <td>{expense.name}</td>
                        <td>{expense.category}</td>
                        <td className="numeric money">{formatMoney(expense.amount_cents)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
