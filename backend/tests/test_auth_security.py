import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr

from app import security


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.mark.parametrize("known", [False, True], ids=["unknown-email", "known-email"])
@pytest.mark.parametrize("matches", [False, True], ids=["mismatch", "match"])
def test_login_performs_one_verification_even_for_unknown_accounts(monkeypatch, known, matches):
    calls = []
    secret = SecretStr(chr(0x61) * 15)
    stored = security.validate_and_hash_credentials(secret, secret) if known else None

    def verify(candidate, encoded):
        calls.append((candidate, encoded))
        return matches

    monkeypatch.setattr(security._PASSWORD_HASH, "verify", verify)
    result = security.verify_credentials(secret, stored)
    correct_call = len(calls) == 1 and calls[0] == (
        chr(0x61) * 15, stored if known else security._DUMMY_PASSWORD_HASH
    )
    assert correct_call
    assert result == (known and matches)


@pytest.mark.parametrize("length", [15, 128])
def test_login_and_registration_share_nfc_rules_and_real_argon2(length):
    composed = SecretStr(chr(0xE9) * length)
    decomposed = SecretStr((chr(0x65) + chr(0x301)) * length)
    encoded = security.validate_and_hash_credentials(composed, decomposed)
    verified = security.verify_credentials(decomposed, encoded)
    assert verified
    wrong_verified = security.verify_credentials(SecretStr(chr(0x61) * length), encoded)
    assert not wrong_verified


@pytest.mark.parametrize("codepoint", [0x20, 0x41, 0x1F697], ids=["spaces", "case", "astral"])
def test_login_preserves_spaces_case_and_codepoints(codepoint):
    secret = SecretStr(chr(codepoint) * 15)
    encoded = security.validate_and_hash_credentials(secret, secret)
    verified = security.verify_credentials(secret, encoded)
    assert verified
    changed_verified = security.verify_credentials(SecretStr(chr(0x61) * 15), encoded)
    assert not changed_verified


@pytest.mark.parametrize("kind", ["short", "long", "surrogate", "nfc-short"])
def test_invalid_login_password_never_reaches_verification(monkeypatch, kind):
    calls = []
    monkeypatch.setattr(security._PASSWORD_HASH, "verify", lambda *args: calls.append(1))
    values = {
        "short": chr(0x61) * 14, "long": chr(0x61) * 129,
        "surrogate": chr(0xD800) * 15, "nfc-short": (chr(0x65) + chr(0x301)) * 14,
    }
    with pytest.raises(security.CredentialValidationError) as caught:
        security.verify_credentials(SecretStr(values[kind]), None)
    leaked = values[kind] in str(caught.value)
    assert not leaked
    assert not calls


def test_corrupt_stored_hash_remains_an_unexpected_error():
    with pytest.raises(Exception) as caught:
        security.verify_credentials(SecretStr(chr(0x61) * 15), "invalid-encoded-hash")
    is_validation_error = isinstance(caught.value, security.CredentialValidationError)
    assert not is_validation_error


def test_dummy_hash_is_generated_once_for_multiple_attempts():
    script = """
import pwdlib
class Hasher:
    def __init__(self):
        self.hashes = 0
        self.verifications = 0
    def hash(self, candidate):
        self.hashes += 1
        return 'dummy-encoded-hash'
    def verify(self, candidate, encoded):
        self.verifications += 1
        return False
hasher = Hasher()
pwdlib.PasswordHash.recommended = staticmethod(lambda: hasher)
import psycopg
psycopg.connect = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError())
from pydantic import SecretStr
from app import security
for _ in range(3):
    security.verify_credentials(SecretStr(chr(0x61) * 15), None)
assert hasher.hashes == 1 and hasher.verifications == 3
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=Path(__file__).resolve().parents[1], capture_output=True,
        text=True, timeout=10, check=False,
    )
    successful = result.returncode == 0
    assert successful


def test_generated_tokens_are_random_canonical_masked_and_hashed_only():
    first = security.generate_session_token()
    second = security.generate_session_token()
    value = first.get_secret_value()
    encoded = security.hash_session_token(first)
    distinct = value != second.get_secret_value()
    canonical = len(value) == 43 and security.parse_session_token(value) is not None
    correct_digest = encoded == hashlib.sha256(value.encode("ascii")).hexdigest()
    safe = value not in repr(first) and value not in str(first)
    assert distinct
    assert canonical
    assert correct_digest
    assert len(encoded) == 64 and encoded == encoded.lower()
    assert safe


@pytest.mark.parametrize(
    "value", [None, "", "a" * 42, "a" * 44, "!" * 43, "\u00e9" * 43,
              "a" * 42 + "=", "A" * 42 + "B", "A" * 43 + "\n"],
    ids=["missing", "empty", "short", "long", "punctuation", "unicode",
         "padding", "noncanonical-last-bits", "newline"],
)
def test_malformed_cookie_tokens_are_rejected_without_reflection(value):
    rejected = security.parse_session_token(value) is None
    assert rejected
    if value is not None:
        with pytest.raises(ValueError) as caught:
            security.hash_session_token(SecretStr(value))
        safe = str(caught.value) == "Invalid session token."
        assert safe
