import { NavLink, Outlet } from 'react-router-dom'

import { UserMenu } from './UserMenu'

// Every entry here has a route behind it. Sections are added to this list in
// the same change that adds their page, so the nav never links to a dead end.
const SECTIONS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/expenses', label: 'Expenses', end: false },
  { to: '/analytics', label: 'Analytics', end: false },
]

/**
 * The frame every signed-in page sits in: navigation, who you are, and a way
 * out.
 *
 * Routes render through <Outlet>, so each page owns its own <h1> and the
 * shell stays out of the way of the content.
 */
export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-header__brand">Expense Tracker</span>

        <nav className="app-nav" aria-label="Sections">
          {SECTIONS.map((section) => (
            <NavLink
              key={section.to}
              to={section.to}
              end={section.end}
              className="app-nav__link"
            >
              {section.label}
            </NavLink>
          ))}
        </nav>

        <div className="app-header__user">
          <UserMenu />
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
