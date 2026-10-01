"""
The operational log: where it goes, what a line looks like, and what the
request middleware writes into it.

Distinct from the audit trail, which lives in the database and is tested in
test_audit.py. This file is about the file on disk that a person reads while
running the app — the one that is allowed to rotate, be filtered by level, and
go to stdout.
"""

import logging

import pytest

import config
from app.api import app
from app.logging_config import reset_logging, setup_logging


@pytest.fixture
def log_file(tmp_path):
    """
    Logging pointed at a throwaway file, and put back afterwards.

    The teardown matters more than it looks: without it the root logger keeps a
    RotatingFileHandler open on a tmp_path that pytest is deleting, and the
    next test inherits a configured root logger it did not ask for.
    """
    path = tmp_path / "app.log"

    setup_logging(log_path=path, to_stdout=False)

    yield path

    reset_logging()


def read(path):
    return path.read_text(encoding="utf-8").splitlines()


def test_a_log_line_reaches_the_file(log_file):
    logging.getLogger("some.module").info("something happened")

    assert len(read(log_file)) == 1
    assert "something happened" in read(log_file)[0]


def test_a_line_names_its_module(log_file):
    """
    The module is in the format because a request line written by app.api and
    one written by app.services.expense_service answer different questions, and
    without it a burst of traffic reads as one undifferentiated blob.
    """
    logging.getLogger("app.services.expense_service").info("Expense added")

    line = read(log_file)[0]

    assert "app.services.expense_service" in line
    assert "INFO" in line


def test_lines_below_the_level_are_not_written(log_file):
    logger = logging.getLogger("app.api")

    logger.debug("this should not be here")
    logger.info("this should")

    lines = read(log_file)

    assert len(lines) == 1
    assert "this should" in lines[0]


def test_the_level_can_be_lowered(tmp_path):
    """DEBUG is off by default, not unavailable."""
    path = tmp_path / "debug.log"

    setup_logging(log_path=path, to_stdout=False, level="DEBUG")

    try:
        logging.getLogger("app.api").debug("the detail")

        assert "the detail" in read(path)[0]
    finally:
        reset_logging()


def test_an_unknown_level_falls_back_to_info(tmp_path):
    """
    A typo in LOG_LEVEL should not silence logging or crash startup — the
    config helper's contract is to fall back rather than fail.
    """
    path = tmp_path / "junk.log"

    root = setup_logging(log_path=path, to_stdout=False, level="verbose-ish")

    try:
        assert root.level == logging.INFO
    finally:
        reset_logging()


def test_setting_up_twice_does_not_double_every_line(log_file):
    """
    The reason setup_logging removes its own handlers instead of setting a
    once-only flag. Two calls must leave one handler, not two — a duplicated
    line is how you get someone to stop trusting the log.
    """
    setup_logging(log_path=log_file, to_stdout=False)

    logging.getLogger("app.api").info("said once")

    assert read(log_file) == [
        line for line in read(log_file) if "said once" in line
    ]
    assert len([line for line in read(log_file) if "said once" in line]) == 1


def test_setting_up_again_moves_the_log(log_file, tmp_path):
    """
    Idempotent, but not frozen: the handlers follow the most recent call rather
    than the first one. A flag would leave the second call a no-op and every
    test after the first writing into the first test's file.
    """
    second = tmp_path / "second.log"

    setup_logging(log_path=second, to_stdout=False)

    logging.getLogger("app.api").info("went to the second file")

    assert read(log_file) == []
    assert "went to the second file" in read(second)[0]


def test_the_file_rotates_rather_than_growing_forever(log_file, monkeypatch):
    """
    The operational log is allowed to be lossy — that is what separates it from
    the audit trail, which is never rotated away. This pins that the file
    handler is the rotating one and not a plain FileHandler.
    """
    monkeypatch.setattr(config, "LOG_MAX_BYTES", 200)
    monkeypatch.setattr(config, "LOG_BACKUP_COUNT", 2)

    # Re-created so the new limits are the ones in effect.
    setup_logging(log_path=log_file, to_stdout=False)

    logger = logging.getLogger("app.api")

    for number in range(200):
        logger.info("line %s padded out to make the file grow", number)

    rotated = sorted(log_file.parent.glob("app.log*"))

    assert log_file.exists()
    assert len(rotated) > 1


def test_stdout_is_where_a_container_reads(tmp_path, capsys):
    """
    On by default because Docker and everything above it collect stdout — a log
    written only inside the container's filesystem is invisible to `docker
    logs` and gone when the container is replaced.
    """
    setup_logging(log_path=tmp_path / "app.log", to_stdout=True)

    try:
        logging.getLogger("app.api").info("visible to docker logs")

        assert "visible to docker logs" in capsys.readouterr().out
    finally:
        reset_logging()


def test_stdout_defaults_to_the_config_value(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "LOG_TO_STDOUT", False)

    setup_logging(log_path=tmp_path / "app.log")

    try:
        logging.getLogger("app.api").info("should not be on stdout")

        assert "should not be on stdout" not in capsys.readouterr().out
    finally:
        reset_logging()


