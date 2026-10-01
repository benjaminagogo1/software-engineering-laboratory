from app.models.expense import Expense


def make_expense(
    expense_id,
    name,
    amount,
    user_id,
    expense_date="2026-01-15",
    category="Food",
    payment_type="Cash",
    merchant=None,
    note=None,
):
    return Expense(
        expense_id, name, amount, user_id, expense_date, category, payment_type,
        merchant, note,
    )


def test_add_expense(repositories, owner_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 1000, owner_id)
    repository.add(expense)

    result = repository.find_by_id(expense.id, owner_id)
    assert result is not None
    assert result == expense


def test_find_expense_by_id_not_found(repositories, owner_id):
      repository, _ = repositories

      result = repository.find_by_id(999, owner_id)

      assert result is None


def test_find_expense_by_id_ignores_another_user(repositories, owner_id, other_user_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 1000, owner_id)
    repository.add(expense)

    assert repository.find_by_id(expense.id, other_user_id) is None


def test_get_all_expenses(repositories, owner_id):
    repository, _ = repositories

    expense1 = make_expense(1, "Food", 1000, owner_id)
    expense2 = make_expense(2, "Transport", 500, owner_id)

    repository.add(expense1)
    repository.add(expense2)

    result = repository.get_all(owner_id)

    assert len(result) == 2
    assert result[0] == expense1
    assert result[1] == expense2


def test_get_all_expenses_is_scoped_to_the_user(repositories, owner_id, other_user_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 1000, owner_id))
    repository.add(make_expense(2, "Rent", 9000, other_user_id))

    result = repository.get_all(owner_id)

    assert len(result) == 1
    assert result[0].name == "Food"


def test_delete_expense(repositories, owner_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 100, owner_id)

    repository.add(expense)
    repository.delete(expense)

    result = repository.find_by_id(expense.id, owner_id)

    assert result is None


def test_delete_expense_leaves_another_users_expense_alone(repositories, owner_id, other_user_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 100, other_user_id)
    repository.add(expense)

    # Deleting by id as a different user must not remove someone else's row.
    repository.delete(make_expense(expense.id, "Food", 100, owner_id))

    assert repository.find_by_id(expense.id, other_user_id) is not None


def test_update_expense(repositories, owner_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 1000, owner_id, "2026-03-02")
    repository.add(expense)

    expense.amount = 2500
    repository.update(expense)

    stored = repository.find_by_id(expense.id, owner_id)

    assert stored.amount == 2500
    assert stored.date == "2026-03-02"


def test_date_is_persisted(repositories, owner_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 1000, owner_id, "2026-07-14")
    repository.add(expense)

    assert repository.find_by_id(expense.id, owner_id).date == "2026-07-14"


def test_category_and_payment_type_are_persisted(repositories, owner_id):
    repository, _ = repositories

    expense = make_expense(
        1, "Food", 1000, owner_id, category="Rent", payment_type="Mobile Money"
    )
    repository.add(expense)

    stored = repository.find_by_id(expense.id, owner_id)

    assert stored.category == "Rent"
    assert stored.payment_type == "Mobile Money"


def test_update_persists_category_and_payment_type(repositories, owner_id):
    repository, _ = repositories

    expense = make_expense(1, "Food", 1000, owner_id)
    repository.add(expense)

    expense.category = "Transport"
    expense.payment_type = "Card"
    repository.update(expense)

    stored = repository.find_by_id(expense.id, owner_id)

    assert stored.category == "Transport"
    assert stored.payment_type == "Card"


def test_search_by_name_is_case_insensitive(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 100, owner_id))
    repository.add(make_expense(2, "Seafood", 200, owner_id))
    repository.add(make_expense(3, "Rent", 300, owner_id))

    matches = repository.search_by_name("foo", owner_id)

    assert [expense.name for expense in matches] == ["Food", "Seafood"]


def test_search_by_name_treats_wildcards_literally(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 100, owner_id))
    repository.add(make_expense(2, "50% off", 200, owner_id))

    # Unescaped, "%" would match every row instead of the literal one.
    matches = repository.search_by_name("%", owner_id)

    assert [expense.name for expense in matches] == ["50% off"]


