import logging

import pytest

from app.models.audit_event import (
    EXPENSE_CREATED,
    EXPENSE_DELETED,
    EXPENSE_UPDATED,
    EXPENSES_DELETED_ALL,
)
from app.repositories.memory_audit_repository import MemoryAuditRepository
from app.services.expense_service import ExpenseService
from app.storage.storage_error import StorageError
from tests.fakes import FakeRepository
from app.services.results import AddResult, UpdateResult, DeleteResult
from app.models.expense import Expense


USER_ID = 1


def make_expense(
    expense_id,
    name,
    amount,
    expense_date="2026-01-15",
    user_id=USER_ID,
    category="Food",
    payment_type="Cash",
    merchant=None,
    note=None,
):
    return Expense(
        expense_id, name, amount, user_id, expense_date, category, payment_type,
        merchant, note,
    )


def build_service():
    repository = FakeRepository()
    # The audit repository rides along on the service, so the tests that assert
    # on the trail read it as service.audit and every existing caller of
    # build_service keeps its two-value unpacking.
    return repository, ExpenseService(repository, MemoryAuditRepository())


def test_add_expense_invalid_name():

      repository, service = build_service()

      expense = make_expense(1, "", 100)

      result = service.add_expense(expense)

      assert result == AddResult.INVALID_NAME




def test_add_expense_invalid_amount():
      repository, service = build_service()

      expense = make_expense(2, "Food", 0)

      result = service.add_expense(expense)

      assert result == AddResult.INVALID_AMOUNT



def test_add_expense_valid_input():
      repository, service = build_service()

      expense = make_expense(4, "food", 1000)

      result = service.add_expense(expense)

      assert result == AddResult.SUCCESS
      assert repository.add_expense == expense



def test_get_expense_by_id_not_found():
    repository, service = build_service()

    result = service.get_expense_by_id(999, USER_ID)

    assert result is None





def test_get_expense_by_id_found():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100)

      repository.add(expense)

      result = service.get_expense_by_id(expense.id, USER_ID)

      assert result == expense


def test_get_expense_by_id_ignores_another_users_expense():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, user_id=2)

      repository.add(expense)

      assert service.get_expense_by_id(expense.id, USER_ID) is None





def test_delete_expense_not_found():
      repository, service = build_service()

      result = service.delete_expense_by_id(999, USER_ID)

      assert result == DeleteResult.NOT_FOUND
      assert repository.delete_expense is None



def test_delete_expense():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000)

      repository.add(expense)

      result = service.delete_expense_by_id(1, USER_ID)
      assert result == DeleteResult.SUCCESS
      assert repository.delete_expense == expense


def test_update_expense():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000)

      repository.add(expense)

      result = service.update_expense(1, 2500, USER_ID)

      assert result == UpdateResult.SUCCESS
      assert repository.find_by_id(1, USER_ID).amount == 2500


def test_update_expense_ignores_another_users_expense():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000, user_id=2)

      repository.add(expense)

      assert service.update_expense(1, 2500, USER_ID) == UpdateResult.NOT_FOUND


# --- Category and payment type ---------------------------------------------


def test_add_expense_rejects_an_unknown_category():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, category="Groceries")

      assert service.add_expense(expense) == AddResult.INVALID_CATEGORY
      assert repository.add_expense is None


def test_add_expense_rejects_an_unknown_payment_type():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, payment_type="Barter")

      assert service.add_expense(expense) == AddResult.INVALID_PAYMENT_TYPE
      assert repository.add_expense is None


def test_add_expense_stores_the_canonical_category():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, category="  food  ")

      assert service.add_expense(expense) == AddResult.SUCCESS
      assert expense.category == "Food"


def test_add_expense_stores_the_canonical_payment_type():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, payment_type="mobile money")

      assert service.add_expense(expense) == AddResult.SUCCESS
      assert expense.payment_type == "Mobile Money"


def test_update_expense_changes_category_and_payment_type():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000)

      repository.add(expense)

      result = service.update_expense(1, 1000, USER_ID, "transport", "card")

      assert result == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.category == "Transport"
      assert stored.payment_type == "Card"


