# Expense Tracker

A personal finance tracker with three interfaces over one service layer:

| Interface | What it is | Where |
|---|---|---|
| **Web app** | React single-page app served by the API | `/app/` |
| **Terminal menu** | Numbered interactive menu | `python main.py` |
| **CLI** | `argparse` subcommands for scripting | `python main.py <command>` |
| **HTTP API** | REST + interactive docs | `/docs` |

All four share the same services (`app/services/`) and the same SQLite database.
The API and the terminal interfaces do not go through each other — each is a
thin front end over `ExpenseService` and `UserService`, so a rule only ever
needs to be written once.

---

## Requirements

- Python 3.12
- Node 22 and npm (only to build or develop the web client)

## Setup

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt

cp .env.example .env
# Then put a long random value in JWT_SECRET_KEY:
venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`JWT_SECRET_KEY` signs both the short-lived bearer tokens API clients use and
the browser's session cookie. The app will not mint a token without it — it
raises a message naming the variable rather than failing somewhere inside the
JWT library. The database is created on first run if it does not exist.

`COOKIE_SECURE` defaults to `true`, which is what production wants. **Set it to
`false` in `.env` if you are serving over plain http** (localhost, a LAN
address) — a `Secure` cookie is silently dropped by the browser over http, so
the login appears to succeed and then never persists.

---

## Running

### Web app

```bash
venv/bin/uvicorn app.api:app --reload --port 8000
```

Then open <http://localhost:8000/app/>. Register an account and you are in.
`/` redirects to `/app/`; `/docs` is the generated API documentation.

### Developing the web client

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on <http://localhost:5173/app/> and proxies every API prefix
through to `http://localhost:8000`, so the browser only ever sees one origin and
cookies behave exactly as they do in production. Run `uvicorn` alongside it.

`npm run build` writes `frontend/dist/`, which is what `uvicorn` serves. The
directory must exist for the SPA routes to work — `app/api.py` mounts it with
`StaticFiles(..., check_dir=False)` so importing the API does not depend on the
frontend having been built, but a request for `/app/` will 404 until it is.

### Terminal menu

```bash
venv/bin/python main.py
```

### CLI

```bash
venv/bin/python main.py register --username ben
venv/bin/python main.py add "Groceries" 24500 --category Food --payment-type Card
venv/bin/python main.py list --username ben
venv/bin/python main.py top-month --username ben
venv/bin/python main.py chart --month 2026-09
```

Commands: `register`, `login`, `add`, `list`, `get`, `update`, `delete`,
`delete-all`, `search`, `top-month`, `months`, `top-day`, `highest`, `lowest`,
`frequency`, `chart`. Everything except `register` and `login` takes
`--username`, and prompts for the password with `getpass` so it stays out of
your shell history. `chart` writes an HTML file to `reports/`.

---

## Logging and the audit trail

These are two different records with two different jobs, and conflating them is
how both end up useless.

**The operational log** — `logs/app.log`, and stdout — is for whoever is running
the software. One line per request, with the status, how long it took, and which
user made it; plus a line for each change a service makes. It rotates at
`LOG_MAX_BYTES` and keeps `LOG_BACKUP_COUNT` generations, and it is filtered by
`LOG_LEVEL`. It is *allowed* to be lossy, and it should be — nobody needs last
quarter's INFO lines.

**The audit trail** — the `audit_events` table — is for whoever has to say,
months later, who deleted what. It is append-only: `AuditRepository` has a
`record` and a `for_user` and deliberately no `update` and no `delete`, because
a trail with an edit method is a trail that can be made to agree with whatever
story is convenient. It is never rotated and never filtered by a level setting.

What it records:

| Action | When | Carried in `detail` |
|---|---|---|
| `user.registered` | an account is created | the username |
| `login.succeeded` | credentials are verified | the username |
| `login.failed` | credentials are rejected | the username, and whether the account existed |
| `logout` | a session ends | — |
| `expense.created` | an expense is added | name, amount, date, category |
| `expense.updated` | a field changes | only the changed fields, each as `{"from": ..., "to": ...}` |
| `expense.deleted` | an expense is removed | the whole row, since this is the last copy of it |
| `expenses.deleted_all` | an account is cleared | how many went |

Three things about it are deliberate and would be easy to "fix" wrongly:

- **A login is recorded in `authenticate`, not in `login`.** The terminal client
  calls `authenticate` and never touches `login`, so auditing the latter would
  leave the CLI as an unaudited way into an account. There is one place every
  surface passes through, and that is where the record is written.
- **The trail is at the service layer, not the API layer.** A route that built
  its own repository would bypass it entirely.
- **A failed audit write does not fail the request.** The expense is already
  saved by then; raising would tell the caller their create failed, and the
  retry would make a second one. The gap is logged at `ERROR` with the
  traceback — which is exactly what the operational log is for. Closing it
  properly means one transaction for both writes, which needs a unit of work
  this codebase does not have yet.

Read it directly — for anything across accounts, this is the only way:

```bash
sqlite3 data/expense.db \
  "SELECT happened_at, action, user_id, detail FROM audit_events ORDER BY id DESC LIMIT 20"
```

