/**
 * The API's shapes.
 *
 * These are not written by hand: `npm run gen:types` reads the OpenAPI document
 * FastAPI publishes and regenerates schema.d.ts from it, so these cannot drift
 * from the server. Editors use them for autocomplete on every API call below.
 *
 * @typedef {import('./schema').components['schemas']['ExpenseResponse']} ExpenseResponse
 * @typedef {import('./schema').components['schemas']['ExpenseRequest']} ExpenseRequest
 * @typedef {import('./schema').components['schemas']['ExpenseUpdatedRequest']} ExpenseUpdatedRequest
 * @typedef {import('./schema').components['schemas']['CreateExpenseResponse']} CreateExpenseResponse
 * @typedef {import('./schema').components['schemas']['DeleteAllResponse']} DeleteAllResponse
 * @typedef {import('./schema').components['schemas']['MessageResponse']} MessageResponse
 * @typedef {import('./schema').components['schemas']['LoginResponse']} LoginResponse
 * @typedef {import('./schema').components['schemas']['SessionResponse']} SessionResponse
 * @typedef {import('./schema').components['schemas']['UserResponse']} UserResponse
 * @typedef {import('./schema').components['schemas']['TopMonthResponse']} TopMonthResponse
 * @typedef {import('./schema').components['schemas']['TopDayResponse']} TopDayResponse
 * @typedef {import('./schema').components['schemas']['DailyTotalResponse']} DailyTotalResponse
 * @typedef {import('./schema').components['schemas']['FrequencyResponse']} FrequencyResponse
 * @typedef {import('./schema').components['schemas']['ChartFragmentResponse']} ChartFragmentResponse
 * @typedef {import('./schema').components['schemas']['ValidationError']} ValidationError
 */

export {}