def test_update_expense_keeps_the_category_when_it_is_omitted():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000, category="Rent", payment_type="Card")

      repository.add(expense)

      assert service.update_expense(1, 2000, USER_ID) == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.category == "Rent"
      assert stored.payment_type == "Card"


def test_update_expense_rejects_an_unknown_category():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000, category="Rent")

      repository.add(expense)

      assert service.update_expense(1, 1000, USER_ID, "Groceries") == UpdateResult.INVALID_CATEGORY
      assert repository.find_by_id(1, USER_ID).category == "Rent"


def test_update_expense_rejects_an_unknown_payment_type():
      repository, service = build_service()

      expense = make_expense(1, "Food", 1000, payment_type="Cash")

      repository.add(expense)

      assert service.update_expense(
            1, 1000, USER_ID, None, "Barter"
      ) == UpdateResult.INVALID_PAYMENT_TYPE
      assert repository.find_by_id(1, USER_ID).payment_type == "Cash"


# --- Analytics -------------------------------------------------------------


def test_get_top_month_returns_the_highest_total():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300, "2026-01-10"))
      repository.add(make_expense(2, "Rent", 700, "2026-02-01"))

      assert service.get_top_month(USER_ID) == ("2026-02", 700)


def test_get_top_month_sums_within_a_month():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 400, "2026-02-01"))
      repository.add(make_expense(2, "Fuel", 400, "2026-02-20"))
      repository.add(make_expense(3, "Rent", 700, "2026-01-01"))

      assert service.get_top_month(USER_ID) == ("2026-02", 800)


def test_get_top_month_tie_prefers_the_most_recent_month():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 500, "2026-01-05"))
      repository.add(make_expense(2, "Rent", 500, "2026-03-05"))

      assert service.get_top_month(USER_ID) == ("2026-03", 500)


def test_get_top_month_without_expenses():
      repository, service = build_service()

      assert service.get_top_month(USER_ID) is None


def test_get_top_month_ignores_other_users_expenses():
      repository, service = build_service()

      repository.add(make_expense(1, "Rent", 9000, "2026-05-01", user_id=2))

      assert service.get_top_month(USER_ID) is None


def test_get_highest_expense():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300))
      highest = make_expense(2, "Rent", 900)
      repository.add(highest)

      assert service.get_highest_expense(USER_ID) == highest


def test_get_highest_expense_prefers_the_lower_id_on_a_tie():
      repository, service = build_service()

      first = make_expense(1, "Food", 900)
      repository.add(first)
      repository.add(make_expense(2, "Rent", 900))

      assert service.get_highest_expense(USER_ID) == first


def test_get_highest_expense_without_expenses():
      repository, service = build_service()

      assert service.get_highest_expense(USER_ID) is None


def test_count_by_name_ignores_case():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100))
      repository.add(make_expense(2, "food", 200))
      repository.add(make_expense(3, "FOOD", 300))
      repository.add(make_expense(4, "Rent", 400))

      assert service.count_by_name("Food", USER_ID) == 3


def test_count_by_name_matches_the_whole_name_only():
      repository, service = build_service()

      repository.add(make_expense(1, "Seafood", 100))

      assert service.count_by_name("food", USER_ID) == 0


def test_count_by_name_without_matches():
      repository, service = build_service()

      assert service.count_by_name("Food", USER_ID) == 0


def test_search_by_name_is_a_case_insensitive_substring_match():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100))
      repository.add(make_expense(2, "Seafood", 200))
      repository.add(make_expense(3, "Rent", 300))

      matches = service.search_by_name("foo", USER_ID)

      assert [expense.name for expense in matches] == ["Food", "Seafood"]


def test_search_by_name_returns_every_attribute():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100, "2026-04-09"))

      match = service.search_by_name("food", USER_ID)[0]

      assert (match.id, match.name, match.amount, match.date, match.user_id) == (
            1, "Food", 100, "2026-04-09", USER_ID
      )


def test_search_by_name_with_a_blank_term_returns_nothing():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100))

      assert service.search_by_name("   ", USER_ID) == []


