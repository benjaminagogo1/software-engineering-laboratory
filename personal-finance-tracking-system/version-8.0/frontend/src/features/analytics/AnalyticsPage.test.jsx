import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AnalyticsPage } from './AnalyticsPage'
import { stubServer } from '../../test/stubServer'

/**
 * The page reads the current month to pick its default, so the clock is frozen
 * rather than the test being right only during September 2026. Only `Date` is
 * faked — `waitFor` and user-event need real timers to make progress.
 */
const TODAY = '2026-09-30T12:00:00'
const MONTH = '2026-09'

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(TODAY))
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

/** @param {object} [overrides] */
function expense(overrides = {}) {
  return {
    id: 1,
    name: 'Groceries',
    amount_cents: 2450000,
    date: '2026-09-02',
    category: 'Food',
    payment_type: 'Card',
    merchant: null,
    note: null,
    ...overrides,
  }
}

const MONTHS = [
  { month: '2026-09', total_cents: 4370000 },
  { month: '2026-08', total_cents: 1800000 },
]

/** The routes every analytics test needs, with any of them overridable. */
function analyticsRoutes(overrides = {}) {
  return {
    'GET /analytics/months': { body: MONTHS },
    'GET /analytics/top-day': { body: { day: 'Saturday', total_cents: 2000000 } },
    'GET /analytics/highest': { body: expense({ amount_cents: 2450000 }) },
    'GET /analytics/lowest': { body: expense({ name: 'Danfo', amount_cents: 120000 }) },
    [`GET /reports/month.fragment?month=${MONTH}`]: {
      body: { css: '.spending-chart { color: red }', html: '<p>Chart</p>' },
    },
    ...overrides,
  }
}

/** The 404 the API answers with when there is nothing to report. */
const NOTHING = { status: 404, body: { detail: 'No expenses found' } }

/**
 * Each tile as [label, value, note].
 *
 * Read positionally rather than by text, because several of these strings —
 * "Sep 2026", "₦43,700.00" — also appear in the month ranking below, and a
 * text query could not tell the two apart.
 */
function tiles() {
  return [...document.querySelectorAll('.tile')].map((tile) =>
    [...tile.children].map((child) => child.textContent),
  )
}

/** Each month in the ranking as [label, total]. */
function ranking() {
  return [...document.querySelectorAll('.bar-row')].map((row) => [
    row.querySelector('.bar-row__label').textContent,
    row.lastElementChild.textContent,
  ])
}

describe('the summary tiles', () => {
  it('answers the four questions from the API', async () => {
    stubServer(analyticsRoutes())

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(tiles()).toHaveLength(4)
    })

    expect(tiles()).toEqual([
      ['Busiest month', '₦43,700.00', 'Sep 2026'],
      ['Busiest weekday', '₦20,000.00', 'Saturday'],
      ['Largest expense', '₦24,500.00', 'Groceries · 2 Sep 2026'],
      ['Smallest expense', '₦1,200.00', 'Danfo · 2 Sep 2026'],
    ])
  })

  it('treats "no expenses found" as an empty state, not a failure', async () => {
    stubServer(analyticsRoutes({
      'GET /analytics/months': { body: [] },
      'GET /analytics/top-day': NOTHING,
      'GET /analytics/highest': NOTHING,
      'GET /analytics/lowest': NOTHING,
    }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(tiles()).toHaveLength(4)
    })

    // A dash in all four, and nothing rendered as a failure.
    expect(tiles().map(([, value]) => value)).toEqual(['—', '—', '—', '—'])
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('still shows a real failure as one', async () => {
    stubServer(analyticsRoutes({
      'GET /analytics/months': { status: 500, body: { detail: 'Database is on fire' } },
    }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Database is on fire')
    })
  })
})

describe('the month ranking', () => {
  it('lists each month with its total', async () => {
    stubServer(analyticsRoutes())

    render(<AnalyticsPage />)

    // Both of these strings also appear in the tiles and the month picker, so
    // the ranking is read as a whole rather than by text query.
    await waitFor(() => {
      expect(ranking()).toHaveLength(2)
    })

    expect(ranking()).toEqual([
      ['Sep 2026', '₦43,700.00'],
      ['Aug 2026', '₦18,000.00'],
    ])
  })

  it('scales the longest bar to the full width and the rest against it', async () => {
    stubServer(analyticsRoutes())

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(ranking()).toHaveLength(2)
    })

    const bars = document.querySelectorAll('.bar-row__bar')

    expect(bars[0]).toHaveStyle({ width: '100%' })
    // 1800000 / 4370000 = 41%
    expect(bars[1]).toHaveStyle({ width: '41%' })
  })

  it('hides the ranking entirely when there is nothing to rank', async () => {
    stubServer(analyticsRoutes({ 'GET /analytics/months': { body: [] } }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText('Chart')).toBeInTheDocument()
    })

    expect(screen.queryByText('Spending by month')).not.toBeInTheDocument()
    expect(ranking()).toHaveLength(0)
  })
})

describe('the chart', () => {
  it('injects the server-rendered fragment', async () => {
    stubServer(analyticsRoutes())

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText('Chart')).toBeInTheDocument()
    })

    expect(document.querySelector('.spending-chart')).toBeInTheDocument()
    expect(document.querySelector('style')?.textContent).toContain('.spending-chart')
  })

  it('redraws when a different month is picked', async () => {
    const { calls } = stubServer(analyticsRoutes({
      'GET /reports/month.fragment?month=2026-08': {
        body: { css: 'x {}', html: '<p>August chart</p>' },
      },
    }))

    render(<AnalyticsPage />)

    await waitFor(() => {
      expect(screen.getByText('Chart')).toBeInTheDocument()
    })

    await userEvent.selectOptions(screen.getByLabelText('Month'), '2026-08')

    await waitFor(() => {
      expect(screen.getByText('August chart')).toBeInTheDocument()
    })

    expect(
      calls.some((call) => call.path === '/reports/month.fragment?month=2026-08'),
    ).toBe(true)
  })

  it('shows a failed chart without taking the page down with it', async () => {
    stubServer(analyticsRoutes({
      [`GET /reports/month.fragment?month=${MONTH}`]: {
        status: 500,
        body: { detail: 'Renderer exploded' },
      },
    }))

    render(<AnalyticsPage />)

    // The tiles above are unaffected: one failing card is not a failing page,
    // and the two loads are independent, so each is waited for on its own.
    await waitFor(() => {
      expect(tiles()).toHaveLength(4)
    })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Renderer exploded')
    })
  })
})
