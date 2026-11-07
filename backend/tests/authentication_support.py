import json

import pytest
from pydantic import SecretStr


AUTH_HEADERS = {
    "Origin": "http://127.0.0.1:5173", "Content-Type": "application/json",
    "X-GarageGuide-CSRF": "1",
}
CSRF_CASES = (
    "missing-origin", "null-origin", "malformed-origin", "untrusted-origin", "referer-only",
    "missing-content-type", "plain-text", "form", "missing-marker", "wrong-marker",
    "duplicate-origin", "duplicate-content-type", "duplicate-marker",
)


def csrf_headers(case):
    headers = list(AUTH_HEADERS.items())
    replacements = {
        "null-origin": ("Origin", "null"), "malformed-origin": ("Origin", "not-an-origin"),
        "untrusted-origin": ("Origin", "https://untrusted.example"),
        "plain-text": ("Content-Type", "text/plain"),
        "form": ("Content-Type", "application/x-www-form-urlencoded"),
        "wrong-marker": ("X-GarageGuide-CSRF", "0"),
    }
    removals = {"missing-origin": "Origin", "referer-only": "Origin",
                "missing-content-type": "Content-Type", "missing-marker": "X-GarageGuide-CSRF"}
    if case in removals:
        headers = [(key, value) for key, value in headers if key != removals[case]]
    elif case in replacements:
        key, value = replacements[case]
        headers = [(name, value if name == key else old) for name, old in headers]
    elif case.startswith("duplicate-"):
        key = {"origin": "Origin", "content-type": "Content-Type", "marker": "X-GarageGuide-CSRF"}[
            case.removeprefix("duplicate-")
        ]
        headers.append(next(pair for pair in headers if pair[0] == key))
    if case == "referer-only":
        headers.append(("Referer", "http://127.0.0.1:5173/register"))
    return headers


class AuthenticationInput:
    def __init__(self, email="user@example.com"):
        self.email = email
        self._password = (chr(0x65) + chr(0x301)) * 15
        self._sensitive = [self._password, chr(0xE9) * 15, "synthetic private driver details"]

    def __repr__(self):
        return "<synthetic authentication input: secrets redacted>"

    def login(self, client, *, changes=None, headers=None, malformed=False):
        body = {"email": self.email, "password": self._password}
        if changes:
            body.update(changes)
        if isinstance(body.get("password"), str):
            self._sensitive.append(body["password"])
        content = '{"password":' if malformed else json.dumps(body, ensure_ascii=True)
        return self.send(client, "POST", "/api/auth/login", content=content, headers=headers)

    def send(self, client, method, path, *, content=None, headers=None):
        try:
            return client.request(
                method, path, content=content,
                headers=(AUTH_HEADERS if headers is None and method == "POST" else headers),
            )
        except Exception:
            pytest.fail("Authentication request raised unexpectedly; details redacted", pytrace=False)

    def result(self, response):
        try:
            return response.json()
        except ValueError:
            pytest.fail("Authentication response was not valid JSON; details redacted", pytrace=False)

    def token(self, response):
        value = response.cookies.get("garageguide_session")
        if not value:
            pytest.fail("Expected a session cookie; details redacted", pytrace=False)
        self._sensitive.append(value)
        return SecretStr(value)

    def install_cookie(self, client, token):
        value = token.get_secret_value()
        self._sensitive.append(value)
        client.cookies.clear()
        client.cookies.set("garageguide_session", value, domain="127.0.0.1", path="/")

    def failure(self, error_type=RuntimeError):
        return error_type("".join(self._sensitive))

    def assert_safe(self, response, caplog):
        assert response.headers.get("cache-control") == "no-store"
        visible = response.text + caplog.text
        leaked = any(value and value in visible for value in self._sensitive)
        assert not leaked
        for record in caplog.records:
            if record.name.startswith("app."):
                safe_log = not record.exc_info and not record.args and not record.stack_info
                assert safe_log
