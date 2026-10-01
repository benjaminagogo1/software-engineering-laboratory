import { describe, expect, it } from 'vitest'

import {
  formatDate,
  formatMoney,
  formatMoneyTick,
  formatMonth,
  toAmountInput,
} from './money'

describe('formatMoney', () => {
  it('groups thousands and always shows two decimals', () => {
    expect(formatMoney(250000)).toBe('₦2,500.00')
    expect(formatMoney(123456750)).toBe('₦1,234,567.50')
    expect(formatMoney(0)).toBe('₦0.00')
  })

  it('groups from the right, not the left', () => {
    // The bug a naive /\d{3}/ replacement produces: ₦1,2345,678.00
    expect(formatMoney(1234567800)).toBe('₦12,345,678.00')
  })

  it('splits kobo by integer arithmetic, so no float is involved', () => {
    expect(formatMoney(250050)).toBe('₦2,500.50')
    expect(formatMoney(5)).toBe('₦0.05')
    expect(formatMoney(10 + 20)).toBe('₦0.30')
  })

  it('does not print a non-number at the user', () => {
    expect(formatMoney(Number.NaN)).toBe('₦0.00')
    expect(formatMoney(Number.POSITIVE_INFINITY)).toBe('₦0.00')
  })
})

describe('formatMoneyTick', () => {
  it('drops the kobo, rounding to the nearest naira', () => {
    expect(formatMoneyTick(1250000)).toBe('₦12,500')
    // ₦12,499.99 rounds up to ₦12,500 rather than truncating to ₦12,499.
    expect(formatMoneyTick(1249999)).toBe('₦12,500')
    expect(formatMoneyTick(1249949)).toBe('₦12,499')
  })
})

describe('toAmountInput', () => {
  it('writes kobo the way the form holds them, with no symbol or grouping', () => {
    expect(toAmountInput(250050)).toBe('2500.50')
    expect(toAmountInput(250000)).toBe('2500.00')
    expect(toAmountInput(5)).toBe('0.05')
    expect(toAmountInput(8590000)).toBe('85900.00')
  })
})

describe('formatDate', () => {
  it('writes a date the way a person reads it', () => {
    expect(formatDate('2026-03-12')).toBe('12 Mar 2026')
  })

  it('does not shift the day for anyone west of UTC', () => {
    // new Date("2026-01-01") is UTC midnight, which renders as 31 Dec in any
    // negative-offset timezone. String parsing is why this one is stable.
    expect(formatDate('2026-01-01')).toBe('1 Jan 2026')
  })

  it('passes through anything it cannot parse rather than inventing a date', () => {
    expect(formatDate('not a date')).toBe('not a date')
  })
})

describe('formatMonth', () => {
  it('names the month', () => {
    expect(formatMonth('2026-03')).toBe('Mar 2026')
  })

  it('passes through anything it cannot parse', () => {
    expect(formatMonth('2026-13')).toBe('2026-13')
  })
})