def test_search_by_name_ignores_other_users_expenses():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100, user_id=2))

      assert service.search_by_name("food", USER_ID) == []


# --- Merchant and note ------------------------------------------------------


def test_add_expense_keeps_merchant_and_note():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, merchant="Shoprite", note="weekly shop")

      assert service.add_expense(expense) == AddResult.SUCCESS
      assert repository.add_expense.merchant == "Shoprite"
      assert repository.add_expense.note == "weekly shop"


def test_add_expense_turns_a_blank_merchant_and_note_into_none():
      repository, service = build_service()

      expense = make_expense(1, "Food", 100, merchant="   ", note="")

      assert service.add_expense(expense) == AddResult.SUCCESS
      assert repository.add_expense.merchant is None
      assert repository.add_expense.note is None


def test_update_expense_sets_merchant_and_note():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 1000))

      result = service.update_expense(1, 1000, USER_ID, merchant="Shoprite", note="weekly")

      assert result == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.merchant == "Shoprite"
      assert stored.note == "weekly"


def test_update_expense_keeps_merchant_and_note_when_they_are_omitted():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 1000, merchant="Shoprite", note="weekly"))

      assert service.update_expense(1, 2500, USER_ID) == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.merchant == "Shoprite"
      assert stored.note == "weekly"


def test_update_expense_clears_merchant_and_note_with_an_empty_string():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 1000, merchant="Shoprite", note="weekly"))

      assert service.update_expense(1, 1000, USER_ID, merchant="", note="") == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.merchant is None
      assert stored.note is None


def test_update_expense_changes_the_name_and_date():
      repository, service = build_service()

      repository.add(make_expense(1, "Grocerys", 1000, expense_date="2026-01-15"))

      result = service.update_expense(
            1, 1000, USER_ID, name="Groceries", date="2026-02-01"
      )

      assert result == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.name == "Groceries"
      assert stored.date == "2026-02-01"


def test_update_expense_keeps_the_name_and_date_when_they_are_omitted():
      repository, service = build_service()

      repository.add(make_expense(1, "Groceries", 1000, expense_date="2026-01-15"))

      assert service.update_expense(1, 2500, USER_ID) == UpdateResult.SUCCESS

      stored = repository.find_by_id(1, USER_ID)
      assert stored.name == "Groceries"
      assert stored.date == "2026-01-15"


def test_update_expense_trims_a_name_that_arrives_with_spaces():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 1000))

      assert service.update_expense(1, 1000, USER_ID, name="  Groceries  ") == UpdateResult.SUCCESS

      assert repository.find_by_id(1, USER_ID).name == "Groceries"


def test_update_expense_rejects_a_name_that_is_only_whitespace():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 1000))

      assert service.update_expense(1, 1000, USER_ID, name="   ") == UpdateResult.INVALID_NAME

      # And left the stored row alone rather than half-applying the edit.
      assert repository.find_by_id(1, USER_ID).name == "Food"


# --- The lowest expense, months, weekdays and the chart's data --------------


def test_get_lowest_expense():
      repository, service = build_service()

      repository.add(make_expense(1, "Rent", 900))
      lowest = make_expense(2, "Snack", 100)
      repository.add(lowest)

      assert service.get_lowest_expense(USER_ID) == lowest


def test_get_lowest_expense_without_expenses():
      repository, service = build_service()

      assert service.get_lowest_expense(USER_ID) is None


def test_get_month_totals_ranks_every_month():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300, "2026-01-10"))
      repository.add(make_expense(2, "Rent", 700, "2026-02-01"))

      assert service.get_month_totals(USER_ID) == [("2026-02", 700), ("2026-01", 300)]


def test_get_top_weekday_names_the_busiest_day():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 400, "2026-07-04"))
      repository.add(make_expense(2, "Fuel", 300, "2026-07-11"))
      repository.add(make_expense(3, "Rent", 500, "2026-07-05"))

      assert service.get_top_weekday(USER_ID) == ("Saturday", 700)


