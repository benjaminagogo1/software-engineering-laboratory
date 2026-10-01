import argparse
import getpass
from datetime import date
from app.auth.policy import WeakCredentials
from app.models.expense import (
    Expense,
    CATEGORIES,
    PAYMENT_TYPES,
    canonical_month,
    parse_amount_cents,
)
from app.services.results import AddResult,UpdateResult, DeleteResult
from app.ui.formatting import AMOUNT_RULE, format_money, format_expense_line
from app.reports.monthly_chart import write_monthly_spending
import config


def amount_in_kobo(text):
      """
      An argparse type for an amount typed in naira. Returns whole kobo.

      Was `type=float`, which accepted "nan" and "inf" — both of which passed
      the service's `amount <= 0` guard — and turned "10.10" into the nearest
      double to 10.1 before it was ever stored. Parsing through Decimal and
      converting once keeps the typed digits exact and makes the two
      non-numbers unparseable here, where argparse answers with a usage message
      and exit code 2 instead of a traceback.

      A negative amount parses fine and is refused by the service, which is
      where the rule lives: "not a number" and "not a valid amount" are
      different failures and deserve different sentences.
      """
      amount_cents = parse_amount_cents(text)

      if amount_cents is None:
            raise argparse.ArgumentTypeError(
                  f"invalid amount: {text!r} (try 2500 or 2500.50)"
            )

      return amount_cents


parser = argparse.ArgumentParser()

subparser = parser.add_subparsers(dest="command", required=True)

register_parser = subparser.add_parser("register")
register_parser.add_argument("--username")

login_parser = subparser.add_parser("login")
login_parser.add_argument("--username")

add_parser = subparser.add_parser("add")
add_parser.add_argument("name")
# `metavar` is what the usage line shows and `dest` is what the value is
# called in code — and the two want different names here, because the person
# types naira and the code carries kobo.
add_parser.add_argument(
      "amount_cents",
      metavar="amount",
      type=amount_in_kobo,
      help="amount in naira, for example 2500 or 2500.50",
)
add_parser.add_argument("--date", dest="expense_date")
add_parser.add_argument("--category", required=True)
add_parser.add_argument("--payment-type", dest="payment_type", required=True)
add_parser.add_argument("--merchant")
add_parser.add_argument("--note")

list_parser = subparser.add_parser("list")

get_parser = subparser.add_parser("get")
get_parser.add_argument("id", type=int)

update_parser = subparser.add_parser("update")
update_parser.add_argument("id", type=int)
update_parser.add_argument(
      "amount_cents",
      metavar="amount",
      type=amount_in_kobo,
      help="new amount in naira, for example 2500 or 2500.50",
)
update_parser.add_argument("--category")
update_parser.add_argument("--payment-type", dest="payment_type")
update_parser.add_argument("--merchant")
update_parser.add_argument("--note")


delete_parser = subparser.add_parser("delete")
delete_parser.add_argument("id", type=int)

delete_all_parser = subparser.add_parser("delete-all")
delete_all_parser.add_argument(
      "--yes",
      action="store_true",
      help="skip the confirmation prompt",
)

search_parser = subparser.add_parser("search")
search_parser.add_argument("name")

top_month_parser = subparser.add_parser("top-month")

months_parser = subparser.add_parser("months")

top_day_parser = subparser.add_parser("top-day")

highest_parser = subparser.add_parser("highest")

lowest_parser = subparser.add_parser("lowest")

frequency_parser = subparser.add_parser("frequency")
frequency_parser.add_argument("name")

chart_parser = subparser.add_parser("chart")
chart_parser.add_argument(
      "--month",
      help="month to chart as YYYY-MM (defaults to the current month)",
)


# The terminal app talks to SQLite directly, so it needs a user id but no
# token: every command except register/login identifies the user the same way.
for command_parser in (
      add_parser,
      list_parser,
      get_parser,
      update_parser,
      delete_parser,
      delete_all_parser,
      search_parser,
      top_month_parser,
      months_parser,
      top_day_parser,
      highest_parser,
      lowest_parser,
      frequency_parser,
      chart_parser,
):
      command_parser.add_argument("--username")


def resolve_user_id(user_service, username):
      """Authenticates a local user and returns their id, or None."""
      if username is None:
            username = input("Username: ")

      password = getpass.getpass("Password: ")

      user = user_service.authenticate(username, password)

      if user is None:
            print("Invalid username or password.")
            return None

      return user.id


