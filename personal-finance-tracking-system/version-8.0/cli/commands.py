import argparse
from app.models.expense import Expense
from app.services.results import AddResult,UpdateResult, DeleteResult


parser = argparse.ArgumentParser()

subparser = parser.add_subparsers(dest="command", required=True)

add_parser = subparser.add_parser("add")
add_parser.add_argument("name")
add_parser.add_argument("amount", type=float)

list_parser = subparser.add_parser("list")

get_parser = subparser.add_parser("get")
get_parser.add_argument("id", type=int)

update_parser = subparser.add_parser("update")
update_parser.add_argument("id", type=int)
update_parser.add_argument("amount", type=float)


delete_parser = subparser.add_parser("delete")
delete_parser.add_argument("id", type=int)

# parser.add_argument("command")
# parser.add_argument("name", nargs="?")
# parser.add_argument("amount", type=float, nargs="?")
# parser.add_argument("id", type=int, nargs="?")


def run(service):
      args= parser.parse_args()

      if args.command == "add":
            expense = Expense(None, args.name, args.amount)
            result = service.add_expense(expense)
            if result == AddResult.SUCCESS:
                  print("Expense added successfully.")
      

      elif args.command == "list":
            expenses = service.get_all_expenses()

            for expense in expenses:
                  print(f"{expense.id}: {expense.name} - N{expense.amount:,.2f}")


      elif args.command == "get":
            expense = service.get_expense_by_id(args.id)
          
            if expense is None:
                  print("Expense not found")
            else:
                  print(f"{expense.id}: {expense.name} - {expense.amount:,.2f}")

      elif args.command == "update":
            result = service.update_expense(args.id, args.amount)

            if result == UpdateResult.SUCCESS:
                  print("Expense updated successfully.")

            elif result == UpdateResult.INVALID_AMOUNT:
                  print("Invalid amount")
            elif result == UpdateResult.NOT_FOUND:
                  print("Expense not found")



      elif args.command == "delete":
            result = service.delete_expense_by_id(args.id)

            if result == DeleteResult.SUCCESS:
                  print("Expense deleted successfully")
            elif result == DeleteResult.NOT_FOUND:
                  print("Expense not found.")