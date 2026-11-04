import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr
from pwdlib import PasswordHash

from app import security
from app.security import CredentialValidationError, validate_and_hash_credentials


pytestmark = pytest.mark.usefixtures("forbid_database")


def _hash_verifies(encoded, candidate):
    try:
        return PasswordHash.recommended().verify(candidate, encoded)
    except Exception:
        pytest.fail("Hash verification failed unexpectedly", pytrace=False)


@pytest.mark.parametrize("length", [15, 128])
@pytest.mark.parametrize("codepoint", [0x61, 0x1F697], ids=["ascii", "astral"])
def test_normalized_codepoint_boundaries_are_accepted(length, codepoint):
    secret = SecretStr(chr(codepoint) * length)
    encoded = validate_and_hash_credentials(secret, secret)
    verified = _hash_verifies(encoded, chr(codepoint) * length)
    assert verified
    uses_argon2 = encoded.startswith("$argon2id$")
    assert uses_argon2


@pytest.mark.parametrize("field", ["password", "password_confirmation"])
@pytest.mark.parametrize("length", [14, 129])
def test_outside_length_boundaries_are_rejected(field, length, monkeypatch):
    def unexpected_hash(*args, **kwargs):
        pytest.fail("Invalid credentials reached the hasher", pytrace=False)

    monkeypatch.setattr(security._PASSWORD_HASH, "hash", unexpected_hash)
    fields = {
        "password": SecretStr(chr(0x61) * 15),
        "password_confirmation": SecretStr(chr(0x61) * 15),
    }
    fields[field] = SecretStr(chr(0x61) * length)
    with pytest.raises(CredentialValidationError) as caught:
        validate_and_hash_credentials(**fields)
    correct_field = caught.value.field == field
    safe_message = str(caught.value) == "Use between 15 and 128 characters."
    assert correct_field
    assert safe_message


@pytest.mark.parametrize("length", [15, 128])
def test_nfc_normalization_precedes_matching_length_and_hashing(length):
    decomposed = SecretStr((chr(0x65) + chr(0x301)) * length)
    composed = SecretStr(chr(0xE9) * length)
    encoded = validate_and_hash_credentials(decomposed, composed)
    verified = _hash_verifies(encoded, chr(0xE9) * length)
    assert verified
    original_verified = _hash_verifies(encoded, (chr(0x65) + chr(0x301)) * length)
    assert not original_verified


def test_nfc_length_is_checked_after_normalization():
    secret = SecretStr((chr(0x65) + chr(0x301)) * 14)
    with pytest.raises(CredentialValidationError) as caught:
        validate_and_hash_credentials(secret, secret)
    correct_field = caught.value.field == "password"
    assert correct_field


def test_passwords_must_match_without_case_folding():
    with pytest.raises(CredentialValidationError) as caught:
        validate_and_hash_credentials(
            SecretStr(chr(0x61) * 15), SecretStr(chr(0x41) * 15)
        )
    correct_field = caught.value.field == "password_confirmation"
    safe_message = str(caught.value) == "Passwords must match."
    assert correct_field
    assert safe_message


@pytest.mark.parametrize("codepoint", [0x20, 0x41], ids=["spaces", "uppercase"])
def test_password_has_no_composition_rule_or_case_space_conversion(codepoint):
    secret = SecretStr(chr(codepoint) * 15)
    encoded = validate_and_hash_credentials(secret, secret)
    verified = _hash_verifies(encoded, chr(codepoint) * 15)
    assert verified
    changed_verified = _hash_verifies(encoded, chr(0x61) * 15)
    assert not changed_verified


def test_leading_internal_and_trailing_spaces_are_preserved():
    secret = SecretStr(chr(0x20) + (chr(0x61) + chr(0x20)) * 7)
    encoded = validate_and_hash_credentials(secret, secret)
    verified = _hash_verifies(encoded, chr(0x20) + (chr(0x61) + chr(0x20)) * 7)
    assert verified
    trimmed_verified = _hash_verifies(encoded, chr(0x61) + (chr(0x20) + chr(0x61)) * 6)
    assert not trimmed_verified


def test_salts_differ_and_wrong_passwords_do_not_verify():
    secret = SecretStr(chr(0x61) * 15)
    first = validate_and_hash_credentials(secret, secret)
    second = validate_and_hash_credentials(secret, secret)
    independent_salts = first != second
    assert independent_salts
    wrong_verified = _hash_verifies(first, chr(0x62) * 15)
    assert not wrong_verified


@pytest.mark.parametrize("field", ["password", "password_confirmation"])
def test_invalid_unicode_is_rejected_without_exposing_values(field):
    fields = {
        "password": SecretStr(chr(0x61) * 15),
        "password_confirmation": SecretStr(chr(0x61) * 15),
    }
    fields[field] = SecretStr(chr(0xD800) * 15)
    with pytest.raises(CredentialValidationError) as caught:
        validate_and_hash_credentials(**fields)
    correct_field = caught.value.field == field
    safe_message = str(caught.value) == "Enter valid Unicode characters."
    assert correct_field
    assert safe_message


def test_credential_failure_and_logs_do_not_expose_plaintext(caplog):
    secret = SecretStr(chr(0x61) * 14)
    with pytest.raises(CredentialValidationError) as caught:
        validate_and_hash_credentials(secret, secret)
    representations = (str(caught.value), repr(caught.value), repr(vars(caught.value)), caplog.text)
    leaked = any(chr(0x61) * 14 in value for value in representations)
    assert not leaked


def test_imports_do_not_connect_to_postgresql():
    script = """
import psycopg
def unexpected(*args, **kwargs):
    raise AssertionError('Credential imports attempted a database connection')
psycopg.connect = unexpected
import app.schemas
import app.security
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    imported_without_database = result.returncode == 0
    assert imported_without_database
