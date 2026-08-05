import json
from models import Expense




def save_expense(expenses):
    text = json.dumps(
        [{"name": e.name, "amount": e.amount} for e in expenses], indent= 4
    )
    try:
        with open("expense.json", "w") as save_file:
            save_file.write(text)
    except OSError:
        print("Error: Unable to write to the file.")






def load_expense():
    try:
        with open("expense.json", "r") as read_file:
            content = read_file.read()
            if content.strip() == "":
                print("No expense saved.")
                return []
            data = json.loads(content)
            expenses = []
            for item in expenses:
                expenses.append(Expense[item["name"], item["amount"]])
            return expenses
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Error: File contain invalid JSON format")