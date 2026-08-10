### ABC allows us to create an abstract base class.


#### 3. What does this mean?
class ExpenseRepository(ABC):


It means:

"ExpenseRepository is an abstract base class."

And Python's abc system can use that class to enforce rules on subclasses.

For example:

class JsonExpenseRepository(ExpenseRepository):
    ...

The idea is that JsonExpenseRepository must satisfy the repository contract.



 



So these two pieces have different jobs:

ABC
 ↓
"This is an abstract base class."

@abstractmethod
 ↓
"This method must be implemented by concrete subclasses."


##### An abstract base class is a parent class that defines a general structure/contract for other classes, without necessarily providing the complete implementation itself.



When Python sees:

@abstractmethod
def save(self, expense):
    pass

the @abstractmethod is telling Python:

"Mark this method as abstract."

In other words:

"This method is part of the contract, but this class does not provide the actual implementation."
- "This operation is required; child classes are responsible for providing the actual behavior."

does not mean:

"Here is how save() works."

It means:

"Any concrete subclass must provide how save() works."

### instantiate

It means create an object from a class.




The key idea

Dependency injection doesn't mean "passing an argument."

The deeper idea is:

A component receives its dependencies from outside instead of constructing those dependencies itself.







Then we'll have to solve interesting questions:

How do we find the next ID?
What happens after deleting ID 2?
Should IDs be reused?
What if the application crashes while creating an ID?
What happens if two processes generate an ID simultaneously?
Should the model or repository generate it?
Why shouldn't we use the array/list index as the ID?

Those are real software-engineering questions, not just syntax.

Then when we move to SQLite and the database says:

"I'll generate the ID for you."

you'll understand why databases have mechanisms such as auto-incrementing/identity columns rather than simply treating them as magic.

And later, when we introduce UUIDs, you'll understand why a system might choose:


#### This is called a race condition.