A user can read their own through `GET /audit`, newest first, bounded by
`?limit=` (default 50, max 200). The route takes no user id, and that is the
security property rather than a missing feature: every account's rows share one
table, so a route that could name a `user_id` would hand any account the history
of every other one. Reading across users is an operator's job, done against the
database where it can be logged and rate-limited properly.

---

## Tests

```bash
venv/bin/python -m pytest -q          # from the repository root
cd frontend && npm test               # the web client
```

The Python suite is the source of truth for behaviour: services, repositories,
migrations, the API, the report renderer, and a contract test that reads the
frontend's own source and checks every endpoint it calls against the routes the
server publishes.

The web client must be tested **from `frontend/`**, not from the repository root
— that is where its Vitest config lives.

No `.env` is needed for the suite: `tests/conftest.py` sets `JWT_SECRET_KEY` and
`COOKIE_SECURE` before it imports the app, so a fresh clone runs green.

### Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request, in three jobs:
the Python suite on 3.12 and 3.13, the frontend suite and build on Node 22, and
a `docker build` that then starts the image and waits for it to answer. The
Docker job is there because the image is the one artifact nothing else
exercises — a mistake in the stage that copies `frontend/dist/` produces a
container that starts and serves nothing.

---

## Docker

```bash
docker build -t expense-tracker .

docker run --rm -p 8000:8000 \
  -e JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  -e COOKIE_SECURE=false \
  -v expense-data:/app/data \
  expense-tracker
```

The image is built in two stages: Node compiles the client, then the Python
stage copies only `frontend/dist/` across, so the toolchain and `node_modules`
never reach the runtime image. The container runs `uvicorn` — the API and the
web client are one service on one port.

`COOKIE_SECURE=false` above is only correct because the container is being
reached over plain http. Behind TLS, leave it at its default of `true`.

---

## Layout

```
app/
  api.py              FastAPI app: routes, auth dependencies, the SPA mount,
                      and the request-logging middleware
  logging_config.py   the operational log: handlers, rotation, stdout, uvicorn
  auth/               password hashing, JWT minting/verification, cookie
                      helpers, the credential policy, the failure throttle
  models/             Expense, AuditEvent, CATEGORIES, PAYMENT_TYPES
  repositories/       in-memory and SQLite implementations of one interface
  services/           ExpenseService, UserService, result enums
  reports/            the monthly spending chart, rendered as HTML
  storage/            connection handling and schema migrations
  ui/                 terminal menus and formatting
cli/commands.py       argparse front end, shares the services with the menu
frontend/             the React client
tests/                pytest suite, including the frontend contract test
```

Migrations live in `app/storage/migrations/` and are applied in order on
connect; each is named `NNN_description.py`.

---

## Security notes

- **Sessions are httpOnly cookies**, never `localStorage` — a token in storage
  is readable by any script that gets injected into the page.
- **CSRF is a stateless double-submit.** The expected token is a `csrf` claim
  inside the signed session JWT, so validation needs no server-side store. Every
  mutating request must echo it in `X-CSRF-Token`.
- **Bearer tokens still work and are unaffected.** `Authorization: Bearer` is
  checked first and always beats an ambient cookie, which is why the CLI, curl
  and tests need no CSRF token — an attacker cannot set a header cross-site.
- **Passwords are hashed with argon2**, never stored or logged in the clear.
- **Guessing is throttled, not locked out.** Failures accumulate against a
  `(username, address)` pair (five free, then a delay that doubles to a
  15-minute cap) and against the address alone at a looser threshold. NIST
  SP 800-63B §5.2.2 prefers this to a hard lockout, and the address in the pair
  key is what stops an attacker locking a real user out of their own account.
  Never keyed on the username alone. `Retry-After` says how long to wait.
- **Passwords have a policy, and it is a length one.** Twelve characters
  minimum, 128 maximum, no composition rule — §5.1.1.2 recommends against them,
  because they produce `Password1!`. No expiry and no history, for the same
  reason. The rules live in `app/auth/policy.py` and are applied in the service,
  so the terminal client is bound by them too.
- **The audit trail is readable by the account it describes.** `GET /audit`
  returns the caller's own recent events and takes no user id — including the
  failed logins aimed at their account, which is how someone being targeted
  finds out.

### Known gaps

Honest list of what is not built yet, in rough order of how much it matters
before this faces the internet:

- **No server-side session revocation.** `POST /logout` clears the cookie; a
  copied token stays valid until it expires. Bounded by `SESSION_TTL_HOURS`.
- **The login throttle is in-process.** Counters live in a dict in the worker
  that saw the failure, so they reset on restart and are per-worker — two
  uvicorn workers means two independent limits. Behind more than one process
  this belongs in Redis or the database; it is worth doing at the same time as
  session revocation, since both want the same store.
- **The password policy is a shape check, not a breach lookup.** It refuses
  twelve characters or fewer and a short list of obvious ones. The real answer
  is a k-anonymity lookup against Have I Been Pwned's range API, which is a
  network call on the registration path and a deliberate decision rather than
  something to add by reflex — see the note at the end of `app/auth/policy.py`.
- **The API is unversioned** and its auth paths do not match the roadmap's
  `/users/register` and `/users/login`.
- **No CORS middleware**, and none is needed while the client is same-origin.
  It becomes necessary the moment another origin does.
