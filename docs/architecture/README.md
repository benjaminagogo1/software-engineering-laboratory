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