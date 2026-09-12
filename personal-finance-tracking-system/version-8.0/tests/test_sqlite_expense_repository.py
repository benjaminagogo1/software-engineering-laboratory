from app.models.expense import Expense

from app.repositories.sqlite_expense_repository import SqliteExpenseRepository


def test_add_expense(tmp_path):
    db_path = tmp_path / "test_expense.db"
    repository = SqliteExpenseRepository(db_path)

    expense = Expense(1, "Food", 1000)
    repository.add(expense)

    result = repository.find_by_id(1)
    assert result is not None
    assert result.id == expense.id
    assert result.name == expense.name
    assert result.amount == expense.amount




def test_find_expense_by_id_not_found(tmp_path):
      db_path = tmp_path / "test_expense.db"
      repository = SqliteExpenseRepository(db_path)

      result = repository.find_by_id(999)

      assert result is None


def test_get_all_expenses(tmp_path):
    db_path = tmp_path / "test_expense.db"
    repository = SqliteExpenseRepository(db_path)

    expense1 = Expense(1, "Food", 1000)
    expense2 = Expense(2, "Transport", 500)

    repository.add(expense1)
    repository.add(expense2)
    
    result = repository.get_all()
    print(result)

    assert len(result) == 2
        