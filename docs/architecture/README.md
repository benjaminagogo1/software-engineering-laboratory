                    SOFTWARE ENGINEERING LABORATORY
                               │
                               ▼
                    PERSONAL FINANCE SYSTEM
                               │
          ┌────────────────────┴────────────────────┐
          │                                         │
       LEARNING                                  BUILDING
          │                                         │
          ▼                                         ▼
      Concepts                                  System
          │                                         │
          └──────────────────┬──────────────────────┘
                             ▼
                           V1
                   Working monolithic system
                             │
                             ▼
                           V2
                    Modular architecture
                             │
                             ▼
                           V3
                 Layered/domain architecture
                             │
                             ▼
                           V4
              Repository abstraction + DI
                             │
                             ▼
                           V5
       Polymorphism + persistence + IDs + testing
                             │
                             ▼
                  ┌─────────────────────┐
                  │ FUTURE EXPERIMENTS  │
                  └─────────────────────┘
                             │
            ┌────────────────┼─────────────────┐
            ▼                ▼                 ▼
           V6               V7                V8
        Database          Logging           Testing
            │
            ▼
           V9
      CLI / Containerization
            │
            ▼
          V10
       Deployment
            │
            ▼
          V11
           API
            │
            ▼
       Production System





                    ┌──────────────────────┐
                    │     Interfaces       │
                    │                      │
                    │ CLI / REST API / ... │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Services        │
                    │                      │
                    │  Business Logic      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Repositories      │
                    │                      │
                    │ Persistence Contract │
                    └──────────┬───────────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
               SQL Database       Other Storage





               V7 — Logging
version-7.0/
├── app/
├── models/
├── repositories/
├── services/
├── storage/
├── ui/
├── logs/
├── config.py
├── main.py
└── README.md




V8 — Testing


version-8.0/
├── app/
├── models/
├── repositories/
├── services/
├── storage/
├── ui/
├── tests/
├── config.py
├── main.py
└── README.md



V9 — CLI + Docker
version-9.0/
├── app/
├── models/
├── repositories/
├── services/
├── storage/
├── cli/
├── tests/
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── config.py
├── main.py
└── README.md


V10 — Deployment
version-10.0/
├── app/
├── models/
├── repositories/
├── services/
├── storage/
├── cli/
├── tests/
├── Dockerfile
├── .dockerignore
├── .env.example
├── requirements.txt
├── config.py
├── main.py
└── README.md




V11 — API DEPLOY FOR REAL-USERS

version-11.0/
├── app/
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── storage/
│   └── config.py
├── tests/
├── Dockerfile
├── .dockerignore
├── .env.example
├── requirements.txt
├── main.py
└── README.md



V1
Basic Python
   ↓
V2
Better program structure
   ↓
V3
OOP / domain model
   ↓
V4
Repository / service separation
   ↓
V5
Persistence + architecture + error boundaries
   ↓
V6
Automated testing
   ↓
V7
SQLite database
   ↓
V8
REST API
   ↓
V9
PostgreSQL
   ↓
V10+
Production-level concerns





V5
│
├── Domain model
├── Repository abstraction
├── Abstract Base Classes
├── Concrete repositories
├── Dependency Injection
├── Service layer
├── UI layer
├── Result objects / enums
├── Validation
├── Input parsing
├── JSON persistence
├── Custom exceptions
├── Exception translation
├── Exception chaining
└── Dependency direction



JsonExpenseRepository
MemoryExpenseRepository
SqlExpenseRepository
PostgresExpenseRepository





OOP/model → Expense
Abstraction → ExpenseRepository(ABC)
Inheritance → JsonExpenseRepository(ExpenseRepository)
Method overriding → repository implementations
Polymorphism → ExpenseService works through the repository abstraction
Dependency injection → ExpenseService(repository)
Repository pattern → persistence separated from business logic
Serialization/deserialization → Expense ↔ dict ↔ JSON
CRUD → add, find, update, delete
ID generation → repository determines the next ID
Persistence → data survives program termination
State synchronization → loading from JSON before operations
CLI/application layers → UI → service → repository → storage





                  main.py
                     │
                     ▼
              ExpenseService
                     │
                     │ dependency
                     ▼
             ExpenseRepository
                     ▲
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
JsonExpenseRepository   Future SqlExpenseRepository
          │
          ▼
      JsonStorage
          │
          ▼
    expense.json




    Version 1
Programming

↓

Version 2
Modular Programming

↓

Version 3
Data Modeling

↓

Version 4
Object-Oriented Design

↓

Version 5
Testing

↓

Version 6
Database

↓

Version 7
REST API

↓

Version 8
Authentication

↓

Version 9
Docker

↓

Version 10
Deployment

↓

Production






personal-finance-tracking-system/
│
├── backend/
│
├── frontend/
│
├── mobile/
│
├── database/
│
├── docs/
│
├── docker/
│
├── tests/
│
├── scripts/
│
├── .github/
│
├── README.md
│
├── LICENSE
│
└── CONTRIBUTING.md




