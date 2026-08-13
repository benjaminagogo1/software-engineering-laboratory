7. This is called serialization

The process:

Python object
      ↓
JSON-compatible representation
      ↓
JSON



And the reverse:

JSON
 ↓
Python data
 ↓
Python object

is called deserialization.

So our Repository is currently doing something like:

        DESERIALIZATION
JSON ─────────────────────► Expense
                 

        SERIALIZATION
Expense ──────────────────► JSON






┌─────────────────────────────┐
│ UI                          │
│ User input validation       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Service                     │
│ Business operations         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Model                       │
│ What makes an Expense valid │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Repository                  │
│ Persistence / retrieval     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Storage                     │
│ JSON file I/O               │
└─────────────────────────────┘





Encapsulation means, broadly:

Controlling how an object's internal state can be accessed or changed.

Our current class is very open:

expense.id
expense.name
expense.amount

Anyone can directly modify everything.

That's fine for a tiny beginner model.


CRUD
 ↓
Architecture
 ↓
Persistence
 ↓
State
 ↓
Serialization
 ↓
Validation
 ↓
Domain rules
 ↓
Invariants
 ↓
Encapsulation
 ↓
Concurrency

CRUD
 ↓
Architecture
 ↓
Persistence
 ↓
State
 ↓
Serialization
 ↓
Validation
 ↓
Domain rules
 ↓
Invariants
 ↓
Encapsulation
 ↓
Concurrency




The same interface:

repository.add(...)

can cause different implementations to execute depending on the actual repository object.

That's polymorphism.


#### Polymorphism means:

One interface, many possible forms/implementations.




                 ExpenseRepository
                  (abstraction)
                       ▲
                       │
             ┌─────────┴─────────┐
             │                   │
             │                   │
             ▼                   ▼
   JsonExpenseRepository   SqlExpenseRepository
             │                   │
             │                   │
             ▼                   ▼
        JSON storage        SQL database







                         ExpenseService
                       │
                       │
              repository.add()
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
      JsonRepository        SqlRepository
             │                   │
             ▼                   ▼
          JSON file           Database



          Inheritance
      ↓
JsonExpenseRepository
      ↓
overrides repository methods
      ↓
abstraction defines contract
      ↓
polymorphism allows Service
to work with different implementations




Inheritance is one mechanism through which polymorphism can be achieved.




There's a beautiful way to think about it

The Service says:

"I don't care HOW you add an expense. Just give me something that behaves as an ExpenseRepository."

The concrete repository says:

"I'll decide how to do it."

So:

              Service
                 │
                 │ "add this expense"
                 ▼
        ExpenseRepository
          (contract)
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
      JSON     SQL     Memory

This is polymorphism in architecture, not merely an OOP trick.






11. So we now have four concepts connected

This is worth remembering:

Inheritance
class JsonExpenseRepository(ExpenseRepository):

means the child derives from the parent.

Abstraction
class ExpenseRepository(ABC):

defines the contract without prescribing the storage implementation.

Method overriding
def add(self, expense):

in the child supplies the concrete implementation.

Polymorphism
self.repository.add(expense)

allows the same Service code to work with different repository implementations.

They work together, but they are not synonyms.





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



Inheritance
     ↓
Abstraction
     ↓
Method overriding
     ↓
Polymorphism
     ↓
Dependency injection
     ↓
Loose coupling



version-5.0/
│
├── app/
│   ├── models/
│   │   └── expense.py
│   │
│   ├── repositories/
│   │   ├── expense_repository.py
│   │   └── json_expense_repository.py
│   │
│   ├── services/
│   │   └── expense_service.py
│   │
│   ├── storage/
│   │   └── json_storage.py
│   │
│   └── ui/
│       └── menus.py
│
├── data/
│   └── expense.json
│
└── main.py


CURRENT
   │
   ▼
Finish the application flow
   │
   ├── proper menu behavior
   ├── input handling
   ├── error handling
   └── clean Service/UI interaction
   │
   ▼
Improve Repository behavior
   │
   ├── consistent return values
   ├── update/delete semantics
   └── persistence consistency
   │
   ▼
Complete the domain model
   │
   └── only the fields/rules actually belonging to V5
   │
   ▼
Test the whole application
   │
   ▼
Refactor where necessary
   │
   ▼
Concurrency
   │
   ├── careful read-modify-write
   ├── file locks
   ├── process locks
   └── atomic file replacement
   │
   ▼
V5 COMPLETE




                 ┌──────────────┐
                 │      UI      │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │   Service    │
                 └──────┬───────┘
                        ↓
              ┌────────────────────┐
              │ ExpenseRepository  │
              │    (abstraction)   │
              └─────────┬──────────┘
                        ↑
              ┌─────────┴──────────┐
              │                    │
       JsonExpenseRepository   Future repository
              │
              ↓
        ┌────────────┐
        │ JsonStorage│
        └─────┬──────┘
              ↓
        expense.json




                      ExpenseRepository
              (public contract)
                    │
        ┌───────────┴───────────┐
        │                       │
      add()                  delete()
      update()               find_by_id()
      get_all()
                    │
                    ▼
          JsonExpenseRepository
                    │
              internal save()
                    │
                    ▼
             JsonStorage
                    │
                    ▼
             expense.json


    



                 USER
                   │
                   ▼
                  UI
                   │
                   │ Expense object
                   ▼
               SERVICE
                   │
                   │ add(expense)
                   ▼
              REPOSITORY
                   │
          ┌────────┴────────┐
          │                 │
      get_all()         assign ID
          │                 │
          └────────┬────────┘
                   │
                   ▼
             self.expenses
                   │
                   │ save()
                   ▼
               STORAGE
                   │
                   │ json.dump()
                   ▼
              expense.json



### delete a particular file

> data/expense.json






Service                         UI

UpdateResult.SUCCESS       →    "Expense updated successfully."
UpdateResult.NOT_FOUND     →    "Expense not found."
UpdateResult.INVALID_AMOUNT →   "Amount must be greater than zero."