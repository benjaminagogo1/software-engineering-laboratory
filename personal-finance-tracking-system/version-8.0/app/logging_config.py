import logging
import logging.handlers
import sys

import config

# Marks the handlers this module added, so setup_logging can remove exactly
# those and nothing else.
#
# The obvious alternative — a module-level `_configured` flag — is wrong the
# moment anything calls setup_logging twice with different arguments. The test
# suite does exactly that (a different log file per test), and with a flag the
# second call is a no-op and every test after the first writes to the first
# test's file. Removing our own handlers by identity is idempotent in the way
# that actually matters: the final state is a function of the last call's
# arguments, not of how many times it was called.
_OWNED = "_expense_tracker_handler"


def _remove_owned_handlers(root):
    for handler in list(root.handlers):
        if getattr(handler, _OWNED, False):
            root.removeHandler(handler)
            handler.close()


def _handler(path, formatter, level):
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)

    setattr(handler, _OWNED, True)

    return handler


def setup_logging(log_path=None, to_stdout=None, level=None):
    """
    Points the root logger at the operational log and returns it.

    Idempotent: calling it again replaces this module's own handlers rather
    than adding a second set, so a line is never written twice.

    **Only the root logger is configured, and nothing here is silenced.** The
    file is written to by every module that logs, which is the point — the
    question "what did the app do" is not answerable from one module's output.
    The one exception is uvicorn's access log, turned off further down for a
    reason that has nothing to do with volume.

    Call this from the application's startup, never at import. Import-time
    configuration means anything that imports `app.api` — every test, every
    tool — inherits a log file in the project directory and a root logger it
    did not ask for. Startup is the first moment the process actually knows
    what it is.
    """
    path = config.LOG_PATH if log_path is None else log_path
    stdout = config.LOG_TO_STDOUT if to_stdout is None else to_stdout
    name = config.LOG_LEVEL if level is None else level

    resolved_level = config.LOG_LEVELS.get(str(name).strip().upper(), logging.INFO)

    formatter = logging.Formatter(config.LOG_FORMAT)

    root = logging.getLogger()
    root.setLevel(resolved_level)

    _remove_owned_handlers(root)

    root.addHandler(_handler(path, formatter, resolved_level))

    if stdout:
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        stream.setLevel(resolved_level)

        setattr(stream, _OWNED, True)

        root.addHandler(stream)

    _quiet_uvicorn()

    return root


def _quiet_uvicorn():
    """
    Hands the request log over to our own middleware.

    uvicorn's access log records the client address, the method, the path and
    the status — and cannot record the user, because it runs below the
    application and has never heard of one. It also formats a fixed line with
    no room for a duration. Since app.api's middleware logs the same request
    with the authenticated user and how long it took, keeping both means every
    request appears twice, once of them strictly worse.

    Nothing is lost by dropping it: the address is in our line too, and the
    lines it wrote before are still in the file. This is the only logger this
    module disables, and it is disabled because it is *replaced*, not because
    it is noisy.

    `propagate` is set on the parent so uvicorn's own error and startup records
    reach the root handlers above; without it they are swallowed by the
    `uvicorn` logger's default configuration and never reach the file.
    """
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn").propagate = True


def reset_logging():
    """
    Removes this module's handlers and puts the root logger back to a bare
    state. For test teardown — a suite that configured logging for one test
    would otherwise leave a handle on that test's tmp_path and write into a
    directory pytest is trying to delete.
    """
    root = logging.getLogger()

    _remove_owned_handlers(root)

    root.setLevel(logging.WARNING)
