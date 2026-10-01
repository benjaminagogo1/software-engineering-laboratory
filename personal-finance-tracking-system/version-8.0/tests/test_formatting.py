from app.models.expense import Expense
from app.ui.formatting import format_money, format_money_tick, format_expense_line


def make_expense(merchant=None, note=None):
    return Expense(
        1, "Food", 2500.0, 7, "2026-07-14", "Food", "Cash", merchant, note
    )


def test_amounts_are_grouped_and_carry_the_currency():
    assert format_money(2500) == "₦2,500.00"
    assert format_money(1234567.5) == "₦1,234,567.50"


def test_axis_ticks_drop_the_decimals():
    assert format_money_tick(12500.0) == "₦12,500"


def test_an_expense_line_shows_every_attribute():
    assert format_expense_line(make_expense()) == (
        "1: Food - ₦2,500.00 (2026-07-14, Food, Cash)"
    )


def test_an_expense_line_adds_merchant_and_note_when_they_are_there():
    line = format_expense_line(
        make_expense(merchant="Shoprite", note="weekly shop")
    )

    assert line == (
        "1: Food - ₦2,500.00 (2026-07-14, Food, Cash, at Shoprite, weekly shop)"
    )
