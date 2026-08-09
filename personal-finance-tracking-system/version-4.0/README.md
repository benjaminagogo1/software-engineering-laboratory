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


does not mean:

"Here is how save() works."

It means:

"Any concrete subclass must provide how save() works."