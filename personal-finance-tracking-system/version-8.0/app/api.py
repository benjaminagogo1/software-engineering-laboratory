import datetime
import logging
import math
import secrets
import time

from contextlib import asynccontextmanager

from app.auth.policy import WeakCredentials
from app.auth.throttle import Throttle
from app.services.expense_service import ExpenseService
from app.repositories.sqlite_expense_repository import SqliteExpenseRepository
from app.repositories.sqlite_audit_repository import SqliteAuditRepository
from app.models.expense import (
      Expense,
      CATEGORIES,
      MAX_AMOUNT_CENTS,
      PAYMENT_TYPES,
      canonical_month,
)
from app.reports.monthly_chart import (
      render_monthly_spending,
      render_monthly_spending_fragment
)
import config
from app.logging_config import setup_logging
from app.schemas.user import UserRegistration, UserLogin
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from app.auth.jwt  import verify_token
from app.auth.cookies import SESSION_COOKIE, clear_session_cookie, set_session_cookie
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.services.results import UpdateResult, AddResult, DeleteResult
from app.services.user_service import UserService
from app.repositories.sqlite_user_repository import SqliteUserRepository


logger = logging.getLogger(__name__)


# auto_error=False so a missing header reaches our own handler: with the
# default, an absent header answers 403 while a bad token answers 401.
security =  HTTPBearer(auto_error=False)


# One audit repository shared by both services, with the surface stamped once
# here. `source` is a property of the process, not of a request, so asking each
# service to supply it would be asking them to guess.
audit_repository = SqliteAuditRepository(config.DB_PATH, source="api")

repository = SqliteExpenseRepository(config.DB_PATH)
service = ExpenseService(repository, audit_repository)


user_repository = SqliteUserRepository(config.DB_PATH)
user_service = UserService(user_repository, audit_repository)


def get_current_user(
      request: Request,
      credentials: HTTPAuthorizationCredentials | None = Depends(security)
      ):
      """
      Identifies the caller from either credential the app accepts: an
      Authorization header, or the session cookie a browser carries.

      An explicit header always wins over an ambient cookie, so an API client
      is never silently downgraded to whatever session happens to be open in
      the browser that made the request.

      Returns the token payload plus the surface it arrived on. The CSRF rule
      below applies to one of those surfaces and not the other, so the caller
      has to be able to tell them apart.
      """
      if credentials is not None:
            payload = verify_token(credentials.credentials)

            if payload is None:
                  raise HTTPException(
                        status_code=401,
                        detail="Invalid or expired token"
                  )

            # Left on the request so the middleware can name the user in the
            # request line it writes after this function has returned. The
            # middleware cannot work this out for itself — it would have to
            # verify the token a second time, and a second verification is a
            # second answer that can disagree with the first.
            request.state.user_id = payload.get("user_id")
            request.state.auth_via = "bearer"

            return {**payload, "via": "bearer"}

      cookie_token = request.cookies.get(SESSION_COOKIE)

      if cookie_token is None:
            raise HTTPException(
                  status_code=401,
                  detail="Not authenticated"
            )

      payload = verify_token(cookie_token)

      if payload is None:
            raise HTTPException(
                  status_code=401,
                  detail="Invalid or expired token"
            )

      request.state.user_id = payload.get("user_id")
      request.state.auth_via = "cookie"

      return {**payload, "via": "cookie"}


def require_csrf(
      current_user = Depends(get_current_user),
      csrf_token: str | None = Header(default=None, alias="X-CSRF-Token")
      ):
      """
      Guards every route that changes state, and is the only dependency those
      routes take — there is no path to a mutation that skips it.

      Bearer callers pass straight through. A cross-site attacker cannot set an
      Authorization header on a forged request, so those requests are not
      forgeable in the first place and a token would add nothing.

      Cookie callers have to echo the value minted into their session, which
      only something running on this origin could have read.
      """
      if current_user["via"] == "bearer":
            return current_user

      expected = current_user.get("csrf")

      if not expected or not csrf_token:
            raise HTTPException(
                  status_code=403,
                  detail="Missing CSRF token"
            )

      # Constant-time: a plain == leaks how much of the token was guessed right.
      if not secrets.compare_digest(csrf_token, expected):
            raise HTTPException(
                  status_code=403,
                  detail="Invalid CSRF token"
            )

      return current_user



