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




V11 — API

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