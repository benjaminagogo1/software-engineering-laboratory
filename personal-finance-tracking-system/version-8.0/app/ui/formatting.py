"""
One place that decides how money and expenses are written out.

Before this existed the naira symbol was hardcoded in a single CLI print
statement, so `list` showed "N2,500.00" while `get`, `search`, `highest` and
`top-month` showed a bare "2,500.00". Currency belongs in one function.

Every function here takes **kobo**, the integer minor unit the rest of the
application stores and passes around, and none of them divides by 100 to get
there. `cents / 100` would put a float back into the one path whose whole point
is that no float touches the number — the rounding would simply move from the
ledger to the screen. `divmod` splits the integer instead.
"""

from app.models.expense import MAX_AMOUNT_CENTS

# The naira sign. Swap this one constant to change the currency everywhere.
CURRENCY_SYMBOL = "₦"


def format_money(amount_cents):
    """Formats kobo as ₦2,500.50 — grouped thousands, two decimals."""
    sign = "-" if amount_cents < 0 else ""
    whole, fraction = divmod(abs(int(amount_cents)), 100)

    return f"{CURRENCY_SYMBOL}{sign}{whole:,}.{fraction:02d}"


def format_money_tick(amount_cents):
    """
    The compact form used on a chart axis, where the kobo are noise:
    ₦12,500 rather than ₦12,500.00.

    Rounds to the nearest naira rather than truncating, so 12,499.99 reads as
    ₦12,500 — the same thing `:,.0f` did when this took a float.
    """
    sign = "-" if amount_cents < 0 else ""
    whole = (abs(int(amount_cents)) + 50) // 100

    return f"{CURRENCY_SYMBOL}{sign}{whole:,}"


def format_expense_line(expense):
    """One line per expense, carrying every attribute it has."""
    line = (
        f"{expense.id}: {expense.name} - {format_money(expense.amount_cents)} "
        f"({expense.date}, {expense.category}, {expense.payment_type}"
    )

    if expense.merchant:
        line += f", at {expense.merchant}"

    if expense.note:
        line += f", {expense.note}"

    return line + ")"


# The sentence both terminal surfaces print when an amount is refused. Written
# once because it is the same refusal in four places — the add and update flows
# of the menu and of the CLI — and four hand-written copies is how the ceiling
# ends up mentioned in two of them.
#
# Both numbers are shown: the kobo count is what the API and the database deal
# in, and the formatted one is what the person actually typed in.
AMOUNT_RULE = (
    f"Amount must be a whole number of kobo, from 1 to {MAX_AMOUNT_CENTS} "
    f"({format_money(MAX_AMOUNT_CENTS)})."
)
