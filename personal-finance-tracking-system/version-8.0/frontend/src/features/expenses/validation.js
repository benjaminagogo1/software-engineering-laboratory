/**
 * The rules an expense form has to satisfy before it is sent.
 *
 * These mirror the server's, not replace them: the API validates every one of
 * these again and is the only thing that actually enforces them. The point of
 * doing it here is that a user who leaves the amount blank finds out instantly
 * rather than after a round trip.
 *
 * The option lists come from api/constants.js, which tests/test_frontend_contract.py
 * pins to app/models/expense.py — so a select can never offer a value the
 * server would reject.
 */

import { CATEGORIES, MAX_AMOUNT_CENTS, PAYMENT_TYPES } from '../../api/constants'
import { formatMoney } from '../../lib/money'

/** A blank optional field is stored as NULL, never as an empty string. */
function blankToNull(value) {
  const trimmed = value.trim()

  return trimmed === '' ? null : trimmed
}

/**
 * "2500.50" -> 250050 kobo, or null when the text is not an amount.
 *
 * Built from the string's own digits rather than `Number(raw) * 100`. That
 * expression is the whole reason this function is written out longhand:
 * `10.10 * 100` is 1009.9999999999999, so the form would send a kobo less than
 * the user typed — and no rounding step hides that reliably, because the error
 * depends on which decimal the user happened to pick. Splitting on the point
 * and padding the fraction never leaves the integers.
 *
 * At most two decimals, and a third is refused rather than rounded away:
 * quietly turning 10.005 into 1000 kobo loses the user's money and tells them
 * nothing. A leading "-" is accepted here and rejected as non-positive below,
 * because "not a number" and "not an amount" deserve different sentences.
 *
 * @param {string} raw
 * @returns {number | null} kobo, or null when the text is not an amount
 */
function parseAmountCents(raw) {
  const match = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(raw)

  if (match === null) {
    return null
  }

  const [, sign, whole, fraction = ''] = match
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, '0'))

  // A number the double cannot hold exactly is not one to send as an amount.
  // The ceiling below is far inside this range, so this is a backstop for
  // absurd input rather than a rule anyone should reach.
  if (!Number.isSafeInteger(cents)) {
    return null
  }

  return sign === '-' ? -cents : cents
}

/**
 * @typedef {object} ExpenseFields
 * @property {string} name
 * @property {string} amount    as typed, in naira — a string, not a number
 * @property {string} date
 * @property {string} category
 * @property {string} payment_type
 * @property {string} merchant
 * @property {string} note
 *
 * @typedef {object} ExpenseFormResult
 * @property {Record<string, string>} errors  empty when the fields are good
 * @property {object} values  what to send, with amount parsed and blanks nulled
 */

/**
 * @param {ExpenseFields} fields
 * @returns {ExpenseFormResult}
 */
export function validateExpense(fields) {
  /** @type {Record<string, string>} */
  const errors = {}

  const name = fields.name.trim()

  if (name === '') {
    errors.name = 'Enter what this expense was for.'
  }

  const raw = fields.amount.trim()
  const amountCents = parseAmountCents(raw)

  if (raw === '') {
    errors.amount = 'Enter an amount.'
  } else if (amountCents === null) {
    // Also catches "1,000" and "₦2,500" — the symbol and the grouping are
    // presentation, and the server takes a bare number.
    errors.amount = 'Enter a number, for example 2500 or 2500.50.'
  } else if (amountCents <= 0) {
    errors.amount = 'Amount must be greater than zero.'
  } else if (amountCents > MAX_AMOUNT_CENTS) {
    errors.amount = `Amount cannot be more than ${formatMoney(MAX_AMOUNT_CENTS)}.`
  }

  const date = fields.date.trim()

  if (date === '') {
    errors.date = 'Enter a date.'
  } else if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    errors.date = 'Use the date picker to choose a date.'
  }

  if (!CATEGORIES.includes(fields.category)) {
    errors.category = 'Choose a category.'
  }

  if (!PAYMENT_TYPES.includes(fields.payment_type)) {
    errors.payment_type = 'Choose a payment type.'
  }

  return {
    errors,
    values: {
      name,
      amount_cents: amountCents,
      date,
      category: fields.category,
      payment_type: fields.payment_type,
      merchant: blankToNull(fields.merchant),
      note: blankToNull(fields.note),
    },
  }
}
