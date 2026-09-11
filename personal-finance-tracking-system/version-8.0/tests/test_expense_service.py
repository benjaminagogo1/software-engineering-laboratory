from app.services.expense_service import ExpenseService
from app.repositories.expense_repository import ExpenseRepository
from app.services.results import AddResult

from app.models.expense import Expense



class FakeRepository(ExpenseRepository):
      def __init__(self):
            self.add_expense = None
            self.expenses = []


      def add(self, expense):
            self.add_expense = expense
            self.expenses.append(expense)


      def get_all(self) -> list[Expense]:
            return []

      def find_by_id(self, expense_id) -> Expense | None:
            for expense in self.expenses:
                  if expense_id == expense_id:
                        return expense
                  
            return None
      

      def update(self, expense):
            pass
      
      def delete(self, expense):
            pass


def test_add_expense_invalid_name():

      repository = FakeRepository()

      service = ExpenseService(repository)

      expense = Expense(1, "", 100)

      result = service.add_expense(expense)

      assert result == AddResult.INVALID_NAME





def test_add_expense_invalid_amount():
      repository = FakeRepository()

      service = ExpenseService(repository)

      expense = Expense(2, "Food", 0)

      result = service.add_expense(expense)

      assert result == AddResult.INVALID_AMOUNT
      




def test_add_expense_valid_input():
      repository = FakeRepository()
      service = ExpenseService(repository)

      expense = Expense(4, "food", 1000)

      result = service.add_expense(expense)

      assert result == AddResult.SUCCESS
      assert repository.add_expense == expense
      



def test_get_expense_by_id_not_found():
    repository = FakeRepository()
    service = ExpenseService(repository)

    result = service.get_expense_by_id(999)

    assert result is None






def test_get_expense_by_id_found():
      repository = FakeRepository()

      service = ExpenseService(repository)

      expense = Expense(1, "Food", 100)

      repository.add(expense)

      result = service.get_expense_by_id(expense.id)

      assert result == expense