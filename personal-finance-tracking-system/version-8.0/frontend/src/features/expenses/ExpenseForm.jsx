import { useId, useState } from 'react'

import { CATEGORIES, PAYMENT_TYPES } from '../../api/constants'
import { toAmountInput, today } from '../../lib/money'
import { validateExpense } from './validation'

/**
 * The empty expense, as the form holds it: everything a string, because that
 * is what an input gives back.
 *
 * @param {import('../../api/types').ExpenseResponse | null} expense
 */
function blankFields(expense) {
  if (expense === null) {
    return {
      name: '',
      amount: '',
      date: today(),
      category: CATEGORIES[0],
      payment_type: PAYMENT_TYPES[0],
      merchant: '',
      note: '',
    }
  }

  return {
    name: expense.name,
    // Back to naira for the input, because that is what the user typed and
    // what they are being asked to edit. The round trip is exact: the parse
    // this feeds is the inverse, so saving without touching the field cannot
    // move the amount by a kobo.
    amount: toAmountInput(expense.amount_cents),
    date: expense.date,
    category: expense.category,
    payment_type: expense.payment_type,
    merchant: expense.merchant ?? '',
    note: expense.note ?? '',
  }
}

/**
 * Add or edit one expense.
 *
 * One component for both, because the fields, the rules and the layout are
 * the same — only the endpoint and the button label differ, and those are the
 * caller's business.
 *
 * @param {object} props
 * @param {import('../../api/types').ExpenseResponse | null} [props.initial]
 * @param {(values: object) => Promise<void>} props.onSubmit
 * @param {() => void} props.onCancel
 * @param {Record<string, string>} [props.serverErrors]  field errors the API returned
 * @param {boolean} [props.busy]
 */
export function ExpenseForm({
  initial = null,
  onSubmit,
  onCancel,
  serverErrors = {},
  busy = false,
}) {
  const prefix = useId()
  const [fields, setFields] = useState(() => blankFields(initial))
  const [errors, setErrors] = useState(/** @type {Record<string, string>} */ ({}))

  const editing = initial !== null

  // The server's own field errors win over anything derived here: it is the
  // authority, and if it disagrees with this form the form is what's wrong.
  const shown = { ...errors, ...serverErrors }

  /** @param {string} field */
  function change(field) {
    return (event) => {
      const { value } = event.target
      setFields((current) => ({ ...current, [field]: value }))
    }
  }

  /** @param {React.FormEvent<HTMLFormElement>} event */
  async function handleSubmit(event) {
    event.preventDefault()

    if (busy) {
      return
    }

    const { errors: found, values } = validateExpense(fields)

    setErrors(found)

    if (Object.keys(found).length > 0) {
      return
    }

    await onSubmit(values)
  }

  /** @param {string} field @param {string} label */
  function errorFor(field, label) {
    if (shown[field] === undefined) {
      return null
    }

    return (
      <span className="field__error" id={`${prefix}-${field}-error`}>
        {shown[field]}
      </span>
    )
  }

  /** @param {string} field */
  function describedBy(field) {
    return shown[field] === undefined ? undefined : `${prefix}-${field}-error`
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      <div className="form__row">
        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-name`}>
            What was it for?
          </label>
          <input
            id={`${prefix}-name`}
            name="name"
            value={fields.name}
            onChange={change('name')}
            aria-invalid={shown.name !== undefined}
            aria-describedby={describedBy('name')}
          />
          {errorFor('name')}
        </div>

        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-amount`}>
            Amount
          </label>
          <input
            id={`${prefix}-amount`}
            name="amount"
            // Not type="number": its spinner and scroll-wheel behaviour
            // silently change an amount the user has already typed.
            inputMode="decimal"
            value={fields.amount}
            onChange={change('amount')}
            aria-invalid={shown.amount !== undefined}
            aria-describedby={describedBy('amount')}
          />
          {errorFor('amount')}
        </div>
      </div>

      <div className="form__row">
        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-date`}>
            Date
          </label>
          <input
            id={`${prefix}-date`}
            name="date"
            type="date"
            value={fields.date}
            onChange={change('date')}
            aria-invalid={shown.date !== undefined}
            aria-describedby={describedBy('date')}
          />
          {errorFor('date')}
        </div>

        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-category`}>
            Category
          </label>
          <select
            id={`${prefix}-category`}
            name="category"
            value={fields.category}
            onChange={change('category')}
            aria-invalid={shown.category !== undefined}
            aria-describedby={describedBy('category')}
          >
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          {errorFor('category')}
        </div>

        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-payment_type`}>
            Paid with
          </label>
          <select
            id={`${prefix}-payment_type`}
            name="payment_type"
            value={fields.payment_type}
            onChange={change('payment_type')}
            aria-invalid={shown.payment_type !== undefined}
            aria-describedby={describedBy('payment_type')}
          >
            {PAYMENT_TYPES.map((paymentType) => (
              <option key={paymentType} value={paymentType}>
                {paymentType}
              </option>
            ))}
          </select>
          {errorFor('payment_type')}
        </div>
      </div>

      <div className="form__row">
        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-merchant`}>
            Where <span className="field__hint">optional</span>
          </label>
          <input
            id={`${prefix}-merchant`}
            name="merchant"
            value={fields.merchant}
            onChange={change('merchant')}
            aria-describedby={describedBy('merchant')}
          />
          {errorFor('merchant')}
        </div>

        <div className="field">
          <label className="field__label" htmlFor={`${prefix}-note`}>
            Note <span className="field__hint">optional</span>
          </label>
          <input
            id={`${prefix}-note`}
            name="note"
            value={fields.note}
            onChange={change('note')}
            aria-describedby={describedBy('note')}
          />
          {errorFor('note')}
        </div>
      </div>

      <div className="form__actions">
        <button type="submit" className="button" disabled={busy}>
          {busy
            ? 'Saving…'
            : editing ? 'Save changes' : 'Add expense'}
        </button>
        <button
          type="button"
          className="button button--secondary"
          onClick={onCancel}
          disabled={busy}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