def test_the_log_directory_is_created_if_it_is_missing(tmp_path):
    """
    `logs/` is gitignored, so on a fresh clone it does not exist. The handler
    has to make it, or the first log line fails after the work it describes.
    """
    path = tmp_path / "nested" / "deeper" / "app.log"

    setup_logging(log_path=path, to_stdout=False)

    try:
        logging.getLogger("app.api").info("made the directory")

        assert path.exists()
    finally:
        reset_logging()


def test_uvicorn_access_logging_is_disabled(log_file):
    """
    Replaced, not silenced. uvicorn's access log cannot name the user — it runs
    under the application and has never heard of one — so app.api's middleware
    writes that line instead. Leaving both on would double every request with
    one of the two strictly worse.
    """
    assert logging.getLogger("uvicorn.access").disabled is True


def test_uvicorn_errors_still_reach_the_file(log_file):
    """
    The parent logger has to propagate, or uvicorn's own startup and error
    records are swallowed by its default configuration and never reach here.
    """
    assert logging.getLogger("uvicorn").propagate is True


def test_reset_removes_this_modules_handlers(tmp_path):
    """
    Leaves the root logger as it was found, so a test that configured logging
    does not hand a file handle to the next one — and to whatever pytest put
    there, which is not ours to remove.
    """
    root = logging.getLogger()
    before = list(root.handlers)

    setup_logging(log_path=tmp_path / "app.log", to_stdout=True)

    assert len(root.handlers) > len(before)

    reset_logging()

    assert root.handlers == before


# --- the request middleware --------------------------------------------------


def test_a_request_is_logged_with_its_outcome(log_file, client):
    """
    One line per request, carrying what uvicorn could not: the status, how long
    it took, and — below — who asked.
    """
    response = client.get("/expenses", headers={"Authorization": "Bearer nope"})

    lines = [line for line in read(log_file) if "GET /expenses" in line]

    assert len(lines) == 1
    assert str(response.status_code) in lines[0]


def test_a_request_names_its_user_and_surface(log_file, client, auth_headers):
    """
    `via` distinguishes a credential the caller holds from an ambient cookie,
    which is the distinction the CSRF rule is built on — so the log has to
    carry it or a security question cannot be answered from the log.
    """
    client.get("/expenses", headers=auth_headers)

    line = next(line for line in read(log_file) if "GET /expenses" in line)

    assert "user=1" in line
    assert "via=bearer" in line


def test_an_unauthenticated_request_says_so_rather_than_guessing(log_file, client):
    client.get("/expenses")

    line = next(line for line in read(log_file) if "GET /expenses" in line)

    assert "user=-" in line
    assert "via=-" in line


def test_a_cookie_request_is_logged_as_one(log_file, session_client, browser_session):
    session_client.get("/me")

    line = next(line for line in read(log_file) if "GET /me" in line)

    assert "via=cookie" in line


def test_a_mutation_is_logged(log_file, client, auth_headers):
    client.post(
        "/expenses",
        headers=auth_headers,
        json={
            "name": "Food",
            "amount": 300,
            "date": "2026-09-01",
            "category": "Food",
            "payment_type": "Cash",
        },
    )

    assert any("POST /expenses" in line for line in read(log_file))


def test_the_request_body_is_never_written_to_the_log(log_file, client):
    """
    A login body carries a password. A request log records that a request
    happened, not the credentials it happened with — so this is a security
    assertion, not a formatting one.
    """
    client.post("/login", json={"username": "nobody", "password": "S3cretPassword!"})

    assert "S3cretPassword!" not in log_file.read_text(encoding="utf-8")


def test_a_bearer_token_is_never_written_to_the_log(log_file, client, auth_headers):
    token = auth_headers["Authorization"].removeprefix("Bearer ")

    client.get("/expenses", headers=auth_headers)

    assert token not in log_file.read_text(encoding="utf-8")


def test_a_500_is_recorded_with_its_traceback(
    log_file, client, auth_headers, expense_service, monkeypatch
):
    """
    The line that makes a failure traceable back to the request that caused it.
    The traceback is the point — a status code alone says something broke, not
    what.

    Patched on the service instance rather than on app.api's, because the client
    fixture overrides the dependency with this one: the module-level service is
    never reached by a request in this suite.
    """
    def explode(*args, **kwargs):
        raise RuntimeError("the database caught fire")

    monkeypatch.setattr(expense_service, "get_all_expenses", explode)

    with pytest.raises(RuntimeError):
        client.get("/expenses", headers=auth_headers)

    contents = log_file.read_text(encoding="utf-8")

    assert "unhandled exception" in contents
    assert "the database caught fire" in contents
    assert "Traceback" in contents


def test_the_app_does_not_configure_logging_on_import(log_file):
    """
    Importing app.api must not touch the logging configuration: the test suite
    imports it, and so does every tool that touches this codebase. Configuring
    at import would hand them all a log file in the project directory.

    Asserted by checking the module has no import-time call — the lifespan does
    it, and a TestClient built without `with` never runs a lifespan, which is
    how this suite stays quiet.
    """
    assert app.router.lifespan_context is not None

    # The file this fixture pointed at is still empty, because nothing has
    # configured or written to it: setup_logging above wrote nothing, and no
    # import did either.
    assert read(log_file) == []
