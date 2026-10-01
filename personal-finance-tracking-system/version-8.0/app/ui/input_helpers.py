from datetime import date

from app.models.expense import canonical_value, canonical_month, parse_amount_cents


def read_int(prompt):
    value = input(prompt)

    try:
        return int(value)
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

def read_amount_cents(prompt):
    """
    Reads an amount typed in naira ("2500", "2500.50") and returns whole kobo.

    This replaced a `read_float` that returned the number as an IEEE-754 float
    — the value that went on to be stored. Decimal reads the typed digits
    exactly, so "10.10" arrives as 1010 kobo rather than as the nearest double
    to 10.1 scaled by a hundred.

    parse_amount_cents is also what refuses "nan" and "inf", both of which
    parse happily as floats and neither of which is an amount.
    """
    amount_cents = parse_amount_cents(input(prompt))

    if amount_cents is None:
        print("Invalid input. Please enter an amount, such as 2500 or 2500.50.")
        return None

    return amount_cents

def read_date(prompt):
    """Returns an ISO date string. A blank answer means today."""
    value = input(prompt).strip()

    if not value:
        return date.today().isoformat()

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        print("Invalid input. Please enter a date as YYYY-MM-DD.")
        return None

def read_month(prompt, default=None):
    """Returns a "YYYY-MM" month. A blank answer means the current month."""
    value = input(prompt).strip()

    if not value:
        return default if default is not None else date.today().strftime("%Y-%m")

    month = canonical_month(value)

    if month is None:
        print("Invalid input. Please enter a month as YYYY-MM.")
        return None

    return month

def read_choice(prompt, allowed, default=None):
    """
    Prompts for one of `allowed`, accepting any casing and returning the
    canonical spelling. A blank answer falls back to `default`, or to the last
    option (normally "Other") when no default is given.
    """
    print(f"Options: {', '.join(allowed)}")

    value = input(prompt).strip()

    if not value:
        return default if default is not None else allowed[-1]

    canonical = canonical_value(value, allowed)

    if canonical is None:
        print(f"Invalid input. Choose one of: {', '.join(allowed)}")
        return None

    return canonical

