import json
import unicodedata

import pytest
from pwdlib import PasswordHash


class RegistrationInput:
    def __init__(self, email=" \tUser@EXAMPLE.COM\n"):
        self.email = email
        self._password = (chr(0x65) + chr(0x301)) * 15
        self._confirmation = chr(0xE9) * 15
        self.hash_marker = chr(0x68) * 30
        self.driver_marker = "Synthetic private SQL/driver information"
        self._sensitive = [
            self._password, self._confirmation, self.hash_marker, self.driver_marker
        ]

    def __repr__(self):
        return "<synthetic registration input: credentials redacted>"

    def failure(self, error_type=RuntimeError, **kwargs):
        return error_type(
            self._password + self._confirmation + self.hash_marker + self.driver_marker,
            **kwargs,
        )

    def send(self, client, case="valid"):
        body = {
            "email": self.email,
            "password": self._password,
            "password_confirmation": self._confirmation,
        }
        if case.startswith("missing-"):
            del body[case.removeprefix("missing-")]
        elif case.startswith("empty-"):
            body[case.removeprefix("empty-")] = ""
        elif case == "invalid-email":
            body["email"] = "invalid"
        elif case == "password-object":
            body["password"] = {"private": self._password}
        elif case == "confirmation-list":
            body["password_confirmation"] = [self._confirmation]
        elif case in {"short", "long", "mismatch", "invalid-unicode"}:
            body["password"] = {
                "short": chr(0x61) * 14, "long": chr(0x61) * 129,
                "mismatch": chr(0x61) * 15, "invalid-unicode": chr(0xD800) * 15,
            }[case]
        for field in ("password", "password_confirmation"):
            if isinstance(body.get(field), str):
                self._sensitive.append(body[field])
        if case == "body-list":
            body = [body]
        try:
            if case == "malformed-json":
                content = ('{"password":' + json.dumps(self._password) + ',').encode()
            elif case == "invalid-utf8":
                content = bytes([0xFF])
            else:
                content = json.dumps(body, ensure_ascii=True).encode("ascii")
            return client.post(
                "/api/auth/register", content=content,
                headers={"Content-Type": "application/json"},
            )
        except Exception:
            pytest.fail("Registration request raised unexpectedly; details redacted", pytrace=False)

    def result(self, response):
        try:
            return response.json()
        except ValueError:
            pytest.fail("Registration did not return JSON; details redacted", pytrace=False)

    def assert_redacted(self, response, caplog):
        visible = response.text + json.dumps(self.result(response), ensure_ascii=False) + caplog.text
        exposed = any(value in visible for value in self._sensitive if value)
        if exposed:
            pytest.fail("Registration exposed sensitive data; details redacted", pytrace=False)
        no_cookie = "set-cookie" not in response.headers and not response.cookies
        assert no_cookie
        for record in caplog.records:
            if record.name == "app.routes.auth":
                safe_record = record.exc_info is None and not record.args and not record.stack_info
                assert safe_record

    def verifies_hash(self, encoded):
        self._sensitive.append(encoded)
        try:
            return PasswordHash.recommended().verify(
                unicodedata.normalize("NFC", self._password), encoded
            )
        except Exception:
            pytest.fail("Stored hash verification failed; details redacted", pytrace=False)
