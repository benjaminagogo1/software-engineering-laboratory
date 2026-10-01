import { describe, expect, it } from 'vitest'

import { CATEGORIES, MAX_AMOUNT_CENTS, PAYMENT_TYPES } from '../../api/constants'
import { validateExpense } from './validation'

/** A valid set of fields, as the form would hold them, for tests to spoil. */
function fields(overrides = {}) {
  return {
    name: 'Groceries',
    amount: '24500',
    date: '2026-09-02',
    category: 'Food',
    payment_type: 'Card',
    merchant: 'Shoprite',
    note: '',
    ...overrides,
  }
}

describe('validateExpense', () => {
  it('accepts a filled-in expense', () => {
    const { errors, values } = validateExpense(fields())

    expect(errors).toEqual({})
    expect(values.amount_cents).toBe(2450000)
  })

  it('turns the typed naira into whole kobo', () => {
    expect(validateExpense(fields({ amount: '2500.50' })).values.amount_cents).toBe(250050)
    expect(validateExpense(fields({ amount: '2500' })).values.amount_cents).toBe(250000)
    expect(validateExpense(fields({ amount: '2500.5' })).values.amount_cents).toBe(250050)
    expect(validateExpense(fields({ amount: '0.5' })).values.amount_cents).toBe(50)
    expect(validateExpense(fields({ amount: '0.05' })).values.amount_cents).toBe(5)
  })

  it('reads the digits exactly, never through a float', () => {
    // The reason this is parsed from the string: 10.10 * 100 in JavaScript is
    // 1009.9999999999999, so the form would send a kobo less than the user
    // typed. Nothing about that is visible in the number itself.
    expect(validateExpense(fields({ amount: '10.10' })).values.amount_cents).toBe(1010)
    expect(validateExpense(fields({ amount: '1.10' })).values.amount_cents).toBe(110)
    expect(validateExpense(fields({ amount: '0.29' })).values.amount_cents).toBe(29)
  })

  it('rejects a third decimal place rather than rounding it away', () => {
    // 10.005 silently becoming 1000 kobo loses the user's money and says
    // nothing about having done it.
    expect(validateExpense(fields({ amount: '10.005' })).errors.amount).toMatch(/number/)
    expect(validateExpense(fields({ amount: '0.001' })).errors.amount).toMatch(/number/)
  })

  it('rejects an amount that is not a number', () => {
    // "1,000" is the form the UI displays, but not the form the API takes.
    expect(validateExpense(fields({ amount: '1,000' })).errors.amount).toMatch(/number/)
    expect(validateExpense(fields({ amount: 'N2500' })).errors.amount).toMatch(/number/)
    expect(validateExpense(fields({ amount: '2.5e3' })).errors.amount).toMatch(/number/)
    expect(validateExpense(fields({ amount: 'NaN' })).errors.amount).toMatch(/number/)
    expect(validateExpense(fields({ amount: 'Infinity' })).errors.amount).toMatch(/number/)
  })

  it('rejects an amount of zero or less', () => {
    expect(validateExpense(fields({ amount: '0' })).errors.amount).toMatch(/greater than zero/)
    expect(validateExpense(fields({ amount: '0.00' })).errors.amount).toMatch(/greater than zero/)
    expect(validateExpense(fields({ amount: '-5' })).errors.amount).toMatch(/greater than zero/)
  })

  it('rejects an amount above the ceiling the API enforces', () => {
    const tooMuch = String(MAX_AMOUNT_CENTS / 100 + 1)

    expect(validateExpense(fields({ amount: tooMuch })).errors.amount).toMatch(/cannot be more than/)

    // And the ceiling itself is allowed — an off-by-one here would refuse the
    // largest amount the server would have taken.
    const exactly = String(MAX_AMOUNT_CENTS / 100)

    expect(validateExpense(fields({ amount: exactly })).errors).toEqual({})
  })

  it('rejects a blank amount rather than treating it as zero', () => {
    expect(validateExpense(fields({ amount: '' })).errors.amount).toMatch(/Enter an amount/)
  })

  it('rejects a blank name', () => {
    expect(validateExpense(fields({ name: '   ' })).errors.name).toMatch(/what this expense was for/)
  })

  it('trims the name', () => {
    expect(validateExpense(fields({ name: '  Groceries  ' })).values.name).toBe('Groceries')
  })

  it('rejects a date that is not a date', () => {
    expect(validateExpense(fields({ date: '02/09/2026' })).errors.date).toBeDefined()
    expect(validateExpense(fields({ date: '' })).errors.date).toBeDefined()
  })

  it('rejects a category the server would reject', () => {
    expect(validateExpense(fields({ category: 'Snacks' })).errors.category).toBeDefined()
  })

  it('rejects a payment type the server would reject', () => {
    expect(validateExpense(fields({ payment_type: 'Barter' })).errors.payment_type).toBeDefined()
  })

  it('accepts every category and payment type the API publishes', () => {
    for (const category of CATEGORIES) {
      expect(validateExpense(fields({ category })).errors).toEqual({})
    }

    for (const payment_type of PAYMENT_TYPES) {
      expect(validateExpense(fields({ payment_type })).errors).toEqual({})
    }
  })

  it('sends a blank optional field as null, not as an empty string', () => {
    const { values } = validateExpense(fields({ merchant: '', note: '   ' }))

    expect(values.merchant).toBeNull()
    expect(values.note).toBeNull()
  })

  it('keeps the optional fields when they are filled in', () => {
    const { values } = validateExpense(fields({ merchant: ' Shoprite ', note: ' weekly ' }))

    expect(values.merchant).toBe('Shoprite')
    expect(values.note).toBe('weekly')
  })

  it('reports every problem at once rather than one at a time', () => {
    const { errors } = validateExpense({
      name: '',
      amount: '',
      date: '',
      category: 'Snacks',
      payment_type: 'Barter',
      merchant: '',
      note: '',
    })

    expect(Object.keys(errors).sort()).toEqual([
      'amount',
      'category',
      'date',
      'name',
      'payment_type',
    ])
  })
})