def get_service():
      return service


def get_user_service():
      return user_service


def get_audit_repository():
      return audit_repository


class AuthLimits:
      """
      Every counter the auth routes share, so a test can replace them as one.

      Three Throttles rather than one, because they are answering three
      different questions and a single threshold would have to be wrong for two
      of them.

      The login pair is the tight one: five failures on one (username, address)
      pair starts the backoff. It is keyed on the address as well as the
      username so that an attacker's failures cannot lock the real user out of
      their own account — the trade explained in app/auth/throttle.py.

      The login address is loose, because it exists to catch one machine
      spraying many usernames, which the pair key never sees.

      Register counts every attempt rather than only refusals: what is being
      protected there is the argon2 hash and the row, and both are spent on a
      request that succeeds.
      """

      def __init__(self):
            self.login_pair = Throttle(threshold=5)
            self.login_address = Throttle(threshold=30)
            self.register_address = Throttle(threshold=10)


auth_limits = AuthLimits()


def get_auth_limits():
      return auth_limits


def client_address(request):
      """
      The address the limiter is keyed on.

      `request.client.host`, and deliberately not the X-Forwarded-For header.
      That header is whatever the caller says it is, so reading it here would
      hand anyone a one-line bypass of every limit above: send a different
      fabricated address each attempt and each one is a fresh key.

      Behind a reverse proxy the correct arrangement is to let uvicorn rewrite
      `request.client` itself — `--proxy-headers --forwarded-allow-ips=<the
      proxy>` — which trusts the header only from a peer that is allowed to set
      it. This function then needs no change and stays correct either way.
      """
      if request.client is None:
            # No peer at all: a test transport, or a socket that has already
            # gone. Anything unattributable shares one key, which errs towards
            # throttling too much rather than too little.
            return "unknown"

      return request.client.host


class LoginAttempt:
      """
      One login attempt, measured against both keys that apply to it.

      Built per request rather than held, so the keys always describe the
      request in hand. The two counters are updated together — a failure that
      counted against one and not the other would leave a hole that is only
      visible to whoever was aiming for it.
      """

      def __init__(self, limits, username, address):
            self.counters = (
                  (limits.login_pair, f"pair:{username.lower()}|{address}"),
                  (limits.login_address, f"ip:{address}"),
            )

      def wait(self):
            """The longest of the two waits, or 0 — the binding constraint."""
            return max(throttle.retry_after(key) for throttle, key in self.counters)

      def failed(self):
            for throttle, key in self.counters:
                  throttle.record(key)

      def succeeded(self):
            """
            Clears both. Without this an honest mistype is a permanent tax, and
            the person least able to work it out is the one paying it.
            """
            for throttle, key in self.counters:
                  throttle.clear(key)


def too_many_attempts(retry_after):
      """
      429, with Retry-After, which is the part that makes it actionable.

      Rounded up: a Retry-After of 0 invites a client to retry immediately and
      be refused again, which reads as a broken server rather than a deliberate
      pause.
      """
      raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Try again later.",
            headers={"Retry-After": str(math.ceil(retry_after))},
      )


class ExpenseRequest(BaseModel):
      name: str
      # A whole number of kobo, not naira: ₦12.34 is 1234. Declaring it `int`
      # is what makes NaN and Infinity unrepresentable rather than merely
      # rejected — Pydantic will not coerce either into an integer, so there is
      # no value to smuggle past a comparison. The bounds are the service's own
      # rule, stated here where a generated client can read them.
      amount_cents: int = Field(gt=0, le=MAX_AMOUNT_CENTS)
      date: datetime.date | None = None
      # Declaring the allowed values in the schema makes the OpenAPI document
      # self-describing, so a generated client gets a union type instead of a
      # bare string. The service still validates and answers 400 — this states
      # the contract, it does not enforce it a second time.
      category: str = Field(json_schema_extra={"enum": list(CATEGORIES)})
      payment_type: str = Field(json_schema_extra={"enum": list(PAYMENT_TYPES)})
      # Optional free text: an expense need not name a payee or carry a note.
      merchant: str | None = None
      note: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    # Echoed back on every state-changing request as X-CSRF-Token. It is not
    # hidden from the page's own scripts — that is the point of double-submit:
    # only script running on this origin is able to read it.
    csrf_token: str


