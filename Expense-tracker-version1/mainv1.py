import json

class Expense:
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount


class ExpenseTracker:
    def __init__(self):
        self.expenses = []


    def add_expense(self, expense):
        self.expenses.append(expense)
        save_expense(self.expenses)


    def show_expense(self):
        if len(self.expenses) == 0:
            print("No expense found")
            return
        for expense in self.expenses:
            print(expense.name, expense.amount)


    def delete_expense(self, expense):
        try:
            self.expenses.remove(expense)
            save_expense(self.expenses)
            return True
        except ValueError:
            return False


    def search_expense(self, name):
        for expense in self.expenses:
            if expense.name == name:
                return expense

        return None



    def update_expense(self, name, amount):
        expense = self.search_expense(name)

        if expense is None:
            return False

        expense.amount = amount
        save_expense(self.expenses)
        return True



tracker = ExpenseTracker()

def add_expense_menu(tracker):
    name = input("Enter expense name ")
    try:
        amount = int(input("Enter expense amount "))
    except ValueError:
        print("Please, only digits are allowed.")
        return  

    expense = Expense(name, amount)
    tracker.add_expense(expense)
    print(f"Expense: '{expense.name}' added successfully!'")



def show_expense_menu(tracker):
    tracker.show_expense()



def search_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense is not found. ")
    else:
        print(expense.name, expense.amount)





def update_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense not found.")
        return
    else:
        print("Expense found.")
        print(expense.name, expense.amount)
    try:
        amount = int(input("Enter new amount: "))
    except ValueError:
        print("Error: Please, only digits are allowed.")
        return
    tracker.update_expense(name, amount)
    print(f"Expense '{expense.name}' updated successfully!")
   


def delete_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense is not found.")
        return
    else:
        print("Expense found.")
        print(expense.name, expense.amount)
    print("Are you sure?  (yes/no)")
    choice = input("Enter your choice. ").lower()
    if choice == "yes":  
        tracker.delete_expense(expense)
        print(f"Expense '{expense.name}' deleted successfully!")
    else:
        print("Deletion cancelled")
    

def save_expense(expenses):
    text = json.dumps(
        [{"name": e.name, "amount": e.amount} for e in expenses], indent=2
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
                print("No expense saved")
                return []
            data = json.loads(content)
            expenses = []
            for item in data:
                expenses.append(Expense(item["name"], item["amount"]))
            return expenses
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Error: File contains invalid JSON faormat.")
        return []

    
def main():
    tracker.expenses = load_expense()


main()
running = True
while running:
    print("\nExpense Tracker")
    print("1. Add Expense")
    print("2. Show Expense")
    print("3. Search Expense")
    print("4. Update Expense")
    print("5. Delete Expense")
    print("6. Exit")

    try:
        choice = int(input("Choose an option:  "))
    except ValueError:
        print("Invalid input: Please, only digits are allowed.")
        continue
    if choice == 1:
        add_expense_menu(tracker)

    if choice == 2:
        show_expense_menu(tracker)

    if choice == 3:
        search_expense_menu(tracker)

    if choice == 4:
        update_expense_menu(tracker)

    if choice == 5:
        delete_expense_menu(tracker)

    if choice == 6:
        running = False

