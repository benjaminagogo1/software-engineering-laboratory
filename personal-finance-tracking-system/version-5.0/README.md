7. This is called serialization

- The process:

- Python object
      ↓
- JSON-compatible representation
      ↓
- JSON



- And the reverse:

- JSON
 ↓
- Python data
 ↓
- Python object

- is called deserialization.

- So our Repository is currently doing something like:

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





## Encapsulation means, broadly:

- Controlling how an object's internal state can be accessed or changed.

- Our current class is very open:

- expense.id
- expense.name
- expense.amount

- Anyone can directly modify everything.

- That's fine for a tiny beginner model.


## CRUD
 ↓
- Architecture
 ↓
- Persistence
 ↓
- State
 ↓
- Serialization
 ↓
- Validation
 ↓
- Domain rules
 ↓
- Invariants
 ↓
- Encapsulation
 ↓
- Concurrency



- The same interface:

- repository.add(...)

can cause different implementations to execute depending on the actual repository object.

- That's polymorphism.


#### Polymorphism means:

### One interface, many possible forms/implementations.




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
-    JsonExpenseRepository
            ↓
-    overrides repository methods
            ↓
-    abstraction defines contract
            ↓
-    polymorphism allows Service
to work with different implementations




### Inheritance is one mechanism through which polymorphism can be achieved.




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

- This is polymorphism in architecture, not merely an OOP trick.






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



ExpenseRepository
       ↑
       ├── JsonExpenseRepository
       ├── SQLiteExpenseRepository
       └── PostgreSQLExpenseRepository






### QUESTIONS 

what is happenning here?

def get_all(self):
    data = self.storage.load()

    self.expenses = []

    for item in data:
        expense = Expense(
            item["id"],
            item["name"],
            item["amount"]
        )

        self.expenses.append(expense)

    return self.expenses



    ExpenseRepository
       │
       ├── add()
       ├── get_all()
       ├── find_by_id()
       ├── update()
       └── delete()
             ▲
             │
    MemoryExpenseRepository




                 ┌──────────────────┐
                 │       UI         │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  ExpenseService  │
                 │                  │
                 │ Business rules   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ ExpenseRepository│
                 │   (abstraction)  │
                 └────────┬─────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
   JsonExpenseRepository      MemoryExpenseRepository
             │                         │
             ▼                         ▼
       JsonStorage               Python list
             │
             ▼
       expense.json



### We've now actually used:

- abstraction
- inheritance
- abstract methods
- dependency injection
- polymorphism
- separation of concerns
- business validation
- persistence abstraction
- domain objects





### The architecture in terms of responsibility

Here's the most important table:


| Component                 | Main responsibility                  |
| ------------------------- | ------------------------------------ |
| `Expense`                 | Represents an expense                |
| UI / menus                | Talks to the user                    |
| `ExpenseService`          | Performs business operations/rules   |
| `ExpenseRepository`       | Defines persistence operations       |
| `JsonExpenseRepository`   | Persists expenses using JSON storage |
| `MemoryExpenseRepository` | Stores expenses in memory            |
| `JsonStorage`             | Reads/writes JSON                    |
| `expense.json`            | Persistent data                      |


## This is separation of concerns.



## Transactions

- Databases also provide transactions.

- A transaction lets multiple operations behave as one logical unit.




## 4. Locks / concurrency control

- Databases also have mechanisms for coordinating simultaneous operations.

Conceptually:

Process A
   ↓
database
   🔒
generate/write
   ↓
release


Process B
   ↓
database
   waits
   ↓
gets its own ID

The actual mechanisms are more sophisticated than simply "lock everything," but the fundamental idea is concurrency control.





#### What is a test case?

A test case is a specific situation we create to check whether one piece of software behaves as expected.


## This pattern is often called Arrange → Act → Assert.


## What is assert?

assert is a Python statement used to say:

"I expect this condition to be true."

For example:

assert 2 + 2 == 4

Python checks the condition:

2 + 2 == 4

It is true, so the program continues.

But:

assert 2 + 2 == 5

is false, so Python reports an AssertionError.




### pytest is a Python testing framework.

A testing framework is a tool that helps us organize, run, and report automated tests.

We already know how to write an expectation:

assert result == AddResult.SUCCESS

But imagine we eventually have:

test_add_expense
test_empty_name
test_invalid_amount
test_update_expense
test_delete_expense
test_find_expense
...

We need a tool that can:

find our tests
run them
tell us which passed
tell us which failed
show useful information when something fails

That's what pytest helps us do.

Without pytest

We could technically write Python code that calls our tests manually:

test_add_expense()
test_update_expense()
test_delete_expense()

But as the project grows, that becomes inconvenient.

With pytest

We can organize tests in test files, and then run:

pytest

pytest discovers the tests and runs them for us.

We might eventually see output like:

================ test session starts ================


tests/test_expense_service.py .....                  [100%]


5 passed


================= 5 passed in 0.12s =================

The exact output can vary.

The important idea is:

pytest is the tool that runs and reports our automated Python tests.

One important distinction

Don't confuse these three things:

assert

Python's built-in mechanism for checking a condition:

assert result == AddResult.SUCCESS
Test

The code we write to verify one particular behavior.

pytest

The tool that discovers and runs those tests.

So:

                 pytest
                   ↓
              runs tests
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
   test_add()            test_update()
        ↓                     ↓
      assert                 assert