class UserResponse(BaseModel):
      id: int
      username: str

class SessionResponse(BaseModel):
      id: int
      username: str
      # The counter-signature for this session, handed back so a page reload
      # can carry on: the client holds it in memory only, and the cookie that
      # would otherwise carry it is unreadable to script by design.
      #
      # None for a bearer caller, which has no session and needs none — a
      # request made with an Authorization header is not forgeable cross-site.
      csrf_token: str | None = None

class ExpenseUpdatedRequest(BaseModel):
      # Same unit and same bounds as ExpenseRequest. Not optional: an update
      # always carries an amount, so there is no "leave it alone" spelling here.
      amount_cents: int = Field(gt=0, le=MAX_AMOUNT_CENTS)
      # Optional, so an existing client can still PUT just an amount.
      name: str | None = None
      # Parsed here rather than in the service: the API owns the wire format,
      # and a malformed date should be a 422 before anything is looked up.
      date: datetime.date | None = None
      category: str | None = None
      payment_type: str | None = None
      # An empty string clears these two; omitting them leaves them alone.
      merchant: str | None = None
      note: str | None = None


class ExpenseResponse(BaseModel):
      id: int
      name: str
      amount_cents: int
      date: str
      category: str
      payment_type: str
      merchant: str | None = None
      note: str | None = None

class CreateExpenseResponse(BaseModel):
      result: str
      expense: ExpenseResponse

class TopMonthResponse(BaseModel):
      month: str
      total_cents: int

class TopDayResponse(BaseModel):
      day: str
      total_cents: int

class DailyTotalResponse(BaseModel):
      date: str
      total_cents: int

class FrequencyResponse(BaseModel):
      name: str
      count: int

class MessageResponse(BaseModel):
      message: str


class ChartFragmentResponse(BaseModel):
      # The renderer's stylesheet, scoped under .spending-chart.
      css: str
      # The body markup, with every interpolated value already escaped.
      html: str

class DeleteAllResponse(BaseModel):
      message: str
      deleted: int


class AuditEventResponse(BaseModel):
      id: int
      # When it happened, as the store wrote it: UTC, with an explicit offset.
      # Passed through as a string rather than parsed into a datetime so the
      # value a client displays is the value in the trail, not a re-rendering
      # of it in whatever timezone this process happens to be in.
      happened_at: str
      action: str
      entity_type: str | None = None
      entity_id: int | None = None
      detail: dict | None = None
      # Which surface it came from — "api" for a browser or an HTTP client,
      # "cli" for the terminal. Worth showing: "I did not do that from the
      # browser" is exactly the question this endpoint exists to answer.
      source: str | None = None


@asynccontextmanager
async def lifespan(_app):
      """
      Configures logging when the server actually starts.

      Here rather than at import because importing `app.api` is not the same as
      running it: the test suite imports this module, and configuration at
      import time would hand every test run a log file in the project directory
      and a root logger the test did not ask for.

      The audit table needs no equivalent — SqliteStorage runs migrations
      whenever a repository is constructed, which happened at import above.
      """
      setup_logging()
      logger.info("API starting up")

      yield


app = FastAPI(lifespan=lifespan)


def _shown(value):
      """A field's value, or "-" when the request never established one."""
      return "-" if value is None else value


