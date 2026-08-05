personal-finance-tracking-system/
│
├── main.py
│   Entry point of the application. Displays the main menu, handles user choices,
│   and coordinates the overall program flow.
│
├── models.py
│   Contains the application's data models (classes), such as the Expense class,
│   which represents an individual expense.
│
├── tracker.py
│   Contains the ExpenseTracker class. Responsible for all business logic such as
│   adding, searching, updating, deleting, and managing expenses.
│
├── menus.py
│   Contains all menu functions that interact with the user by collecting input,
│   displaying output, and calling the appropriate tracker methods.
│
├── storage.py
│   Handles data persistence, including saving expenses to and loading expenses
│   from the JSON file.
│
├── utils.py
│   Contains reusable helper functions such as input validation, formatting,
│   and other utility functions shared across the project.
│
├── data/
│   Stores the application's persistent data files.
│   │
│   └── expense.json
│       JSON file used to permanently store all expense records.
│
└── README.md
    Project documentation containing the project overview, features, installation
    instructions, usage guide, folder structure, and future improvements.