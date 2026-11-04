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
)


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
