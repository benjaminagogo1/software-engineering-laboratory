import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ExpenseListPage } from './ExpenseListPage'
import { stubServer } from '../../test/stubServer'

/**
 * @param {object} [overrides]
 * @returns {import('../../api/types').ExpenseResponse}
 */
function expense(overrides = {}) {
  return {
    id: 1,
    name: 'Groceries',
    amount_cents: 2450000,
    date: '2026-09-02',
    category: 'Food',
    payment_type: 'Card',
    merchant: 'Shoprite',
    note: null,
    ...overrides,
  }
}

/** The table rows, without the header. */
function rows() {
  return within(screen.getByRole('table')).getAllByRole('row').slice(1)
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('the list', () => {
  it('shows each expense and the running total', async () => {
    stubServer({
      'GET /expenses': {
        body: [
          expense({ id: 1, name: 'Groceries', amount_cents: 2450000 }),
          expense({ id: 2, name: 'Danfo', amount_cents: 120000, category: 'Transport' }),
        ],
      },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(2))

    expect(screen.getByText('Groceries')).toBeInTheDocument()
    expect(screen.getByText('₦24,500.00')).toBeInTheDocument()
    expect(screen.getByText('₦1,200.00')).toBeInTheDocument()
    expect(screen.getByText(/2 expenses · ₦25,700.00/)).toBeInTheDocument()
  })

  it('says so when there is nothing yet', async () => {
    stubServer({ 'GET /expenses': { body: [] } })

    render(<ExpenseListPage />)

    await waitFor(() => {
      expect(screen.getByText(/Nothing recorded yet/)).toBeInTheDocument()
    })
  })

  it('shows the newest expense first, whatever order the API returned', async () => {
    // The API answers in insertion order — a contract the CLI depends on — so
    // the order a reader expects has to be applied here.
    stubServer({
      'GET /expenses': {
        body: [
          expense({ id: 1, name: 'Oldest', date: '2026-08-01' }),
          expense({ id: 2, name: 'Newest', date: '2026-09-21' }),
          expense({ id: 3, name: 'Middle', date: '2026-09-02' }),
        ],
      },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(3))

    expect(
      rows().map((row) => within(row).getAllByRole('cell')[1].textContent),
    ).toEqual(['Newest', 'Middle', 'Oldest'])
  })

  it('breaks a tie on the same day by the most recently entered', async () => {
    stubServer({
      'GET /expenses': {
        body: [
          expense({ id: 7, name: 'Entered first', date: '2026-09-21' }),
          expense({ id: 9, name: 'Entered second', date: '2026-09-21' }),
        ],
      },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(2))

    expect(
      rows().map((row) => within(row).getAllByRole('cell')[1].textContent),
    ).toEqual(['Entered second', 'Entered first'])
  })

  it('shows the server sentence when the list cannot be loaded', async () => {
    stubServer({ 'GET /expenses': { status: 500, body: { detail: 'Database is on fire' } } })

    render(<ExpenseListPage />)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Database is on fire')
    })
  })
})

describe('adding', () => {
  it('sends the parsed values and reloads the list', async () => {
    let items = [expense()]

    const { calls } = stubServer({
      'GET /expenses': () => ({ body: items }),
      'POST /expenses': ({ options }) => {
        const sent = JSON.parse(options.body)
        items = [...items, expense({ id: 2, ...sent, date: sent.date })]
        return { status: 201, body: { result: 'success', expense: items[1] } }
      },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))
    await userEvent.type(screen.getByLabelText('What was it for?'), 'Danfo')
    await userEvent.type(screen.getByLabelText('Amount'), '1200')
    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))

    await waitFor(() => expect(rows()).toHaveLength(2))

    const posted = calls.find((call) => call.method === 'POST')

    expect(posted.body).toMatchObject({
      name: 'Danfo',
      amount_cents: 120000,
      category: 'Food',
      payment_type: 'Cash',
      // Blank optional fields go as null, which is what the API stores.
      merchant: null,
      note: null,
    })
    expect(screen.getByRole('status')).toHaveTextContent('Expense added')
  })

  it('sends whole kobo, whatever the typed decimals were', async () => {
    // The case the integer column exists for: 10.10 naira is 1010 kobo
    // exactly. Through a float it is 1009.9999999999999, and the expense
    // would be stored a kobo light.
    const { calls } = stubServer({ 'GET /expenses': { body: [] } })

    render(<ExpenseListPage />)

    await waitFor(() => {
      expect(screen.getByText(/Nothing recorded yet/)).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))
    await userEvent.type(screen.getByLabelText('What was it for?'), 'Okpa')
    await userEvent.type(screen.getByLabelText('Amount'), '10.10')
    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'POST')).toBe(true)
    })

    const posted = calls.find((call) => call.method === 'POST')

    expect(posted.body.amount_cents).toBe(1010)
  })

  it('refuses a third decimal place rather than rounding the money away', async () => {
    const { calls } = stubServer({ 'GET /expenses': { body: [] } })

    render(<ExpenseListPage />)

    await waitFor(() => {
      expect(screen.getByText(/Nothing recorded yet/)).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))
    await userEvent.type(screen.getByLabelText('What was it for?'), 'Okpa')
    await userEvent.type(screen.getByLabelText('Amount'), '10.005')
    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))

    expect(
      await screen.findByText(/Enter a number, for example 2500 or 2500.50/),
    ).toBeInTheDocument()
    expect(calls.some((call) => call.method === 'POST')).toBe(false)
  })

  it('refuses a blank amount without troubling the server', async () => {
    const { calls } = stubServer({ 'GET /expenses': { body: [] } })

    render(<ExpenseListPage />)

    await waitFor(() => {
      expect(screen.getByText(/Nothing recorded yet/)).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))
    await userEvent.type(screen.getByLabelText('What was it for?'), 'Danfo')
    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))

    expect(await screen.findByText('Enter an amount.')).toBeInTheDocument()
    expect(calls.some((call) => call.method === 'POST')).toBe(false)
  })

  it('puts a field error the server sends under the field it names', async () => {
    stubServer({
      'GET /expenses': { body: [] },
      'POST /expenses': {
        status: 422,
        body: {
          detail: [{ loc: ['body', 'amount'], msg: 'Input should be a valid number' }],
        },
      },
    })

    render(<ExpenseListPage />)

    await waitFor(() => {
      expect(screen.getByText(/Nothing recorded yet/)).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))
    await userEvent.type(screen.getByLabelText('What was it for?'), 'Danfo')
    await userEvent.type(screen.getByLabelText('Amount'), '1200')
    await userEvent.click(screen.getByRole('button', { name: 'Add expense' }))

    expect(
      await screen.findByText('Input should be a valid number'),
    ).toBeInTheDocument()

    expect(screen.getByLabelText('Amount')).toHaveAttribute('aria-invalid', 'true')
  })
})

