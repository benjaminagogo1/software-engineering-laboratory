/**
 * The API, named the way the app talks about it.
 *
 * Every path the client uses appears in this file exactly once, written as a
 * plain string literal. tests/test_frontend_contract.py reads them and checks
 * each one against the routes the server actually publishes, so a renamed
 * endpoint fails the Python suite rather than producing a 404 in the browser.
 */

import { api } from './client'

export const auth = {
  /**
   * @param {{username: string, password: string}} credentials
   * @returns {Promise<import('./types').UserResponse>}
   */
  register: (credentials) => api.post('/register', credentials),

  /**
   * Sets the httpOnly session cookie and returns the CSRF token to echo on
   * every write from here on.
   *
   * @param {{username: string, password: string}} credentials
   * @returns {Promise<import('./types').LoginResponse>}
   */
  login: (credentials) => api.post('/login', credentials),

  /** @returns {Promise<import('./types').MessageResponse>} */
  logout: () => api.post('/logout'),

  /**
   * Who we are, and the CSRF token again — the client holds that in memory
   * only, so a page reload has to ask for it back.
   *
   * @returns {Promise<import('./types').SessionResponse>}
   */
  me: () => api.get('/me'),
}

export const expenses = {
  /** @returns {Promise<import('./types').ExpenseResponse[]>} */
  list: () => api.get('/expenses'),

  /**
   * @param {number} id
   * @returns {Promise<import('./types').ExpenseResponse>}
   */
  find: (id) => api.get(`/expenses/${id}`),

  /**
   * @param {import('./types').ExpenseRequest} expense
   * @returns {Promise<import('./types').CreateExpenseResponse>}
   */
  create: (expense) => api.post('/expenses', expense),

  /**
   * @param {number} id
   * @param {import('./types').ExpenseUpdatedRequest} changes
   * @returns {Promise<import('./types').MessageResponse>}
   */
  update: (id, changes) => api.put(`/expenses/${id}`, changes),

  /**
   * @param {number} id
   * @returns {Promise<import('./types').MessageResponse>}
   */
  remove: (id) => api.remove(`/expenses/${id}`),

  /** @returns {Promise<import('./types').DeleteAllResponse>} */
  removeAll: () => api.remove('/expenses'),

  /**
   * @param {string} name
   * @returns {Promise<import('./types').ExpenseResponse[]>}
   */
  search: (name) => api.get(`/expenses/search?name=${encodeURIComponent(name)}`),
}

export const analytics = {
  /** @returns {Promise<import('./types').TopMonthResponse>} */
  topMonth: () => api.get('/analytics/top-month'),

  /** @returns {Promise<import('./types').TopMonthResponse[]>} */
  months: () => api.get('/analytics/months'),

  /** @returns {Promise<import('./types').TopDayResponse>} */
  topDay: () => api.get('/analytics/top-day'),

  /** @returns {Promise<import('./types').ExpenseResponse>} */
  highest: () => api.get('/analytics/highest'),

  /** @returns {Promise<import('./types').ExpenseResponse>} */
  lowest: () => api.get('/analytics/lowest'),

  /**
   * @param {string} name
   * @returns {Promise<import('./types').FrequencyResponse>}
   */
  frequency: (name) => api.get(`/analytics/frequency?name=${encodeURIComponent(name)}`),

  /**
   * Sparse: days with no spending are absent rather than zero.
   *
   * @param {string} month  "YYYY-MM"
   * @returns {Promise<import('./types').DailyTotalResponse[]>}
   */
  daily: (month) => api.get(`/analytics/daily?month=${encodeURIComponent(month)}`),
}

export const reports = {
  /**
   * The monthly chart, rendered by the server as a stylesheet and a body
   * fragment rather than as a whole document — see features/analytics/MonthlyChart.
   *
   * @param {string} month  "YYYY-MM"
   * @returns {Promise<import('./types').ChartFragmentResponse>}
   */
  monthFragment: (month) =>
    api.get(`/reports/month.fragment?month=${encodeURIComponent(month)}`),
}
