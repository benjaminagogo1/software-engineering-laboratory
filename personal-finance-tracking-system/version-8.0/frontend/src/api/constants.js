/**
 * The option lists the API accepts, mirroring CATEGORIES and PAYMENT_TYPES in
 * app/models/expense.py.
 *
 * The API declares these in its own schema (see ExpenseRequest in app/api.py),
 * so a select offering a value the server would reject is the failure mode
 * this has to avoid. tests/test_frontend_contract.py reads this file and fails
 * if the two lists ever disagree.
 */

export const CATEGORIES = [
  'Food',
  'Transport',
  'Bills',
  'Rent',
  'Health',
  'Entertainment',
  'Other',
]

export const PAYMENT_TYPES = [
  'Cash',
  'Card',
  'Transfer',
  'Mobile Money',
  'Other',
]

/**
 * The largest amount the API accepts, in kobo — mirrors MAX_AMOUNT_CENTS in
 * app/models/expense.py, and pinned by the same contract test as the lists
 * above. Checked in the form so the user hears about it before the round trip.
 */
export const MAX_AMOUNT_CENTS = 100000000000
