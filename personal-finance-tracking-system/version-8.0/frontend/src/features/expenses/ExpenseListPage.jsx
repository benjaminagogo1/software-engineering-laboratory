import { useState } from 'react'

import { ApiError } from '../../api/errors'
import { expenses as expensesApi } from '../../api/endpoints'
import { ErrorNote } from '../../components/ErrorNote'
import { Loading } from '../../components/Loading'
import { useApi } from '../../lib/useApi'
import { useDebouncedValue } from '../../lib/useDebouncedValue'
import { formatDate, formatMoney } from '../../lib/money'
import { ExpenseForm } from './ExpenseForm'

/** What the user is being asked to type before a whole list is deleted. */
const CONFIRMATION_WORD = 'DELETE'

/**
 * Newest first, and the newest-entered first among expenses on the same day.
 *
 * The API returns expenses in insertion order — a contract the CLI's `list`
 * command relies on — so the ordering a reader expects is this layer's job.
 * Sorting a copy, because the array came from state and sorting it in place
 * would mutate what the hook is holding.
 *
 * @param {import('../../api/types').ExpenseResponse[]} list
 * @returns {import('../../api/types').ExpenseResponse[]}
 */
function sortNewestFirst(list) {
  return [...list].sort(
    (left, right) =>
      right.date.localeCompare(left.date) || right.id - left.id,
  )
}

/**
 * The expense list, and everything you can do to it.
 *
 * Search goes to the server rather than filtering the array in memory: the
 * API already defines what "matches" means (the CLI's `search` command uses
 * the same endpoint), and a second definition here would be a second thing to
 * keep in step.
 */
