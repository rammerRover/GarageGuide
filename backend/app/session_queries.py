from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

import psycopg
from pydantic import SecretStr

from app import database, security
from app.config import Settings
from app.schemas import RegistrationResponse, SessionResponse


class InvalidSessionError(ValueError):
    def __init__(self):
        super().__init__("Not authenticated.")


@dataclass(frozen=True)
class AuthenticatedSession:
    user: RegistrationResponse
    session_id: int
    expires_at: datetime

    def public_response(self) -> SessionResponse:
        return SessionResponse(user=self.user, expires_at=self.expires_at)


@dataclass(frozen=True)
class IssuedSession:
    session: AuthenticatedSession
    token: SecretStr = field(repr=False)


def _lock_session(connection: psycopg.Connection, token_hash: str) -> int | None:
    row = connection.execute(
        "SELECT id FROM public.user_sessions WHERE token_hash = %s FOR UPDATE",
        (token_hash,),
    ).fetchone()
    return row[0] if row is not None else None


def _database_time(connection: psycopg.Connection) -> datetime:
    return connection.execute("SELECT clock_timestamp()").fetchone()[0]


def _revoke_locked(
    connection: psycopg.Connection, session_id: int, now: datetime, *, valid_only: bool
) -> None:
    validity = (
        " AND %s < expires_at AND %s < created_at + INTERVAL '8 hours'"
        if valid_only else ""
    )
    parameters = (now, session_id, now, now) if valid_only else (now, session_id)
    connection.execute(
        "UPDATE public.user_sessions SET revoked_at = %s "
        "WHERE id = %s AND revoked_at IS NULL" + validity,
        parameters,
    )


def _remove_invalid_sessions(
    connection: psycopg.Connection, user_id: int, now: datetime
) -> None:
    connection.execute(
        "DELETE FROM public.user_sessions WHERE user_id = %s "
        "AND (revoked_at IS NOT NULL OR expires_at <= %s "
        "OR created_at + INTERVAL '8 hours' <= %s)",
        (user_id, now, now),
    )


def create_session(
    settings: Settings, *, user: RegistrationResponse,
    presented_token: SecretStr | None = None,
    prepare_response: Callable[[IssuedSession], None] | None = None,
) -> IssuedSession:
    token = security.generate_session_token()
    token_hash = security.hash_session_token(token)
    previous_hash = security.hash_session_token(presented_token) if presented_token else None
    with database.connect_database(settings, read_only=False) as connection:
        if previous_hash is not None:
            previous_id = _lock_session(connection, previous_hash)
            if previous_id is not None:
                _revoke_locked(connection, previous_id, _database_time(connection), valid_only=True)
        _remove_invalid_sessions(connection, user.id, _database_time(connection))
        row = connection.execute(
            "WITH stamp AS (SELECT clock_timestamp() AS now) "
            "INSERT INTO public.user_sessions (user_id, token_hash, created_at, expires_at) "
            "SELECT %s, %s, now, now + INTERVAL '30 minutes' FROM stamp "
            "RETURNING id, expires_at",
            (user.id, token_hash),
        ).fetchone()
        if row is None:
            raise RuntimeError("Session insertion returned no record")
        result = IssuedSession(AuthenticatedSession(user, row[0], row[1]), token)
        result.session.public_response().model_dump_json()
        # Step 3 can serialize the HTTP body and cookie before commit without sending them.
        if prepare_response is not None:
            prepare_response(result)
    return result


def validate_and_extend_session(
    settings: Settings, token: SecretStr | None
) -> AuthenticatedSession:
    if token is None:
        raise InvalidSessionError()
    token_hash = security.hash_session_token(token)
    with database.connect_database(settings, read_only=False) as connection:
        session_id = _lock_session(connection, token_hash)
        if session_id is None:
            raise InvalidSessionError()
        # Transaction/statement start time could predate a row-lock wait.
        now = _database_time(connection)
        row = connection.execute(
            "UPDATE public.user_sessions "
            "SET expires_at = LEAST(%s + INTERVAL '30 minutes', created_at + INTERVAL '8 hours') "
            "WHERE id = %s AND revoked_at IS NULL AND %s < expires_at "
            "AND %s < created_at + INTERVAL '8 hours' RETURNING user_id, expires_at",
            (now, session_id, now, now),
        ).fetchone()
        if row is None:
            raise InvalidSessionError()
        user = connection.execute(
            "SELECT id, email, created_at FROM public.users WHERE id = %s", (row[0],)
        ).fetchone()
        if user is None:
            raise InvalidSessionError()
        result = AuthenticatedSession(
            RegistrationResponse(id=user[0], email=user[1], created_at=user[2]), session_id, row[1]
        )
        result.public_response().model_dump_json()
    return result


def revoke_session(settings: Settings, token: SecretStr | None) -> None:
    if token is None:
        return
    token_hash = security.hash_session_token(token)
    with database.connect_database(settings, read_only=False) as connection:
        session_id = _lock_session(connection, token_hash)
        if session_id is not None:
            _revoke_locked(connection, session_id, _database_time(connection), valid_only=False)
