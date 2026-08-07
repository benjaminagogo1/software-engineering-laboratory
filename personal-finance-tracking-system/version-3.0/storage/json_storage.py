import json
from models.expense import Expense


class JsonStorage:

    def save(self, expenses):
        text = json.dumps(
            [
                {
                    "name": expense.name,
                    "amount": expense.amount,
                    "date": expense.date
                }
                for expense in expenses
            ],
            indent=4
        )

        try:
            with open("data/expense.json", "w") as save_file:
                save_file.write(text)
        except OSError:
            print("Error: Unable to write to the file.")

    def load(self):
        try:
            with open("data/expense.json", "r") as read_file:
                content = read_file.read()

                if content.strip() == "":
                    print("No expense saved yet.")
                    return []

                data = json.loads(content)

                expenses = []

                for item in data:
                    expenses.append(
                        Expense(
                            item["name"],
                            item["amount"],
                            item["date"]
                        )
                    )

                return expenses

        except FileNotFoundError:
            return []

        except json.JSONDecodeError:
            print("Error: File contains invalid JSON format.")
            return []