def test_get_top_weekday_without_expenses():
      repository, service = build_service()

      assert service.get_top_weekday(USER_ID) is None


def test_get_daily_totals_returns_only_days_with_spending():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300, "2026-07-04"))
      repository.add(make_expense(2, "Rent", 900, "2026-07-18"))

      assert service.get_daily_totals("2026-07", USER_ID) == [
            ("2026-07-04", 300),
            ("2026-07-18", 900),
      ]


def test_get_daily_totals_normalizes_an_unpadded_month():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300, "2026-07-04"))

      assert service.get_daily_totals("2026-7", USER_ID) == [("2026-07-04", 300)]


def test_get_daily_totals_rejects_something_that_is_not_a_month():
      repository, service = build_service()

      assert service.get_daily_totals("last month", USER_ID) is None


def test_delete_all_expenses_reports_how_many_went():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100))
      repository.add(make_expense(2, "Rent", 900))

      assert service.delete_all_expenses(USER_ID) == 2
      assert service.get_all_expenses(USER_ID) == []


def test_delete_all_expenses_leaves_other_users_alone():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100))
      repository.add(make_expense(2, "Rent", 900, user_id=2))

      service.delete_all_expenses(USER_ID)

      assert len(service.get_all_expenses(2)) == 1


# --- the audit trail ---------------------------------------------------------
#
# What the service records, not where it is kept: test_audit.py holds both
# stores to the same contract, and these assert that the right events reach
# one of them.


def test_adding_an_expense_records_it():
      repository, service = build_service()

      service.add_expense(make_expense(1, "Food", 300))

      assert service.audit.actions() == [EXPENSE_CREATED]

      recorded = service.audit.events[0]

      assert recorded.user_id == USER_ID
      assert recorded.entity_type == "expense"
      assert recorded.entity_id == 1
      assert recorded.detail == {
            "name": "Food",
            "amount": 300,
            "date": "2026-01-15",
            "category": "Food",
      }


def test_the_recorded_category_is_the_canonical_one():
      """What was stored, not what was typed — the trail has to match the row."""
      repository, service = build_service()

      service.add_expense(make_expense(1, "Food", 300, category="food"))

      assert service.audit.events[0].detail["category"] == "Food"


@pytest.mark.parametrize("expense,reason", [
      (make_expense(1, "   ", 300), "a blank name"),
      (make_expense(1, "Food", 0), "a non-positive amount"),
      (make_expense(1, "Food", 300, category="Shopping"), "an unknown category"),
      (make_expense(1, "Food", 300, payment_type="Crypto"), "an unknown payment type"),
])
def test_a_rejected_expense_is_not_recorded(expense, reason):
      """
      Nothing was created, so there is nothing to have created. A trail that
      recorded attempts as though they were changes would be describing a
      database that never existed.
      """
      repository, service = build_service()

      service.add_expense(expense)

      assert service.audit.actions() == []


def test_deleting_an_expense_records_what_it_was():
      """
      The row is gone from the database by the time anyone reads this, so the
      trail entry is the only remaining record of it — it has to carry the
      whole thing, not just the id.
      """
      repository, service = build_service()

      repository.add(make_expense(
            1, "Rent", 45000, "2026-03-01", category="Rent",
            payment_type="Transfer", merchant="Landlord", note="March",
      ))

      service.delete_expense_by_id(1, USER_ID)

      assert service.audit.actions() == [EXPENSE_DELETED]

      recorded = service.audit.events[0]

      assert recorded.entity_id == 1
      assert recorded.user_id == USER_ID
      assert recorded.detail == {
            "name": "Rent",
            "amount": 45000,
            "date": "2026-03-01",
            "category": "Rent",
            "payment_type": "Transfer",
            "merchant": "Landlord",
            "note": "March",
      }


def test_deleting_something_that_is_not_there_records_nothing():
      repository, service = build_service()

      assert service.delete_expense_by_id(99, USER_ID) == DeleteResult.NOT_FOUND

      assert service.audit.actions() == []