def run(service, user_service):
      args= parser.parse_args()

      if args.command == "register":
            username = args.username or input("Username: ")
            password = getpass.getpass("Password: ")

            # Caught rather than left to reach the user as a traceback. The
            # policy is the same one the API applies, because it lives in the
            # service — so a rule added there covers this prompt too.
            try:
                  user = user_service.register_user(username, password)
            except WeakCredentials as refused:
                  print(refused)
                  return

            if user is None:
                  print("Username already exists.")
            else:
                  print(f"User {user.username} registered successfully.")

            return


      if args.command == "login":
            user_id = resolve_user_id(user_service, args.username)

            if user_id is not None:
                  print(f"Logged in as user {user_id}.")

            return


      user_id = resolve_user_id(user_service, args.username)

      if user_id is None:
            return

      if args.command == "add":
            expense_date = args.expense_date

            if expense_date is None:
                  expense_date = date.today().isoformat()
            else:
                  try:
                        expense_date = date.fromisoformat(expense_date).isoformat()
                  except ValueError:
                        print("Invalid date. Please use YYYY-MM-DD.")
                        return

            expense = Expense(
                  None,
                  args.name,
                  args.amount,
                  user_id,
                  expense_date,
                  args.category,
                  args.payment_type,
                  args.merchant,
                  args.note
            )
            result = service.add_expense(expense)
            if result == AddResult.SUCCESS:
                  print("Expense added successfully.")
            elif result == AddResult.INVALID_NAME:
                  print("Expense name cannot be empty.")
            elif result == AddResult.INVALID_AMOUNT:
                  print(AMOUNT_RULE)
            elif result == AddResult.INVALID_CATEGORY:
                  print(f"Category must be one of: {', '.join(CATEGORIES)}")
            elif result == AddResult.INVALID_PAYMENT_TYPE:
                  print(f"Payment type must be one of: {', '.join(PAYMENT_TYPES)}")


      elif args.command == "list":
            expenses = service.get_all_expenses(user_id)

            if not expenses:
                  print("No expenses found.")

            for expense in expenses:
                  print(format_expense_line(expense))


      elif args.command == "get":
            expense = service.get_expense_by_id(args.id, user_id)

            if expense is None:
                  print("Expense not found")
            else:
                  print(format_expense_line(expense))

      elif args.command == "update":
            result = service.update_expense(
                  args.id,
                  args.amount,
                  user_id,
                  args.category,
                  args.payment_type,
                  args.merchant,
                  args.note
            )

            if result == UpdateResult.SUCCESS:
                  print("Expense updated successfully.")

            elif result == UpdateResult.INVALID_AMOUNT:
                  print(AMOUNT_RULE)
            elif result == UpdateResult.NOT_FOUND:
                  print("Expense not found")
            elif result == UpdateResult.INVALID_CATEGORY:
                  print(f"Category must be one of: {', '.join(CATEGORIES)}")
            elif result == UpdateResult.INVALID_PAYMENT_TYPE:
                  print(f"Payment type must be one of: {', '.join(PAYMENT_TYPES)}")



      elif args.command == "delete":
            result = service.delete_expense_by_id(args.id, user_id)

            if result == DeleteResult.SUCCESS:
                  print("Expense deleted successfully")
            elif result == DeleteResult.NOT_FOUND:
                  print("Expense not found.")


      elif args.command == "delete-all":
            existing = service.get_all_expenses(user_id)

            if not existing:
                  print("No expenses found.")
                  return

            print(f"This deletes all {len(existing)} of your expenses. It cannot be undone.")

            # --yes exists for scripting; typed otherwise, because this is the
            # one command here that cannot be undone.
            if not args.yes:
                  confirmation = input('Type "yes" to confirm: ').strip().lower()

                  if confirmation != "yes":
                        print("Cancelled. Nothing was deleted.")
                        return

            print(f"Deleted {service.delete_all_expenses(user_id)} expense(s).")


      elif args.command == "search":
            matches = service.search_by_name(args.name, user_id)

            if not matches:
                  print("No matching expenses found.")
                  return

            for expense in matches:
                  print(format_expense_line(expense))


      elif args.command == "top-month":
            top_month = service.get_top_month(user_id)

            if top_month is None:
                  print("No expenses found.")
            else:
                  month, total = top_month
                  print(f"Highest spending month: {month} - {format_money(total)}")


      elif args.command == "months":
            totals = service.get_month_totals(user_id)

            if not totals:
                  print("No expenses found.")
                  return

            largest = totals[0][1]
            width = max(len(month) for month, _ in totals)

            for month, total in totals:
                  filled = max(1, round(total / largest * 24))
                  print(f"{month:<{width}}  {'█' * filled} {format_money(total)}")


      elif args.command == "top-day":
            top_day = service.get_top_weekday(user_id)

            if top_day is None:
                  print("No expenses found.")
            else:
                  day, total = top_day
                  print(f"Highest spending day of the week: {day} - {format_money(total)}")


      elif args.command == "highest":
            expense = service.get_highest_expense(user_id)

            if expense is None:
                  print("No expenses found.")
            else:
                  print(format_expense_line(expense))


      elif args.command == "lowest":
            expense = service.get_lowest_expense(user_id)

            if expense is None:
                  print("No expenses found.")
            else:
                  print(format_expense_line(expense))


      elif args.command == "frequency":
            count = service.count_by_name(args.name, user_id)

            print(f"{args.name} appears {count} time(s).")


      elif args.command == "chart":
            month = args.month or date.today().strftime("%Y-%m")
            month = canonical_month(month)

            if month is None:
                  print("Invalid month. Please use YYYY-MM.")
                  return

            daily_totals = service.get_daily_totals(month, user_id)

            path = write_monthly_spending(month, daily_totals, config.REPORTS_DIR)

            print(f"Chart written to {path}")
            print("Open that file in a browser to view it.")
