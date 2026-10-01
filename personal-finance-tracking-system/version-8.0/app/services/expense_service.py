from app.services.results import UpdateResult
from app.services.results import AddResult

from app.services.results import DeleteResult
from app.models.expense import (
    canonical_category,
    canonical_payment_type,
    canonical_month,
    clean_optional_text,
    valid_amount_cents,
)
from app.models.audit_event import (
    AuditEvent,
    EXPENSE_CREATED,
    EXPENSE_DELETED,
    EXPENSE_UPDATED,
    EXPENSES_DELETED_ALL,
)
from app.repositories.expense_repository import ExpenseRepository
from app.services.audited_service import AuditedService
import logging

logger = logging.getLogger(__name__)

class ExpenseService(AuditedService):

    def __init__(self, repository: ExpenseRepository, audit):
        super().__init__(audit)

        self.repository = repository

    def add_expense(self, expense):
        if not expense.name.strip():
            return AddResult.INVALID_NAME

        if not valid_amount_cents(expense.amount_cents):
            return AddResult.INVALID_AMOUNT

        category = canonical_category(expense.category)

        if category is None:
            return AddResult.INVALID_CATEGORY

        payment_type = canonical_payment_type(expense.payment_type)

        if payment_type is None:
            return AddResult.INVALID_PAYMENT_TYPE

        # Store the canonical spelling so "food" and "Food" can never become
        # two different categories.
        expense.category = category
        expense.payment_type = payment_type

        # Merchant and note carry no fixed set, so they are only tidied: a
        # blank one becomes None rather than an empty string.
        expense.merchant = clean_optional_text(expense.merchant)
        expense.note = clean_optional_text(expense.note)

        self.repository.add(expense)
        logger.info("Expense added successfully: id=%s,", expense.id)

        self._record(AuditEvent(
            action=EXPENSE_CREATED,
            user_id=expense.user_id,
            entity_type="expense",
            entity_id=expense.id,
            detail={
                "name": expense.name,
                "amount_cents": expense.amount_cents,
                "date": expense.date,
                "category": expense.category,
            },
        ))

        return AddResult.SUCCESS

    def get_all_expenses(self, user_id):
        return self.repository.get_all(user_id)

    def get_expense_by_id(self, expense_id, user_id):
        return self.repository.find_by_id(expense_id, user_id)

    def get_top_month(self, user_id):
        """The month with the highest total spending, as (month, total)."""
        return self.repository.get_top_month(user_id)

    def get_month_totals(self, user_id):
        """Every month's total spending, highest first."""
        return self.repository.get_month_totals(user_id)

    def get_top_weekday(self, user_id):
        """The weekday with the highest total spending, as (name, total)."""
        return self.repository.get_top_weekday(user_id)

    def get_daily_totals(self, month, user_id):
        """
        Per-day totals within `month`, as ("YYYY-MM-DD", total) rows.

        Returns None when `month` isn't a month, so a caller can tell a bad
        argument apart from a month that simply has no expenses (which is an
        empty list).
        """
        canonical = canonical_month(month)

        if canonical is None:
            return None

        return self.repository.get_daily_totals(canonical, user_id)

    def get_highest_expense(self, user_id):
        """The single most expensive expense."""
        return self.repository.get_highest(user_id)

    def get_lowest_expense(self, user_id):
        """The single cheapest expense."""
        return self.repository.get_lowest(user_id)

    def count_by_name(self, name, user_id):
        """How many times this expense name occurs, ignoring case."""
        return self.repository.count_by_name(name, user_id)

    def search_by_name(self, name, user_id):
        """Every expense whose name contains `name`, ignoring case."""
        if not name.strip():
            return []

        return self.repository.search_by_name(name, user_id)

    def delete_expense_by_id(self, expense_id, user_id):
        expense = self.repository.find_by_id(expense_id, user_id)

        if expense is None:
            return DeleteResult.NOT_FOUND

        # The whole row, read before the DELETE, because after it this is the
        # only copy left. A trail entry that says only "expense 14 deleted"
        # cannot answer the question the trail exists to answer — what was it,
        # and how much — and an audit row that cannot reconstruct the thing it
        # describes is bookkeeping, not evidence.
        snapshot = {
            "name": expense.name,
            "amount_cents": expense.amount_cents,
            "date": expense.date,
            "category": expense.category,
            "payment_type": expense.payment_type,
            "merchant": expense.merchant,
            "note": expense.note,
        }

        self.repository.delete(expense)

        logger.info("Expense deleted successfully: id=%s", expense.id)

        self._record(AuditEvent(
            action=EXPENSE_DELETED,
            user_id=user_id,
            entity_type="expense",
            entity_id=expense.id,
            detail=snapshot,
        ))

        return DeleteResult.SUCCESS

    def delete_all_expenses(self, user_id):
        """
        Removes every expense this user owns and reports how many went.

        Only ever the calling user's own — clearing one account must never
        touch another's.
        """
        deleted = self.repository.delete_all(user_id)

        logger.info("Deleted %s expense(s) for user %s", deleted, user_id)

        # The count, not a copy of every row. Bulk-clearing an account is a
        # single deliberate act, and the expenses themselves are already in the
        # trail as their own expense.created rows — copying them again here
        # would double the storage for no new information. What this row adds
        # is the fact of the sweep and how much it took, which nothing else
        # records.
        self._record(AuditEvent(
            action=EXPENSES_DELETED_ALL,
            user_id=user_id,
            entity_type="expense",
            detail={"deleted": deleted},
        ))

        return deleted

    def update_expense(
        self,
        expense_id,
        amount_cents,
        user_id,
        category=None,
        payment_type=None,
        merchant=None,
        note=None,
        name=None,
        date=None,
    ):
        """
        Updates an expense. A None argument leaves that field alone — with one
        deliberate exception: merchant and note can be *cleared* by passing an
        empty string, because "remove the note" is a real edit and there would
        otherwise be no way to express it.

        name and date are editable too, so a typo in what you bought or a
        mis-keyed date can be corrected rather than deleted and re-entered.
        Neither can be cleared: an expense always has both. The date arrives
        already validated by the caller that parsed it — this layer has no
        calendar of its own to check it against.

        The amount is the one field with no None case: an update always carries
        an amount, so there is no "leave it alone" spelling for it, and a caller
        that has no new amount has no business calling update at all.
        """
        if not valid_amount_cents(amount_cents):
            return UpdateResult.INVALID_AMOUNT

        if name is not None:
            stripped = name.strip()

            if not stripped:
                return UpdateResult.INVALID_NAME

            canonical_name = stripped
        else:
            canonical_name = None

        if category is not None:
            canonical = canonical_category(category)

            if canonical is None:
                return UpdateResult.INVALID_CATEGORY
        else:
            canonical = None

        if payment_type is not None:
            canonical_payment = canonical_payment_type(payment_type)

            if canonical_payment is None:
                return UpdateResult.INVALID_PAYMENT_TYPE
        else:
            canonical_payment = None

        expense = self.repository.find_by_id(expense_id, user_id)

        if expense is None:
            return UpdateResult.NOT_FOUND

        # Each edit is recorded with the value it replaced, and only when it
        # actually replaced something. `changes` is built here, before any
        # assignment, because each `expense.x` below overwrites the old value —
        # after the first assignment the original is gone.
        changes = {}

        def change(field_name, old, new):
            if old != new:
                changes[field_name] = {"from": old, "to": new}

        change("amount_cents", expense.amount_cents, amount_cents)
        expense.amount_cents = amount_cents

        # Only the fields actually supplied are changed.
        if canonical_name is not None:
            change("name", expense.name, canonical_name)
            expense.name = canonical_name

        if date is not None:
            change("date", expense.date, date)
            expense.date = date

        if canonical is not None:
            change("category", expense.category, canonical)
            expense.category = canonical

        if canonical_payment is not None:
            change("payment_type", expense.payment_type, canonical_payment)
            expense.payment_type = canonical_payment

        if merchant is not None:
            cleaned_merchant = clean_optional_text(merchant)
            change("merchant", expense.merchant, cleaned_merchant)
            expense.merchant = cleaned_merchant

        if note is not None:
            cleaned_note = clean_optional_text(note)
            change("note", expense.note, cleaned_note)
            expense.note = cleaned_note

        self.repository.update(expense)

        logger.info("Expense updated successfully: id=%s", expense.id)

        # A no-op update is not an audit event. A form re-submitted unchanged
        # shouldn't leave a row implying someone altered the record, or a real
        # edit becomes harder to find among them.
        if changes:
            self._record(AuditEvent(
                action=EXPENSE_UPDATED,
                user_id=user_id,
                entity_type="expense",
                entity_id=expense.id,
                detail=changes,
            ))

        return UpdateResult.SUCCESS