version-14.0/
│
├── backend/
├── frontend/
├── database/
├── docker/
├── nginx/
├── tests/
├── docs/
├── CI/
└── README.md





Browser
       ↓
HTML
CSS
JavaScript
       ↓
FastAPI Backend
       ↓
Database



version-12.0/
│
├── app/
├── auth/
├── api/
├── database/
└── README.md



version-11.0/
│
├── app/
│
├── api/
│   ├── routes.py
│   └── schemas.py
│
├── main.py
└── README.md



version-10.0/
│
├── app/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md


version-9.0/
│
├── app/
├── cli/
│   └── commands.py
├── tests/
└── README.md


version-8.0/
│
├── app/
├── tests/
│   ├── test_tracker.py
│   ├── test_storage.py
│   └── test_models.py
│
├── main.py
└── README.md


version-7.0/
│
├── app/
├── logs/
│   └── app.log
├── config.py
├── tests/
├── main.py
└── README.md


































































Version 1.0 — Monolithic Application

Goal: Learn Python fundamentals and OOP.

version-1.0/
│
├── main.py
├── expense.json
└── README.md

Topics learned:

Classes
Objects
Methods
Lists
CRUD
JSON
File handling
OOP basics
Version 2.0 — Modular Project

Goal: Learn project organization.

version-2.0/
│
├── main.py
├── models.py
├── tracker.py
├── menus.py
├── storage.py
├── utils.py
├── data/
│   └── expense.json
└── README.md

Topics:

Modules
Imports
Separation of concerns
Code organization
Version 3.0 — Packages

Instead of many files together:

version-3.0/
│
├── main.py
├── models/
│   ├── __init__.py
│   └── expense.py
│
├── services/
│   ├── __init__.py
│   └── tracker.py
│
├── storage/
│   ├── __init__.py
│   └── json_storage.py
│
├── ui/
│   ├── __init__.py
│   └── menus.py
│
├── utils/
│   ├── __init__.py
│   └── helpers.py
│
├── data/
│   └── expense.json
└── README.md

New concepts:

Packages
__init__.py
Absolute imports
Relative imports
Version 4.0 — Real Architecture
version-4.0/
│
├── app/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   ├── storage/
│   ├── ui/
│   └── utils/
│
├── data/
├── tests/
├── main.py
└── README.md

New concepts:

Repository Pattern
Layers
Application architecture
Version 5.0 — Database

Goodbye JSON.

version-5.0/
│
├── app/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── database/
│   │   ├── connection.py
│   │   └── schema.py
│   └── ui/
│
├── database/
│   └── expenses.db
│
├── tests/
├── main.py
└── README.md

Now you'll learn:

SQLite
SQL
CRUD with databases
Version 6.0 — Configuration
version-6.0/
│
├── app/
├── config.py
├── .env
├── .gitignore
├── requirements.txt
├── tests/
├── data/
└── README.md

New topics:

Environment variables
Configuration management
Dependency management
Version 7.0 — Logging
version-7.0/
│
├── app/
├── logs/
│   └── app.log
├── config.py
├── tests/
├── main.py
└── README.md

Learn:

Logging
Debugging
Monitoring
Version 8.0 — Testing
version-8.0/
│
├── app/
├── tests/
│   ├── test_tracker.py
│   ├── test_storage.py
│   └── test_models.py
│
├── main.py
└── README.md

Learn:

Unit testing
Assertions
Test-driven thinking
Version 9.0 — Command Line Application

Instead of interactive menus:

finance add Rice 2500
finance search Rice
finance delete Rice

Structure:

version-9.0/
│
├── app/
├── cli/
│   └── commands.py
├── tests/
└── README.md
Version 10.0 — Docker
version-10.0/
│
├── app/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
Version 11.0 — REST API

Now your application stops being just a local program.

version-11.0/
│
├── app/
│
├── api/
│   ├── routes.py
│   └── schemas.py
│
├── main.py
└── README.md

Technology:

FastAPI

Now people can use:

POST /expenses
GET /expenses
DELETE /expenses
Version 12.0 — Authentication
version-12.0/
│
├── app/
├── auth/
├── api/
├── database/
└── README.md

Now every user has their own account.

Version 13.0 — Web Frontend
Browser
       ↓
HTML
CSS
JavaScript
       ↓
FastAPI Backend
       ↓
Database
Version 14.0 — Production
version-14.0/
│
├── backend/
├── frontend/
├── database/
├── docker/
├── nginx/
├── tests/
├── docs/
├── CI/
└── README.md

Topics:

Docker Compose
Nginx
Deployment
CI/CD
GitHub Actions
Final Version — Personal Finance Tracking System
personal-finance-tracking-system/
│
├── backend/
│
├── frontend/
│
├── mobile/
│
├── database/
│
├── docs/
│
├── docker/
│
├── tests/
│
├── scripts/
│
├── .github/
│
├── README.md
│
├── LICENSE
│
└── CONTRIBUTING.md

This is no longer a learning project—it's a production application.