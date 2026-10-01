import datetime
import decimal


CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Rent",
    "Health",
    "Entertainment",
    "Other",
)

PAYMENT_TYPES = (
    "Cash",
    "Card",
    "Transfer",
    "Mobile Money",
    "Other",
)


# Money is stored as a whole number of minor units — kobo, since the currency
# is the naira — and never as a float.
#
# A float cannot represent 0.1 exactly, so "ten kobo plus twenty kobo" summed
# to 0.30000000000000004, and a month's total drifted by whatever the additions
# happened to accumulate. In a ledger that is not a rounding nicety, it is a
# wrong answer. An integer count of kobo is exact under addition, comparison
# and SUM(), which is every operation this application performs on money.
#
# The name carries the unit on purpose: `expense.amount` reading as naira in
# one file and kobo in another is exactly the bug this prevents.
MAX_AMOUNT_CENTS = 100_000_000_000  # ₦1,000,000,000


_HUNDRED = decimal.Decimal(100)


def parse_amount_cents(value):
    """
    Reads an amount someone typed ("2500", "2500.5", "2500.50") as whole kobo,
    or returns None when it is not a usable amount.

    Decimal rather than float, and for the same reason money is stored as an
    integer: `float("0.1") * 100` is 10.000000000000002, so parsing through a
    float reintroduces at the front door the imprecision the column was changed
    to eliminate. Decimal reads the typed digits exactly, and only the final
    conversion to int can round — which it is not allowed to do here.

    A third decimal place is refused rather than rounded away. Quietly turning
    "10.005" into 1000 kobo loses money and tells nobody.

    Also the guard against the values that used to reach the database:
    "nan", "inf" and "-inf" all parse as Decimals, and `is_finite` is what
    rejects them.
    """
    if not isinstance(value, str):
        return None

    text = value.strip()

    if not text:
        return None

    try:
        amount = decimal.Decimal(text)
    except decimal.InvalidOperation:
        return None

    if not amount.is_finite():
        return None

    cents = amount * _HUNDRED

    if cents != cents.to_integral_value():
        return None

    return int(cents)


def valid_amount_cents(value):
    """
    Whether `value` is an amount this application is willing to store: a whole
    number of kobo, positive, and no larger than the ceiling.

    bool is excluded explicitly. It is a subclass of int, so `isinstance(True,
    int)` is True and `amount_cents=True` would otherwise sail through as one
    kobo — a bug that reads as a working call.

    Floats are excluded for the reason the column is an integer at all. 2500.5
    kobo is not an amount that exists, and letting it reach SQLite would turn a
    readable validation failure into a StorageError raised from the CHECK
    constraint — worse, a float that *is* whole would be silently accepted here
    and only rejected by the column, so the rule would live in two places.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        return False

    return 0 < value <= MAX_AMOUNT_CENTS



# Indexed the way SQLite's strftime('%w') numbers weekdays: Sunday is 0.
WEEKDAYS = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)


def canonical_value(value, allowed):
    """
    Maps a user-supplied value onto its canonical spelling from `allowed`,
    ignoring case and surrounding whitespace, or returns None when the value
    isn't allowed at all.

    Storing the canonical spelling is the whole point of a fixed set:
    "food" and "Food" must not end up as two different categories, or any
    later grouping by category would be meaningless.
    """
    if not isinstance(value, str):
        return None

    lookup = {
        allowed_value.lower(): allowed_value
        for allowed_value in allowed
    }

    return lookup.get(value.strip().lower())


def canonical_category(value):
    return canonical_value(value, CATEGORIES)


def canonical_payment_type(value):
    return canonical_value(value, PAYMENT_TYPES)


def weekday_name(number):
    """Turns a weekday number (Sunday = 0) into its name."""
    return WEEKDAYS[int(number)]


def canonical_month(value):
    """
    Normalizes a "YYYY-MM" month onto its zero-padded spelling ("2026-7" ->
    "2026-07"), or returns None when it isn't a month at all.

    Expenses store dates as "YYYY-MM-DD", so every month grouping compares
    against this same string form — accepting an unpadded month here keeps
    that comparison from silently matching nothing.
    """
    if not isinstance(value, str):
        return None

    try:
        return datetime.datetime.strptime(value.strip(), "%Y-%m").strftime("%Y-%m")
    except ValueError:
        return None


def clean_optional_text(value):
    """
    Trims an optional free-text field, mapping a blank or missing value onto
    None so "no merchant" is stored one way rather than as "" or " ".
    """
    if not isinstance(value, str):
        return None

    stripped = value.strip()

    return stripped or None


class Expense:
    def __init__(
        self,
        expense_id,
        name,
        amount_cents,
        user_id,
        date,
        category,
        payment_type,
        merchant=None,
        note=None,
    ):
        self.id = expense_id
        self.name = name
        # A whole number of kobo. See MAX_AMOUNT_CENTS for why this is not a
        # float; app.ui.formatting turns it into "₦2,500.50" at the edge.
        self.amount_cents = amount_cents
        self.user_id = user_id
        # Stored as an ISO string ("YYYY-MM-DD") rather than a datetime.date:
        # SQLite hands rows back as strings, so row mapping stays uniform.
        self.date = date
        self.category = category
        self.payment_type = payment_type
        # Optional, and genuinely optional: an expense need not say who was
        # paid or why, so these default to None rather than "Other".
        self.merchant = merchant
        self.note = note

    def __eq__(self, other):
        if not isinstance(other, Expense):
            return False

        return (
            self.id == other.id
            and self.name == other.name
            and self.amount_cents == other.amount_cents
            and self.user_id == other.user_id
            and self.date == other.date
            and self.category == other.category
            and self.payment_type == other.payment_type
            and self.merchant == other.merchant
            and self.note == other.note
        )