@app.middleware("http")
async def log_requests(request: Request, call_next):
      """
      Writes one line per request, and that line is why uvicorn's access log is
      switched off in app.logging_config: it can say a request happened, but it
      cannot say who made it, because it runs underneath the application and a
      user is something only the application knows.

      `user` and `via` are read off request.state, which get_current_user set
      while resolving the route. They are therefore "-" for anything that never
      reached it — a 401, or a public route — which is the honest answer rather
      than a guess.

      The body is never read and the Authorization header is never touched.
      Both are logged-adjacent and neither belongs in a file: a body can carry a
      password, and a header can carry a token that grants a session. A request
      log records that a thing happened, not the credentials it happened with.

      Duration is measured here rather than taken from anything downstream,
      because nothing downstream has an opinion about wall-clock time — and it
      covers the whole request, including the time spent in middleware above
      this one and in the response body.
      """
      started = time.perf_counter()

      try:
            response = await call_next(request)
      except Exception:
            # Re-raised, not swallowed. This line's job is to make a 500
            # traceable back to the request that caused it — the traceback
            # itself still goes where FastAPI would have sent it.
            logger.exception(
                  "%s %s -> unhandled exception after %.1fms (user=%s via=%s)",
                  request.method,
                  request.url.path,
                  (time.perf_counter() - started) * 1000,
                  _shown(getattr(request.state, "user_id", None)),
                  _shown(getattr(request.state, "auth_via", None)),
            )
            raise

      elapsed = (time.perf_counter() - started) * 1000

      user_id = getattr(request.state, "user_id", None)
      auth_via = getattr(request.state, "auth_via", None)

      message = "%s %s -> %s in %.1fms (user=%s via=%s)"

      args = (
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
            _shown(user_id),
            _shown(auth_via),
      )

      # The SPA's hashed assets are one line each per page load and say nothing
      # about what the application did — only that a browser fetched a file it
      # had not cached. DEBUG keeps them available to anyone who wants them
      # without letting them bury the requests that matter.
      if request.url.path.startswith("/app/assets/"):
            logger.debug(message, *args)
      else:
            logger.info(message, *args)

      return response



@app.get("/expenses", response_model=list[ExpenseResponse])
def get_expenses(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):

      return service.get_all_expenses(current_user["user_id"])


# Declared above GET /expenses/{expense_id} on purpose: routes match in
# registration order, so otherwise "search" would be captured as an
# expense_id and rejected as a non-integer.
@app.get("/expenses/search", response_model=list[ExpenseResponse])
def search_expenses(
      name: str,
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):

      return service.search_by_name(name, current_user["user_id"])


