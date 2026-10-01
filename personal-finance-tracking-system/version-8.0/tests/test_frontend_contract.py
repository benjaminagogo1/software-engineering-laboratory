"""
The frontend and the API have to agree, and nothing in either language's
compiler checks that they do.

TypeScript was the original answer here, but the client is plain JavaScript
now — so this file is the contract. It reads the client's source as text and
compares it against the running application: the option lists against the
model, and every path the client calls against the routes the server actually
publishes.

Reading the files rather than importing them keeps the Python suite free of a
Node toolchain — `pytest` stays the one command that always runs, whether or
not `npm install` has ever been run in this checkout.
"""

import re
from pathlib import Path

import pytest

from app.api import app
from app.models.expense import CATEGORIES, PAYMENT_TYPES

FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "src" / "api"
CONSTANTS = FRONTEND / "constants.js"
ENDPOINTS = FRONTEND / "endpoints.js"


def _js_string_list(source, name):
    """
    The strings of an `export const NAME = ['a', 'b']` array.

    Deliberately a narrow parser rather than a JavaScript engine: the arrays
    have one shape, and a test that can fail for reasons other than a real
    mismatch is worse than no test.
    """
    match = re.search(
        rf"export const {name} = \[(.*?)\]",
        source,
        re.DOTALL,
    )

    assert match is not None, f"{name} was not found in {CONSTANTS.name}"

    return tuple(re.findall(r"'([^']*)'", match.group(1)))


def _client_calls():
    """
    Every (method, path) the client makes.

    Path templates are normalised to a `{}` placeholder so `/expenses/${id}`
    can be compared against the server's `/expenses/{expense_id}` without
    either side having to know the other's spelling.
    """
    source = ENDPOINTS.read_text()

    verbs = {"get": "GET", "post": "POST", "put": "PUT", "remove": "DELETE"}
    calls = []

    for verb, path in re.findall(
        r"api\.(get|post|put|remove)\(\s*[`'\"]([^`'\"]+)[`'\"]",
        source,
    ):
        calls.append((verbs[verb], re.sub(r"\$\{[^}]*\}", "{}", path.split("?")[0])))

    return calls


def _server_routes():
    """Every (method, path) the application publishes, normalised the same way."""
    routes = set()

    for route in app.routes:
        path = getattr(route, "path", None)

        if path is None:
            continue

        for method in getattr(route, "methods", None) or ():
            routes.add((method, re.sub(r"\{[^}]*\}", "{}", path)))

    return routes


def test_the_client_calls_something():
    """Guards the parsers: an empty list would make the checks below vacuous."""
    assert len(_client_calls()) >= 10
    assert len(_server_routes()) >= 10


def test_categories_match_the_model():
    assert _js_string_list(CONSTANTS.read_text(), "CATEGORIES") == CATEGORIES


def test_payment_types_match_the_model():
    assert _js_string_list(CONSTANTS.read_text(), "PAYMENT_TYPES") == PAYMENT_TYPES


@pytest.mark.parametrize("method,path", _client_calls())
def test_every_path_the_client_calls_exists(method, path):
    """A renamed endpoint fails here, not as a 404 in the browser."""
    assert (method, path) in _server_routes()


def test_the_option_lists_are_not_empty():
    """A parser that silently matched nothing would pass the comparisons above."""
    source = CONSTANTS.read_text()

    assert _js_string_list(source, "CATEGORIES")
    assert _js_string_list(source, "PAYMENT_TYPES")