def test_search_by_name_scoped_to_the_user(repositories, owner_id, other_user_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 100, other_user_id))

    assert repository.search_by_name("food", owner_id) == []


def test_count_by_name_ignores_case(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 100, owner_id))
    repository.add(make_expense(2, "food", 200, owner_id))
    repository.add(make_expense(3, "Rent", 300, owner_id))

    assert repository.count_by_name("FOOD", owner_id) == 2


def test_count_by_name_matches_a_whole_name(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Seafood", 100, owner_id))

    assert repository.count_by_name("food", owner_id) == 0


def test_get_top_month_groups_by_month(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, owner_id, "2026-01-10"))
    repository.add(make_expense(2, "Fuel", 400, owner_id, "2026-02-01"))
    repository.add(make_expense(3, "Rent", 400, owner_id, "2026-02-20"))

    assert repository.get_top_month(owner_id) == ("2026-02", 800)


def test_get_top_month_without_expenses(repositories, owner_id):
    repository, _ = repositories

    assert repository.get_top_month(owner_id) is None


def test_get_highest_expense(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, owner_id))
    highest = make_expense(2, "Rent", 900, owner_id)
    repository.add(highest)

    assert repository.get_highest(owner_id) == highest


def test_get_highest_expense_without_expenses(repositories, owner_id):
    repository, _ = repositories

    assert repository.get_highest(owner_id) is None


# --- Merchant and note ------------------------------------------------------


def test_merchant_and_note_are_persisted(repositories, owner_id):
    repository, _ = repositories

    repository.add(
        make_expense(1, "Food", 1000, owner_id, merchant="Shoprite", note="weekly shop")
    )

    stored = repository.find_by_id(1, owner_id)

    assert stored.merchant == "Shoprite"
    assert stored.note == "weekly shop"


def test_merchant_and_note_default_to_none(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 1000, owner_id))

    stored = repository.find_by_id(1, owner_id)

    assert stored.merchant is None
    assert stored.note is None


def test_update_persists_merchant_and_note(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 1000, owner_id))

    expense = repository.find_by_id(1, owner_id)
    expense.merchant = "Shoprite"
    expense.note = "weekly shop"
    repository.update(expense)

    stored = repository.find_by_id(1, owner_id)

    assert stored.merchant == "Shoprite"
    assert stored.note == "weekly shop"


def test_update_can_clear_merchant_and_note(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 1000, owner_id, merchant="Shoprite", note="weekly"))

    expense = repository.find_by_id(1, owner_id)
    expense.merchant = None
    expense.note = None
    repository.update(expense)

    stored = repository.find_by_id(1, owner_id)

    assert stored.merchant is None
    assert stored.note is None


# --- The lowest expense -----------------------------------------------------


def test_get_lowest_expense(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Rent", 9000, owner_id))
    lowest = make_expense(2, "Snack", 100, owner_id)
    repository.add(lowest)

    assert repository.get_lowest(owner_id) == lowest


def test_get_lowest_expense_prefers_the_lower_id_on_a_tie(repositories, owner_id):
    repository, _ = repositories

    first = make_expense(1, "Snack", 100, owner_id)
    repository.add(first)
    repository.add(make_expense(2, "Water", 100, owner_id))

    assert repository.get_lowest(owner_id) == first


def test_get_lowest_expense_without_expenses(repositories, owner_id):
    repository, _ = repositories

    assert repository.get_lowest(owner_id) is None


def test_get_lowest_expense_ignores_another_users(repositories, owner_id, other_user_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Snack", 100, other_user_id))

    assert repository.get_lowest(owner_id) is None


# --- Comparing months -------------------------------------------------------


def test_get_month_totals_ranks_every_month(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, owner_id, "2026-01-10"))
    repository.add(make_expense(2, "Fuel", 400, owner_id, "2026-02-01"))
    repository.add(make_expense(3, "Rent", 400, owner_id, "2026-02-20"))
    repository.add(make_expense(4, "Bus", 900, owner_id, "2026-03-05"))

    assert repository.get_month_totals(owner_id) == [
        ("2026-03", 900),
        ("2026-02", 800),
        ("2026-01", 300),
    ]


def test_get_month_totals_break_a_tie_on_the_most_recent_month(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 500, owner_id, "2026-01-05"))
    repository.add(make_expense(2, "Rent", 500, owner_id, "2026-03-05"))

    assert repository.get_month_totals(owner_id) == [("2026-03", 500), ("2026-01", 500)]