@app.get("/analytics/top-month", response_model=TopMonthResponse)
def get_top_month(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      top_month = service.get_top_month(current_user["user_id"])

      if top_month is None:
            raise HTTPException(status_code=404, detail="No expenses found")

      month, total = top_month

      return {
            "month": month,
            "total_cents": total
      }


@app.get("/analytics/frequency", response_model=FrequencyResponse)
def get_frequency(
      name: str,
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      count = service.count_by_name(
            name,
            current_user["user_id"]
      )

      return {
            "name": name,
            "count": count
      }


@app.get("/analytics/highest", response_model=ExpenseResponse)
def get_highest_expense(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      expense = service.get_highest_expense(current_user["user_id"])

      if expense is None:
            raise HTTPException(status_code=404, detail="No expenses found")

      return expense


@app.get("/analytics/lowest", response_model=ExpenseResponse)
def get_lowest_expense(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      expense = service.get_lowest_expense(current_user["user_id"])

      if expense is None:
            raise HTTPException(status_code=404, detail="No expenses found")

      return expense


@app.get("/analytics/months", response_model=list[TopMonthResponse])
def get_month_totals(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      # Every month's total, highest first, so months can be compared rather
      # than only ranked. No expenses is an empty ranking, not a 404.
      return [
            {"month": month, "total_cents": total}
            for month, total in service.get_month_totals(current_user["user_id"])
      ]


@app.get("/analytics/top-day", response_model=TopDayResponse)
def get_top_day(
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      top_day = service.get_top_weekday(current_user["user_id"])

      if top_day is None:
            raise HTTPException(status_code=404, detail="No expenses found")

      day, total = top_day

      return {
            "day": day,
            "total_cents": total
      }


@app.get("/analytics/daily", response_model=list[DailyTotalResponse])
def get_daily_totals(
      month: str,
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      canonical = canonical_month(month)

      if canonical is None:
            raise HTTPException(
                  status_code=400,
                  detail="Month must be in YYYY-MM format"
            )

      return [
            {"date": row_date, "total_cents": total}
            for row_date, total in service.get_daily_totals(
                  canonical,
                  current_user["user_id"]
            )
      ]


@app.get("/reports/month", response_class=HTMLResponse)
def monthly_report(
      month: str,
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      """
      The spending graph for one month, served as a self-contained HTML page.

      Same renderer the CLI `chart` command writes to a file — the API just
      hands the document straight back instead.
      """
      canonical = canonical_month(month)

      if canonical is None:
            raise HTTPException(
                  status_code=400,
                  detail="Month must be in YYYY-MM format"
            )

      daily_totals = service.get_daily_totals(
            canonical,
            current_user["user_id"]
      )

      return render_monthly_spending(canonical, daily_totals)


@app.get("/reports/month.fragment", response_model=ChartFragmentResponse)
def monthly_report_fragment(
      month: str,
      service= Depends(get_service),
      current_user= Depends(get_current_user)
      ):
      """
      The same chart as /reports/month, split so the browser client can place
      it inside a page it already has: the stylesheet and a body fragment,
      rather than a whole document with a <head> of its own.

      Deliberately the same renderer, not a second one in JavaScript. The
      stylesheet is scoped under .spending-chart and every user-supplied
      string in the renderer is escaped, so the client can inject both as-is.
      """
      canonical = canonical_month(month)

      if canonical is None:
            raise HTTPException(
                  status_code=400,
                  detail="Month must be in YYYY-MM format"
            )

      daily_totals = service.get_daily_totals(
            canonical,
            current_user["user_id"]
      )

      css, html_fragment = render_monthly_spending_fragment(
            canonical,
            daily_totals
      )

      return {"css": css, "html": html_fragment}


@app.post("/register", response_model=UserResponse, status_code=201)
def register_user(
      user_request: UserRegistration,
      request: Request,
      limits= Depends(get_auth_limits),
      user_service= Depends(get_user_service)
      ):
      """
      Creates an account.

      Rate limited by address, and every attempt counts rather than only the
      refused ones — what this route costs is an argon2 hash and a row, and a
      request that succeeds spends both.
      """
      counter = f"ip:{client_address(request)}"

      wait = limits.register_address.retry_after(counter)

      if wait > 0:
            too_many_attempts(wait)

      limits.register_address.record(counter)

      try:
            user = user_service.register_user(
                  user_request.username,
                  user_request.password
            )
      except WeakCredentials as refused:
            # 400, not 409. The username was never the problem — the pair was
            # unacceptable, and telling the two apart is what lets the client
            # show the person the actual sentence.
            raise HTTPException(status_code=400, detail=str(refused))

      if user is None:
            raise HTTPException(
                  status_code=409,
                  detail="Username already exists"
            )

      return {
            "id": user.id,
            "username": user.username
      }


@app.post("/login", response_model=LoginResponse)
def login_user(
      user_request: UserLogin,
      request: Request,
      response: Response,
      limits= Depends(get_auth_limits),
      user_service= Depends(get_user_service)
      ):
      """
      Exchanges credentials for a session, within the limits on guessing.

      The counters are checked before the credentials are, so a throttled
      request costs no argon2 verification — which is the point of throttling a
      password route rather than only refusing at the end.
      """
      attempt = LoginAttempt(
            limits,
            user_request.username,
            client_address(request)
      )

      wait = attempt.wait()

      if wait > 0:
            too_many_attempts(wait)

      tokens = user_service.login(
            user_request.username,
            user_request.password
      )

      if tokens is None:
            attempt.failed()

            raise HTTPException(
                  status_code=401,
                  detail="Invalid username or password"
            )

      # Only after a real success, so a correct password is what clears the
      # count — not merely the absence of a failure.
      attempt.succeeded()

      # The session travels in an httpOnly cookie, so script on the page can
      # never read it even if the page is compromised. The access token still
      # comes back in the body for clients that hold their own credential.
      set_session_cookie(response, tokens.session_token)

      return {
            "access_token": tokens.access_token,
            "token_type": "bearer",
            "csrf_token": tokens.csrf_token
      }


@app.post("/logout", response_model=MessageResponse)
def logout(
      response: Response,
      # The user, not a throwaway: the trail records who logged out, and the
      # guard is require_csrf, which resolves the same identity anyway.
      current_user= Depends(require_csrf),
      user_service= Depends(get_user_service)
      ):
      """
      Ends the browser session.

      Worth being honest about the limit: the cookie is cleared, but the token
      inside it was stateless, so a copy taken beforehand stays valid until it
      expires. Revoking early needs a server-side session store.
      """
      user_service.logout(current_user["user_id"])

      clear_session_cookie(response)

      return {"message": "Logged out"}


@app.get("/me", response_model=SessionResponse)
def get_me(
      current_user= Depends(get_current_user),
      user_service= Depends(get_user_service)
      ):
      """
      Who the caller is, and the CSRF token to use from here.

      The browser client needs this on every page load: without it, a reload
      has no way to tell an expired session from an empty expense list — and
      no way to recover the CSRF token it can only hold in memory.
      """
      user = user_service.repository.find_by_id(current_user["user_id"])

      if user is None:
            # A token that verifies but names a user who no longer exists.
            raise HTTPException(
                  status_code=401,
                  detail="Not authenticated"
            )

      return {
            "id": user.id,
            "username": user.username,
            "csrf_token": current_user.get("csrf")
      }



@app.get("/audit", response_model=list[AuditEventResponse])
def read_audit(
      limit: int = Query(default=50, ge=1, le=200),
      current_user = Depends(get_current_user),
      audit = Depends(get_audit_repository)
      ):
      """
      The caller's own recent activity, newest first.

      **Only the caller's own.** There is no parameter for reading another
      user's trail, and that is not an omission to be filled in later: the
      trail holds every user's rows in one table, so a route that could name a
      user_id would hand any account the history of every other one. Reading
      across users is an operator's job, done against the database directly,
      which is also where it can be logged and rate-limited properly. If this
      application ever grows an administrator role, that role gets its own
      route with its own authorization decision — not a widened parameter here.

      Failed logins aimed at this user appear in it. `login.failed` is recorded
      against the account when the username exists and against nobody when it
      does not, so the account being guessed against is the one that sees it.
      That is the useful half: a run of failures in your own trail is what
      someone trying to get into your account looks like from the inside.

      `limit` is bounded rather than cursor-paginated. The read is a person
      looking back over their own recent history, not an export; anything that
      genuinely needs the whole trail reads the table, where the two indexes
      are there for it.
      """
      events = audit.for_user(current_user["user_id"], limit=limit)

      return [
            {
                  "id": event.id,
                  "happened_at": event.happened_at,
                  "action": event.action,
                  "entity_type": event.entity_type,
                  "entity_id": event.entity_id,
                  "detail": event.detail,
                  "source": event.source,
            }
            for event in events
      ]


@app.post("/expenses", response_model=CreateExpenseResponse, status_code=201)
def create_expense(
      expense_request: ExpenseRequest,
      service = Depends(get_service),
      current_user = Depends(require_csrf)
      ):

      expense = Expense(
            None,
            expense_request.name,
            expense_request.amount_cents,
            current_user["user_id"],
            (expense_request.date or datetime.date.today()).isoformat(),
            expense_request.category,
            expense_request.payment_type,
            expense_request.merchant,
            expense_request.note
      )


      result = service.add_expense(expense)

      if result == AddResult.INVALID_NAME:
            raise HTTPException(status_code=400, detail="Name cannot be empty")

      if result == AddResult.INVALID_AMOUNT:
            raise HTTPException(
                  status_code=400,
                  detail=(
                        "Amount must be a whole number of kobo between 1 and "
                        f"{MAX_AMOUNT_CENTS}"
                  )
            )

      if result == AddResult.INVALID_CATEGORY:
            raise HTTPException(
                  status_code=400,
                  detail=f"Category must be one of: {', '.join(CATEGORIES)}"
            )

      if result == AddResult.INVALID_PAYMENT_TYPE:
            raise HTTPException(
                  status_code=400,
                  detail=f"Payment type must be one of: {', '.join(PAYMENT_TYPES)}"
            )

      return {
            "result": result.name,
            "expense": expense
      }


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int,
      service = Depends(get_service),
      current_user = Depends(get_current_user)
      ):
      expense = service.get_expense_by_id(
            expense_id,
            current_user["user_id"]
            )

      if expense is None:
            raise HTTPException(status_code=404, detail= "Expense not found.")

      return expense


@app.put("/expenses/{expense_id}", response_model=MessageResponse)
def update_expense(
    expense_id: int,
    expense_request: ExpenseUpdatedRequest,
    service=Depends(get_service),
    current_user=Depends(require_csrf)
):
    result = service.update_expense(
        expense_id,
        expense_request.amount_cents,
        current_user["user_id"],
        expense_request.category,
        expense_request.payment_type,
        expense_request.merchant,
        expense_request.note,
        expense_request.name,
        expense_request.date.isoformat() if expense_request.date else None
    )

    if result == UpdateResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Expense not found")

    if result == UpdateResult.INVALID_NAME:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    if result == UpdateResult.INVALID_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=(
                "Amount must be a whole number of kobo between 1 and "
                f"{MAX_AMOUNT_CENTS}"
            )
        )

    if result == UpdateResult.INVALID_CATEGORY:
        raise HTTPException(
            status_code=400,
            detail=f"Category must be one of: {', '.join(CATEGORIES)}"
        )

    if result == UpdateResult.INVALID_PAYMENT_TYPE:
        raise HTTPException(
            status_code=400,
            detail=f"Payment type must be one of: {', '.join(PAYMENT_TYPES)}"
        )

    return {"message": "Expense updated successfully"}


@app.delete("/expenses/{expense_id}", response_model=MessageResponse)
def delete_expense(
    expense_id: int,
    service=Depends(get_service),
    current_user=Depends(require_csrf)
):
    result = service.delete_expense_by_id(
        expense_id,
        current_user["user_id"]
    )

    if result == DeleteResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense deleted successfully"}


# The collection, not an item: this clears the caller's whole expense list.
# Only ever their own — everyone else's rows are untouched, because the delete
# is scoped by user_id like every other query.
@app.delete("/expenses", response_model=DeleteAllResponse)
def delete_all_expenses(
    service=Depends(get_service),
    current_user=Depends(require_csrf)
):
    deleted = service.delete_all_expenses(current_user["user_id"])

    return {
        "message": f"Deleted {deleted} expense(s)",
        "deleted": deleted
    }


# --- The browser client -----------------------------------------------------
#
# Served under /app rather than from the root, because the routes above already
# claim /expenses, /analytics, /reports, /login and /register: an SPA using
# those as its own client-side paths would shadow them. /docs, /redoc and
# /openapi.json are registered when FastAPI() is constructed, before anything
# here, so they are unaffected.
#
# Registration order carries the same meaning it does above: the assets mount
# is declared first so /app/assets/... is matched by it rather than swallowed
# by the catch-all underneath.


app.mount(
      "/app/assets",
      # check_dir=False so importing this module does not depend on the
      # frontend having been built yet: an unbuilt client should serve 404s
      # here, not break the API and the entire test suite at import time.
      StaticFiles(directory=config.FRONTEND_DIST / "assets", check_dir=False),
      name="assets"
)


@app.get("/app/{_client_path:path}", response_class=HTMLResponse, include_in_schema=False)
def browser_client(_client_path: str):
      """
      Serves the single-page client for any of the routes it owns.

      The path is unused on purpose: every client-side route resolves to the
      same document, and the router inside that document takes over.
      """
      index = config.FRONTEND_DIST / "index.html"

      if not index.exists():
            raise HTTPException(
                  status_code=503,
                  detail=(
                        "The frontend has not been built. Run "
                        "`npm install && npm run build` in frontend/."
                  )
            )

      return FileResponse(index)


@app.get("/", include_in_schema=False)
def root():
      return RedirectResponse("/app/")
