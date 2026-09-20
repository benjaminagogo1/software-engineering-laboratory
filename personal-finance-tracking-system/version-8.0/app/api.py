from app.services.expense_service import ExpenseService
from app.repositories.sqlite_expense_repository import SqliteExpenseRepository
from app.models.expense import Expense
import config
from fastapi import Depends
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.results import UpdateResult, AddResult, DeleteResult



repository = SqliteExpenseRepository(config.DB_PATH)
service = ExpenseService(repository)


def get_service():
      return service

class ExpenseRequest(BaseModel):
      name: str
      amount: float


class ExpenseUpdatedRequest(BaseModel):
      amount: float


class ExpenseResponse(BaseModel):
      id: int
      name: str
      amount: float

class CreateExpenseResponse(BaseModel):
      result: str
      expense: ExpenseResponse

class MessageResponse(BaseModel):
      message: str


app = FastAPI()


@app.get("/expenses", response_model=list[ExpenseResponse])
def get_expenses(service= Depends(get_service)):
      return service.get_all_expenses()


@app.post("/expenses", response_model=CreateExpenseResponse, status_code=201)
def create_expense(expense_request: ExpenseRequest, service = Depends(get_service)):
      expense = Expense(
            None,
            expense_request.name,
            expense_request.amount
      )
      

      result = service.add_expense(expense)

      if result == AddResult.INVALID_NAME:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
      
      if result == AddResult.INVALID_AMOUNT:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")

      return {
            "result": result.name,
            "expense": expense
      }


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, service = Depends(get_service)):
      expense = service.get_expense_by_id(expense_id)

      if expense is None:
            raise HTTPException(status_code=404, detail= "Expense not found.")
      
      return expense


@app.put("/expenses/{expense_id}", response_model=MessageResponse)
def update_expense(expense_id: int, expense_request: ExpenseUpdatedRequest, service= Depends(get_service)):

      result = service.update_expense(expense_id, expense_request.amount)

      if result == UpdateResult.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Expense not found")
      
      if result == UpdateResult.INVALID_AMOUNT:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")
      return {"message": "Expense updated successfully"}


@app.delete("/expenses/{expense_id}", response_model=MessageResponse)
def delete_expense(expense_id: int, service= Depends(get_service)):
      result = service.delete_expense_by_id(expense_id)
      if result == DeleteResult.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Expense not found")
          
           
      return {"message": "Expense deleted successfully"}




