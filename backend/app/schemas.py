from typing import Annotated

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)

from app.security import validate_login_password


def _trim_email(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


AccountEmail = Annotated[
    EmailStr, BeforeValidator(_trim_email), AfterValidator(str.lower)
]


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(strict=True, hide_input_in_errors=True)

    email: AccountEmail
    password: SecretStr
    password_confirmation: SecretStr


class RegistrationResponse(BaseModel):
    id: int = Field(gt=0, strict=True)
    email: AccountEmail
    created_at: AwareDatetime


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True, hide_input_in_errors=True, extra="forbid")

    email: AccountEmail
    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        return validate_login_password(value)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(strict=True, hide_input_in_errors=True, extra="forbid")


class SessionResponse(BaseModel):
    user: RegistrationResponse
    expires_at: AwareDatetime
