from app.repositories.expense_repository import ExpenseRepository
from app.models.expense import Expense



class FakeRepository(ExpenseRepository):
      def __init__(self):
            self.add_expense = None
            self.expenses = []
            self.delete_expense = None


      def add(self, expense):
            expense.id = len(self.expenses) + 1
            self.add_expense = expense
            self.expenses.append(expense)


      def get_all(self) -> list[Expense]:
            return self.expenses

      def find_by_id(self, expense_id) -> Expense | None:
            for expense in self.expenses:
                  if expense.id == expense_id:
                        return expense
                  
            return None
      

      def update(self, expense):
            pass
      
      def delete(self, expense):
            self.delete_expense = expense