export function ExpenseListPage() {
  const [query, setQuery] = useState('')
  const settledQuery = useDebouncedValue(query)

  // Bumped after every successful write to re-run the loader. The hook keys
  // off its dependency list, so changing this is what makes it refetch.
  const [version, setVersion] = useState(0)

  const [editing, setEditing] = useState(
    /** @type {import('../../api/types').ExpenseResponse | null} */ (null),
  )
  const [adding, setAdding] = useState(false)
  const [busy, setBusy] = useState(false)
  const [fieldErrors, setFieldErrors] = useState(/** @type {Record<string, string>} */ ({}))
  const [notice, setNotice] = useState(/** @type {string | null} */ (null))
  const [failure, setFailure] = useState(/** @type {Error | null} */ (null))
  const [confirmingDelete, setConfirmingDelete] = useState(/** @type {number | null} */ (null))
  const [typedConfirmation, setTypedConfirmation] = useState('')

  const { status, data, error } = useApi(
    () => (settledQuery === '' ? expensesApi.list() : expensesApi.search(settledQuery)),
    [settledQuery, version],
  )

  const list = sortNewestFirst(data ?? [])
  // Integer kobo, so this sum is exact however many rows it adds up.
  const total = list.reduce((sum, expense) => sum + expense.amount_cents, 0)

  function reload() {
    setVersion((current) => current + 1)
  }

  /** Closes whichever form is open and clears everything it left behind. */
  function closeForm() {
    setAdding(false)
    setEditing(null)
    setFieldErrors({})
  }

  /**
   * Runs a write, then either reloads or shows what the server objected to.
   *
   * @param {() => Promise<unknown>} action
   * @param {string} done  what to say when it works
   */
  async function write(action, done) {
    setBusy(true)
    setFailure(null)
    setFieldErrors({})

    try {
      await action()
      setNotice(done)
      closeForm()
      reload()
    } catch (error) {
      // A field-level complaint belongs next to the field; anything else is
      // about the request as a whole and belongs at the top of the page.
      if (error instanceof ApiError && Object.keys(error.fieldErrors).length > 0) {
        setFieldErrors(error.fieldErrors)
      } else {
        setFailure(error instanceof Error ? error : new Error('Something went wrong.'))
        closeForm()
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>Expenses</h1>
        <p className="page-head__subtitle">
          {status === 'ready'
            ? `${list.length} ${list.length === 1 ? 'expense' : 'expenses'} · ${formatMoney(total)}`
            : 'Your spending, newest first'}
        </p>
      </div>

      {notice !== null && (
        <div className="alert alert--success" role="status">
          {notice}
        </div>
      )}

      {failure !== null && <ErrorNote error={failure} />}

      <div className="stack">
        {adding || editing !== null ? (
          <div className="card">
            <h2 className="card__head">
              {editing !== null ? `Edit “${editing.name}”` : 'New expense'}
            </h2>
            <ExpenseForm
              // Remounting on a different expense is what resets the fields;
              // keying by id is cheaper than syncing state in an effect.
              key={editing?.id ?? 'new'}
              initial={editing}
              onSubmit={(values) =>
                editing !== null
                  ? write(
                      () => expensesApi.update(editing.id, values),
                      'Expense updated',
                    )
                  : write(() => expensesApi.create(values), 'Expense added')
              }
              onCancel={closeForm}
              serverErrors={fieldErrors}
              busy={busy}
            />
          </div>
        ) : (
          <div className="row row--end">
            <button
              type="button"
              className="button"
              onClick={() => {
                setNotice(null)
                setAdding(true)
              }}
            >
              Add expense
            </button>
          </div>
        )}

        <div className="card">
          <div className="card__head">
            <h2>All expenses</h2>
            <div className="field field--inline">
              <label className="visually-hidden" htmlFor="search">
                Search expenses by name
              </label>
              <input
                id="search"
                type="search"
                placeholder="Search by name…"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
          </div>

          {status === 'loading' && <Loading label="Loading your expenses…" />}

          {status === 'error' && <ErrorNote error={error} onRetry={reload} />}

          {status === 'ready' && list.length === 0 && (
            <p className="empty">
              {settledQuery === ''
                ? 'Nothing recorded yet. Add your first expense to get started.'
                : `Nothing matches “${settledQuery}”.`}
            </p>
          )}

          {status === 'ready' && list.length > 0 && (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Name</th>
                    <th scope="col">Category</th>
                    <th scope="col">Paid with</th>
                    <th scope="col">Where</th>
                    <th scope="col" className="numeric">
                      Amount
                    </th>
                    <th scope="col">
                      <span className="visually-hidden">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((expense) => (
                    <tr key={expense.id}>
                      <td>
                        <time dateTime={expense.date}>{formatDate(expense.date)}</time>
                      </td>
                      <td>
                        {expense.name}
                        {expense.note !== null && (
                          <span className="table__note">{expense.note}</span>
                        )}
                      </td>
                      <td>{expense.category}</td>
                      <td>{expense.payment_type}</td>
                      <td>{expense.merchant ?? '—'}</td>
                      <td className="numeric money">{formatMoney(expense.amount_cents)}</td>
                      <td className="table__actions">
                        {confirmingDelete === expense.id ? (
                          <>
                            <span className="muted">Delete?</span>
                            <button
                              type="button"
                              className="button button--danger button--small"
                              disabled={busy}
                              onClick={() =>
                                write(
                                  () => expensesApi.remove(expense.id),
                                  'Expense deleted',
                                ).then(() => setConfirmingDelete(null))
                              }
                            >
                              Yes
                            </button>
                            <button
                              type="button"
                              className="button button--ghost button--small"
                              onClick={() => setConfirmingDelete(null)}
                            >
                              No
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="button button--ghost button--small"
                              onClick={() => {
                                setNotice(null)
                                setAdding(false)
                                setFieldErrors({})
                                setEditing(expense)
                              }}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="button button--ghost button--small"
                              onClick={() => setConfirmingDelete(expense.id)}
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {status === 'ready' && list.length > 0 && (
          <div className="card card--danger">
            <h2 className="card__head">Delete everything</h2>
            <p className="muted">
              Removes all {list.length} of your expenses. There is no undo.
              Type <strong>{CONFIRMATION_WORD}</strong> to confirm.
            </p>
            <div className="row">
              <label className="visually-hidden" htmlFor="confirm-delete-all">
                Type {CONFIRMATION_WORD} to confirm
              </label>
              <input
                id="confirm-delete-all"
                value={typedConfirmation}
                placeholder={CONFIRMATION_WORD}
                onChange={(event) => setTypedConfirmation(event.target.value)}
              />
              <button
                type="button"
                className="button button--danger"
                disabled={typedConfirmation !== CONFIRMATION_WORD || busy}
                onClick={() =>
                  write(expensesApi.removeAll, 'Every expense deleted').then(() =>
                    setTypedConfirmation(''),
                  )
                }
              >
                Delete all
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
