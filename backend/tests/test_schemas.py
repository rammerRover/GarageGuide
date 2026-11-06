from datetime import datetime, timezone

import pytest
from pydantic import EmailStr, SecretStr, TypeAdapter, ValidationError

from app.schemas import AccountEmail, RegistrationRequest, RegistrationResponse


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.fixture
def secret():
    return SecretStr(chr(0x61) * 15)


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        (" \tUser@EXAMPLE.COM\n", "user@example.com"),
        ("First.Last+garage@Example.COM", "first.last+garage@example.com"),
        ("Te\u0301st@EXAMPLE.COM", "t\u00e9st@example.com"),
    ],
    ids=["whitespace-and-case", "preserve-dots-and-alias", "validator-normalization"],
)
def test_shared_email_process(email, expected, secret):
    request = RegistrationRequest(
        email=email, password=secret, password_confirmation=secret
    )
    assert request.email == expected
    assert TypeAdapter(AccountEmail).validate_python(email) == expected


def test_email_is_trimmed_before_emailstr_validation(monkeypatch):
    original = EmailStr._validate
    observed = []

    def record_input(cls, value):
        observed.append(value)
        return original(value)

    monkeypatch.setattr(EmailStr, "_validate", classmethod(record_input))
    adapter = TypeAdapter(AccountEmail)
    assert adapter.validate_python(" \tUser@EXAMPLE.COM\n") == "user@example.com"
    assert observed == ["User@EXAMPLE.COM"]


@pytest.mark.parametrize("email", ["", "invalid", "a@", None, 42, b"a@example.com"])
def test_request_rejects_invalid_email(email, secret):
    with pytest.raises(ValidationError):
        RegistrationRequest(
            email=email, password=secret, password_confirmation=secret
        )


def test_password_fields_are_secretstr_and_masked(secret):
    request = RegistrationRequest(
        email="user@example.com", password=secret, password_confirmation=secret
    )
    fields_are_secret = isinstance(request.password, SecretStr) and isinstance(
        request.password_confirmation, SecretStr
    )
    assert fields_are_secret
    representations = (
        repr(request), str(request), repr(request.model_dump()), request.model_dump_json()
    )
    leaked = any(chr(0x61) * 15 in value for value in representations)
    assert not leaked


@pytest.mark.parametrize("field", ["password", "password_confirmation"])
@pytest.mark.parametrize(
    "invalid",
    [None, 42, True, [], {}, bytes([0x61] * 15)],
    ids=[
        "absent-value", "numeric-value", "boolean-value",
        "sequence-value", "mapping-value", "binary-value",
    ],
)
def test_password_fields_reject_non_string_values(field, invalid, secret):
    fields = {
        "email": "user@example.com",
        "password": secret,
        "password_confirmation": secret,
    }
    fields[field] = invalid
    with pytest.raises(ValidationError):
        RegistrationRequest(**fields)


@pytest.mark.parametrize("field", ["email", "password", "password_confirmation"])
def test_all_request_fields_are_required(field, secret):
    fields = {
        "email": "user@example.com",
        "password": secret,
        "password_confirmation": secret,
    }
    del fields[field]
    with pytest.raises(ValidationError):
        RegistrationRequest(**fields)


def test_validation_exception_text_hides_raw_password_input(secret):
    with pytest.raises(ValidationError) as caught:
        RegistrationRequest(
            email="user@example.com",
            password={"value": chr(0x61) * 15},
            password_confirmation=secret,
        )
    leaked = chr(0x61) * 15 in str(caught.value)
    assert not leaked


def test_response_exposes_only_public_fields(secret):
    response = RegistrationResponse(
        id=1,
        email="User@EXAMPLE.COM",
        created_at=datetime(2026, 11, 4, tzinfo=timezone.utc),
        password_hash="excluded",
        password=secret,
        password_confirmation=secret,
    )
    result = response.model_dump(mode="json")
    only_public_fields = set(result) == {"id", "email", "created_at"}
    assert only_public_fields
    assert result == {
        "id": 1,
        "email": "user@example.com",
        "created_at": "2026-11-04T00:00:00Z",
    }


@pytest.mark.parametrize("user_id", [0, -1, True, "1"])
def test_response_requires_a_positive_integer_id(user_id):
    with pytest.raises(ValidationError):
        RegistrationResponse(
            id=user_id,
            email="user@example.com",
            created_at=datetime(2026, 11, 4, tzinfo=timezone.utc),
        )


def test_response_requires_a_timezone_aware_timestamp():
    with pytest.raises(ValidationError):
        RegistrationResponse(
            id=1, email="user@example.com", created_at=datetime(2026, 11, 4)
        )
