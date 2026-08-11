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