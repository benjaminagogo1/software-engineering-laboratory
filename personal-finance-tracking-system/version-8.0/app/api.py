from app.services.expense_service import ExpenseService
from app.repositories.sqlite_expense_repository import SqliteExpenseRepository
from app.models.expense import Expense
import config
from app.schemas.user import UserRegistration, UserLogin
from fastapi.security import HTTPBearer
from fastapi import Depends
from app.auth.jwt  import verify_access_token
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.results import UpdateResult, AddResult, DeleteResult
from app.services.user_service import UserService
from app.repositories.sqlite_user_repository import SqliteUserRepository



security =  HTTPBearer()


repository = SqliteExpenseRepository(config.DB_PATH)
service = ExpenseService(repository)


user_repository = SqliteUserRepository(config.DB_PATH)
user_service = UserService(user_repository)


def get_current_user(credentials = Depends(security)):
      token = credentials.credentials
      payload = verify_access_token(token)

      if payload is None:
            raise HTTPException(
                  status_code =401,
                  detail = "Invalid or expired token"
            )
      return payload



def get_service():
      return service

class ExpenseRequest(BaseModel):
      name: str
      amount: float
     

class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
      id: int
      username: str

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
def get_expenses(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      
      return service.get_all_expenses(current_user["user_id"])


@app.post("/register", response_model=UserResponse, status_code=201)
def register_user(user_request: UserRegistration):
      user = user_service.register_user(
            user_request.username,
            user_request.password
      )

      if user is None:
            raise HTTPException(
                  status_code=409,
                  detail="Username already exists"
            )

      return {
            "id": user.id,
            "username": user.username
      }


@app.post("/login", response_model=LoginResponse)
def login_user(user_request: UserLogin):
      token = user_service.login_user(
            user_request.username,
            user_request.password
      )

      if token is None:
            raise HTTPException(
                  status_code=401,
                  detail="Invalid username or password"
            )

      return {
            "access_token": token,
            "token_type": "bearer"
      }



@app.post("/expenses", response_model=CreateExpenseResponse, status_code=201)
def create_expense(
      expense_request: ExpenseRequest, 
      service = Depends(get_service),
      current_user = Depends(get_current_user)
      ):
      
      expense = Expense(
            None,
            expense_request.name,
            expense_request.amount,
            current_user["user_id"]
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
def get_expense(expense_id: int, 
      service = Depends(get_service),
      current_user = Depends(get_current_user)
      ):
      expense = service.get_expense_by_id(
            expense_id,
            current_user["user_id"]
            )

      if expense is None:
            raise HTTPException(status_code=404, detail= "Expense not found.")
      
      return expense


@app.put("/expenses/{expense_id}", response_model=MessageResponse)
def update_expense(
    expense_id: int,
    expense_request: ExpenseUpdatedRequest,
    service=Depends(get_service),
    current_user=Depends(get_current_user)
):
    result = service.update_expense(
        expense_id,
        expense_request.amount,
        current_user["user_id"]
    )

    if result == UpdateResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Expense not found")

    if result == UpdateResult.INVALID_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero"
        )

    return {"message": "Expense updated successfully"}


@app.delete("/expenses/{expense_id}", response_model=MessageResponse)
def delete_expense(
    expense_id: int,
    service=Depends(get_service),
    current_user=Depends(get_current_user)
):
    result = service.delete_expense_by_id(
        expense_id,
        current_user["user_id"]
    )

    if result == DeleteResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense deleted successfully"}

