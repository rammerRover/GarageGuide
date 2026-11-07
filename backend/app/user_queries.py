from datetime import datetime

import psycopg

from app import database, security
from app.config import Settings
from app.schemas import LoginRequest, RegistrationResponse


EMAIL_UNIQUE_CONSTRAINT = "users_email_key"


class DuplicateEmailError(ValueError):
    def __init__(self):
        super().__init__("An account with this email already exists.")


def find_user_id(connection: psycopg.Connection, email: str) -> int | None:
    row = connection.execute(
        "SELECT id FROM public.users WHERE email = %s", (email,)
    ).fetchone()
    return row[0] if row is not None else None


def insert_user(
    connection: psycopg.Connection, email: str, password_hash: str
) -> tuple[int, str, datetime]:
    row = connection.execute(
        "INSERT INTO public.users (email, password_hash) VALUES (%s, %s) "
        "RETURNING id, email, created_at",
        (email, password_hash),
    ).fetchone()
    if row is None:
        raise RuntimeError("Account insertion returned no public record")
    return row


def create_user(
    settings: Settings, *, email: str, password_hash: str
) -> tuple[int, str, datetime]:
    try:
        with database.connect_database(settings, read_only=False) as connection:
            if find_user_id(connection, email) is not None:
                raise DuplicateEmailError()
            user = insert_user(connection, email, password_hash)
    except psycopg.errors.UniqueViolation as error:
        # Translate only after the connection context has rolled back and closed.
        if error.diag.constraint_name == EMAIL_UNIQUE_CONSTRAINT:
            raise DuplicateEmailError() from None
        raise
    return user


def verify_user_credentials(
    settings: Settings, credentials: LoginRequest
) -> RegistrationResponse | None:
    # Keep stored credentials inside this verification boundary; only public data leaves.
    with database.connect_database(settings, read_only=True) as connection:
        row = connection.execute(
            "SELECT id, email, created_at, password_hash FROM public.users WHERE email = %s",
            (credentials.email,),
        ).fetchone()
    verified = security.verify_credentials(
        credentials.password, row[3] if row is not None else None
    )
    if not verified:
        return None
    return RegistrationResponse(id=row[0], email=row[1], created_at=row[2])