describe('editing', () => {
  it('loads the row into the form and PUTs the changes', async () => {
    const { calls } = stubServer({
      'GET /expenses': { body: [expense()] },
      'PUT /expenses/1': { body: { message: 'Expense updated successfully' } },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))

    const name = screen.getByLabelText('What was it for?')
    expect(name).toHaveValue('Groceries')

    await userEvent.clear(name)
    await userEvent.type(name, 'Groceries and household')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'PUT')).toBe(true)
    })

    const put = calls.find((call) => call.method === 'PUT')

    expect(put.path).toBe('/expenses/1')
    expect(put.body).toMatchObject({ name: 'Groceries and household', amount_cents: 2450000 })
    expect(screen.getByRole('status')).toHaveTextContent('Expense updated')
  })

  it('shows the amount in naira and gives back the same kobo untouched', async () => {
    // The round trip that has to be exact: an expense with kobo in it opens in
    // the form as naira, and saving without touching the field must not move
    // the amount. ₦2,500.50 goes in and 250050 comes back.
    const { calls } = stubServer({
      'GET /expenses': { body: [expense({ amount_cents: 250050 })] },
      'PUT /expenses/1': { body: { message: 'Expense updated successfully' } },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))

    expect(screen.getByLabelText('Amount')).toHaveValue('2500.50')

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'PUT')).toBe(true)
    })

    const put = calls.find((call) => call.method === 'PUT')

    expect(put.body.amount_cents).toBe(250050)
  })
})

describe('deleting', () => {
  it('asks before it deletes', async () => {
    const { calls } = stubServer({
      'GET /expenses': { body: [expense()] },
      'DELETE /expenses/1': { body: { message: 'Expense deleted successfully' } },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))

    // Nothing has been sent yet — the row is asking.
    expect(calls.some((call) => call.method === 'DELETE')).toBe(false)
    expect(screen.getByText('Delete?')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Yes' }))

    await waitFor(() => {
      expect(calls.some((call) => call.method === 'DELETE')).toBe(true)
    })
  })

  it('backs out when the answer is no', async () => {
    const { calls } = stubServer({ 'GET /expenses': { body: [expense()] } })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))
    await userEvent.click(screen.getByRole('button', { name: 'No' }))

    expect(screen.queryByText('Delete?')).not.toBeInTheDocument()
    expect(calls.some((call) => call.method === 'DELETE')).toBe(false)
  })
})

describe('deleting everything', () => {
  it('keeps the button disabled until the word is typed', async () => {
    stubServer({ 'GET /expenses': { body: [expense()] } })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    const button = screen.getByRole('button', { name: 'Delete all' })
    expect(button).toBeDisabled()

    await userEvent.type(screen.getByLabelText('Type DELETE to confirm'), 'DELETE')

    expect(button).toBeEnabled()
  })

  it('rejects a near miss', async () => {
    stubServer({ 'GET /expenses': { body: [expense()] } })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.type(screen.getByLabelText('Type DELETE to confirm'), 'delete')

    // Case matters: this is a confirmation, not a keyword search.
    expect(screen.getByRole('button', { name: 'Delete all' })).toBeDisabled()
  })
})

describe('searching', () => {
  it('asks the server rather than filtering in memory, once the typing stops', async () => {
    const { calls } = stubServer({
      'GET /expenses': { body: [expense()] },
      '* /expenses/search?name=danfo': { body: [expense({ id: 2, name: 'Danfo' })] },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.type(screen.getByLabelText('Search expenses by name'), 'danfo')

    // Waiting on the old row disappearing is what proves the response landed —
    // the row count alone is unchanged either way.
    await waitFor(() => {
      expect(screen.queryByText('Groceries')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Danfo')).toBeInTheDocument()

    // One request for five keystrokes is the point of the debounce.
    const searches = calls.filter((call) => call.path.startsWith('/expenses/search'))

    expect(searches).toHaveLength(1)
  })

  it('says when nothing matches', async () => {
    stubServer({
      'GET /expenses': { body: [expense()] },
      '* /expenses/search?name=zzz': { body: [] },
    })

    render(<ExpenseListPage />)

    await waitFor(() => expect(rows()).toHaveLength(1))

    await userEvent.type(screen.getByLabelText('Search expenses by name'), 'zzz')

    await waitFor(() => {
      expect(screen.getByText('Nothing matches “zzz”.')).toBeInTheDocument()
    })
  })
})
