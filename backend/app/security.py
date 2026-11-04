import unicodedata

from pydantic import SecretStr
from pwdlib import PasswordHash


_PASSWORD_HASH = PasswordHash.recommended()


class CredentialValidationError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


def validate_and_hash_credentials(
    password: SecretStr, password_confirmation: SecretStr
) -> str:
    values = {
        "password": unicodedata.normalize("NFC", password.get_secret_value()),
        "password_confirmation": unicodedata.normalize(
            "NFC", password_confirmation.get_secret_value()
        ),
    }
    for field, value in values.items():
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise CredentialValidationError(field, "Enter valid Unicode characters.")
        if not 15 <= len(value) <= 128:
            raise CredentialValidationError(
                field, "Use between 15 and 128 characters."
            )
    if values["password"] != values["password_confirmation"]:
        raise CredentialValidationError(
            "password_confirmation", "Passwords must match."
        )
    return _PASSWORD_HASH.hash(values["password"])