def test_get_month_totals_agree_with_get_top_month(repositories, owner_id):
    """The ranking's first row has to be the month get_top_month reports."""
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, owner_id, "2026-01-10"))
    repository.add(make_expense(2, "Rent", 900, owner_id, "2026-03-05"))

    assert repository.get_month_totals(owner_id)[0] == repository.get_top_month(owner_id)


def test_get_month_totals_without_expenses(repositories, owner_id):
    repository, _ = repositories

    assert repository.get_month_totals(owner_id) == []


def test_get_month_totals_ignore_another_users_expenses(repositories, owner_id, other_user_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Rent", 9000, other_user_id, "2026-05-01"))

    assert repository.get_month_totals(owner_id) == []


# --- The busiest day of the week -------------------------------------------


def test_get_top_weekday_names_the_busiest_day(repositories, owner_id):
    repository, _ = repositories

    # Two Saturdays (400 + 300) beat the single Sunday of 500.
    repository.add(make_expense(1, "Food", 400, owner_id, "2026-07-04"))
    repository.add(make_expense(2, "Fuel", 300, owner_id, "2026-07-11"))
    repository.add(make_expense(3, "Rent", 500, owner_id, "2026-07-05"))

    assert repository.get_top_weekday(owner_id) == ("Saturday", 700)


def test_get_top_weekday_tie_prefers_the_earlier_weekday(repositories, owner_id):
    repository, _ = repositories

    # Sunday and Saturday both total 500; Sunday comes first in the week.
    repository.add(make_expense(1, "Food", 500, owner_id, "2026-07-05"))
    repository.add(make_expense(2, "Rent", 500, owner_id, "2026-07-04"))

    assert repository.get_top_weekday(owner_id) == ("Sunday", 500)


def test_get_top_weekday_without_expenses(repositories, owner_id):
    repository, _ = repositories

    assert repository.get_top_weekday(owner_id) is None


def test_get_top_weekday_ignores_another_users_expenses(repositories, owner_id, other_user_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Rent", 9000, other_user_id, "2026-07-04"))

    assert repository.get_top_weekday(owner_id) is None


# --- Daily totals -----------------------------------------------------------


def test_get_daily_totals_sums_each_day(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, owner_id, "2026-07-04"))
    repository.add(make_expense(2, "Fuel", 200, owner_id, "2026-07-04"))
    repository.add(make_expense(3, "Rent", 900, owner_id, "2026-07-18"))

    assert repository.get_daily_totals("2026-07", owner_id) == [
        ("2026-07-04", 500),
        ("2026-07-18", 900),
    ]


def test_get_daily_totals_ignore_other_months(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, owner_id, "2026-06-30"))

    assert repository.get_daily_totals("2026-07", owner_id) == []


def test_get_daily_totals_ignore_another_users_expenses(repositories, owner_id, other_user_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 300, other_user_id, "2026-07-04"))

    assert repository.get_daily_totals("2026-07", owner_id) == []


# --- Deleting everything ----------------------------------------------------


def test_delete_all_removes_every_expense_of_that_user(repositories, owner_id):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 100, owner_id))
    repository.add(make_expense(2, "Rent", 900, owner_id))

    assert repository.delete_all(owner_id) == 2
    assert repository.get_all(owner_id) == []


def test_delete_all_leaves_another_users_expenses_alone(
    repositories, owner_id, other_user_id
):
    repository, _ = repositories

    repository.add(make_expense(1, "Food", 100, owner_id))
    repository.add(make_expense(2, "Rent", 900, other_user_id))

    repository.delete_all(owner_id)

    assert repository.find_by_id(2, other_user_id) is not None


def test_delete_all_without_expenses_reports_nothing_deleted(repositories, owner_id):
    repository, _ = repositories

    assert repository.delete_all(owner_id) == 0
