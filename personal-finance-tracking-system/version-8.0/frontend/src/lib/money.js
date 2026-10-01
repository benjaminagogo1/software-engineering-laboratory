/**
 * How money and dates are written out in the browser.
 *
 * Mirrors app/ui/formatting.py. Two interfaces that spell the same number
 * differently is a bug users notice, so the symbol and the grouping rule are
 * the same here as they are in the CLI.
 *
 * The money functions take **kobo**, the integer minor unit the API and the
 * database deal in, and none of them divides by 100 to get there — the split is
 * `Math.trunc` and `%` on an integer. `cents / 100` would put a float back into
 * the last step of a path whose whole point is that no float touches the
 * number, and the rounding would simply move from the ledger to the screen.
 *
 * Written by hand rather than with Intl.NumberFormat: ICU data varies between
 * browsers and Node builds, and a number that renders differently depending on
 * whose machine you are on is not something to discover in production.
 */

/** The naira sign. Swap this one constant to change the currency everywhere. */
export const CURRENCY_SYMBOL = '₦'

/**
 * Groups the integer part in threes without touching a locale database.
 *
 * @param {string} whole  digits only, no sign
 * @returns {string}
 */
function group(whole) {
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * ₦2,500.50 — grouped thousands, always two decimals.
 *
 * @param {number} amountCents
 * @returns {string}
 */
export function formatMoney(amountCents) {
  if (!Number.isFinite(amountCents)) {
    return `${CURRENCY_SYMBOL}0.00`
  }

  const cents = Math.trunc(amountCents)
  const sign = cents < 0 ? '-' : ''
  const whole = Math.trunc(Math.abs(cents) / 100)
  const fraction = String(Math.abs(cents) % 100).padStart(2, '0')

  return `${CURRENCY_SYMBOL}${sign}${group(String(whole))}.${fraction}`
}

/**
 * The compact form for an axis or a tile, where the kobo are noise:
 * ₦12,500 rather than ₦12,500.00.
 *
 * Rounds to the nearest naira rather than truncating, so ₦12,499.99 reads as
 * ₦12,500 — the same thing `toFixed(0)` did when this took naira.
 *
 * @param {number} amountCents
 * @returns {string}
 */
export function formatMoneyTick(amountCents) {
  if (!Number.isFinite(amountCents)) {
    return `${CURRENCY_SYMBOL}0`
  }

  const cents = Math.trunc(amountCents)
  const sign = cents < 0 ? '-' : ''
  const whole = Math.trunc((Math.abs(cents) + 50) / 100)

  return `${CURRENCY_SYMBOL}${sign}${group(String(whole))}`
}

/**
 * Kobo as a plain editable string: 250050 -> "2500.50".
 *
 * The inverse of the parser in features/expenses/validation.js, and
 * deliberately without the symbol or the thousands separators: this goes into a
 * text input, and the form has to be able to hand back exactly what it was
 * shown. Opening the edit form on ₦2,500.50 and saving it unchanged must not
 * move a kobo.
 *
 * @param {number} amountCents
 * @returns {string}
 */
export function toAmountInput(amountCents) {
  const cents = Math.trunc(amountCents)
  const sign = cents < 0 ? '-' : ''
  const whole = Math.trunc(Math.abs(cents) / 100)
  const fraction = String(Math.abs(cents) % 100).padStart(2, '0')

  return `${sign}${whole}.${fraction}`
}

const MONTHS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

/**
 * "2026-03-12" -> "12 Mar 2026".
 *
 * Parsed by hand rather than with `new Date(...)`: that constructor reads a
 * bare YYYY-MM-DD as UTC midnight, so anywhere west of Greenwich it renders
 * as the previous day — the classic off-by-one-day date bug.
 *
 * @param {string} iso
 * @returns {string}
 */
export function formatDate(iso) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)

  if (match === null) {
    return iso
  }

  const [, year, month, day] = match
  const name = MONTHS[Number(month) - 1]

  return name === undefined ? iso : `${Number(day)} ${name} ${year}`
}

/**
 * "2026-03" -> "March 2026".
 *
 * @param {string} month
 * @returns {string}
 */
export function formatMonth(month) {
  const match = /^(\d{4})-(\d{2})$/.exec(month)

  if (match === null) {
    return month
  }

  const [, year, index] = match
  const name = MONTHS[Number(index) - 1]

  return name === undefined ? month : `${name} ${year}`
}

/** @returns {string} today as "YYYY-MM-DD", in the user's own timezone. */
export function today() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')

  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/** @returns {string} this month as "YYYY-MM", in the user's own timezone. */
export function thisMonth() {
  return today().slice(0, 7)
}
