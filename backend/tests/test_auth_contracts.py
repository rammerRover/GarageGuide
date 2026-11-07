from datetime import datetime, timezone

import pytest
from pydantic import SecretStr, ValidationError

from app.schemas import LoginRequest, LogoutRequest, RegistrationRequest, SessionResponse


pytestmark = pytest.mark.usefixtures("forbid_database")


@pytest.mark.parametrize("email", [" \tUser@EXAMPLE.COM\n", "Te\u0301st@EXAMPLE.COM"])
def test_login_and_registration_use_identical_shared_email_processing(email):
    secret = SecretStr(chr(0x61) * 15)
    login = LoginRequest(email=email, password=secret)
    registration = RegistrationRequest(email=email, password=secret, password_confirmation=secret)
    assert login.email == registration.email


def test_login_normalizes_password_and_masks_all_normal_representations():
    request = LoginRequest(email="user@example.com", password=(chr(0x65) + chr(0x301)) * 15)
    normalized = request.password == SecretStr(chr(0xE9) * 15)
    assert normalized
    safe = all(
        chr(0xE9) * 15 not in value
        for value in (repr(request), str(request), repr(request.model_dump()), request.model_dump_json())
    )
    assert safe


@pytest.mark.parametrize("change", [
    {"email": "invalid"}, {"password": None}, {"password": 42}, {"password": []},
    {"id": 1}, {"password_confirmation": "ignored-is-not-allowed"},
    {"token": "ignored-is-not-allowed"},
])
def test_login_rejects_invalid_credentials_and_extra_identity_controls(change):
    fields = {"email": "user@example.com", "password": SecretStr(chr(0x61) * 15)}
    fields.update(change)
    with pytest.raises(ValidationError):
        LoginRequest(**fields)


@pytest.mark.parametrize("field", ["email", "password"])
def test_login_requires_both_fields(field):
    fields = {"email": "user@example.com", "password": SecretStr(chr(0x61) * 15)}
    del fields[field]
    with pytest.raises(ValidationError):
        LoginRequest(**fields)


@pytest.mark.parametrize("kind", ["short", "long", "surrogate", "nfc-short"])
def test_login_schema_rejects_invalid_passwords_before_lookup(kind):
    values = {
        "short": chr(0x61) * 14, "long": chr(0x61) * 129,
        "surrogate": chr(0xD800) * 15, "nfc-short": (chr(0x65) + chr(0x301)) * 14,
    }
    with pytest.raises(ValidationError) as caught:
        LoginRequest(email="user@example.com", password=values[kind])
    leaked = values[kind] in str(caught.value)
    assert not leaked


def test_logout_contract_accepts_only_an_empty_object():
    assert LogoutRequest().model_dump() == {}
    with pytest.raises(ValidationError):
        LogoutRequest(user_id=1)


def test_session_response_whitelists_only_public_user_and_expiration():
    timestamp = datetime(2026, 11, 6, tzinfo=timezone.utc)
    response = SessionResponse(
        user={"id": 1, "email": "User@EXAMPLE.COM", "created_at": timestamp,
              "password_hash": "excluded", "token_hash": "excluded"},
        expires_at=timestamp, token="excluded", session_id=2,
    )
    assert response.model_dump(mode="json") == {
        "user": {"id": 1, "email": "user@example.com", "created_at": "2026-11-06T00:00:00Z"},
        "expires_at": "2026-11-06T00:00:00Z",
    }


@pytest.mark.parametrize("field", ["created_at", "expires_at"])
def test_session_response_requires_aware_timestamps(field):
    timestamp = datetime(2026, 11, 6, tzinfo=timezone.utc)
    fields = {"user": {"id": 1, "email": "user@example.com", "created_at": timestamp},
              "expires_at": timestamp}
    if field == "created_at":
        fields["user"][field] = timestamp.replace(tzinfo=None)
    else:
        fields[field] = timestamp.replace(tzinfo=None)
    with pytest.raises(ValidationError):
        SessionResponse(**fields)
