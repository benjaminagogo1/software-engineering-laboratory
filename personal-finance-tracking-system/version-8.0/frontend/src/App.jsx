import { Route, Routes } from 'react-router-dom'

import { RequireAuth } from './components/RequireAuth'
import { AppShell } from './components/AppShell'
import { NotFoundPage } from './features/NotFoundPage'
import { LoginPage } from './features/auth/LoginPage'
import { AnalyticsPage } from './features/analytics/AnalyticsPage'
import { ExpenseListPage } from './features/expenses/ExpenseListPage'
import { OverviewPage } from './features/overview/OverviewPage'

/**
 * The app's routes.
 *
 * Everything except /login sits behind RequireAuth, and the shell is a layout
 * route around them so the header does not unmount as the user moves between
 * sections.
 */
export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<OverviewPage />} />
        <Route path="/expenses" element={<ExpenseListPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>

      {/* Signed in or not, an unknown path is an unknown path. */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
