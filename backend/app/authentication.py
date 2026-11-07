import logging

import psycopg
from fastapi import Depends, Request, Response
from fastapi.exceptions import HTTPException
from pydantic import SecretStr

from app import security, session_queries
from app.config import (
    AuthConfigurationError, AuthSettings, Settings, get_auth_settings, get_settings,
    is_loopback_host,
)


SESSION_COOKIE_NAME = "garageguide_session"
CSRF_HEADER = "X-GarageGuide-CSRF"
logger = logging.getLogger(__name__)


class AuthenticationFailure(HTTPException):
    def __init__(self, status_code: int, *, deleted_cookie: str | None = None):
        messages = {
            401: "Not authenticated.",
            403: "Request not allowed.",
            503: "Authentication unavailable. Please try again.",
            500: "Internal server error",
        }
        headers = {"Cache-Control": "no-store"}
        if deleted_cookie is not None:
            headers["Set-Cookie"] = deleted_cookie
        super().__init__(status_code=status_code, detail=messages[status_code], headers=headers)


class RequestPolicyError(ValueError):
    def __init__(self):
        super().__init__("Request not allowed.")


def validate_cookie_transport(request: Request, settings: AuthSettings) -> None:
    if not settings.cookie_secure:
        # ASGI's bound server address is independent of Host/forwarded headers.
        server = request.scope.get("server")
        if not server or not is_loopback_host(server[0]):
            raise RequestPolicyError()


def require_mutation_policy(request: Request, settings: AuthSettings) -> None:
    validate_cookie_transport(request, settings)
    origins = request.headers.getlist("origin")
    content_types = request.headers.getlist("content-type")
    markers = request.headers.getlist(CSRF_HEADER)
    if (
        len(origins) != 1 or origins[0] not in settings.trusted_frontend_origins
        or len(content_types) != 1
        or content_types[0].split(";", 1)[0].strip().lower() != "application/json"
        or markers != ["1"]
    ):
        raise RequestPolicyError()


def _cookie_attributes(settings: AuthSettings) -> dict:
    return {
        "path": "/", "secure": settings.cookie_secure,
        "httponly": True, "samesite": "lax",
    }


def set_session_cookie(
    response: Response, token: SecretStr, request: Request, settings: AuthSettings
) -> None:
    validate_cookie_transport(request, settings)
    response.set_cookie(
        SESSION_COOKIE_NAME, token.get_secret_value(), **_cookie_attributes(settings)
    )


def clear_session_cookie(
    response: Response, request: Request, settings: AuthSettings
) -> None:
    validate_cookie_transport(request, settings)
    response.delete_cookie(SESSION_COOKIE_NAME, **_cookie_attributes(settings))


def request_auth_settings(request: Request) -> AuthSettings:
    settings = getattr(request.state, "auth_settings", None)
    if settings is None:
        try:
            provider = request.app.dependency_overrides.get(get_auth_settings, get_auth_settings)
            settings = provider()
            validate_cookie_transport(request, settings)
        except AuthConfigurationError:
            raise AuthenticationFailure(503) from None
        except RequestPolicyError:
            raise AuthenticationFailure(403) from None
        request.state.auth_settings = settings
    return settings


def read_session_token(request: Request) -> SecretStr | None:
    return security.parse_session_token(request.cookies.get(SESSION_COOKIE_NAME))


def require_authenticated_session(
    request: Request, settings: Settings = Depends(get_settings),
    auth_settings: AuthSettings = Depends(request_auth_settings),
) -> session_queries.AuthenticatedSession:
    try:
        validate_cookie_transport(request, auth_settings)
        return session_queries.validate_and_extend_session(settings, read_session_token(request))
    except session_queries.InvalidSessionError:
        response = Response()
        clear_session_cookie(response, request, auth_settings)
        raise AuthenticationFailure(401, deleted_cookie=response.headers["set-cookie"]) from None
    except (psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
        logger.warning("Authentication database unavailable")
        raise AuthenticationFailure(503) from None
    except RequestPolicyError:
        raise
    except Exception:
        logger.error("Authentication failed unexpectedly")
        raise AuthenticationFailure(500) from None
