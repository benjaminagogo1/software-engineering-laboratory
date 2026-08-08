import json
from models.expense import Expense
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "expense.json"


class JsonStorage:

    def save_expense(self, expenses):
        text = json.dumps(
            [
                {
                    "name": expense.name,
                    "amount": expense.amount,
                    "date": expense.date.isoformat()
                }
                for expense in expenses
            ],
            indent=4
        )

        try:
            with open(DATA_FILE, "w") as save_file:
                save_file.write(text)
        except OSError:
            return False
        return True

    def load(self):
        try:
            with open(DATA_FILE, "r") as read_file:
                content = read_file.read()

                if content.strip() == "":
                    print("No expense saved yet.")
                    return []

                data = json.loads(content)

                expenses = []

                for item in data:
                    try:
                        date = datetime.strptime(item["date"], "%Y-%m-%d").date()
                    except ValueError:
                        date = datetime.strptime(item["date"],"%d/%m/%y").date()
                    expenses.append(
                        Expense(
                            item["name"],
                            item["amount"],
                            date
                        )
                    )

                return expenses

        except FileNotFoundError:
            return []

        except json.JSONDecodeError:
            print("Error: File contains invalid JSON format.")
            return []