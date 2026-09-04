# Personal Finance Tracking System (Version 6.0)

## Overview

Version 6.0 replaces JSON-file storage with a real database (SQLite),
while keeping every layer above storage — repository interface, service,
UI — completely untouched. This is the payoff of the repository
abstraction introduced in v4: swapping the persistence mechanism is a
one-file change (`main.py`), not a rewrite.

It also introduces **environment-based configuration**, so settings like
the database path live outside the code instead of being hardcoded.

## What changed since v5.0

- **New: `app/storage/sqlite_storage.py`** — owns the raw SQLite
  connection and SQL statements. Knows nothing about `Expense` objects,
  only about rows. This mirrors the job `json_storage.py` did for JSON.
- **New: `app/repositories/sqlite_expense_repository.py`** — implements
  the same `ExpenseRepository` contract (`add`, `get_all`, `find_by_id`,
  `update`, `delete`) as `JsonExpenseRepository`, but talks to
  `SqliteStorage` instead of `JsonStorage`.
- **New: `config.py`** — reads settings from environment variables
  (via `.env`) instead of hardcoding paths in the code.
- **New: `.env` / `.env.example`** — `.env` holds the actual local
  settings and is gitignored; `.env.example` is the committed template
  showing what variables the app expects.
- **Changed: `main.py`** — now builds a `SqliteExpenseRepository`
  instead of a `JsonExpenseRepository`. `ExpenseService` and every menu
  function are imported and used exactly as before.
- **Unchanged:** `models/expense.py`, `repositories/expense_repository.py`,
  `repositories/memory_expense_repository.py`, `services/`, `ui/`.

## Why the repository pattern matters here

`ExpenseService` depends only on the `ExpenseRepository` interface, not
on any concrete storage class:

```python
class ExpenseService:
    def __init__(self, repository: ExpenseRepository):
        self.repository = repository
```

Because of that, going from JSON to SQLite required zero changes to
`ExpenseService`, zero changes to the UI, and zero changes to the tests
you'd write against the service. Only one new class was needed
(`SqliteExpenseRepository`), and one line in `main.py` changed to use it.
This is the concrete benefit of coding to an abstraction instead of a
concrete class — a decision made back in v4 pays off here in v6.

## Why environment variables

Hardcoding `"data/expense.db"` inside the repository class would tie the
code to one specific environment. Reading it from `os.getenv("DB_PATH", ...)`
means:

- The same code can point at a different database path (or later, a
  different database entirely) per environment (dev, test, prod)
  without editing source files.
- Secrets or environment-specific values never need to be committed —
  `.env` is gitignored, only `.env.example` (with placeholder values)
  is tracked in git.

## Project Structure

```text
version-6.0/
├── app/
│   ├── models/
│   │   └── expense.py
│   ├── repositories/
│   │   ├── expense_repository.py          # ABC contract
│   │   ├── json_expense_repository.py      # not used by main.py anymore
│   │   ├── memory_expense_repository.py
│   │   └── sqlite_expense_repository.py    # new
│   ├── services/
│   │   ├── expense_service.py
│   │   └── results.py
│   ├── storage/
│   │   ├── storage_error.py
│   │   └── sqlite_storage.py               # new
│   └── ui/
│       ├── input_helpers.py
│       └── menus.py
├── data/
│   └── expense.db          # created automatically on first run
├── .env                     # local settings (gitignored)
├── .env.example             # committed template
├── .gitignore
├── config.py                 # new
├── requirements.txt           # new
└── main.py
```

## How to Run

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example environment file (or just keep the provided `.env`):

   ```bash
   cp .env.example .env
   ```

3. Run:

   ```bash
   python main.py
   ```

The `expenses` table and the `data/expense.db` file are created
automatically the first time the app runs — no manual setup needed.

## Learning Objectives

- Reading and writing to a real relational database with the built-in
  `sqlite3` module (no ORM yet — that's a natural next experiment).
- Seeing dependency inversion pay off: the service and UI layers didn't
  need to know storage changed.
- Managing configuration through environment variables with
  `python-dotenv`, and the convention of committing `.env.example`
  instead of `.env`.
- Keeping database access wrapped in a dedicated `StorageError` so the
  UI layer only ever deals with one exception type, regardless of
  whether the underlying failure came from a corrupted JSON file or a
  broken database connection.

## What's still missing (candidates for v7+)

- No logging yet — failures print to the console but aren't recorded
  anywhere (that's the plan for v7).
- No automated tests (v8).
- `JsonExpenseRepository` and `MemoryExpenseRepository` are kept in the
  codebase for reference/comparison but are no longer wired into `main.py`.
