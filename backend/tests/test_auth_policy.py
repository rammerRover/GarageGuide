from http.cookies import SimpleCookie

import pytest
from fastapi import Request, Response

from app.authentication import (
    RequestPolicyError, clear_session_cookie, require_mutation_policy, set_session_cookie,
    validate_cookie_transport,
)
from app.config import AuthSettings
from app.security import generate_session_token


pytestmark = pytest.mark.usefixtures("forbid_database")


def request_for(headers=None, server=("127.0.0.1", 8000)):
    if headers is None:
        headers = [
            ("origin", "http://127.0.0.1:5173"),
            ("content-type", "application/json"), ("x-garageguide-csrf", "1"),
        ]
    return Request({
        "type": "http", "method": "POST", "path": "/api/auth/login",
        "scheme": "http", "server": server,
        "headers": [(key.encode("ascii"), value.encode("ascii")) for key, value in headers],
    })


@pytest.fixture
def settings():
    return AuthSettings("testing", False, "http://127.0.0.1:8000")


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5173", "http://127.0.0.1:4173"])
@pytest.mark.parametrize("content_type", ["application/json", "application/json; charset=utf-8"])
def test_explicit_local_origins_and_json_charset_are_allowed(settings, origin, content_type):
    require_mutation_policy(request_for([
        ("origin", origin), ("content-type", content_type), ("x-garageguide-csrf", "1"),
    ]), settings)


@pytest.mark.parametrize("origin", [
    None, "null", "", "http://localhost:5173", "https://untrusted.example",
    "http://127.0.0.1:5173/", "http://127.0.0.1:5173/path", "http://127.0.0.1:5173, null",
])
def test_missing_null_malformed_untrusted_origins_are_rejected(settings, origin):
    headers = [("content-type", "application/json"), ("x-garageguide-csrf", "1")]
    if origin is not None:
        headers.append(("origin", origin))
    with pytest.raises(RequestPolicyError) as caught:
        require_mutation_policy(request_for(headers), settings)
    assert str(caught.value) == "Request not allowed."


@pytest.mark.parametrize("header", ["origin", "content-type", "x-garageguide-csrf"])
def test_duplicate_security_headers_are_rejected(settings, header):
    headers = [("origin", "http://127.0.0.1:5173"), ("content-type", "application/json"),
               ("x-garageguide-csrf", "1")]
    headers.append(next(pair for pair in headers if pair[0] == header))
    with pytest.raises(RequestPolicyError):
        require_mutation_policy(request_for(headers), settings)


@pytest.mark.parametrize("content_type", [None, "text/plain", "application/x-www-form-urlencoded", "multipart/form-data"])
def test_json_content_type_is_required(settings, content_type):
    headers = [("origin", "http://127.0.0.1:5173"), ("x-garageguide-csrf", "1")]
    if content_type:
        headers.append(("content-type", content_type))
    with pytest.raises(RequestPolicyError):
        require_mutation_policy(request_for(headers), settings)


@pytest.mark.parametrize("marker", [None, "", "0", "true", "1 "])
def test_exact_csrf_marker_is_required(settings, marker):
    headers = [("origin", "http://127.0.0.1:5173"), ("content-type", "application/json")]
    if marker is not None:
        headers.append(("x-garageguide-csrf", marker))
    with pytest.raises(RequestPolicyError):
        require_mutation_policy(request_for(headers), settings)


@pytest.mark.parametrize("server", [None, ("0.0.0.0", 8000), ("192.0.2.1", 8000), ("testserver", 80)])
def test_host_and_forwarded_headers_cannot_enable_insecure_serving(settings, server):
    request = request_for([
        ("host", "127.0.0.1:8000"), ("x-forwarded-host", "127.0.0.1:8000"),
        ("forwarded", "host=127.0.0.1:8000;proto=http"),
    ], server=server)
    with pytest.raises(RequestPolicyError):
        validate_cookie_transport(request, settings)


@pytest.mark.parametrize("production", [False, True])
def test_cookie_issue_and_delete_match_and_only_delete_has_expiration(production):
    settings = (
        AuthSettings("production", True, "https://garage.example", "https://garage.example")
        if production else AuthSettings("testing", False, "http://127.0.0.1:8000")
    )
    response, deleted = Response(), Response()
    token = generate_session_token()
    request = request_for()
    set_session_cookie(response, token, request, settings)
    clear_session_cookie(deleted, request, settings)
    issued_cookie, deleted_cookie = SimpleCookie(), SimpleCookie()
    issued_cookie.load(response.headers["set-cookie"])
    deleted_cookie.load(deleted.headers["set-cookie"])
    issued, removed = issued_cookie["garageguide_session"], deleted_cookie["garageguide_session"]
    correct_value = issued.value == token.get_secret_value()
    assert correct_value
    for attribute in ("path", "samesite", "secure", "httponly", "domain"):
        matching = issued[attribute] == removed[attribute]
        assert matching
    flags_correct = (
        issued["path"] == "/" and issued["samesite"] == "lax" and issued["httponly"]
        and bool(issued["secure"]) == production and not issued["domain"]
    )
    assert flags_correct
    no_persistent_lifetime = not issued["max-age"] and not issued["expires"]
    assert no_persistent_lifetime
    deletion_expires = removed["max-age"] == "0" and bool(removed["expires"]) and not removed.value
    assert deletion_expires


def test_insecure_cookie_cannot_be_issued_or_deleted_on_nonloopback(settings):
    response = Response()
    request = request_for(server=("0.0.0.0", 8000))
    with pytest.raises(RequestPolicyError):
        set_session_cookie(response, generate_session_token(), request, settings)
    with pytest.raises(RequestPolicyError):
        clear_session_cookie(response, request, settings)
    assert "set-cookie" not in response.headers


def test_production_trusts_only_configured_https_frontend():
    settings = AuthSettings("production", True, "https://garage.example", "https://garage.example")
    require_mutation_policy(request_for([
        ("origin", "https://garage.example"), ("content-type", "application/json"),
        ("x-garageguide-csrf", "1"),
    ], server=("192.0.2.1", 443)), settings)
    with pytest.raises(RequestPolicyError):
        require_mutation_policy(request_for(), settings)