def test_deleting_another_users_expense_records_nothing():
      """
      The repository returns nothing for an expense that is not yours, so the
      service never gets past the lookup — a probe for someone else's row
      leaves no trace, and leaves nothing to attribute to you either.
      """
      repository, service = build_service()

      repository.add(make_expense(1, "Rent", 45000, user_id=2))

      assert service.delete_expense_by_id(1, USER_ID) == DeleteResult.NOT_FOUND

      assert service.audit.actions() == []


def test_deleting_everything_records_the_sweep_and_its_size():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 100))
      repository.add(make_expense(2, "Rent", 900))

      service.delete_all_expenses(USER_ID)

      assert service.audit.actions() == [EXPENSES_DELETED_ALL]

      recorded = service.audit.events[0]

      assert recorded.detail == {"deleted": 2}
      assert recorded.user_id == USER_ID


def test_clearing_an_empty_account_is_still_recorded():
      """
      Zero is an answer, not an absence. "Nothing was there when I asked" and
      "nobody ever asked" are different facts about an account, and only one of
      them is on the trail if this is skipped.
      """
      repository, service = build_service()

      service.delete_all_expenses(USER_ID)

      assert service.audit.actions() == [EXPENSES_DELETED_ALL]
      assert service.audit.events[0].detail == {"deleted": 0}


def test_updating_an_expense_records_only_what_changed():
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300))

      service.update_expense(1, 350, USER_ID, name="Groceries")

      assert service.audit.actions() == [EXPENSE_UPDATED]

      assert service.audit.events[0].detail == {
            "amount": {"from": 300, "to": 350},
            "name": {"from": "Food", "to": "Groceries"},
      }


def test_an_update_that_changes_nothing_records_nothing():
      """
      A form re-submitted untouched is not an edit. Recording it would put a
      row in the trail implying someone altered the record, and enough of them
      would make a real edit hard to find.
      """
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300))

      service.update_expense(1, 300, USER_ID, name="Food")

      assert service.audit.actions() == []


def test_clearing_a_note_is_recorded_as_a_change():
      """
      Empty string is the one argument that means "remove this", so it has to
      produce a record — passing it is a deliberate edit even though the new
      value is nothing.
      """
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300, note="lunch with Ada"))

      service.update_expense(1, 300, USER_ID, note="")

      assert service.audit.events[0].detail == {
            "note": {"from": "lunch with Ada", "to": None},
      }


def test_updating_something_that_is_not_there_records_nothing():
      repository, service = build_service()

      assert service.update_expense(99, 350, USER_ID) == UpdateResult.NOT_FOUND

      assert service.audit.actions() == []


def test_an_update_the_service_rejects_records_nothing():
      """Validation runs before the lookup, so nothing was touched."""
      repository, service = build_service()

      repository.add(make_expense(1, "Food", 300))

      assert service.update_expense(1, 0, USER_ID) == UpdateResult.INVALID_AMOUNT

      assert service.audit.actions() == []


def test_a_record_is_attributed_to_the_expenses_owner():
      """
      Taken from the expense rather than from the caller's argument: an expense
      belongs to whoever it was created for, and that is who the trail is
      about.
      """
      repository, service = build_service()

      service.add_expense(make_expense(1, "Food", 300, user_id=7))

      assert service.audit.events[0].user_id == 7


class FailingAuditRepository:
      """A store that is broken in the way a full disk is broken."""

      def record(self, event):
            raise StorageError("Unable to write to the audit trail")


def test_a_failing_trail_does_not_fail_the_write(caplog):
      """
      The expense is already saved when this runs. Raising here would answer the
      caller with an error for an expense that exists, and the client that
      retries a failed create makes a second one.

      The gap is the cost of that choice, so it has to be loud: this asserts the
      ERROR line, not just that nothing raised.
      """
      repository = FakeRepository()
      service = ExpenseService(repository, FailingAuditRepository())

      with caplog.at_level(logging.ERROR):
            result = service.add_expense(make_expense(1, "Food", 300))

      assert result == AddResult.SUCCESS
      assert service.get_all_expenses(USER_ID) != []

      assert "AUDIT GAP" in caplog.text
      assert EXPENSE_CREATED in caplog.text
