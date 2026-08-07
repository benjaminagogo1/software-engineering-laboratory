import json
from models.expense import Expense
print("storage.py is executing...")



def save_expense(expenses):
    text = json.dumps(
        [{"name": e.name, "amount": e.amount, "date": e.date} for e in expenses], indent= 4
    )
    try:
        with open("data/expense.json", "w") as save_file:
            save_file.write(text)
    except OSError:
        print("Error: Unable to write to the file.")





def load_expense():
    try:
        with open("data/expense.json", "r") as read_file:
            content = read_file.read()
            if content.strip() == "":
                print("No expense saved yet.")
                return []
            data = json.loads(content)
            expenses = []
            for item in data:
                expenses.append(Expense(item["name"], item["amount"], item["date"]))
            return expenses
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Error: File contain invalid JSON format")