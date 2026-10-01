import { useState } from 'react'

import { analytics } from '../../api/endpoints'
import { ErrorNote } from '../../components/ErrorNote'
import { Loading } from '../../components/Loading'
import { absentIfMissing } from '../../lib/absentIfMissing'
import { formatDate, formatMoney, formatMonth, thisMonth } from '../../lib/money'
import { useApi } from '../../lib/useApi'
import { MonthlyChart } from './MonthlyChart'

/**
 * The four answers worth putting at the top, loaded together.
 *
 * Each endpoint answers 404 when there is nothing to report, which is an empty
 * state rather than a failure — `absentIfMissing` turns it into a null the
 * tiles can render as a dash.
 */
function useSummary() {
  return useApi(
    async () => {
      const [months, topDay, highest, lowest] = await Promise.all([
        analytics.months(),
        absentIfMissing(analytics.topDay()),
        absentIfMissing(analytics.highest()),
        absentIfMissing(analytics.lowest()),
      ])

      // The ranking arrives highest first, so its head is the busiest month.
      return { months, topMonth: months[0] ?? null, topDay, highest, lowest }
    },
    [],
  )
}

/** @param {{label: string, value: string, note: string}} props */
function Tile({ label, value, note }) {
  return (
    <div className="tile">
      <span className="tile__label">{label}</span>
      <span className="tile__value money">{value}</span>
      <span className="tile__note">{note}</span>
    </div>
  )
}

export function AnalyticsPage() {
  const summary = useSummary()
  const [month, setMonth] = useState(thisMonth())

  const months = summary.data?.months ?? []

  // The current month is always offered, even before anything has been spent
  // in it — otherwise a new account has an empty picker and nothing to look at.
  const choices = months.some((entry) => entry.month === month)
    ? months
    : [{ month, total_cents: 0 }, ...months]

  // The ranking arrives highest first, which is what the bars are scaled to.
  const biggest = months[0]?.total_cents ?? 0

  return (
    <>
      <div className="page-head">
        <h1>Analytics</h1>
        <p className="page-head__subtitle">Where the money has been going</p>
      </div>

      {summary.status === 'loading' && <Loading label="Working it out…" />}

      {summary.status === 'error' && <ErrorNote error={summary.error} />}

      {summary.status === 'ready' && (
        <div className="stack">
          <div className="tiles">
            <Tile
              label="Busiest month"
              value={summary.data.topMonth === null
                ? '—'
                : formatMoney(summary.data.topMonth.total_cents)}
              note={summary.data.topMonth === null
                ? 'nothing recorded yet'
                : formatMonth(summary.data.topMonth.month)}
            />

            <Tile
              label="Busiest weekday"
              value={summary.data.topDay === null
                ? '—'
                : formatMoney(summary.data.topDay.total_cents)}
              note={summary.data.topDay?.day ?? 'nothing recorded yet'}
            />

            <Tile
              label="Largest expense"
              value={summary.data.highest === null
                ? '—'
                : formatMoney(summary.data.highest.amount_cents)}
              note={summary.data.highest === null
                ? 'nothing recorded yet'
                : `${summary.data.highest.name} · ${formatDate(summary.data.highest.date)}`}
            />

            <Tile
              label="Smallest expense"
              value={summary.data.lowest === null
                ? '—'
                : formatMoney(summary.data.lowest.amount_cents)}
              note={summary.data.lowest === null
                ? 'nothing recorded yet'
                : `${summary.data.lowest.name} · ${formatDate(summary.data.lowest.date)}`}
            />
          </div>

          {months.length > 0 && (
            <div className="card">
              <h2 className="card__head">Spending by month</h2>
              <ul className="bars">
                {months.map((entry) => (
                  <li className="bar-row" key={entry.month}>
                    <span className="bar-row__label">{formatMonth(entry.month)}</span>
                    {/* The bar is decoration on a number that is already
                        written out — its width is not the only way to read
                        the value, and it carries no text of its own. */}
                    <span
                      className="bar-row__bar"
                      aria-hidden="true"
                      style={{
                        width: `${Math.round((entry.total_cents / (biggest || 1)) * 100)}%`,
                      }}
                    />
                    <span className="money">{formatMoney(entry.total_cents)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="card">
            <div className="card__head">
              <h2>Daily spending</h2>
              <div className="field field--inline">
                <label className="field__label" htmlFor="chart-month">
                  Month
                </label>
                <select
                  id="chart-month"
                  value={month}
                  onChange={(event) => setMonth(event.target.value)}
                >
                  {choices.map((entry) => (
                    <option key={entry.month} value={entry.month}>
                      {formatMonth(entry.month)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <MonthlyChart month={month} />
          </div>
        </div>
      )}
    </>
  )
}
