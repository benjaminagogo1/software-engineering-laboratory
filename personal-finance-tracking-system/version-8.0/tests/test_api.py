from app.services.expense_service import ExpenseService
from tests.fakes import FakeRepository
from app.models.expense import Expense
from app.api import app, get_service
from fastapi.testclient import TestClient

client = TestClient(app)



def get_test_service():
      repository = FakeRepository()

      expense = Expense(1, "Food", 2500.0)
      repository.add(expense)
      
      return ExpenseService(repository)

app.dependency_overrides[get_service] = get_test_service

def test_get_expenses():
      response = client.get("/expenses")
      assert response.status_code == 200
      
      expenses = response.json()

      assert isinstance(expenses[0], dict)

      assert isinstance(response.json(), list)

      for expense in expenses:
            assert isinstance(expense, dict)

            assert "id" in expense

            assert "name" in expense
            assert "amount" in expense

            assert isinstance(expense["id"], int)

            assert isinstance(expense["name"], str)

            assert isinstance(expense["amount"], float)





def test_create_expense():
      response = client.post(
            "/expenses",
            json={
                  "name": "Test Food",
                  "amount": 2500
            }
      )

      assert response.status_code == 201
      assert response.json()["result"] == "SUCCESS"

      expense =  response.json()["expense"]
      assert expense["name"] == "Test Food"
      assert expense["amount"] == 2500