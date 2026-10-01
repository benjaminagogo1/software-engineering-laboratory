import logging

logger = logging.getLogger(__name__)


class AuditedService:
    """
    The base for every service that writes to the audit trail.

    Only two services do today, which is not enough on its own to justify a
    base class — but the thing being shared here is a *policy*, not code. Both
    services have to make the same choice about what happens when the trail
    write fails, and if that choice is written down twice it will eventually be
    made twice. One definition, one docstring, one place to change it.

    `audit` is required rather than defaulted to None. The terminal client and
    the API both write through these services, so a trail built here covers
    both surfaces. An optional argument would let a composition root forget it
    and produce a service that looks audited and is not — and a trail with a
    hole nobody knows about is worse than no trail, because it gets trusted.
    """

    def __init__(self, audit):
        self.audit = audit

    def _record(self, event):
        """
        Records an event, and never lets the recording undo the work.

        The write already happened by the time this is called, so raising here
        would answer the caller with a failure for work that succeeded — and a
        client that retries a "failed" create makes a duplicate. So a failure
        is logged loudly and the operation stands.

        That leaves a gap, and the gap is the trade-off. It is visible because
        it is logged at ERROR with the traceback, which is the one thing the
        operational log is genuinely for. Closing it properly means writing the
        change and its audit row in one transaction, which needs a unit of work
        this codebase does not have yet.
        """
        try:
            self.audit.record(event)
        except Exception:
            logger.exception(
                "AUDIT GAP: %s for user %s was not recorded",
                event.action,
                event.user_id,
            )
