import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Reads the .env file in the project root and loads its key=value pairs
# into the process environment (os.environ), if they aren't already set.
load_dotenv()

# os.getenv(key, default) reads the environment variable if present,
# otherwise falls back to the default. This means the app runs fine
# even if someone forgets to create a .env file.
DB_PATH = os.getenv("DB_PATH", "data/expense.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


BASE_DIR = Path(__file__).resolve().parent

# Where `chart` writes its HTML reports.
REPORTS_DIR = BASE_DIR / "reports"

# The built browser client. FastAPI serves its contents; `npm run build` in
# frontend/ is what puts them here.
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


def _env_flag(name, default):
      """Reads a boolean env var, accepting the spellings people actually type."""
      raw = os.getenv(name)

      if raw is None:
            return default

      return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name, default):
      """Reads an integer env var, falling back rather than crashing on junk."""
      raw = os.getenv(name)

      if raw is None:
            return default

      try:
            return int(raw.strip())
      except ValueError:
            return default


# Whether the session cookie is marked Secure, so the browser will only send it
# over https. On by default, because that is what production needs.
#
# It has to be switchable: `Secure` cookies are dropped over plain http, so
# developing on http://localhost (or a LAN address) with this left on produces a
# login that appears to succeed and then never persists.
COOKIE_SECURE = _env_flag("COOKIE_SECURE", default=True)

# How long a browser session lasts before the user has to log in again. The
# bearer tokens API clients use are deliberately much shorter-lived (15 minutes);
# this is longer because there is no refresh path behind it.
SESSION_TTL_HOURS = _env_int("SESSION_TTL_HOURS", default=12)


def require_jwt_secret():
      """
      Returns the token signing secret, or raises if none is configured.

      Called wherever a token is minted or verified rather than at import time,
      so a missing .env fails with a sentence naming the actual problem instead
      of an opaque error from inside the JWT library.
      """
      if not JWT_SECRET_KEY:
            raise RuntimeError(
                  "JWT_SECRET_KEY is not set. Copy .env.example to .env and give "
                  "it a long random value, for example:\n"
                  '  python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )

      return JWT_SECRET_KEY


LOG_LEVELS = {
      "DEBUG": logging.DEBUG,
      "INFO": logging.INFO,
      "WARNING": logging.WARNING,
      "ERROR": logging.ERROR,
      "CRITICAL": logging.CRITICAL
}

# Where the operational log is written. Overridable so a container can point it
# at a mounted volume, and so a test can point it at tmp_path.
#
# A relative value from the environment is resolved against BASE_DIR rather
# than the process's working directory: the API is started from the project
# root but `chart` and the CLI can be run from anywhere, and a log that lands
# in a different place depending on where you stood is a log that goes missing.
LOG_PATH = Path(os.getenv("LOG_PATH", "logs/app.log"))
if not LOG_PATH.is_absolute():
      LOG_PATH = BASE_DIR / LOG_PATH

# Whether log lines also go to stdout.
#
# On by default, because that is how a container is read: Docker and every
# orchestrator on top of it collect stdout, and a log written only to a file
# inside the container's filesystem is invisible to `docker logs` and gone when
# the container is replaced. A developer running uvicorn by hand wants the same
# thing, for the same reason — the terminal is where they are already looking.
LOG_TO_STDOUT = _env_flag("LOG_TO_STDOUT", default=True)

# What the file handler is allowed to write before it rotates, and how many
# rotated files are kept. 5 MB × 6 files is ~30 MB of history — enough to cover
# a busy week at INFO, small enough that nobody has to think about disk.
LOG_MAX_BYTES = _env_int("LOG_MAX_BYTES", default=5_000_000)
LOG_BACKUP_COUNT = _env_int("LOG_BACKUP_COUNT", default=5)

# What the line looks like. The module name is in there because a request line
# from app.api and one from app.services.expense_service answer different
# questions, and without it every line from a request reads as one blob.
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
