import hashlib
import re
import secrets
import unicodedata

from pydantic import SecretStr
from pwdlib import PasswordHash


_PASSWORD_HASH = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = _PASSWORD_HASH.hash(secrets.token_urlsafe(32))
_SESSION_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]\Z", re.ASCII)


class CredentialValidationError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


def _normalize_password(secret: SecretStr, field: str) -> str:
    value = unicodedata.normalize("NFC", secret.get_secret_value())
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise CredentialValidationError(field, "Enter valid Unicode characters.")
    if not 15 <= len(value) <= 128:
        raise CredentialValidationError(field, "Use between 15 and 128 characters.")
    return value


def validate_login_password(password: SecretStr) -> SecretStr:
    return SecretStr(_normalize_password(password, "password"))


def validate_and_hash_credentials(
    password: SecretStr, password_confirmation: SecretStr
) -> str:
    normalized = _normalize_password(password, "password")
    confirmation = _normalize_password(password_confirmation, "password_confirmation")
    if normalized != confirmation:
        raise CredentialValidationError(
            "password_confirmation", "Passwords must match."
        )
    return _PASSWORD_HASH.hash(normalized)


def verify_credentials(password: SecretStr, password_hash: str | None) -> bool:
    normalized = _normalize_password(password, "password")
    # Unknown accounts still do one Argon2 verification using the process-local hash.
    verified = _PASSWORD_HASH.verify(
        normalized, _DUMMY_PASSWORD_HASH if password_hash is None else password_hash
    )
    return verified and password_hash is not None


def generate_session_token() -> SecretStr:
    return SecretStr(secrets.token_urlsafe(32))


def parse_session_token(value: str | None) -> SecretStr | None:
    if not isinstance(value, str) or _SESSION_TOKEN_PATTERN.fullmatch(value) is None:
        return None
    return SecretStr(value)


def hash_session_token(token: SecretStr) -> str:
    value = token.get_secret_value()
    if parse_session_token(value) is None:
        raise ValueError("Invalid session token.")
    return hashlib.sha256(value.encode("ascii")).hexdigest()
